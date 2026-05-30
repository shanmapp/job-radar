from crawlers.filters import is_relevant, matches_location
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

LOCATION_TERMS = ["united kingdom", "uk", "england", "scotland", "wales", "london",
                  "italy", "italia", "maranello", "milan", "rome", "turin",
                  "switzerland", "swiss", "geneva", "zurich", "basel"]

ROLE_KEYWORDS = ["strategy", "brand", "partnerships", "sponsorship"]


def is_relevant(title):
    title_lower = title.lower()
    return any(k in title_lower for k in ROLE_KEYWORDS)


def matches_location(location_str):
    if not location_str:
        return False
    return any(term in location_str.lower() for term in LOCATION_TERMS)


def make_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    service = webdriver.ChromeService(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def crawl_mclaren():
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://racingcareers.mclaren.com/")
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/o/']")))
        time.sleep(3)

        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/o/']"):
            href = a.get_attribute("href")
            title = a.text.strip()
            if href in seen or not title or title == "View job":
                continue
            seen.add(href)

            try:
                card = a.find_element(By.XPATH, "./ancestor::*[.//*[contains(@class,'job-location-city')]][1]")
                city = card.find_element(By.CSS_SELECTOR, "[class*='job-location-city']").text.strip()
                try:
                    country = card.find_element(By.CSS_SELECTOR, "[class*='job-location-country']").text.strip()
                except Exception:
                    country = ""
                location = f"{city}, {country}".strip(", ")
            except Exception:
                location = ""

            if is_relevant(title) and matches_location(location):
                jobs.append({
                    "company": "McLaren Racing",
                    "title": title,
                    "location": location,
                    "link": href,
                    "number": href
                })

        print(f"McLaren Racing: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"McLaren crawler error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_red_bull():
    jobs = []
    driver = make_driver()
    try:
        # Set cookie consent before loading jobs
        driver.get("https://careers.redbullracing.com")
        time.sleep(2)
        driver.add_cookie({"name": "OptanonAlertBoxClosed", "value": "2024-01-01T00:00:00.000Z", "domain": "careers.redbullracing.com"})
        driver.add_cookie({"name": "OptanonConsent", "value": "isGpcEnabled=0&datestamp=Mon+Jan+01+2024&version=202301.1.0&isIABGlobal=false&hosts=&consentId=abc&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1", "domain": "careers.redbullracing.com"})

        driver.get("https://careers.redbullracing.com/en/sites/CX_2/jobs")
        time.sleep(10)

        # Oracle renders via shadow DOM — extract job IDs from source and titles from body text
        import re
        src = driver.page_source
        job_ids = re.findall(r'careers\.redbullracing\.com/en/sites/CX_2/job/(\d+)', src)
        job_ids = list(dict.fromkeys(job_ids))  # dedupe, preserve order

        body_lines = [l.strip() for l in driver.find_element(By.TAG_NAME, "body").text.split("\n") if l.strip()]
        # Job titles appear as ALL CAPS lines in the body text
        title_lines = [l for l in body_lines if l.isupper() and len(l) > 5 and not any(x in l for x in ["JOBS", "EVENTS", "LOCATIONS", "CATEGORIES", "DATES", "ACCEPT", "DECLINE"])]

        # Pair titles with IDs (they appear in the same order)
        for i, title in enumerate(title_lines):
            link = f"https://careers.redbullracing.com/en/sites/CX_2/job/{job_ids[i]}" if i < len(job_ids) else "https://careers.redbullracing.com/en/sites/CX_2/jobs"
            if is_relevant(title):
                jobs.append({
                    "company": "Red Bull Racing",
                    "title": title.title(),
                    "location": "Milton Keynes, United Kingdom",
                    "link": link,
                    "number": link
                })

        print(f"Red Bull Racing: {len(jobs)} matching jobs (from {len(title_lines)} total)")
    except Exception as e:
        print(f"Red Bull crawler error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_mercedes():
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://www.mercedesamgf1.com/careers/vacancies")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/careers/vacancies/REQ']")))
        time.sleep(3)

        rows = driver.find_elements(By.CSS_SELECTOR, "tr[class*='vacancylist_vacancies__row']")
        for row in rows:
            try:
                link_el = row.find_element(By.CSS_SELECTOR, "a[href*='/careers/vacancies/REQ']")
                link = link_el.get_attribute("href")
                row_text = row.text.strip().split("\n")
                title = row_text[0] if row_text else ""

                # Mercedes is based in Brackley, UK — all roles UK unless stated otherwise
                location = "Brackley, United Kingdom"

                if is_relevant(title):
                    jobs.append({
                        "company": "Mercedes-AMG F1",
                        "title": title,
                        "location": location,
                        "link": link,
                        "number": link
                    })
            except Exception:
                continue

        print(f"Mercedes-AMG F1: {len(jobs)} matching jobs (from {len(rows)} total)")
    except Exception as e:
        print(f"Mercedes crawler error: {e}")
    finally:
        driver.quit()
    return jobs
