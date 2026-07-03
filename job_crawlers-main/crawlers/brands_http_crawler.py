from crawlers.filters import is_relevant, matches_location
"""
HTTP-based crawlers for brand companies using Greenhouse, Lever, SmartRecruiters, and Workday APIs.
All functions return a list of job dicts: {company, title, location, link, number}
"""
import requests
from crawlers.brands_config import (
    GREENHOUSE_COMPANIES, LEVER_COMPANIES, SMARTRECRUITERS_COMPANIES,
    WORKABLE_COMPANIES, TEAMTAILOR_COMPANIES, BREEZY_COMPANIES, PINPOINT_COMPANIES,
)

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


# ── Workable ─────────────────────────────────────────────────────────────────

def _crawl_workable(company_name, account_slug):
    jobs = []
    try:
        r = requests.post(
            f"https://apply.workable.com/api/v3/accounts/{account_slug}/jobs",
            json={},
            timeout=15,
            headers={"User-Agent": UA}
        )
        r.raise_for_status()
        for job in r.json().get("results", []):
            title = job.get("title", "")
            loc = job.get("location", {})
            city = loc.get("city", "")
            country = loc.get("country", "")
            location = ", ".join(filter(None, [city, country]))
            shortcode = job.get("shortcode", "")
            link = f"https://apply.workable.com/{account_slug}/j/{shortcode}/"
            job_id = str(job.get("id", ""))

            if is_relevant(title) and matches_location(location):
                jobs.append({"company": company_name, "title": title,
                             "location": location, "link": link, "number": job_id})

        print(f"{company_name}: {len(jobs)} matching jobs")
    except Exception as e:
        print(f"{company_name} (Workable) error: {e}")
    return jobs


def crawl_all_workable():
    jobs = []
    for company, account_slug in WORKABLE_COMPANIES.items():
        jobs.extend(_crawl_workable(company, account_slug))
    return jobs


# ── Teamtailor ───────────────────────────────────────────────────────────────

def _crawl_teamtailor(company_name, host):
    jobs = []
    try:
        r = requests.get(
            f"https://{host}/jobs.json",
            timeout=15,
            headers={"User-Agent": UA, "Accept": "application/json"}
        )
        r.raise_for_status()
        for job in r.json().get("items", []):
            title = job.get("title", "")
            link = job.get("url", "")
            job_id = job.get("id", "")

            job_locations = job.get("_jobposting", {}).get("jobLocation", [])
            address = job_locations[0].get("address", {}) if job_locations else {}
            city = address.get("addressLocality", "")
            country = address.get("addressCountry", "")
            location = ", ".join(filter(None, [city, country]))

            if is_relevant(title) and matches_location(location):
                jobs.append({"company": company_name, "title": title,
                             "location": location, "link": link, "number": job_id})

        print(f"{company_name}: {len(jobs)} matching jobs")
    except Exception as e:
        print(f"{company_name} (Teamtailor) error: {e}")
    return jobs


def crawl_all_teamtailor():
    jobs = []
    for company, host in TEAMTAILOR_COMPANIES.items():
        jobs.extend(_crawl_teamtailor(company, host))
    return jobs


# ── Breezy HR ────────────────────────────────────────────────────────────────

def _crawl_breezy(company_name, subdomain):
    jobs = []
    try:
        r = requests.get(
            f"https://{subdomain}.breezy.hr/json",
            timeout=15,
            headers={"User-Agent": UA}
        )
        r.raise_for_status()
        for job in r.json():
            title = job.get("name", "")
            location = job.get("location", {}).get("name", "")
            link = job.get("url", "")
            job_id = str(job.get("id", ""))

            if is_relevant(title) and matches_location(location):
                jobs.append({"company": company_name, "title": title,
                             "location": location, "link": link, "number": job_id})

        print(f"{company_name}: {len(jobs)} matching jobs")
    except Exception as e:
        print(f"{company_name} (Breezy HR) error: {e}")
    return jobs


def crawl_all_breezy():
    jobs = []
    for company, subdomain in BREEZY_COMPANIES.items():
        jobs.extend(_crawl_breezy(company, subdomain))
    return jobs


# ── Pinpoint ─────────────────────────────────────────────────────────────────

def _crawl_pinpoint(company_name, host):
    jobs = []
    try:
        r = requests.get(
            f"https://{host}/postings.json",
            timeout=15,
            headers={"User-Agent": UA}
        )
        r.raise_for_status()
        for job in r.json().get("data", []):
            title = job.get("title", "")
            loc = job.get("location", {})
            city = loc.get("city", "")
            region = loc.get("name", "")
            location = ", ".join(filter(None, [city, region]))
            link = job.get("url", "")
            job_id = job.get("id", "")

            if is_relevant(title) and matches_location(location):
                jobs.append({"company": company_name, "title": title,
                             "location": location, "link": link, "number": job_id})

        print(f"{company_name}: {len(jobs)} matching jobs")
    except Exception as e:
        print(f"{company_name} (Pinpoint) error: {e}")
    return jobs


def crawl_all_pinpoint():
    jobs = []
    for company, host in PINPOINT_COMPANIES.items():
        jobs.extend(_crawl_pinpoint(company, host))
    return jobs


# ── Combined entry point ─────────────────────────────────────────────────────

def crawl_all_brands_http():
    jobs = []
    jobs.extend(crawl_all_greenhouse())
    jobs.extend(crawl_all_lever())
    jobs.extend(crawl_all_smartrecruiters())
    jobs.extend(crawl_all_workable())
    jobs.extend(crawl_all_teamtailor())
    jobs.extend(crawl_all_breezy())
    jobs.extend(crawl_all_pinpoint())
    return jobs
