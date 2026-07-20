from crawlers.filters import is_relevant, matches_location, passes_filters, ROLE_KEYWORDS
import requests
from bs4 import BeautifulSoup

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
