from crawlers.filters import is_relevant, matches_location, passes_filters
"""HTTP-based crawlers for soccer clubs: Arsenal (Teamtailor), Liverpool, PSG (Workday API),
Manchester City (SAP SuccessFactors)."""
import requests
from bs4 import BeautifulSoup
from crawlers.brands_http_crawler import _crawl_successfactors


def crawl_man_city():
    """City Football Group runs SAP SuccessFactors (coreCSB) at
    careers.cityfootballgroup.com/search-jobs — fully server-rendered, so the
    shared csb HTTP parser handles it. Replaces the Selenium version, which
    only scraped the first rendered page and risked silent zeros."""
    return _crawl_successfactors("Manchester City FC",
                                 "careers.cityfootballgroup.com",
                                 "/search-jobs", "csb")


def crawl_arsenal():
    jobs = []
    try:
        resp = requests.get(
            "https://careers.arsenal.com/jobs.json",
            timeout=15,
            headers={"Accept": "application/json"}
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])

        for item in items:
            title = item.get("title", "").strip()
            url = item.get("url", "")
            jp = item.get("_jobposting", {})
            loc_list = jp.get("jobLocation", [])
            location = ""
            if loc_list:
                addr = loc_list[0].get("address", {})
                city = addr.get("addressLocality", "")
                country = addr.get("addressCountry", "")
                location = f"{city}, {country}".strip(", ")

            if passes_filters(title, company="Arsenal FC"):
                jobs.append({
                    "company": "Arsenal FC",
                    "title": title,
                    "location": location or "London, UK",
                    "link": url,
                    "number": url
                })

        print(f"Arsenal FC: {len(jobs)} matching jobs (from {len(items)} total)")
    except Exception as e:
        print(f"Arsenal crawler error: {e}")

    return jobs


def crawl_liverpool():
    jobs = []
    try:
        resp = requests.get(
            "https://jobsearch.liverpoolfc.com/",
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for li in soup.select("ul.jobs li"):
            link_el = li.select_one("a")
            title_el = li.select_one(".job-list-title")
            loc_el = li.select_one("[itemprop=jobLocation]")

            if not title_el or not link_el:
                continue

            title = title_el.get_text(strip=True)
            link = link_el.get("href", "")
            location = loc_el.get_text(strip=True) if loc_el else "Liverpool, UK"

            if passes_filters(title, company="Liverpool FC"):
                jobs.append({
                    "company": "Liverpool FC",
                    "title": title,
                    "location": location,
                    "link": link,
                    "number": link
                })

        print(f"Liverpool FC: {len(jobs)} matching jobs")
    except Exception as e:
        print(f"Liverpool crawler error: {e}")

    return jobs


def crawl_chelsea_cfcw():
    """Chelsea FC Holdings Ltd runs a separate UKG Workforce Ready ATS (covers CFCW/commercial
    roles not listed on the CoreHR portal used by crawl_chelsea)."""
    jobs = []
    try:
        base = "https://secure.workforceready.eu"
        resp = requests.get(
            f"{base}/ta/rest/ui/recruitment/companies/%7C6189861/job-requisitions",
            params={"offset": 1, "size": 50, "sort": "desc", "ein_id": "", "lang": "en-GB"},
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            },
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        reqs = data.get("job_requisitions", [])

        for req in reqs:
            title = req.get("job_title", "").strip()
            job_id = req.get("id")
            loc = req.get("location", {})
            location = ", ".join(filter(None, [loc.get("city"), loc.get("country")])) or "London, UK"
            link = f"{base}/ta/6189861.careers?ApplyToJob={job_id}&full_apply=&jobid={job_id}"

            if passes_filters(title, company="Chelsea FC"):
                jobs.append({
                    "company": "Chelsea FC",
                    "title": title,
                    "location": location,
                    "link": link,
                    "number": str(job_id)
                })

        print(f"Chelsea FC (Workforce Ready): {len(jobs)} matching jobs (from {len(reqs)} total)")
    except Exception as e:
        print(f"Chelsea Workforce Ready crawler error: {e}")

    return jobs


def crawl_psg():
    jobs = []
    try:
        base = "https://parissaintgermain.wd3.myworkdayjobs.com"
        # Workday's CXS API rejects limit > 20 with a plain 400 — this crawler
        # sat erroring on every run with limit=50 until a raw-pull audit
        # noticed. Page through 20 at a time instead.
        postings, offset, total = [], 0, None
        while total is None or offset < total:
            resp = requests.post(
                f"{base}/wday/cxs/parissaintgermain/rejoigneznous/jobs",
                json={"appliedFacets": {}, "limit": 20, "offset": offset,
                      "searchText": ""},
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Origin": base,
                    "Referer": f"{base}/rejoigneznous",
                },
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            total = data.get("total", 0)
            batch = data.get("jobPostings", [])
            if not batch:
                break
            postings.extend(batch)
            offset += 20

        for posting in postings:
            title = posting.get("title", "")
            # bulletFields carries the req number, not a location; PSG is a
            # single-site club so the location is always Paris.
            location_str = (posting.get("locationsText") or "").strip()
            external_path = posting.get("externalPath", "")
            link = f"https://parissaintgermain.wd3.myworkdayjobs.com/en-US/rejoigneznous{external_path}"

            if passes_filters(title, company="Paris Saint-Germain"):
                jobs.append({
                    "company": "Paris Saint-Germain",
                    "title": title,
                    "location": location_str or "Paris, France",
                    "link": link,
                    "number": external_path
                })

        print(f"Paris Saint-Germain: {len(jobs)} matching jobs (from {data.get('total', 0)} total)")
    except Exception as e:
        print(f"PSG crawler error: {e}")

    return jobs
