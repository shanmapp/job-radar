import asyncio
import concurrent.futures
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request
from flask_cors import CORS
from crawlers.amazon_crawler import run_crawler_for_amazon
from crawlers.f1_http_crawler import crawl_aston_martin, crawl_ferrari
from crawlers.f1_selenium_crawler import crawl_mclaren, crawl_red_bull, crawl_mercedes
from crawlers.f1_extra_http_crawler import crawl_haas
from crawlers.f1_extra_selenium_crawler import crawl_alpine, crawl_williams, crawl_cadillac, crawl_sauber, crawl_formula1
from crawlers.soccer_http_crawler import crawl_arsenal, crawl_liverpool
from crawlers.soccer_selenium_crawler import crawl_man_city, crawl_chelsea, crawl_tottenham, crawl_bayern, crawl_psg
from crawlers.brands_http_crawler import crawl_all_brands_http
from crawlers.brands_selenium_crawler import crawl_all_brands_selenium
from database.mongo import ensure_company_document, add_jobs_if_not_exists
from email_config.email_setup import send_email

app = Flask(__name__)
CORS(app)

scheduler = BackgroundScheduler()
scheduler.start()

def check_new_job(receiverEmail=None):
    print("Checking for new jobs...")
    asyncio.run(run_crawler_for_amazon(receiverEmail))

def _run_crawler(crawler):
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
                ensure_company_document(jobs[0]["company"])
                all_new_jobs.extend(add_jobs_if_not_exists(jobs))
            except Exception as e:
                print(f"DB error: {e}")
    return all_new_jobs

def check_f1_jobs(receiverEmail=None):
    crawlers = [
        crawl_aston_martin, crawl_ferrari,
        crawl_mclaren, crawl_red_bull, crawl_mercedes,
        crawl_alpine, crawl_williams, crawl_cadillac, crawl_sauber,
        crawl_haas, crawl_formula1,
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(_run_crawler, crawlers))

    all_new_jobs = _save_jobs(results)

    if all_new_jobs:
        send_email(all_new_jobs, receiverEmail)
        print(f"Sent {len(all_new_jobs)} new F1 jobs via Telegram")
    else:
        print("No new F1 jobs found")

@app.route('/check_new_job', methods=['GET'])
def handle_check_new_job():
    check_new_job()
    return {"message": "Job check complete"}, 200

def check_soccer_jobs(receiverEmail=None):
    crawlers = [crawl_arsenal, crawl_liverpool, crawl_man_city, crawl_chelsea, crawl_tottenham, crawl_bayern, crawl_psg]

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(_run_crawler, crawlers))

    all_new_jobs = _save_jobs(results)

    if all_new_jobs:
        send_email(all_new_jobs, receiverEmail)
        print(f"Sent {len(all_new_jobs)} new soccer jobs via Telegram")
    else:
        print("No new soccer jobs found")

@app.route('/f1', methods=['GET'])
def handle_check_f1():
    check_f1_jobs()
    return {"message": "F1 job check complete"}, 200

@app.route('/soccer', methods=['GET'])
def handle_check_soccer():
    check_soccer_jobs()
    return {"message": "Soccer job check complete"}, 200


def check_brand_jobs(receiverEmail=None):
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        http_future = executor.submit(crawl_all_brands_http)
        selenium_future = executor.submit(crawl_all_brands_selenium)
        results = [http_future.result() or [], selenium_future.result() or []]

    all_new_jobs = _save_jobs(results)
    if all_new_jobs:
        send_email(all_new_jobs, receiverEmail)
        print(f"Sent {len(all_new_jobs)} new brand jobs via Telegram")
    else:
        print("No new brand jobs found")


@app.route('/brands', methods=['GET'])
def handle_check_brands():
    check_brand_jobs()
    return {"message": "Brand job check complete"}, 200

@app.route('/main', methods=['POST'])
def handle_check_periodically():
    data = request.get_json() or {}
    receiver_email = data.get("email")
    print("Received email:", receiver_email)

    if not receiver_email:
        return {"error": "Email is required"}, 400

    # Schedule Amazon crawler
    job_id = f"job_check_{receiver_email}"
    if not scheduler.get_job(job_id):
        scheduler.add_job(
            check_new_job,
            'interval',
            minutes=15,
            args=[receiver_email],
            id=job_id
        )

    # Schedule F1 crawler
    f1_job_id = f"f1_check_{receiver_email}"
    if not scheduler.get_job(f1_job_id):
        scheduler.add_job(check_f1_jobs, 'interval', minutes=30, args=[receiver_email], id=f1_job_id)

    # Schedule soccer crawler
    soccer_job_id = f"soccer_check_{receiver_email}"
    if not scheduler.get_job(soccer_job_id):
        scheduler.add_job(check_soccer_jobs, 'interval', minutes=30, args=[receiver_email], id=soccer_job_id)

    # Schedule brands crawler
    brands_job_id = f"brands_check_{receiver_email}"
    if not scheduler.get_job(brands_job_id):
        scheduler.add_job(check_brand_jobs, 'interval', minutes=60, args=[receiver_email], id=brands_job_id)

    return {"message": f"Scheduled Amazon (15min), F1 (30min), Soccer (30min), Brands (60min) checks for {receiver_email}"}, 200

if __name__ == '__main__':
    app.run(debug=False, port=8000)


