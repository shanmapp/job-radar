"""
Selenium crawlers for brand companies.
Workday companies reuse the generic _crawl_workday_selenium pattern.
Custom sites each have their own scraping logic.
"""
import time
import concurrent.futures
from functools import partial
from crawlers.filters import is_relevant, matches_location
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from crawlers.brands_config import WORKDAY_COMPANIES, SELENIUM_COMPANIES


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


# ── Workday (all brand Workday companies share the same DOM) ─────────────────

def _crawl_workday(company_name, careers_url):
    jobs = []
    driver = make_driver()
    try:
        driver.get(careers_url)
        wait = WebDriverWait(driver, 20)
        try:
            driver.find_element(By.XPATH, '//*[contains(text(),"Accept") or contains(text(),"accept")]').click()
            time.sleep(1)
        except Exception:
            pass
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-automation-id="jobTitle"]')))
        time.sleep(3)

        seen = set()
        cards = driver.find_elements(By.CSS_SELECTOR, '[data-automation-id="compositeJobListItem"]') or \
                driver.find_elements(By.CSS_SELECTOR, '[data-automation-id="jobTitle"]')

        for card in cards:
            try:
                title_el = card if card.get_attribute("data-automation-id") == "jobTitle" \
                           else card.find_element(By.CSS_SELECTOR, '[data-automation-id="jobTitle"]')
                title = title_el.text.strip()
                link = title_el.get_attribute("href") or ""
                if link in seen or not title:
                    continue
                seen.add(link)

                loc_els = card.find_elements(By.CSS_SELECTOR,
                    '[data-automation-id="location"],[data-automation-id="locationText"],dd[class*="location"]')
                location = loc_els[0].text.strip() if loc_els else ""

                if is_relevant(title) and matches_location(location):
                    jobs.append({"company": company_name, "title": title,
                                 "location": location, "link": link, "number": link})
            except Exception:
                continue

        print(f"{company_name}: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"{company_name} (Workday) error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_all_workday():
    tasks = [partial(_crawl_workday, name, url) for name, url in WORKDAY_COMPANIES.items()]
    jobs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        for result in executor.map(lambda f: f(), tasks):
            jobs.extend(result or [])
    return jobs


# ── Custom site crawlers ─────────────────────────────────────────────────────

def _crawl_generic(company_name, url, job_sel, title_sel, location_sel=None, link_attr="href"):
    """Generic crawler for sites with consistent job card structure."""
    jobs = []
    driver = make_driver()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        try:
            driver.find_element(By.XPATH, '//*[contains(text(),"Accept") or contains(text(),"Agree")]').click()
            time.sleep(1)
        except Exception:
            pass
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, job_sel)))
        time.sleep(4)

        seen = set()
        for card in driver.find_elements(By.CSS_SELECTOR, job_sel):
            try:
                title_el = card.find_element(By.CSS_SELECTOR, title_sel)
                title = title_el.text.strip()
                link = (title_el.get_attribute(link_attr) or
                        card.find_element(By.TAG_NAME, "a").get_attribute("href") or "")
                if link in seen or not title:
                    continue
                seen.add(link)

                location = ""
                if location_sel:
                    loc_els = card.find_elements(By.CSS_SELECTOR, location_sel)
                    location = loc_els[0].text.strip() if loc_els else ""

                if is_relevant(title) and matches_location(location):
                    jobs.append({"company": company_name, "title": title,
                                 "location": location, "link": link, "number": link})
            except Exception:
                continue

        print(f"{company_name}: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"{company_name} error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_netflix():
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://explore.jobs.netflix.net/careers")
        wait = WebDriverWait(driver, 20)
        try:
            driver.find_element(By.XPATH, '//*[contains(text(),"Accept")]').click()
            time.sleep(1)
        except Exception:
            pass
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='job'], [class*='JobCard'], [class*='result'], a[href*='/careers/']")))
        time.sleep(4)

        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/careers/jobs/']"):
            href = a.get_attribute("href")
            title = a.text.strip() or a.get_attribute("textContent").strip()
            if not href or not title or href in seen or len(title) < 5:
                continue
            seen.add(href)

            try:
                card = a.find_element(By.XPATH, "./ancestor::*[.//*[contains(@class,'location') or contains(text(),'London') or contains(text(),'United Kingdom')]][1]")
                loc_els = card.find_elements(By.CSS_SELECTOR, "[class*='location'],[class*='Location']")
                location = loc_els[0].text.strip() if loc_els else ""
            except Exception:
                location = ""

            if is_relevant(title) and matches_location(location):
                jobs.append({"company": "Netflix", "title": title,
                             "location": location, "link": href, "number": href})

        print(f"Netflix: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Netflix error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_nike():
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://careers.nike.com/jobs?q=brand+OR+partnerships+OR+sponsorship&l=United+Kingdom&country=United+Kingdom")
        wait = WebDriverWait(driver, 20)
        try:
            driver.find_element(By.XPATH, '//*[contains(text(),"Accept")]').click()
            time.sleep(1)
        except Exception:
            pass
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='job'], a[href*='/job/']")))
        time.sleep(4)

        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/job/']"):
            href = a.get_attribute("href")
            title = a.text.strip()
            if not href or not title or href in seen or len(title) < 5:
                continue
            seen.add(href)
            try:
                card = a.find_element(By.XPATH, "./ancestor::*[.//*[contains(@class,'location')]  ][1]")
                loc_els = card.find_elements(By.CSS_SELECTOR, "[class*='location']")
                location = loc_els[0].text.strip() if loc_els else "United Kingdom"
            except Exception:
                location = "United Kingdom"

            if is_relevant(title) and matches_location(location):
                jobs.append({"company": "Nike", "title": title,
                             "location": location, "link": href, "number": href})

        print(f"Nike: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Nike error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_adidas():
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://careers.adidas-group.com/jobs?q=brand+OR+partnerships+OR+sponsorship&country=GBR")
        wait = WebDriverWait(driver, 20)
        try:
            driver.find_element(By.XPATH, '//*[contains(text(),"Accept") or contains(text(),"Agree")]').click()
            time.sleep(1)
        except Exception:
            pass
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='job'], a[href*='/jobs/']")))
        time.sleep(5)

        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/jobs/']"):
            href = a.get_attribute("href")
            title = a.text.strip()
            if not href or not title or href in seen or len(title) < 5 or href == driver.current_url:
                continue
            seen.add(href)
            try:
                card = a.find_element(By.XPATH, "./ancestor::*[.//*[contains(@class,'location') or contains(@class,'city')]  ][1]")
                loc_els = card.find_elements(By.CSS_SELECTOR, "[class*='location'],[class*='city']")
                location = loc_els[0].text.strip() if loc_els else ""
            except Exception:
                location = ""

            if is_relevant(title) and matches_location(location):
                jobs.append({"company": "Adidas", "title": title,
                             "location": location, "link": href, "number": href})

        print(f"Adidas: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Adidas error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_red_bull_brand():
    """Red Bull (drink company) - separate from Red Bull Racing F1."""
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://jobs.redbull.com/gb-en/jobs")
        wait = WebDriverWait(driver, 20)
        try:
            driver.find_element(By.XPATH, '//*[contains(text(),"Accept")]').click()
            time.sleep(1)
        except Exception:
            pass
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/jobs/'], [class*='job'], [class*='JobCard']")))
        time.sleep(5)

        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/jobs/']"):
            href = a.get_attribute("href")
            title = a.text.strip() or a.get_attribute("textContent").strip()
            if not href or not title or href in seen or len(title) < 5 or href.endswith("/jobs/"):
                continue
            seen.add(href)
            try:
                card = a.find_element(By.XPATH, "./ancestor::*[.//*[contains(@class,'location') or contains(text(),'United Kingdom')]  ][1]")
                loc_els = card.find_elements(By.CSS_SELECTOR, "[class*='location'],[class*='city']")
                location = loc_els[0].text.strip() if loc_els else ""
            except Exception:
                location = ""

            if is_relevant(title) and matches_location(location):
                jobs.append({"company": "Red Bull", "title": title,
                             "location": location, "link": href, "number": href})

        print(f"Red Bull: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Red Bull error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_ea():
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://jobs.ea.com/en_US/careers/SearchJobs/brand OR partnerships OR sponsorship?3_112_3=175297")
        wait = WebDriverWait(driver, 20)
        time.sleep(6)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='ShowJob'], [class*='job'], tr")))
        time.sleep(3)

        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='ShowJob']"):
            href = a.get_attribute("href")
            title = a.text.strip()
            if not href or not title or href in seen:
                continue
            seen.add(href)
            try:
                row = a.find_element(By.XPATH, "./ancestor::tr[1]")
                tds = row.find_elements(By.TAG_NAME, "td")
                location = tds[1].text.strip() if len(tds) > 1 else "United Kingdom"
            except Exception:
                location = "United Kingdom"

            if is_relevant(title) and matches_location(location):
                jobs.append({"company": "EA Sports", "title": title,
                             "location": location, "link": href, "number": href})

        print(f"EA Sports: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"EA Sports error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_amazon_studios():
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://www.amazon.jobs/en/search?base_query=brand+OR+partnerships+OR+sponsorship&loc_query=United+Kingdom&business_category%5B%5D=amazon-studios")
        wait = WebDriverWait(driver, 20)
        time.sleep(5)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".job-tile, [class*='job-tile'], a[href*='/jobs/']")))
        time.sleep(3)

        seen = set()
        for tile in driver.find_elements(By.CSS_SELECTOR, ".job-tile, [class*='job-tile']"):
            try:
                title_el = tile.find_element(By.CSS_SELECTOR, "h3 a, .job-title a, a")
                title = title_el.text.strip()
                href = title_el.get_attribute("href") or ""
                if not title or href in seen:
                    continue
                seen.add(href)

                loc_els = tile.find_elements(By.CSS_SELECTOR, ".location, [class*='location']")
                location = loc_els[0].text.strip() if loc_els else "United Kingdom"

                if is_relevant(title) and matches_location(location):
                    jobs.append({"company": "Amazon Studios", "title": title,
                                 "location": location, "link": href, "number": href})
            except Exception:
                continue

        print(f"Amazon Studios: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Amazon Studios error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_apple():
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://jobs.apple.com/en-gb/search?q=brand+OR+partnerships+OR+sponsorship&location=united-kingdom-GBR")
        wait = WebDriverWait(driver, 20)
        time.sleep(5)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='table--advanced-search'] tr, .result--two-lines, a[href*='/en-gb/details/']")))
        time.sleep(3)

        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/en-gb/details/']"):
            href = a.get_attribute("href")
            title = a.text.strip()
            if not href or not title or href in seen:
                continue
            seen.add(href)
            try:
                row = a.find_element(By.XPATH, "./ancestor::tr[1]")
                tds = row.find_elements(By.TAG_NAME, "td")
                location = tds[-1].text.strip() if tds else "United Kingdom"
            except Exception:
                location = "United Kingdom"

            if is_relevant(title) and matches_location(location):
                jobs.append({"company": "Apple", "title": title,
                             "location": location, "link": href, "number": href})

        print(f"Apple: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Apple error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_nintendo():
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://careers.nintendo.com/job-openings/?location=United+Kingdom")
        wait = WebDriverWait(driver, 20)
        time.sleep(6)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='job'], a[href*='job'], tr")))
        time.sleep(3)

        seen = set()
        body_lines = [l.strip() for l in driver.find_element(By.TAG_NAME, "body").text.split("\n") if l.strip()]
        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='job']")

        for a in links:
            href = a.get_attribute("href") or ""
            title = a.text.strip()
            if not title or href in seen or len(title) < 5:
                continue
            seen.add(href)
            if is_relevant(title):
                jobs.append({"company": "Nintendo", "title": title,
                             "location": "United Kingdom", "link": href, "number": href})

        print(f"Nintendo: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Nintendo error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_patagonia():
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://www.patagonia.com/jobs-at-patagonia/")
        wait = WebDriverWait(driver, 20)
        time.sleep(6)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='job'], [class*='job'], [class*='position']")))
        time.sleep(3)

        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='job'], a[href*='career']"):
            href = a.get_attribute("href")
            title = a.text.strip()
            if not href or not title or href in seen or len(title) < 5:
                continue
            seen.add(href)
            try:
                card = a.find_element(By.XPATH, "./ancestor::*[.//*[contains(@class,'location') or contains(@class,'city')]  ][1]")
                loc_els = card.find_elements(By.CSS_SELECTOR, "[class*='location'],[class*='city']")
                location = loc_els[0].text.strip() if loc_els else ""
            except Exception:
                location = ""

            if is_relevant(title) and matches_location(location):
                jobs.append({"company": "Patagonia", "title": title,
                             "location": location, "link": href, "number": href})

        print(f"Patagonia: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Patagonia error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_notion():
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://www.notion.so/careers")
        wait = WebDriverWait(driver, 20)
        time.sleep(6)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/careers/'], [class*='job'], [class*='role']")))
        time.sleep(3)

        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/careers/']"):
            href = a.get_attribute("href")
            title = a.text.strip() or a.get_attribute("textContent").strip()
            if not href or not title or href in seen or len(title) < 5 or href.endswith("/careers/"):
                continue
            seen.add(href)
            try:
                card = a.find_element(By.XPATH, "./ancestor::*[.//*[contains(@class,'location')]  ][1]")
                loc_els = card.find_elements(By.CSS_SELECTOR, "[class*='location']")
                location = loc_els[0].text.strip() if loc_els else ""
            except Exception:
                location = ""

            if is_relevant(title) and matches_location(location):
                jobs.append({"company": "Notion", "title": title,
                             "location": location, "link": href, "number": href})

        print(f"Notion: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Notion error: {e}")
    finally:
        driver.quit()
    return jobs


def crawl_gucci():
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://kering.wd3.myworkdayjobs.com/Kering")
        wait = WebDriverWait(driver, 20)
        try:
            driver.find_element(By.XPATH, '//*[contains(text(),"Accept")]').click()
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
            # Filter to Gucci brand roles only
            if "gucci" not in title.lower() and "gucci" not in link.lower():
                # still include if keyword matches — Kering board has all brands
                pass
            if is_relevant(title) and matches_location("United Kingdom"):  # Kering UK office
                jobs.append({"company": "Gucci / Kering", "title": title,
                             "location": "United Kingdom", "link": link, "number": link})

        print(f"Gucci/Kering: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Gucci/Kering error: {e}")
    finally:
        driver.quit()
    return jobs


# ── Combined entry point ─────────────────────────────────────────────────────

CUSTOM_CRAWLERS = [
    crawl_netflix, crawl_nike, crawl_adidas, crawl_red_bull_brand,
    crawl_ea, crawl_amazon_studios, crawl_apple, crawl_nintendo,
    crawl_patagonia, crawl_notion, crawl_gucci,
]


def crawl_all_brands_selenium():
    workday_tasks = [partial(_crawl_workday, name, url) for name, url in WORKDAY_COMPANIES.items()]
    all_tasks = workday_tasks + CUSTOM_CRAWLERS

    jobs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        for result in executor.map(lambda f: f(), all_tasks):
            jobs.extend(result or [])
    return jobs
