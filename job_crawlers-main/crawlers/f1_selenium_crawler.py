from crawlers.filters import is_relevant, matches_location, passes_filters
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from crawlers.driver import make_driver, quit_driver

LOCATION_TERMS = ["united kingdom", "uk", "england", "scotland", "wales", "london",
                  "italy", "italia", "maranello", "milan", "rome", "turin",
                  "switzerland", "swiss", "geneva", "zurich", "basel"]


def matches_location(location_str):
    if not location_str:
        return False
    return any(term in location_str.lower() for term in LOCATION_TERMS)


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

            if passes_filters(title, location, company="McLaren Racing"):
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
        quit_driver(driver)
    return jobs


# Red Bull Racing moved to the HTTP Oracle CX crawler and Mercedes-AMG F1 to
# the HTTP Next.js crawler (both in f1_http_crawler) — see those for details.


