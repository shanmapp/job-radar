from crawlers.filters import is_relevant, matches_location, passes_filters, matches_keywords
"""Selenium crawlers for soccer clubs: Man City, Chelsea, Tottenham, Bayern Munich, PSG."""
import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from crawlers.driver import make_driver, quit_driver
from crawlers.silent_zero import report as _report_raw


# Manchester City moved to the HTTP SuccessFactors crawler
# (soccer_http_crawler.crawl_man_city) — its coreCSB board is server-rendered.


def crawl_chelsea():
    """Chelsea uses CoreHR (Oracle APEX). Submit form then parse body text for job titles."""
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://my.corehr.com/pls/coreportal_cfcp/erq_search_package.search_form?p_company=1001&p_internal_external=E")
        wait = WebDriverWait(driver, 20)
        time.sleep(4)

        # Submit the search form
        driver.execute_script("callErecruitDoSearch.submit()")
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(),"results") or contains(text(),"Vacancies")]')))
        time.sleep(3)

        body_text = driver.find_element(By.TAG_NAME, "body").text
        lines = [l.strip() for l in body_text.split("\n") if l.strip() and len(l.strip()) > 5]

        # Job titles appear before "Apply" in the listing
        seen = set()
        candidates = set()  # plausible vacancy-title lines (raw board proxy)
        for i, line in enumerate(lines):
            if line in seen:
                continue
            # Skip navigation/form labels
            if any(w in line.lower() for w in ["search", "login", "register", "vacancies", "click", "apply", "chelsea fc", "stamford", "sessional", "contract", "results", "navigation", "criteria", "keywords", "location", "type", "copyright"]):
                continue
            candidates.add(line)
            if matches_keywords(line):
                seen.add(line)
                jobs.append({
                    "company": "Chelsea FC",
                    "title": line,
                    "location": "London, United Kingdom",
                    "link": "https://my.corehr.com/pls/coreportal_cfcp/erq_search_package.search_form?p_company=1001&p_internal_external=E",
                    "number": line
                })

        # Raw board size: prefer CoreHR's own "N vacancies/results" count,
        # fall back to the number of candidate title lines.
        m = re.search(r'(\d+)\s+(?:vacanc|result|match|position)', body_text, re.I)
        _report_raw("Chelsea FC", int(m.group(1)) if m else len(candidates))
        print(f"Chelsea FC: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Chelsea crawler error: {e}")
    finally:
        quit_driver(driver)
    return jobs


def crawl_tottenham():
    """WebRecruit (MHR) - jobs are anchor tags with javascript:void(0) hrefs, listed by text."""
    jobs = []
    driver = make_driver()
    base_url = "https://ce0812li.webitrent.com/ce0812li_webrecruitment/wrd/run/etrec179gf.open?wvid=9447152BOp"
    try:
        driver.get(base_url)
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(),"matches found") or contains(text(),"Results")]')))
        time.sleep(3)

        seen = set()  # candidate job-listing anchors (non-nav) = raw board proxy
        for a in driver.find_elements(By.TAG_NAME, "a"):
            title = a.text.strip()
            href = a.get_attribute("href") or ""
            if not title or len(title) < 5 or title in seen:
                continue
            # Skip navigation links
            if any(w in title.lower() for w in ["search", "login", "register", "apply", "contact", "forgotten", "application", "profile"]):
                continue
            seen.add(title)

            if passes_filters(title, company="Tottenham Hotspur"):
                jobs.append({
                    "company": "Tottenham Hotspur",
                    "title": title,
                    "location": "London, United Kingdom",
                    "link": base_url,
                    "number": title
                })

        # Raw board size: prefer WebRecruit's own "N matches found" count, fall
        # back to the number of candidate (non-nav) job anchors.
        m = re.search(r'(\d+)\s+matches?\s+found',
                      driver.find_element(By.TAG_NAME, "body").text, re.I)
        _report_raw("Tottenham Hotspur", int(m.group(1)) if m else len(seen))
        print(f"Tottenham Hotspur: {len(jobs)} matching jobs (page loaded OK)")
    except Exception as e:
        print(f"Tottenham crawler error: {e}")
    finally:
        quit_driver(driver)
    return jobs


# Bayern Munich moved to the HTTP SuccessFactors crawler
# (soccer_http_crawler.crawl_bayern) — careers.fcbayern.com/search/ is a
# server-rendered SF board.
#
# PSG moved to the HTTP Workday crawler (soccer_http_crawler.crawl_psg) — its
# Workday board is fully reachable via the CXS JSON API, so Selenium was
# redundant.
