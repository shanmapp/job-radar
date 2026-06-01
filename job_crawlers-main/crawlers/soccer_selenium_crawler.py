from crawlers.filters import is_relevant, matches_location
"""Selenium crawlers for soccer clubs: Man City, Chelsea, Tottenham, Bayern Munich, PSG."""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def make_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    service = webdriver.ChromeService("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)


def crawl_man_city():
    """City Football Group - uses /search-jobs with job links containing /job/ in href."""
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://careers.cityfootballgroup.com/search-jobs")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/job/']")))
        time.sleep(3)

        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/job/']"):
            href = a.get_attribute("href")
            title = a.text.strip()
            if not href or not title or href in seen or len(title) < 5:
                continue
            seen.add(href)

            # Find location: sibling text after "Location" label near this element
            try:
                container = a.find_element(By.XPATH, "./ancestor::*[count(.//*[contains(@href,'/job/')])=1][1]")
                body_text = container.text
                lines = [l.strip() for l in body_text.split("\n") if l.strip()]
                location = ""
                for i, line in enumerate(lines):
                    if "location" in line.lower() and i + 1 < len(lines):
                        location = lines[i + 1]
                        break
            except Exception:
                location = "Manchester, United Kingdom"

            if is_relevant(title):
                jobs.append({
                    "company": "Manchester City FC",
                    "title": title,
                    "location": location or "Manchester, United Kingdom",
                    "link": href,
                    "number": href
                })

        print(f"Manchester City FC: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Man City crawler error: {e}")
    finally:
        driver.quit()
    return jobs


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
        for i, line in enumerate(lines):
            if line in seen:
                continue
            # Skip navigation/form labels
            if any(w in line.lower() for w in ["search", "login", "register", "vacancies", "click", "apply", "chelsea fc", "stamford", "sessional", "contract", "results", "navigation", "criteria", "keywords", "location", "type", "copyright"]):
                continue
            if matches_keywords(line):
                seen.add(line)
                jobs.append({
                    "company": "Chelsea FC",
                    "title": line,
                    "location": "London, United Kingdom",
                    "link": "https://my.corehr.com/pls/coreportal_cfcp/erq_search_package.search_form?p_company=1001&p_internal_external=E",
                    "number": line
                })

        print(f"Chelsea FC: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Chelsea crawler error: {e}")
    finally:
        driver.quit()
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

        seen = set()
        for a in driver.find_elements(By.TAG_NAME, "a"):
            title = a.text.strip()
            href = a.get_attribute("href") or ""
            if not title or len(title) < 5 or title in seen:
                continue
            # Skip navigation links
            if any(w in title.lower() for w in ["search", "login", "register", "apply", "contact", "forgotten", "application", "profile"]):
                continue
            seen.add(title)

            if is_relevant(title):
                jobs.append({
                    "company": "Tottenham Hotspur",
                    "title": title,
                    "location": "London, United Kingdom",
                    "link": base_url,
                    "number": title
                })

        print(f"Tottenham Hotspur: {len(jobs)} matching jobs (page loaded OK)")
    except Exception as e:
        print(f"Tottenham crawler error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_bayern():
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://careers.fcbayern.com/")
        wait = WebDriverWait(driver, 20)
        time.sleep(8)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a, [class*='job'], [class*='vacancy'], [class*='position']")))
        time.sleep(2)

        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='job'], a[href*='vacanc'], a[href*='stell'], a[href*='position']"):
            href = a.get_attribute("href")
            title = a.get_attribute("textContent").strip()
            if not href or not title or href in seen or len(title) < 5:
                continue
            seen.add(href)

            try:
                card = a.find_element(By.XPATH, "./ancestor::*[.//*[contains(@class,'location') or contains(@class,'city')]][1]")
                loc_el = card.find_element(By.CSS_SELECTOR, "[class*='location'], [class*='city']")
                location = loc_el.text.strip()
            except Exception:
                location = "Munich, Germany"

            if is_relevant(title):
                jobs.append({
                    "company": "Bayern Munich",
                    "title": title,
                    "location": location,
                    "link": href,
                    "number": href
                })

        # Fallback: body text parse
        if not jobs:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            for line in body_text.split("\n"):
                line = line.strip()
                if len(line) > 5 and matches_keywords(line):
                    jobs.append({
                        "company": "Bayern Munich",
                        "title": line,
                        "location": "Munich, Germany",
                        "link": "https://careers.fcbayern.com/",
                        "number": line
                    })

        print(f"Bayern Munich: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Bayern crawler error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_psg():
    """PSG uses Workday - reuse same pattern as F1 Workday crawler."""
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://parissaintgermain.wd3.myworkdayjobs.com/rejoigneznous")
        wait = WebDriverWait(driver, 20)
        try:
            btn = driver.find_element(By.XPATH, '//*[contains(text(),"Accept") or contains(text(),"Accepter")]')
            btn.click()
            time.sleep(1)
        except Exception:
            pass
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-automation-id="jobTitle"]')))
        time.sleep(3)

        seen = set()
        for title_el in driver.find_elements(By.CSS_SELECTOR, '[data-automation-id="jobTitle"]'):
            title = title_el.text.strip()
            link = title_el.get_attribute("href") or ""
            if link in seen or not title:
                continue
            seen.add(link)

            if is_relevant(title):
                jobs.append({
                    "company": "Paris Saint-Germain",
                    "title": title,
                    "location": "Paris, France",
                    "link": link,
                    "number": link
                })

        print(f"Paris Saint-Germain: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"PSG crawler error: {e}")
    finally:
        driver.quit()
    return jobs
