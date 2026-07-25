from crawlers.filters import is_relevant, matches_location, passes_filters
from crawlers.silent_zero import report as _report_raw
"""HTTP-based crawlers for Haas F1 (BambooHR API) and Cadillac F1 (Workable API)."""
import requests


def crawl_cadillac():
    """Cadillac F1 runs on Workable (cadillacf1team). The v3 jobs API is public
    and pages via a `nextPage` token — the Selenium crawler only saw the first
    rendered page. Single UK base (Silverstone), so location is pre-checked."""
    jobs = []
    try:
        token, total = None, None
        while True:
            resp = requests.post(
                "https://apply.workable.com/api/v3/accounts/cadillacf1team/jobs",
                json={"token": token} if token else {},
                timeout=15, headers={"User-Agent": "Mozilla/5.0"}
            )
            resp.raise_for_status()
            data = resp.json()
            total = data.get("total", 0) if total is None else total
            for job in data.get("results", []):
                title = job.get("title", "")
                loc = job.get("location", {})
                location = ", ".join(filter(None, [loc.get("city", ""), loc.get("country", "")]))
                shortcode = job.get("shortcode", "")
                if passes_filters(title, location, company="Cadillac F1"):
                    jobs.append({
                        "company": "Cadillac F1",
                        "title": title,
                        "location": location,
                        "link": f"https://apply.workable.com/cadillacf1team/j/{shortcode}/",
                        "number": str(job.get("id", "")),
                    })
            token = data.get("nextPage")
            if not token:
                break

        _report_raw("Cadillac F1", total or 0)
        print(f"Cadillac F1: {len(jobs)} matching jobs (from {total} total)")
    except Exception as e:
        print(f"Cadillac F1 crawler error: {e}")

    return jobs

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
        _report_raw("Haas F1", len(data.get("result", [])))

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
