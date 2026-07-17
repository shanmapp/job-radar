"""
Selenium crawlers for brand companies.
Workday companies reuse the generic _crawl_workday_selenium pattern.
Custom sites each have their own scraping logic.
"""
import time
import concurrent.futures
from functools import partial
from crawlers.filters import is_relevant, matches_location, passes_filters
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from crawlers.driver import make_driver, quit_driver
from crawlers.brands_config import WORKDAY_COMPANIES, SELENIUM_COMPANIES, HEURISTIC_COMPANIES


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

                if passes_filters(title, location):
                    jobs.append({"company": company_name, "title": title,
                                 "location": location, "link": link, "number": link})
            except Exception:
                continue

        print(f"{company_name}: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"{company_name} (Workday) error: {e}")
    finally:
        quit_driver(driver)
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

                if passes_filters(title, location):
                    jobs.append({"company": company_name, "title": title,
                                 "location": location, "link": link, "number": link})
            except Exception:
                continue

        print(f"{company_name}: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"{company_name} error: {e}")
    finally:
        quit_driver(driver)
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

            if passes_filters(title, location):
                jobs.append({"company": "Nike", "title": title,
                             "location": location, "link": href, "number": href})

        print(f"Nike: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Nike error: {e}")
    finally:
        quit_driver(driver)
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

            if passes_filters(title, location):
                jobs.append({"company": "Adidas", "title": title,
                             "location": location, "link": href, "number": href})

        print(f"Adidas: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Adidas error: {e}")
    finally:
        quit_driver(driver)
    return jobs


def crawl_red_bull_brand():
    """Red Bull (drink company) - separate from Red Bull Racing F1.
    Site redesign killed the old /gb-en/jobs listing (404); jobs now live at
    /gb-en/results?locations=<id> with per-job links like /gb-en/<slug>-ref<id>."""
    jobs = []
    driver = make_driver()
    try:
        driver.get("https://jobs.redbull.com/gb-en/results?locations=2060")
        wait = WebDriverWait(driver, 20)
        try:
            driver.find_element(By.XPATH, '//*[contains(text(),"Accept")]').click()
            time.sleep(1)
        except Exception:
            pass
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='-ref']")))
        time.sleep(5)

        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='-ref']"):
            href = a.get_attribute("href")
            if not href or href in seen:
                continue
            seen.add(href)
            lines = [l.strip() for l in a.text.split("\n") if l.strip()]
            # layout: "<Category><EmploymentType>" / Title / Location, ...
            title = lines[1] if len(lines) > 1 else ""
            location = lines[2] if len(lines) > 2 else ""
            if title and passes_filters(title, location):
                jobs.append({"company": "Red Bull", "title": title,
                             "location": location, "link": href, "number": href})

        print(f"Red Bull: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Red Bull error: {e}")
    finally:
        quit_driver(driver)
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

            if passes_filters(title, location):
                jobs.append({"company": "EA Sports", "title": title,
                             "location": location, "link": href, "number": href})

        print(f"EA Sports: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"EA Sports error: {e}")
    finally:
        quit_driver(driver)
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

            if passes_filters(title, location):
                jobs.append({"company": "Apple", "title": title,
                             "location": location, "link": href, "number": href})

        print(f"Apple: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Apple error: {e}")
    finally:
        quit_driver(driver)
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
            if passes_filters(title):
                jobs.append({"company": "Nintendo", "title": title,
                             "location": "United Kingdom", "link": href, "number": href})

        print(f"Nintendo: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Nintendo error: {e}")
    finally:
        quit_driver(driver)
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

            if passes_filters(title, location):
                jobs.append({"company": "Patagonia", "title": title,
                             "location": location, "link": href, "number": href})

        print(f"Patagonia: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Patagonia error: {e}")
    finally:
        quit_driver(driver)
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
        wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, '[data-automation-id="jobTitle"]')
                   or "no job openings" in d.find_element(By.TAG_NAME, "body").text.lower())
        time.sleep(3)

        if not driver.find_elements(By.CSS_SELECTOR, '[data-automation-id="jobTitle"]'):
            print("Gucci/Kering: 0 matching jobs (no openings currently listed)")
            return jobs

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
            if passes_filters(title, "United Kingdom"):  # Kering UK office
                jobs.append({"company": "Gucci / Kering", "title": title,
                             "location": "United Kingdom", "link": link, "number": link})

        print(f"Gucci/Kering: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Gucci/Kering error: {e}")
    finally:
        quit_driver(driver)
    return jobs


