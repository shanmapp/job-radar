from crawlers.filters import is_relevant, matches_location, passes_filters, TARGET_COUNTRIES
"""
HTTP-based crawlers for brand companies using Greenhouse, Lever, SmartRecruiters, and Workday APIs.
All functions return a list of job dicts: {company, title, location, link, number}
"""
import requests
import re
from crawlers.brands_config import (
    GREENHOUSE_COMPANIES, LEVER_COMPANIES, SMARTRECRUITERS_COMPANIES,
    WORKABLE_COMPANIES, TEAMTAILOR_COMPANIES, BREEZY_COMPANIES, PINPOINT_COMPANIES,
    CONSIDER_COMPANIES, JOBYLON_COMPANIES, PHENOM_COMPANIES,
    SUCCESSFACTORS_COMPANIES, ASHBY_COMPANIES, EIGHTFOLD_COMPANIES,
    WORKDAY_COMPANIES,
)
import html as html_lib

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

            if passes_filters(title, location, company=company_name):
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

            if passes_filters(title, location, company=company_name):
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

                if passes_filters(title, location, company=company_name):
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

            if passes_filters(title, location, company=company_name):
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

            if passes_filters(title, location, company=company_name):
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

            if passes_filters(title, location, company=company_name):
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

            if passes_filters(title, location, company=company_name):
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


# ── Consider ─────────────────────────────────────────────────────────────────

def _crawl_consider(company_name, host, board_id):
    jobs = []
    try:
        session = requests.Session()
        page = session.get(f"https://{host}/jobs", timeout=15, headers={"User-Agent": UA})
        page.raise_for_status()
        match = re.search(r'csrfToken":"([^"]+)"', page.text)
        if not match:
            raise ValueError("csrf token not found in careers page")
        csrf_token = match.group(1)

        r = session.post(
            f"https://{host}/api-boards/search-jobs",
            json={"meta": {"size": 100}, "board": {"id": board_id, "isParent": False}, "query": {}},
            timeout=15,
            headers={
                "User-Agent": UA,
                "Accept": "application/json",
                "X-CSRF-Token": csrf_token,
                "Referer": f"https://{host}/jobs",
            },
        )
        r.raise_for_status()
        for job in r.json().get("jobs", []):
            title = job.get("title", "")
            location = ", ".join(job.get("locations", []))
            link = job.get("applyUrl", "")
            job_id = str(job.get("jobId", ""))

            if passes_filters(title, location, company=company_name):
                jobs.append({"company": company_name, "title": title,
                             "location": location, "link": link, "number": job_id})

        print(f"{company_name}: {len(jobs)} matching jobs")
    except Exception as e:
        print(f"{company_name} (Consider) error: {e}")
    return jobs


def crawl_all_consider():
    jobs = []
    for company, (host, board_id) in CONSIDER_COMPANIES.items():
        jobs.extend(_crawl_consider(company, host, board_id))
    return jobs


# ── Jobylon ──────────────────────────────────────────────────────────────────
# The CDN embed endpoint returns a JS snippet containing the rendered job list
# HTML; job link slugs and per-job "Location:" values are regex-parsed from it.

def _crawl_jobylon(company_name, company_id, default_country):
    jobs = []
    try:
        r = requests.get(
            f"https://cdn.jobylon.com/jobs/companies/{company_id}/embed/v1/",
            params={"target": "jobylon-jobs-widget", "page_size": 100},
            timeout=20, headers={"User-Agent": UA}
        )
        r.raise_for_status()
        # Each job block: id="jobylon-job-<id>" ... job-title>TITLE< ...
        # jobylon-location"><strong>Location:</strong> CITY</li>
        blocks = re.split(r'id="jobylon-job-(\d+)"', r.text)[1:]
        for job_id, block in zip(blocks[0::2], blocks[1::2]):
            tm = re.search(r'jobylon-job-title[^>]*>([^<]+)<', block)
            lm = re.search(r'jobylon-location"><strong>[^<]*</strong>\s*([^<]+)<', block)
            sm = re.search(r'jobs/(%s-[a-z0-9-]+)' % job_id, r.text)
            title = html_lib.unescape(tm.group(1).strip()) if tm else ""
            location = html_lib.unescape(lm.group(1).strip()) if lm else ""
            if location and default_country.lower() not in location.lower():
                location = f"{location}, {default_country}"
            link = (f"https://emp.jobylon.com/jobs/{sm.group(1)}/" if sm
                    else f"https://emp.jobylon.com/jobs/{job_id}/")

            if passes_filters(title, location, company=company_name):
                jobs.append({"company": company_name, "title": title,
                             "location": location, "link": link, "number": job_id})

        print(f"{company_name}: {len(jobs)} matching jobs")
    except Exception as e:
        print(f"{company_name} (Jobylon) error: {e}")
    return jobs


