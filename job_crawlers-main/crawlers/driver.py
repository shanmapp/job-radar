from selenium import webdriver


def make_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-sync")
    options.add_argument("--no-first-run")
    options.add_argument("--mute-audio")
    options.add_argument("--hide-scrollbars")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.binary_location = "/usr/bin/google-chrome"
    service = webdriver.ChromeService("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    # set_page_load_timeout is enforced *by* chromedriver. If Chrome/chromedriver
    # itself wedges, the Python client would otherwise block forever on the
    # command socket (no default read timeout) — this is how one stuck LVMH
    # crawl froze the whole scheduler for 2.5 days. A client-side command
    # timeout makes a hung browser raise instead of hanging indefinitely.
    try:
        driver.command_executor.set_timeout(90)
    except Exception:
        pass
    return driver


def quit_driver(driver):
    try:
        driver.quit()
    except Exception:
        pass
