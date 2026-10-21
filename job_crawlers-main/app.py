import concurrent.futures
import subprocess
import threading
import psutil
from datetime import datetime
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_cors import CORS
from crawlers.f1_http_crawler import crawl_aston_martin, crawl_ferrari, crawl_red_bull, crawl_mercedes
from crawlers.f1_selenium_crawler import crawl_mclaren
from crawlers.f1_extra_http_crawler import crawl_haas, crawl_cadillac
from crawlers.f1_extra_selenium_crawler import crawl_alpine, crawl_williams, crawl_sauber, crawl_formula1
from crawlers.soccer_http_crawler import crawl_arsenal, crawl_man_utd, crawl_liverpool, crawl_chelsea_cfcw, crawl_psg, crawl_man_city, crawl_bayern
from crawlers.soccer_selenium_crawler import crawl_chelsea, crawl_tottenham
from crawlers.brands_http_crawler import crawl_all_brands_http
from crawlers.brands_selenium_crawler import crawl_all_brands_selenium
from crawlers.health import check_sources
from crawlers.silent_zero import run_daily_zero_check
from database.mongo import ensure_company_document, add_jobs_if_not_exists
from email_config.email_setup import send_email, send_alert

app = Flask(__name__)
CORS(app)

scheduler = BackgroundScheduler()
scheduler.start()

def _run_crawler(crawler):
    mem = psutil.virtual_memory()
    if mem.percent > 85:
        print(f"Skipping {crawler.__name__} — memory at {mem.percent:.0f}%")
        return []
    try:
        return crawler() or []
    except Exception as e:
        print(f"Crawler error ({crawler.__name__}): {e}")
        return []

def _save_jobs(jobs_list):
    all_new_jobs = []
    for jobs in jobs_list:
        if jobs:
            try:
                # A batch can mix companies (brand crawlers return one big list).
                # Every company needs its document, or add_jobs_if_not_exists's
                # update_one matches nothing and silently drops the job.
                for company in {job["company"] for job in jobs}:
                    ensure_company_document(company)
                all_new_jobs.extend(add_jobs_if_not_exists(jobs))
            except Exception as e:
                print(f"DB error: {e}")
    return all_new_jobs