def crawl_all_jobylon():
    jobs = []
    for company, (company_id, default_country) in JOBYLON_COMPANIES.items():
        jobs.extend(_crawl_jobylon(company, company_id, default_country))
    return jobs


# ── Phenom People ────────────────────────────────────────────────────────────
# The /widgets endpoint takes an unauthenticated JSON POST and pages through
# the whole external job index 100 at a time.

_PHENOM_PAGE_CAP = 10


def _crawl_phenom(company_name, base):
    jobs = []
    try:
        seen_total = None
        for start in range(0, _PHENOM_PAGE_CAP * 100, 100):
            payload = {"lang": "en_us", "deviceType": "desktop", "country": "us",
                       "pageName": "search-results", "ddoKey": "refineSearch",
                       "from": start, "jobs": True, "counts": True,
                       "all_fields": ["category", "country"], "size": 100,
                       "siteType": "external", "keywords": "", "global": True,
                       "selected_fields": {}, "locationData": {}}
            r = requests.post(f"{base}/widgets", json=payload, timeout=25,
                              headers={"User-Agent": UA})
            r.raise_for_status()
            data = r.json().get("refineSearch", {})
            seen_total = data.get("totalHits") or 0
            batch = data.get("data", {}).get("jobs", [])
            if not batch:
                break
            for job in batch:
                title = (job.get("title") or "").strip()
                location = job.get("location") or ", ".join(filter(None, [
                    job.get("city"), job.get("state"), job.get("country")]))
                job_id = job.get("jobId") or job.get("reqId") or ""
                # applyUrl points at the underlying ATS apply form; strip the
                # trailing /apply to land on the readable posting instead.
                link = re.sub(r"/apply$", "", job.get("applyUrl") or "") or \
                    f"{base}/job/{job.get('jobSeqNo', '')}"

                if passes_filters(title, location, company=company_name):
                    jobs.append({"company": company_name, "title": title,
                                 "location": location, "link": link,
                                 "number": job_id})
            if start + 100 >= seen_total:
                break

        print(f"{company_name}: {len(jobs)} matching jobs")
    except Exception as e:
        print(f"{company_name} (Phenom) error: {e}")
    return jobs


def crawl_all_phenom():
    jobs = []
    for company, base in PHENOM_COMPANIES.items():
        jobs.extend(_crawl_phenom(company, base))
    return jobs


# ── SAP SuccessFactors (server-rendered Career Site Builder sites) ───────────
# No JSON API, but these sites return the full job list as plain HTML.
# Under Armour uses the stock CSB markup (jobTitle-link anchors + location-value
# divs, paginated via ?startrow=N); Heineken's custom /Job-Listing uses
# job-list-item blocks with <p class="nation"> locations and a composite
# ?page=0,0,N parameter (three paged widgets share it; ours is the third).

_SF_PAGE_CAP = 60  # pages; both sites serve 10 jobs/page

# Stock CSB locations use ISO country codes ("London, GB, W1F 7PS"), which the
# name-based location filter can't see — expand codes for the target countries.
_ISO_COUNTRIES = {
    "GB": "United Kingdom", "AU": "Australia", "AT": "Austria", "DK": "Denmark",
    "FI": "Finland", "FR": "France", "DE": "Germany", "HK": "Hong Kong",
    "IE": "Ireland", "IT": "Italy", "JP": "Japan", "KR": "Korea",
    "NL": "Netherlands", "NO": "Norway", "PL": "Poland", "ES": "Spain",
    "SE": "Sweden", "CH": "Switzerland",
}


def _expand_iso_location(location):
    parts = [p.strip() for p in location.split(",")]
    return ", ".join(_ISO_COUNTRIES.get(p, p) for p in parts)