# ── ATP Tour (HiBob) ──────────────────────────────────────────────────────────

def crawl_atp():
    """ATP uses HiBob (Angular SPA). Job cards are <careers-ui-job-listing-list-item>
    elements with no real per-job href (client-side routing only), so we link back
    to the jobs page itself — same fallback pattern as crawl_chelsea below."""
    jobs = []
    driver = make_driver()
    url = "https://atptourinc.careers.hibob.com/jobs"
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "careers-ui-job-listing-list-item")))
        time.sleep(3)

        for item in driver.find_elements(By.CSS_SELECTOR, "careers-ui-job-listing-list-item"):
            try:
                title = item.find_element(By.CSS_SELECTOR, ".b-heading span").text.strip()
                lines = [l.strip() for l in item.text.split("\n") if l.strip()]
                # second line is "Department · Location · EmploymentType · WorkspaceType"
                parts = [p.strip() for p in lines[1].split("·")] if len(lines) > 1 else []
                location = parts[1] if len(parts) > 1 else ""

                if passes_filters(title, location):
                    jobs.append({"company": "ATP Tour", "title": title,
                                 "location": location, "link": url, "number": title})
            except Exception:
                continue

        print(f"ATP Tour: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"ATP Tour error: {e}")
    finally:
        quit_driver(driver)
    return jobs


# ── Manchester United (CandidateManager) ──────────────────────────────────────

def crawl_man_utd():
    jobs = []
    driver = make_driver()
    url = "https://www.candidatemanager.net/cm/p/pJobs.aspx?mid=YFDU&sid=YAZAZEV"
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='pJobDetails']")))
        time.sleep(2)

        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='pJobDetails']"):
            href = a.get_attribute("href") or ""
            title = a.text.strip()
            if not title or href in seen:
                continue
            seen.add(href)
            try:
                row = a.find_element(By.XPATH, "./ancestor::tr[1]")
                tds = row.find_elements(By.TAG_NAME, "td")
                location = tds[2].text.strip() if len(tds) > 2 else "Manchester, United Kingdom"
            except Exception:
                location = "Manchester, United Kingdom"

            if passes_filters(title, location):
                jobs.append({"company": "Manchester United", "title": title,
                             "location": location, "link": href, "number": href})

        print(f"Manchester United: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Manchester United error: {e}")
    finally:
        quit_driver(driver)
    return jobs


# ── LVMH group job hub ────────────────────────────────────────────────────────
# lvmh.com/en/join-us/our-job-offers aggregates every maison (Moët Hennessy,
# Louis Vuitton, Dior, Sephora, ...). The listing is Algolia-backed and the
# `query` URL param performs a server-side full-text search, so one page load
# per role keyword covers the whole group. The underlying /api/search endpoint
# is Akamai bot-walled (503 to non-browser requests), hence Selenium.
# Each query page shows the ~10 newest matches (index is timestamp-desc),
# which is sufficient for a radar polling every 15-60 minutes.

LVMH_QUERIES = ["sponsorship", "partnership", "brand", "licensing", "strategy", "sport"]

