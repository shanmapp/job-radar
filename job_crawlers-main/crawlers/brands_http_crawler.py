from crawlers.filters import is_relevant, matches_location
"""
HTTP-based crawlers for brand companies using Greenhouse, Lever, SmartRecruiters, and Workday APIs.
All functions return a list of job dicts: {company, title, location, link, number}
"""
import requests
from crawlers.brands_config import GREENHOUSE_COMPANIES, LEVER_COMPANIES, SMARTRECRUITERS_COMPANIES

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


# ── Greenhouse ──────────────────────────────────────────────────────────────

def _crawl_greenhouse(company_name, board_id):
    jobs = []
    try:
        r = requests.get(
            f"https://boards-api.greenhouse.io/v1/boards/{board_id}/jobs",
            params={"content": "false"},
            timeout=15,
            headers={"User-Agent": UA}
        )
        r.raise_for_status()
        for job in r.json().get("jobs", []):
            title = job.get("title", "")
            location = job.get("location", {}).get("name", "")
            link = job.get("absolute_url", "")
            job_id = str(job.get("id", ""))

            if is_relevant(title) and matches_location(location):
                jobs.append({"company": company_name, "title": title,
                             "location": location, "link": link, "number": job_id})

        print(f"{company_name}: {len(jobs)} matching jobs")
    except Exception as e:
        print(f"{company_name} (Greenhouse) error: {e}")
    return jobs


def crawl_all_greenhouse():
    jobs = []
    for company, board_id in GREENHOUSE_COMPANIES.items():
        jobs.extend(_crawl_greenhouse(company, board_id))
    return jobs


# ── Lever ────────────────────────────────────────────────────────────────────

def _crawl_lever(company_name, company_id):
    jobs = []
    try:
        r = requests.get(
            f"https://api.lever.co/v0/postings/{company_id}",
            params={"mode": "json"},
            timeout=15,
            headers={"User-Agent": UA}
        )
        r.raise_for_status()
        for job in r.json():
            title = job.get("text", "")
            cats = job.get("categories", {})
            all_locations = cats.get("allLocations", [cats.get("location", "")])
            location = ", ".join(all_locations) if all_locations else ""
            link = job.get("hostedUrl", "")
            job_id = job.get("id", "")

            if is_relevant(title) and matches_location(location):
                jobs.append({"company": company_name, "title": title,
                             "location": location, "link": link, "number": job_id})

        print(f"{company_name}: {len(jobs)} matching jobs")
    except Exception as e:
        print(f"{company_name} (Lever) error: {e}")
    return jobs


def crawl_all_lever():
    jobs = []
    for company, company_id in LEVER_COMPANIES.items():
        jobs.extend(_crawl_lever(company, company_id))
    return jobs


# ── SmartRecruiters ──────────────────────────────────────────────────────────

def _crawl_smartrecruiters(company_name, company_id):
    jobs = []
    try:
        offset = 0
        limit = 100
        while True:
            r = requests.get(
                f"https://api.smartrecruiters.com/v1/companies/{company_id}/postings",
                params={"limit": limit, "offset": offset},
                timeout=15,
                headers={"User-Agent": UA}
            )
            r.raise_for_status()
            data = r.json()
            postings = data.get("content", [])
            if not postings:
                break

            for job in postings:
                title = job.get("name", "")
                loc = job.get("location", {})
                city = loc.get("city", "")
                country = loc.get("country", "")
                location = f"{city}, {country}".strip(", ")
                job_id = job.get("id", "")
                link = f"https://careers.smartrecruiters.com/{company_id}/{job_id}"

                if is_relevant(title) and matches_location(location):
                    jobs.append({"company": company_name, "title": title,
                                 "location": location, "link": link, "number": job_id})

            if offset + limit >= data.get("totalFound", 0):
                break
            offset += limit

        print(f"{company_name}: {len(jobs)} matching jobs")
    except Exception as e:
        print(f"{company_name} (SmartRecruiters) error: {e}")
    return jobs


def crawl_all_smartrecruiters():
    jobs = []
    for company, company_id in SMARTRECRUITERS_COMPANIES.items():
        jobs.extend(_crawl_smartrecruiters(company, company_id))
    return jobs


# ── Combined entry point ─────────────────────────────────────────────────────

def crawl_all_brands_http():
    jobs = []
    jobs.extend(crawl_all_greenhouse())
    jobs.extend(crawl_all_lever())
    jobs.extend(crawl_all_smartrecruiters())
    return jobs