def _crawl_successfactors(company_name, host, path, style):
    jobs, seen = [], set()
    try:
        for page in range(_SF_PAGE_CAP):
            params = ({"startrow": page * 10} if style == "csb"
                      else {"page": f"0,0,{page}"})
            r = requests.get(f"https://{host}{path}", params=params,
                             timeout=20, headers={"User-Agent": UA})
            if style == "csb":
                titles = dict(re.findall(
                    r'class="jobTitle-link[^"]*"[^>]*href="/job/[^"]*?/(\d+)/"[^>]*>'
                    r'\s*([^<]+?)\s*<', r.text))
                hrefs = {jid: href for href, jid in re.findall(
                    r'class="jobTitle-link[^"]*"[^>]*href="(/job/[^"]*?/(\d+)/)"',
                    r.text)}
                locs = dict(re.findall(
                    r'id="job-(\d+)-desktop-section-location-value"[^>]*>'
                    r'\s*([^<]+?)\s*<', r.text))
                page_jobs = [(hrefs.get(jid, ""), title,
                              _expand_iso_location(locs.get(jid, "")))
                             for jid, title in titles.items()]
            else:
                blocks = r.text.split('class="job-list-item"')[1:]
                page_jobs = []
                for block in blocks:
                    tm = re.search(r'<a href="(/job/[^"]+)"[^>]*>([^<]+)</a>', block)
                    lm = re.search(r'class="nation"[^>]*>\s*([^<]+?)\s*<', block)
                    if tm:
                        page_jobs.append((tm.group(1), tm.group(2),
                                          lm.group(1) if lm else ""))
            new = [(h, t, l) for h, t, l in page_jobs if h and h not in seen]
            if not new:
                break
            for href, title, location in new:
                seen.add(href)
                title = html_lib.unescape(title)
                location = html_lib.unescape(location)
                number = href.rstrip("/").rsplit("/", 1)[-1]

                if passes_filters(title, location, company=company_name):
                    jobs.append({"company": company_name, "title": title,
                                 "location": location,
                                 "link": f"https://{host}{href}",
                                 "number": number})

        print(f"{company_name}: {len(jobs)} matching jobs")
    except Exception as e:
        print(f"{company_name} (SuccessFactors) error: {e}")
    return jobs


def crawl_all_successfactors():
    jobs = []
    for company, (host, path, style) in SUCCESSFACTORS_COMPANIES.items():
        jobs.extend(_crawl_successfactors(company, host, path, style))
    return jobs


# ── Workday (CXS JSON API) ───────────────────────────────────────────────────
# Every Workday board exposes /wday/cxs/<tenant>/<site>/jobs, which returns the
# full posting list paged 20 at a time (the API rejects limit > 20 with a 400).
# This replaces the Selenium Workday crawler, which only scraped the first page
# of rendered cards and silently dropped the rest of large boards.

_WD_PAGE = 20  # Workday hard-caps limit at 20 per request

def _crawl_workday_http(company_name, careers_url):
    jobs = []
    try:
        base, _, query = careers_url.partition("?")
        host = base.split("//", 1)[-1].split("/", 1)[0]
        tenant = host.split(".", 1)[0]
        site = base.rstrip("/").rsplit("/", 1)[-1]
        # A "?q=term" suffix (e.g. ESPN, Lippincott) filters server-side.
        search_text = ""
        m = re.search(r"(?:^|&)q=([^&]+)", query)
        if m:
            from urllib.parse import unquote_plus
            search_text = unquote_plus(m.group(1))

        cxs = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
        offset, total = 0, None
        while total is None or offset < total:
            r = requests.post(cxs, json={"appliedFacets": {}, "limit": _WD_PAGE,
                                         "offset": offset, "searchText": search_text},
                              headers={"Accept": "application/json",
                                       "Content-Type": "application/json",
                                       "User-Agent": UA}, timeout=20)
            r.raise_for_status()
            data = r.json()
            total = data.get("total", 0)
            batch = data.get("jobPostings", [])
            if not batch:
                break
            for p in batch:
                title = (p.get("title") or "").strip()
                location = (p.get("locationsText") or "").strip()
                ext = p.get("externalPath", "")
                link = f"https://{host}/en-US/{site}{ext}"
                if passes_filters(title, location, company=company_name):
                    jobs.append({"company": company_name, "title": title,
                                 "location": location, "link": link, "number": ext})
            offset += _WD_PAGE

        print(f"{company_name}: {len(jobs)} matching jobs (from {total} total)")
    except Exception as e:
        print(f"{company_name} (Workday) error: {e}")
    return jobs


def crawl_all_workday_http():
    jobs = []
    for company, url in WORKDAY_COMPANIES.items():
        jobs.extend(_crawl_workday_http(company, url))
    return jobs


# ── PUMA (custom Elasticsearch endpoint) ─────────────────────────────────────
# about.puma.com/dd_job_search proxies an Elasticsearch index of all postings
# and accepts arbitrary ES queries unauthenticated. Documents carry title,
# city, country and the public posting path in _source.url. The server clamps
# size to 10 regardless of the requested value, so page with `from`.