def crawl_lvmh():
    jobs = []
    driver = make_driver()
    try:
        seen = set()
        for q in LVMH_QUERIES:
            driver.get(f"https://www.lvmh.com/en/join-us/our-job-offers?query={q}")
            try:
                WebDriverWait(driver, 15).until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "a[href*='/join-us/our-job-offers/']")))
            except Exception:
                continue  # no results for this keyword
            time.sleep(2)

            for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/join-us/our-job-offers/']"):
                href = a.get_attribute("href") or ""
                title = a.text.strip()
                if not title or href in seen:
                    continue
                seen.add(href)

                # Card layout: Title / MAISON / REFERENCE / ... /
                # "Place of employment :" / <location> / ...
                company, location = "LVMH", ""
                try:
                    card = a.find_element(By.XPATH,
                        "./ancestor::*[contains(., 'Place of employment')][1]")
                    lines = [l.strip() for l in card.text.split("\n") if l.strip()]
                    if len(lines) > 1 and lines[0].lower() == title.lower():
                        company = lines[1].title()
                    for i, line in enumerate(lines):
                        if line.lower().startswith("place of employment") and i + 1 < len(lines):
                            location = lines[i + 1]
                            break
                except Exception:
                    pass

                if passes_filters(title, location):
                    jobs.append({"company": company, "title": title,
                                 "location": location, "link": href, "number": href})

        print(f"LVMH hub: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"LVMH hub error: {e}")
    finally:
        quit_driver(driver)
    return jobs


# ── TeamWork Online (New York Yankees, LA Lakers) ─────────────────────────────

def _crawl_teamworkonline(company_name, url, default_location=""):
    jobs = []
    driver = make_driver()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.organization-portal__job-details")))
        time.sleep(3)

        seen = set()
        for card in driver.find_elements(By.CSS_SELECTOR, "div.organization-portal__job-details"):
            try:
                a = card.find_element(By.TAG_NAME, "a")
                href = a.get_attribute("href") or ""
                if href in seen:
                    continue
                seen.add(href)

                lines = [l.strip() for l in card.text.split("\n") if l.strip()]
                title = lines[0] if lines else ""
                # lines are: [title, org name, "City · ST", level/department]
                location = lines[2] if len(lines) > 2 else default_location

                if passes_filters(title, location):
                    jobs.append({"company": company_name, "title": title,
                                 "location": location, "link": href, "number": href})
            except Exception:
                continue

        print(f"{company_name}: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"{company_name} error: {e}")
    finally:
        quit_driver(driver)
    return jobs


def crawl_yankees():
    url = ("https://www.teamworkonline.com/baseball-jobs/baseballjobs/major-league-baseball"
           "?employment_opportunity_search%5Bquery%5D=&employment_opportunity_search%5Bcategory_id%5D="
           "&employment_opportunity_search%5Borganization_id%5D=28229")
    return _crawl_teamworkonline("New York Yankees", url, "New York, United States")


def crawl_lakers():
    url = "https://www.teamworkonline.com/basketball-jobs/los-angeles-lakers/los-angeles-lakers-jobs"
    return _crawl_teamworkonline("LA Lakers", url, "Los Angeles, United States")


# ── Generic heuristic crawler (no known ATS / no clean API) ──────────────────

def _crawl_heuristic(company_name, url, default_location=""):
    """Fallback crawler for sites with no recognizable ATS: follows any
    job/career/vacancy-looking link, then looks for a location near it in
    the DOM. Same resilient pattern already used by crawl_nike/crawl_patagonia
    above."""
    jobs = []
    driver = make_driver()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        try:
            driver.find_element(By.XPATH,
                '//*[contains(text(),"Accept") or contains(text(),"Agree") or contains(text(),"Consent")]').click()
            time.sleep(1)
        except Exception:
            pass

        link_sel = "a[href*='job'], a[href*='career'], a[href*='vacan'], a[href*='position'], a[href*='req']"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, link_sel)))
        time.sleep(5)

        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, link_sel):
            href = a.get_attribute("href") or ""
            title = (a.text or a.get_attribute("textContent") or "").strip()
            if not href or not title or href in seen or len(title) < 5 or href.rstrip("/") == url.rstrip("/"):
                continue
            seen.add(href)

            location = default_location
            try:
                card = a.find_element(By.XPATH,
                    "./ancestor::*[.//*[contains(@class,'location') or contains(@class,'city')]][1]")
                loc_els = card.find_elements(By.CSS_SELECTOR, "[class*='location'],[class*='city']")
                if loc_els and loc_els[0].text.strip():
                    location = loc_els[0].text.strip()
            except Exception:
                pass

            if passes_filters(title, location):
                jobs.append({"company": company_name, "title": title,
                             "location": location, "link": href, "number": href})

        print(f"{company_name}: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"{company_name} error: {e}")
    finally:
        quit_driver(driver)
    return jobs


# ── Paramount (SAP SuccessFactors, UK-jobs category page) ────────────────────

def crawl_paramount():
    """Paramount's SuccessFactors instance exposes a static UK-scoped category
    page (/go/UK-Jobs/...) that server-renders real listings — no auth wall,
    unlike the Hershey/Nestle/Ferrero SF instances tried in this pass."""
    jobs = []
    driver = make_driver()
    url = "https://careers.paramount.com/go/UK-Jobs/8711800/"
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.jobTitle-link")))
        time.sleep(2)

        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a.jobTitle-link"):
            href = a.get_attribute("href") or ""
            title = a.text.strip()
            if not title or href in seen:
                continue
            seen.add(href)
            try:
                li = a.find_element(By.XPATH, "./ancestor::li[1]")
                li_lines = li.text.splitlines()
                location = li_lines[li_lines.index("Location") + 1] if "Location" in li_lines else "London, United Kingdom"
            except Exception:
                location = "London, United Kingdom"

            if passes_filters(title, location):
                jobs.append({"company": "Paramount", "title": title,
                             "location": location, "link": href, "number": href})

        print(f"Paramount: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Paramount error: {e}")
    finally:
        quit_driver(driver)
    return jobs


# ── Ferrero (custom careers site) ────────────────────────────────────────────

def crawl_ferrero():
    jobs = []
    driver = make_driver()
    url = "https://www.ferrerocareers.com/int/en/jobs"
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/int/en/jobs/']")))
        time.sleep(2)

        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/int/en/jobs/']"):
            href = a.get_attribute("href") or ""
            if href in seen or href.rstrip("/") == url.rstrip("/"):
                continue
            seen.add(href)
            try:
                card = a.find_element(By.XPATH, "./ancestor::article[1]")
                lines = [l.strip() for l in card.text.split("\n") if l.strip()]
                title = lines[0] if lines else ""
                # layout: Title / Department / "Job ID:" / <id> / Location / EmploymentType / Details
                location = lines[lines.index("Job ID:") + 2] if "Job ID:" in lines else ""
            except Exception:
                title, location = "", ""

            if title and passes_filters(title, location):
                jobs.append({"company": "Ferrero", "title": title,
                             "location": location, "link": href, "number": href})

        print(f"Ferrero: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Ferrero error: {e}")
    finally:
        quit_driver(driver)
    return jobs


# ── Nestle (custom Drupal careers site) ──────────────────────────────────────

def crawl_nestle():
    jobs = []
    driver = make_driver()
    url = "https://www.nestlejobs.com/job-search"
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/job/']"):
            href = a.get_attribute("href") or ""
            if href in seen:
                continue
            seen.add(href)
            lines = [l.strip() for l in a.text.split("\n") if l.strip()]
            title = lines[1] if len(lines) > 1 else (lines[0] if lines else "")
            location = next((l.replace("Location(s): ", "") for l in lines if l.startswith("Location(s):")), "")

            if title and passes_filters(title, location):
                jobs.append({"company": "Nestle", "title": title,
                             "location": location, "link": href, "number": href})

        print(f"Nestle: {len(jobs)} matching jobs found")
    except Exception as e:
        print(f"Nestle error: {e}")
    finally:
        quit_driver(driver)
    return jobs


# ── Combined entry point ─────────────────────────────────────────────────────

CUSTOM_CRAWLERS = [
    crawl_nike, crawl_adidas, crawl_red_bull_brand,
    crawl_ea, crawl_apple, crawl_nintendo,
    crawl_patagonia, crawl_gucci,
    crawl_atp, crawl_man_utd, crawl_yankees, crawl_lakers,
    crawl_paramount, crawl_ferrero, crawl_nestle, crawl_lvmh,
]


def crawl_all_brands_selenium():
    workday_tasks = [partial(_crawl_workday, name, url) for name, url in WORKDAY_COMPANIES.items()]
    heuristic_tasks = [partial(_crawl_heuristic, name, url, loc) for name, (url, loc) in HEURISTIC_COMPANIES.items()]
    all_tasks = workday_tasks + CUSTOM_CRAWLERS + heuristic_tasks

    jobs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        for result in executor.map(lambda f: f(), all_tasks):
            jobs.extend(result or [])
    return jobs
