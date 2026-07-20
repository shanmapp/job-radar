from crawlers.filters import is_relevant, matches_location, passes_filters
"""HTTP-based crawlers for Haas F1 (BambooHR API)."""
import requests

# Haas UK base - Banbury; Italy base - Maranello/Castelnuovo Rangone
HAAS_UK_CITIES = ["banbury", "london", "oxford", "bicester", "silverstone"]
HAAS_IT_CITIES = ["maranello", "castelnuovo", "modena", "milan", "milan"]
HAAS_CH_CITIES = ["geneva", "zurich", "basel", "berne"]


def _haas_location_ok(city):
    city_lower = (city or "").lower()
    return any(c in city_lower for c in HAAS_UK_CITIES + HAAS_IT_CITIES + HAAS_CH_CITIES)


def crawl_haas():
    jobs = []
    try:
        resp = requests.get(
            "https://haasf1team.bamboohr.com/careers/list",
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        )
        resp.raise_for_status()
        data = resp.json()

        for job in data.get("result", []):
            title = job.get("jobOpeningName", "").strip()
            city = job.get("location", {}).get("city", "")
            job_id = job.get("id", "")
            link = f"https://haasf1team.bamboohr.com/careers/{job_id}"

            if _haas_location_ok(city) and passes_filters(title, company="Haas F1"):
                jobs.append({
                    "company": "Haas F1",
                    "title": title,
                    "location": city,
                    "link": link,
                    "number": job_id
                })

        print(f"Haas F1: {len(jobs)} matching jobs (from {data.get('meta', {}).get('totalCount', 0)} total)")
    except Exception as e:
        print(f"Haas F1 crawler error: {e}")

    return jobs