def crawl_puma():
    jobs = []
    try:
        start, total = 0, None
        while total is None or start < min(total, 1000):
            r = requests.post(
                "https://about.puma.com/dd_job_search",
                json={"from": start, "size": 10,
                      "query": {"bool": {"must": [{"term": {"language": "en"}}]}}},
                timeout=25, headers={"User-Agent": UA})
            r.raise_for_status()
            hits = r.json().get("hits", {})
            total = (hits.get("total") or {}).get("value", 0)
            batch = hits.get("hits", [])
            if not batch:
                break
            for hit in batch:
                src = hit.get("_source", {})
                title = (src.get("title") or "").strip()
                location = ", ".join(filter(None, [src.get("city"), src.get("country")]))
                link = f"https://about.puma.com{src.get('url', '')}"
                number = str(src.get("entity_id", ""))

                if passes_filters(title, location, company="Puma"):
                    jobs.append({"company": "Puma", "title": title,
                                 "location": location, "link": link,
                                 "number": number})
            start += 10

        print(f"Puma: {len(jobs)} matching jobs")
    except Exception as e:
        print(f"Puma (dd_job_search) error: {e}")
    return jobs


# ── Ashby ────────────────────────────────────────────────────────────────────

def _crawl_ashby(company_name, board_slug):
    jobs = []
    try:
        r = requests.get(
            f"https://api.ashbyhq.com/posting-api/job-board/{board_slug}",
            timeout=15, headers={"User-Agent": UA})
        r.raise_for_status()
        for job in r.json().get("jobs", []):
            title = job.get("title", "")
            location = job.get("location", "")
            link = job.get("jobUrl", "")
            job_id = job.get("id", "")

            if passes_filters(title, location, company=company_name):
                jobs.append({"company": company_name, "title": title,
                             "location": location, "link": link, "number": job_id})

        print(f"{company_name}: {len(jobs)} matching jobs")
    except Exception as e:
        print(f"{company_name} (Ashby) error: {e}")
    return jobs


def crawl_all_ashby():
    jobs = []
    for company, slug in ASHBY_COMPANIES.items():
        jobs.extend(_crawl_ashby(company, slug))
    return jobs


# ── Eightfold AI ─────────────────────────────────────────────────────────────

# The API serves 10 positions per page no matter what num asks for, so page
# by the actual batch size. Cap guards against a runaway loop (~1000 jobs).
_EIGHTFOLD_PAGE_CAP = 100


def _crawl_eightfold(company_name, host, domain):
    jobs = []
    try:
        start, count, pages = 0, None, 0
        while pages < _EIGHTFOLD_PAGE_CAP and (count is None or start < count):
            r = requests.get(
                f"{host}/api/apply/v2/jobs",
                params={"domain": domain, "num": 100, "start": start},
                timeout=20, headers={"User-Agent": UA})
            r.raise_for_status()
            data = r.json()
            count = data.get("count") or 0
            batch = data.get("positions", [])
            if not batch:
                break
            start += len(batch)
            pages += 1
            for pos in batch:
                title = (pos.get("name") or "").strip()
                location = pos.get("location") or ", ".join(pos.get("locations") or [])
                link = pos.get("canonicalPositionUrl") or f"{host}/careers/job/{pos.get('id')}"
                job_id = str(pos.get("display_job_id") or pos.get("id") or "")

                if passes_filters(title, location, company=company_name):
                    jobs.append({"company": company_name, "title": title,
                                 "location": location, "link": link,
                                 "number": job_id})

        print(f"{company_name}: {len(jobs)} matching jobs")
    except Exception as e:
        print(f"{company_name} (Eightfold) error: {e}")
    return jobs


def crawl_all_eightfold():
    jobs = []
    for company, (host, domain) in EIGHTFOLD_COMPANIES.items():
        jobs.extend(_crawl_eightfold(company, host, domain))
    return jobs


# ── Amazon (UK roles via the public search.json API) ─────────────────────────
# Replaces the Selenium "Amazon Studios" crawler (its .job-tile selectors died
# in a redesign). search.json ignores loc_query but honors
# normalized_country_code[]; locations come back as "GB, London".

_AMAZON_QUERIES = ["brand", "partnerships", "sponsorship", "internship", "graduate"]


