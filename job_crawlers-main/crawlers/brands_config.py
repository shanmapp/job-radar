"""
Config for all brand/entertainment company crawlers.
Each entry: company display name -> {platform, platform-specific params}
"""

GREENHOUSE_COMPANIES = {
    "Pokemon Company":      "pokemoncareers",
    "Mojang (Minecraft)":   "mojangab",
    "Take-Two Interactive": "taketwo",
    "2K Games":             "2k",
}

LEVER_COMPANIES = {
    "Spotify": "spotify",
}

SMARTRECRUITERS_COMPANIES = {
    # LVMH umbrella covers Louis Vuitton, Dior, Givenchy, etc.
    "LVMH": "LVMH2",
}

# Workday Selenium: {company name: full careers URL}
WORKDAY_COMPANIES = {
    "The North Face":   "https://vfc.wd5.myworkdayjobs.com/northface_careers",
    "Disney":           "https://disney.wd5.myworkdayjobs.com/disneycareer",
    "Yeti":             "https://yeticoolers.wd5.myworkdayjobs.com/YETI",
    "Coca-Cola":        "https://coke.wd1.myworkdayjobs.com/coca-cola-careers",
    "Lego":             "https://lego.wd103.myworkdayjobs.com/LEGO_External",
    "TKO (UFC/WWE)":    "https://wwecorp.wd5.myworkdayjobs.com/TKO",
    "Warner Bros.":     "https://warnerbros.wd5.myworkdayjobs.com/global",
    "Sony":             "https://sonyglobal.wd1.myworkdayjobs.com/SonyGlobalCareers",
    # Mojang (Minecraft) is covered by Greenhouse - no separate Microsoft entry needed
}

# Custom / Selenium-only: {company name: careers_url}
SELENIUM_COMPANIES = {
    "Netflix":          "https://explore.jobs.netflix.net/careers",
    "Nike":             "https://careers.nike.com/jobs",
    "Adidas":           "https://careers.adidas-group.com/jobs",
    "Red Bull":         "https://jobs.redbull.com/gb-en",
    "EA Sports":        "https://jobs.ea.com/en_US/careers/SearchJobs",
    "Nintendo":         "https://careers.nintendo.com/job-openings/",
    "Patagonia":        "https://www.patagonia.com/jobs-at-patagonia/",
    "Apple":            "https://jobs.apple.com/en-gb/search",
    "Amazon Studios":   "https://www.amazon.jobs/en/search?base_query=brand+OR+partnerships+OR+sponsorship&loc_query=United+Kingdom",
    "Notion":           "https://www.notion.so/careers",
    "Gucci":            "https://www.gucci.com/us/en/st/careers-jobs",
}
