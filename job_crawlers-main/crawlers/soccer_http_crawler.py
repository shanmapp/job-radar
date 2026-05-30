from crawlers.filters import is_relevant, matches_location
"""HTTP-based crawlers for soccer clubs: Arsenal (Teamtailor), Liverpool, PSG (Workday API)."""
import requests
from bs4 import BeautifulSoup

ROLE_KEYWORDS = ["strategy", "brand", "partnerships", "sponsorship"]
SENIORITY_KEYWORDS = ["coordinator", "specialist", "executive", "associate", "analyst", "assistant", "junior"]


def is_relevant(title):
    t = title.lower()
    return any(k in t for k in ROLE_KEYWORDS)


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

            if is_relevant(title):
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

            if is_relevant(title):
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


def crawl_psg():
    jobs = []
    try:
        base = "https://parissaintgermain.wd3.myworkdayjobs.com"
        resp = requests.post(
            f"{base}/wday/cxs/parissaintgermain/rejoigneznous/jobs",
            json={"appliedFacets": {}, "limit": 50, "offset": 0, "searchText": ""},
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

        for posting in data.get("jobPostings", []):
            title = posting.get("title", "")
            location_str = " ".join(posting.get("bulletFields", []))
            external_path = posting.get("externalPath", "")
            link = f"https://parissaintgermain.wd3.myworkdayjobs.com/en-US/rejoigneznous{external_path}"

            if is_relevant(title):
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