def crawl_amazon_uk():
    jobs, seen = [], set()
    try:
        for query in _AMAZON_QUERIES:
            r = requests.get(
                "https://www.amazon.jobs/en/search.json",
                params={"base_query": query, "normalized_country_code[]": "GBR",
                        "result_limit": 100},
                timeout=20, headers={"User-Agent": UA})
            r.raise_for_status()
            for job in r.json().get("jobs", []):
                job_id = str(job.get("id_icims") or job.get("id") or "")
                if not job_id or job_id in seen:
                    continue
                seen.add(job_id)
                title = job.get("title", "")
                location = (job.get("location") or "").replace("GB,", "United Kingdom,")
                link = "https://www.amazon.jobs" + (job.get("job_path") or "")

                if passes_filters(title, location, company="Amazon"):
                    jobs.append({"company": "Amazon", "title": title,
                                 "location": location, "link": link,
                                 "number": job_id})

        print(f"Amazon: {len(jobs)} matching jobs")
    except Exception as e:
        print(f"Amazon (search.json) error: {e}")
    return jobs


# ── Combined entry point ─────────────────────────────────────────────────────

# ── Jibe/iCIMS careers front ends ────────────────────────────────────────────
# Jibe sites expose a plain JSON API at <domain>/api/jobs (NOT under sub-paths
# like /main — those serve the Angular shell). No auth, stable across
# consecutive requests; it was the HTML search page that was bot-flaky.
# Params: location, keywords, page, limit (limit raises the 10-per-page
# default; num_items/pageSize don't work). meta_data.canonical_url gives the
# public job link.

JIBE_COMPANIES = {
    # company: (domain, honors server-side ?location= filtering)
    # PepsiCo covers Frito-Lay, Gatorade and SodaStream on the same site.
    "PepsiCo":       ("https://www.pepsicojobs.com", True),
    "Publicis":      ("https://careers.publicisgroupe.com", True),
    # General Mills ignores the location param — small board, scan it all.
    "General Mills": ("https://careers.generalmills.com", False),
}

_JIBE_PAGE_CAP = 10  # safety valve: never pull more than 1000 jobs per query


def _jibe_pages(base, extra_params):
    """Yield /api/jobs payloads, following pagination until exhausted."""
    page = 1
    while page <= _JIBE_PAGE_CAP:
        params = {"page": page, "limit": 100}
        params.update(extra_params)
        r = requests.get(f"{base}/api/jobs", params=params, timeout=20,
                         headers={"User-Agent": UA, "Accept": "application/json"})
        r.raise_for_status()
        data = r.json()
        yield data
        if page * 100 >= (data.get("totalCount") or 0):
            return
        page += 1


def _crawl_jibe(company_name, base, location_filtering):
    jobs, seen = [], set()

    def consume(payload):
        for item in payload.get("jobs", []):
            data = item.get("data", {})
            title = (data.get("title") or "").strip()
            location = data.get("full_location") or data.get("short_location") or ""
            slug = str(data.get("slug") or data.get("req_id") or "")
            if not slug or slug in seen:
                continue
            seen.add(slug)
            link = ((data.get("meta_data") or {}).get("canonical_url")
                    or f"{base}/jobs/{slug}?lang=en-us")

            # Server-side location matching is fuzzy (multi-location postings
            # from other countries leak in), so always re-verify locally.
            if passes_filters(title, location, company=company_name):
                jobs.append({"company": company_name, "title": title,
                             "location": location, "link": link, "number": slug})

    if location_filtering:
        for country in TARGET_COUNTRIES:
            try:
                for payload in _jibe_pages(base, {"location": country}):
                    consume(payload)
            except Exception as e:
                print(f"{company_name} (Jibe) error for {country}: {e}")
    else:
        try:
            for payload in _jibe_pages(base, {}):
                consume(payload)
        except Exception as e:
            print(f"{company_name} (Jibe) error: {e}")

    print(f"{company_name}: {len(jobs)} matching jobs")
    return jobs


def crawl_all_jibe():
    jobs = []
    for company, (base, location_filtering) in JIBE_COMPANIES.items():
        jobs.extend(_crawl_jibe(company, base, location_filtering))
    return jobs


def crawl_all_brands_http():
    jobs = []
    jobs.extend(crawl_all_greenhouse())
    jobs.extend(crawl_all_lever())
    jobs.extend(crawl_all_smartrecruiters())
    jobs.extend(crawl_all_workable())
    jobs.extend(crawl_all_teamtailor())
    jobs.extend(crawl_all_breezy())
    jobs.extend(crawl_all_pinpoint())
    jobs.extend(crawl_all_consider())
    jobs.extend(crawl_all_jibe())
    jobs.extend(crawl_all_jobylon())
    jobs.extend(crawl_all_phenom())
    jobs.extend(crawl_all_successfactors())
    jobs.extend(crawl_all_workday_http())
    jobs.extend(crawl_puma())
    jobs.extend(crawl_all_ashby())
    jobs.extend(crawl_all_eightfold())
    jobs.extend(crawl_amazon_uk())
    return jobs
