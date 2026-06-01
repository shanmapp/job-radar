from crawlers.filters import is_relevant, matches_location
"""Selenium crawlers for Williams F1, Cadillac F1, Sauber/Audi F1, Alpine F1."""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def matches_location(loc):
    if not loc:
        return False
    return any(t in loc.lower() for t in LOCATION_TERMS)


def _crawl_workday_selenium(company_name, careers_url, filter_location=True):
    """Generic Workday Selenium crawler. All Workday sites share data-automation-id attributes."""
    jobs = []
    driver = make_driver()
    try:
        driver.get(careers_url)
        wait = WebDriverWait(driver, 20)
        # Accept cookies if present
        try:
            btn = driver.find_element(By.XPATH, '//*[contains(text(),"Accept") or contains(text(),"accept")]')
            btn.click()
            time.sleep(1)
        except Exception:
            pass
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-automation-id="jobTitle"]')))
        time.sleep(3)

        cards = driver.find_elements(By.CSS_SELECTOR, '[data-automation-id="compositeJobListItem"], li[class*="job"]')
        if not cards:
            cards = driver.find_elements(By.CSS_SELECTOR, '[data-automation-id="jobTitle"]')

        seen = set()
        for card in cards:
            try:
                title_el = card if card.get_attribute("data-automation-id") == "jobTitle" else card.find_element(By.CSS_SELECTOR, '[data-automation-id="jobTitle"]')
                title = title_el.text.strip()
                link = title_el.get_attribute("href") or ""

                loc_els = card.find_elements(By.CSS_SELECTOR, '[data-automation-id="location"], [data-automation-id="locationText"], dd[class*="location"]')
                location = loc_els[0].text.strip() if loc_els else ""

                if link in seen or not title:
                    continue
                seen.add(link)

                location_ok = (not filter_location) or matches_location(location)
                if is_relevant(title) and location_ok:
                    jobs.append({
                        "company": company_name,
                        "title": title,
                        "location": location,
                        "link": link,
                        "number": link
                    })
            except Exception:
                continue

        print(f"{company_name}: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"{company_name} Workday crawler error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_alpine():
    return _crawl_workday_selenium(
        "Alpine F1",
        "https://alliancewd.wd3.myworkdayjobs.com/alpine-racing-careers",
        filter_location=True
    )


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


def crawl_williams():
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://careers.williamsf1.com/")
        wait = WebDriverWait(driver, 20)
        time.sleep(6)

        # Attrax renders job cards - look for job links
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/job/'], a[href*='vacancy'], [class*='job']")))
        time.sleep(2)

        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/job/']"):
            href = a.get_attribute("href")
            title = a.get_attribute("textContent").strip()
            if not href or not title or href in seen or len(title) < 3:
                continue
            seen.add(href)

            try:
                card = a.find_element(By.XPATH, "./ancestor::*[.//*[contains(@class,'location') or contains(@class,'city')]][1]")
                loc_el = card.find_element(By.CSS_SELECTOR, "[class*='location'], [class*='city']")
                location = loc_el.text.strip()
            except Exception:
                location = "Grove, United Kingdom"

            if is_relevant(title) and matches_location(location):
                jobs.append({
                    "company": "Williams F1",
                    "title": title,
                    "location": location,
                    "link": href,
                    "number": href
                })

        print(f"Williams F1: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Williams crawler error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_cadillac():
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://cadillacf1team.workable.com/")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li[data-ui='job'], .jobs-list li, a[href*='/j/']")))
        time.sleep(3)

        for li in driver.find_elements(By.CSS_SELECTOR, "li[data-ui='job'], .jobs-list li"):
            try:
                a = li.find_element(By.TAG_NAME, "a")
                title = li.find_element(By.CSS_SELECTOR, "h3, h2, [class*='title']").text.strip()
                href = a.get_attribute("href")
                loc_els = li.find_elements(By.CSS_SELECTOR, "[class*='location'], [class*='city'], [data-ui='job-location']")
                location = loc_els[0].text.strip() if loc_els else "United Kingdom"

                if is_relevant(title) and matches_location(location):
                    jobs.append({
                        "company": "Cadillac F1",
                        "title": title,
                        "location": location,
                        "link": href,
                        "number": href
                    })
            except Exception:
                continue

        print(f"Cadillac F1: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Cadillac crawler error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_sauber():
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://www.sauber-group.com/corporate/jobs")
        time.sleep(12)  # React SPA needs extra load time

        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='job'], a[href*='position'], a[href*='vacancy']"):
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
                location = "Hinwil, Switzerland"

            if is_relevant(title) and matches_location(location):
                jobs.append({
                    "company": "Audi F1 (Sauber)",
                    "title": title,
                    "location": location,
                    "link": href,
                    "number": href
                })

        print(f"Audi F1 (Sauber): {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Sauber crawler error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_formula1():
    """Formula 1 uses Workday at formulaone.wd3.myworkdayjobs.com."""
    return _crawl_workday_selenium(
        "Formula 1",
        "https://formulaone.wd3.myworkdayjobs.com/F1",
        filter_location=True
    )
