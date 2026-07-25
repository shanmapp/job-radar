from crawlers.filters import is_relevant, matches_location, passes_filters, ROLE_KEYWORDS
import requests
import re
import json
from bs4 import BeautifulSoup


def crawl_red_bull():
    """Red Bull Racing runs Oracle Cloud Recruiting (CX). The public REST API
    lives on the Fusion backend host (iagtme.fa.ocs.oraclecloud.com), site
    CX_2 — the careers.redbullracing.com front end only serves the JS shell.
    Replaces the Selenium crawler."""
    jobs = []
    try:
        base = ("https://iagtme.fa.ocs.oraclecloud.com/hcmRestApi/resources/latest"
                "/recruitingCEJobRequisitions")
        offset, total = 0, None
        while total is None or offset < total:
            r = requests.get(base, timeout=25,
                headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
                params={"onlyData": "true",
                        "expand": "requisitionList.secondaryLocations",
                        "finder": f"findReqs;siteNumber=CX_2,limit=100,offset={offset}"})
            r.raise_for_status()
            data = r.json().get("items", [{}])[0]
            reqs = data.get("requisitionList", [])
            total = data.get("TotalJobsCount", data.get("totalResults")) or len(reqs)
            if not reqs:
                break
            for req in reqs:
                title = req.get("Title", "")
                location = req.get("PrimaryLocation", "")
                req_id = req.get("Id", "")
                link = f"https://careers.redbullracing.com/en/sites/CX_2/job/{req_id}"
                if passes_filters(title, location, company="Red Bull Racing"):
                    jobs.append({"company": "Red Bull Racing", "title": title,
                                 "location": location, "link": link, "number": str(req_id)})
            offset += len(reqs)

        print(f"Red Bull Racing: {len(jobs)} matching jobs (from {total} total)")
    except Exception as e:
        print(f"Red Bull Racing crawler error: {e}")
    return jobs


def crawl_mercedes():
    """Mercedes-AMG F1 is a Next.js site; vacancies are embedded in the
    __NEXT_DATA__ JSON (Contentful-backed). Single UK base (Brackley/Brixworth),
    so location is fixed. Replaces the Selenium crawler."""
    jobs = []
    try:
        r = requests.get("https://www.mercedesamgf1.com/careers/vacancies",
                         timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
        if not m:
            print("Mercedes-AMG F1: __NEXT_DATA__ not found (site changed?)")
            return jobs
        vacancies = json.loads(m.group(1))["props"]["pageProps"].get("vacancies", [])
        for v in vacancies:
            f = v.get("fields", {})
            title = f.get("title", "")
            vid = f.get("id") or v.get("sys", {}).get("id", "")
            link = f"https://www.mercedesamgf1.com/careers/vacancies/{vid}"
            if passes_filters(title, "United Kingdom", company="Mercedes-AMG F1"):
                jobs.append({"company": "Mercedes-AMG F1", "title": title,
                             "location": "Brackley, United Kingdom", "link": link,
                             "number": str(vid)})
        print(f"Mercedes-AMG F1: {len(jobs)} matching jobs (from {len(vacancies)} total)")
    except Exception as e:
        print(f"Mercedes-AMG F1 crawler error: {e}")
    return jobs

LOCATION_TERMS = ["united kingdom", "uk", "england", "scotland", "wales", "london",
                  "italy", "italia", "maranello", "milan", "rome", "turin",
                  "switzerland", "swiss", "geneva", "zurich", "basel"]


def matches_location(location_str):
    if not location_str:
        return False
    return any(term in location_str.lower() for term in LOCATION_TERMS)


def crawl_aston_martin():
    jobs = []
    try:
        resp = requests.get(
            "https://astonmartinf1.pinpointhq.com/postings.json",
            timeout=15,
            headers={"Accept": "application/json"}
        )
        resp.raise_for_status()
        items = resp.json().get("data", [])

        for item in items:
            title = item.get("title", "").strip()
            loc_obj = item.get("location") or {}
            location = f"{loc_obj.get('city', '')}, {loc_obj.get('province', '')}".strip(", ")
            link = item.get("url", f"https://astonmartinf1.pinpointhq.com/en/postings/{item.get('id','')}")

            if passes_filters(title, location, company="Aston Martin F1"):
                jobs.append({
                    "company": "Aston Martin F1",
                    "title": title,
                    "location": location,
                    "link": link,
                    "number": str(item.get("id", title))
                })

        print(f"Aston Martin F1: {len(jobs)} matching jobs (from {len(items)} total)")
    except Exception as e:
        print(f"Aston Martin F1 crawler error: {e}")

    return jobs


def crawl_ferrari():
    jobs = []
    seen = set()

    for keyword in ROLE_KEYWORDS:
        try:
            resp = requests.get(
                "https://jobs.ferrari.com/search",
                params={"q": keyword},
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            for tile in soup.select(".job-tile"):
                data_url = tile.get("data-url", "")
                if not data_url or data_url in seen:
                    continue

                title_el = tile.select_one(".title a") or tile.select_one("a")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)

                loc_val = tile.select_one("[id$='-location-value']")
                location = loc_val.get_text(strip=True) if loc_val else ""

                if not passes_filters(title, location, company="Ferrari F1"):
                    continue

                seen.add(data_url)
                link = f"https://jobs.ferrari.com{data_url}" if data_url.startswith("/") else data_url

                jobs.append({
                    "company": "Ferrari F1",
                    "title": title,
                    "location": location,
                    "link": link,
                    "number": data_url
                })

        except Exception as e:
            print(f"Ferrari crawler error ({keyword}): {e}")

    print(f"Ferrari F1: {len(jobs)} matching jobs found")
    return jobs