def check_f1_jobs():
    crawlers = [
        crawl_aston_martin, crawl_ferrari,
        crawl_mclaren, crawl_red_bull, crawl_mercedes,
        crawl_alpine, crawl_williams, crawl_cadillac, crawl_sauber,
        crawl_haas, crawl_formula1,
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        results = list(executor.map(_run_crawler, crawlers))

    all_new_jobs = _save_jobs(results)

    if all_new_jobs:
        send_email(all_new_jobs)
        print(f"Sent {len(all_new_jobs)} new F1 jobs via Telegram")
    else:
        print("No new F1 jobs found")

def check_soccer_jobs():
    crawlers = [crawl_arsenal, crawl_liverpool, crawl_man_city, crawl_man_utd, crawl_chelsea, crawl_chelsea_cfcw, crawl_tottenham, crawl_bayern, crawl_psg]

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        results = list(executor.map(_run_crawler, crawlers))

    all_new_jobs = _save_jobs(results)

    if all_new_jobs:
        send_email(all_new_jobs)
        print(f"Sent {len(all_new_jobs)} new soccer jobs via Telegram")
    else:
        print("No new soccer jobs found")

@app.route('/f1', methods=['GET'])
def handle_check_f1():
    concurrent.futures.ThreadPoolExecutor(max_workers=1).submit(check_f1_jobs)
    return {"message": "F1 job check started"}, 202

@app.route('/soccer', methods=['GET'])
def handle_check_soccer():
    concurrent.futures.ThreadPoolExecutor(max_workers=1).submit(check_soccer_jobs)
    return {"message": "Soccer job check started"}, 202


def check_brand_jobs():
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        results = list(executor.map(_run_crawler, [crawl_all_brands_http, crawl_all_brands_selenium]))

    all_new_jobs = _save_jobs(results)
    if all_new_jobs:
        send_email(all_new_jobs)
        print(f"Sent {len(all_new_jobs)} new brand jobs via Telegram")
    else:
        print("No new brand jobs found")


@app.route('/brands', methods=['GET'])
def handle_check_brands():
    concurrent.futures.ThreadPoolExecutor(max_workers=1).submit(check_brand_jobs)
    return {"message": "Brand job check started"}, 202


def check_crawler_health():
    """Probe every crawler source host; alert on Telegram if any are dead.

    A dead source otherwise fails silently (caught exception, empty result)
    and looks identical to "no matching jobs" — this is how a Moët Hennessy
    posting was missed. Alerts repeat daily until the source is fixed."""
    try:
        dead = check_sources()
    except Exception as e:
        print(f"Health check error: {e}")
        return
    if dead:
        lines = "\n".join(f"- `{host}`: {err}" for host, err in sorted(dead.items()))
        try:
            send_alert(f"*Crawler health alert*\nUnreachable job sources:\n{lines}")
        except Exception as e:
            print(f"Health alert send error: {e}")


# If no crawl pass completes for this long, the scheduler is effectively dead
# (wedged crawl, crashed thread). Must exceed the ~7h quiet-hours gap plus one
# off-peak interval, so a normal overnight lull never trips it.
_STALENESS_THRESHOLD_H = 10


def check_crawl_freshness():
    """Alert if no crawl pass has completed within the staleness threshold.

    The source-health check only probes host reachability — it reported 80/80
    healthy while a wedged LVMH crawl froze every scheduled run for 2.5 days
    (2026-08-24). This watches the actual heartbeat instead, so a stalled
    scheduler is caught within hours rather than by a human noticing no emails."""
    global _staleness_alerted
    age_h = (datetime.now(EST_TZ) - _last_crawl_success).total_seconds() / 3600
    if age_h < _STALENESS_THRESHOLD_H:
        _staleness_alerted = False
        return
    if _staleness_alerted:
        return  # already alerted for this episode; don't spam hourly
    try:
        send_alert(f"*Crawler stalled*\nNo crawl pass has completed in "
                   f"{age_h:.1f}h (last success {_last_crawl_success:%Y-%m-%d %H:%M %Z}). "
                   f"The scheduler is likely wedged — restart `job-radar`.")
        _staleness_alerted = True
    except Exception as e:
        print(f"Staleness alert send error: {e}")


def send_silent_zero_alert():
    """Daily: flag crawlers whose job board has come back empty 3 checks running.
    Uses raw (pre-filter) board size, so "no in-scope roles" (which is normal for
    most companies) does NOT trip it — only a genuinely empty/broken board does."""
    try:
        dead = run_daily_zero_check()
    except Exception as e:
        print(f"Silent-zero check error: {e}")
        return
    if not dead:
        return
    lines = "\n".join(f"* {company}" for company in dead)
    try:
        send_alert(f"These companies are returning 0 jobs\n\n{lines}")
    except Exception as e:
        print(f"Silent-zero alert send error: {e}")


@app.route('/silentzero', methods=['GET'])
def handle_silent_zero():
    concurrent.futures.ThreadPoolExecutor(max_workers=1).submit(send_silent_zero_alert)
    return {"message": "Silent-zero check queued"}, 202


@app.route('/health', methods=['GET'])
def handle_check_health():
    concurrent.futures.ThreadPoolExecutor(max_workers=1).submit(check_crawler_health)
    return {"message": "Source health check started"}, 202

UK_TZ = pytz.timezone("Europe/London")
EST_TZ = pytz.timezone("America/New_York")

def is_quiet_hours():
    now = datetime.now(EST_TZ)
    return now.hour >= 23 or now.hour < 6

def is_peak_hours():
    now = datetime.now(UK_TZ)
    return now.weekday() < 5 and 8 <= now.hour < 18  # Mon-Fri 8am-6pm UK

_crawl_lock = threading.Lock()

# Heartbeat: EST timestamp of the last crawl pass that finished within budget.
# Seeded at import so a freshly (re)started process isn't instantly "stale".
_last_crawl_success = datetime.now(EST_TZ)
# Alert only once per staleness episode, reset when a crawl succeeds again.
_staleness_alerted = False

def _kill_stray_chrome():
    try:
        subprocess.run(["pkill", "-f", "google-chrome"], capture_output=True)
        subprocess.run(["pkill", "-f", "chromedriver"], capture_output=True)
    except Exception:
        pass

# Max wall-clock time for one crawl pass. A healthy full brand/F1/soccer pass
# finishes in a few minutes; anything past this is a wedged Chrome or a network
# call with no timeout. Bounding it here means a stuck crawler can never again
# hold the scheduler's single instance slot indefinitely (a hung LVMH crawl
# froze every hourly run for 2.5 days on 2026-08-24).
_CRAWL_BUDGET_S = 25 * 60


def _run_with_budget(fn):
    """Run fn() in a worker thread, returning True if it finished within the
    budget, False if it timed out. Python can't force-kill the thread, but
    _kill_stray_chrome() makes any wedged Selenium call raise (thanks to the
    driver's 90s command timeout) so the lingering thread unwinds on its own."""
    done = threading.Event()

    def target():
        try:
            fn()
        finally:
            done.set()

    threading.Thread(target=target, name=f"crawl-{fn.__name__}", daemon=True).start()
    return done.wait(_CRAWL_BUDGET_S)


def smart_crawl(fn):
    if is_quiet_hours():
        print(f"Quiet hours (11pm–6am EST) — skipping {fn.__name__}")
        return
    minutes = 15 if is_peak_hours() else 60
    print(f"Running {fn.__name__} (next check in {minutes}min)")
    # acquire with a timeout instead of `with _crawl_lock:` so a previous pass
    # that is still wedged can never block this call forever.
    if not _crawl_lock.acquire(timeout=_CRAWL_BUDGET_S):
        print(f"{fn.__name__}: previous crawl still running after "
              f"{_CRAWL_BUDGET_S // 60}min — killing stray Chrome, skipping this run")
        _kill_stray_chrome()
    else:
        try:
            if _run_with_budget(fn):
                global _last_crawl_success, _staleness_alerted
                _last_crawl_success = datetime.now(EST_TZ)
                _staleness_alerted = False
            else:
                print(f"{fn.__name__}: exceeded {_CRAWL_BUDGET_S // 60}min budget — "
                      f"killing stray Chrome so the crawl thread unwinds")
        finally:
            _kill_stray_chrome()
            _crawl_lock.release()
    job_id = f"smart_{fn.__name__}"
    scheduler.reschedule_job(job_id, trigger='interval', minutes=minutes)

def schedule_all_crawlers():
    crawlers = [check_f1_jobs, check_soccer_jobs, check_brand_jobs]
    initial_interval = 15 if is_peak_hours() else 60
    for fn in crawlers:
        job_id = f"smart_{fn.__name__}"
        if not scheduler.get_job(job_id):
            scheduler.add_job(
                smart_crawl,
                'interval',
                minutes=initial_interval,
                args=[fn],
                id=job_id
            )
            print(f"Scheduled {fn.__name__} (interval: {initial_interval}min)")
    if not scheduler.get_job("source_health"):
        scheduler.add_job(check_crawler_health, 'cron', hour=9, minute=0,
                          timezone=EST_TZ, id="source_health")
        print("Scheduled daily source health check (9am EST)")
    if not scheduler.get_job("crawl_freshness"):
        scheduler.add_job(check_crawl_freshness, 'interval', hours=1,
                          id="crawl_freshness")
        print("Scheduled hourly crawl-freshness watchdog")
    # Daily silent-zero alert disabled 2026-08-01 (user request): after the
    # Workday total-clobber and LVMH NameError fixes, the remaining standing
    # flags are genuinely-empty small boards (LOLA, Wolff Olins, Jackman,
    # Siegel+Gale, Mojang) and General Mills' permanent zero during its iCIMS
    # migration — all noise, no signal. The detector + /silentzero endpoint
    # stay available for manual on-demand checks; only the auto-send is off.
    # if not scheduler.get_job("silent_zero"):
    #     scheduler.add_job(send_silent_zero_alert, 'cron', hour=9, minute=30,
    #                       timezone=EST_TZ, id="silent_zero")
    #     print("Scheduled daily silent-zero check (9:30am EST)")

schedule_all_crawlers()

@app.route('/main', methods=['POST'])
def handle_check_periodically():
    schedule_all_crawlers()
    return {"message": "Crawlers scheduled — 15min (peak) / 60min (off-peak)"}, 200

if __name__ == '__main__':
    app.run(debug=False, port=8000)


