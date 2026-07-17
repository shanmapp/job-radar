import concurrent.futures
import subprocess
import threading
import psutil
from datetime import datetime
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_cors import CORS
from crawlers.f1_http_crawler import crawl_aston_martin, crawl_ferrari
from crawlers.f1_selenium_crawler import crawl_mclaren, crawl_red_bull, crawl_mercedes
from crawlers.f1_extra_http_crawler import crawl_haas
from crawlers.f1_extra_selenium_crawler import crawl_alpine, crawl_williams, crawl_cadillac, crawl_sauber, crawl_formula1
from crawlers.soccer_http_crawler import crawl_arsenal, crawl_liverpool, crawl_chelsea_cfcw
from crawlers.soccer_selenium_crawler import crawl_man_city, crawl_chelsea, crawl_tottenham, crawl_bayern, crawl_psg
from crawlers.brands_http_crawler import crawl_all_brands_http
from crawlers.brands_selenium_crawler import crawl_all_brands_selenium
from crawlers.health import check_sources
from crawlers.filters import drain_near_misses
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
    crawlers = [crawl_arsenal, crawl_liverpool, crawl_man_city, crawl_chelsea, crawl_chelsea_cfcw, crawl_tottenham, crawl_bayern, crawl_psg]

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


def send_near_miss_digest():
    """Weekly Telegram digest of near-misses (in-scope location, title failed
    the role keywords). Makes silent filter drops reviewable — the NBA
    internship, PL Kicks and Amplify U misses would all have shown up here."""
    try:
        items = drain_near_misses()
    except Exception as e:
        print(f"Near-miss drain error: {e}")
        return
    if not items:
        return
    _CAP = 80  # keep the Telegram message readable
    lines = "\n".join(f"- {title} ({loc})" if loc else f"- {title}"
                      for title, loc in items[:_CAP])
    extra = f"\n…and {len(items) - _CAP} more" if len(items) > _CAP else ""
    try:
        send_alert("*Weekly near-miss digest*\n"
                   f"{len(items)} in-scope jobs were dropped by the role-keyword "
                   "filter this week. If any look interesting, the keyword list "
                   f"needs widening:\n{lines}{extra}")
    except Exception as e:
        print(f"Near-miss digest send error: {e}")


@app.route('/nearmisses', methods=['GET'])
def handle_near_misses():
    concurrent.futures.ThreadPoolExecutor(max_workers=1).submit(send_near_miss_digest)
    return {"message": "Near-miss digest queued"}, 202


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

def _kill_stray_chrome():
    try:
        subprocess.run(["pkill", "-f", "google-chrome"], capture_output=True)
        subprocess.run(["pkill", "-f", "chromedriver"], capture_output=True)
    except Exception:
        pass

def smart_crawl(fn):
    if is_quiet_hours():
        print(f"Quiet hours (11pm–6am EST) — skipping {fn.__name__}")
        return
    minutes = 15 if is_peak_hours() else 60
    print(f"Running {fn.__name__} (next check in {minutes}min)")
    with _crawl_lock:
        fn()
        _kill_stray_chrome()
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
    if not scheduler.get_job("near_miss_digest"):
        scheduler.add_job(send_near_miss_digest, 'cron', day_of_week='sun',
                          hour=10, minute=0, timezone=EST_TZ,
                          id="near_miss_digest")
        print("Scheduled weekly near-miss digest (Sun 10am EST)")

schedule_all_crawlers()

@app.route('/main', methods=['POST'])
def handle_check_periodically():
    schedule_all_crawlers()
    return {"message": "Crawlers scheduled — 15min (peak) / 60min (off-peak)"}, 200

if __name__ == '__main__':
    app.run(debug=False, port=8000)


