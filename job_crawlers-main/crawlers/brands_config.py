"""
Config for all brand/entertainment company crawlers.
Each entry: company display name -> {platform, platform-specific params}
"""

GREENHOUSE_COMPANIES = {
    "Pokemon Company":      "pokemoncareers",
    "Mojang (Minecraft)":   "mojangab",
    "Take-Two Interactive": "taketwo",
    "2K Games":             "2k",
    "Interbrand":           "interbrand",
    "IDEO":                 "ideo",
    "IDEO.org":             "ideoorg",
    "Sid Lee":              "sidlee",
    "Landor":               "landor",
    "WPP":                  "wpp",
    "Monster Energy":       "monsterenergy",
    "NFL":                  "nflcareers",
    "NY Knicks (MSG Sports)": "msgsports",
    "Sony Interactive Entertainment": "sonyinteractiveentertainmentglobal",
    # MLB's careers pages embed Greenhouse job boards, confirmed via iframe src
    "MLB":                  "majorleaguebaseball",
    "MLB Network":          "mlbnetwork",
    # mrbeastjobs.com is a custom front-end whose own meta description says
    # "synced from public Greenhouse boards"; confirmed live via job-boards.greenhouse.io
    "MrBeast":              "mrbeastyoutube",
}

LEVER_COMPANIES = {
    "Spotify":   "spotify",
    "Arc'teryx": "arcteryx.com",
}

SMARTRECRUITERS_COMPANIES = {
    # LVMH umbrella covers Louis Vuitton, Dior, Givenchy, etc.
    "LVMH":            "LVMH2",
    "AB InBev":        "ABInBev1",
    "McDonald's":      "mcdonaldscorporation",
    "NBCUniversal":    "NBCUniversal3",
}

# Workable: {company name: account slug}
WORKABLE_COMPANIES = {
    "Wolff Olins": "wolff-olins",
    "JKR":         "jones-knowles-ritchie",
    "Jackman":     "jackman-reinvents",
}

# Teamtailor: {company name: full jobs.json host (teamtailor subdomain or custom domain)}
TEAMTAILOR_COMPANIES = {
    "Koto":      "koto.teamtailor.com",
    "LOLA":      "lolamullenlowe.teamtailor.com",
    "DixonBaxi": "joinus.dixonbaxi.com",
    "Saffron":   "saffron.teamtailor.com",
}

# Breezy HR: {company name: subdomain slug}
BREEZY_COMPANIES = {
    "Siegel+Gale": "siegel-gale",
}

# Pinpoint (ATS): {company name: full postings.json host}
PINPOINT_COMPANIES = {
    "FIFA": "jobs.fifa.com",
}

# Consider (ATS): {company name: (careers host, board id)}
# Confirmed live: careers.night.co/jobs is "Powered by Consider" (product.consider.com),
# board id "night-media". The search API needs a CSRF token + session cookie minted by
# a plain GET of the careers page first (no browser/JS execution required).
CONSIDER_COMPANIES = {
    "Night": ("careers.night.co", "night-media"),
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
    "NBA":              "https://nba.wd108.myworkdayjobs.com/nbacareers",
    "P&G":              "https://pg.wd5.myworkdayjobs.com/1000",
    "Unilever":         "https://unilever.wd3.myworkdayjobs.com/Unilever_Experienced_Professionals",
    "Aritzia":          "https://aritzia.wd3.myworkdayjobs.com/External",
    "Edelman":          "https://djeholdings.wd5.myworkdayjobs.com/edelman-careers-E200",
    "Warner Music (US)":     "https://wmg.wd1.myworkdayjobs.com/WMGUS",
    "Warner Music (Global)": "https://wmg.wd1.myworkdayjobs.com/WMGGLOBAL",
    "Universal Music Group": "https://umusic.wd5.myworkdayjobs.com/UMGUS",
    # ESPN roles live in the Disney Workday tenant — filtered via search query, not a separate site
    "ESPN":             "https://disney.wd5.myworkdayjobs.com/disneycareer?q=ESPN",
    # Lippincott is on parent Marsh McLennan's Workday tenant — filtered via search query
    "Lippincott":       "https://mmc.wd1.myworkdayjobs.com/MMC?q=Lippincott",
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

# Generic heuristic Selenium: sites with no clean ATS API, scraped via a shared
# resilient a[href*='job'] pattern (same style as crawl_netflix/crawl_nike/etc).
# Entries: {company name: (careers_url, default_location_fallback)}
#
# 2026-07 fingerprinting pass: every entry below was curl-inspected live to identify
# the real backing ATS. None could be upgraded to a verified API/Selenium crawler in
# that session because the sandbox used had no Chrome/chromedriver (so nothing that
# needs JS rendering could be confirmed against real DOM), and the enterprise ATS
# platforms below (iCIMS, SAP SuccessFactors, Avature, PhenomPeople) do not expose an
# unauthenticated JSON job-search API the way Greenhouse/Lever/SmartRecruiters do —
# their public endpoints are either JS-only (job data fetched client-side after a
# React/Angular bundle boots) or return 401/"tenant not identified" when hit directly.
# Left here on purpose per the "don't force a broken crawler" rule; comments record
# the confirmed platform + tenant so a future pass with real browser access can go
# straight to writing a bespoke platform crawler (grouped like WORKDAY_COMPANIES)
# instead of re-fingerprinting from scratch.
HEURISTIC_COMPANIES = {
    # Confirmed iCIMS (subdomain publicisgroupe.icims.com). /jobs/search is a JS SPA
    # (Jibe widget on top of iCIMS); direct requests to the icims.com subdomain hit
    # an Auth0 login wall / rate limit, so no unauthenticated JSON API found.
    "Publicis":                         ("https://careers.publicisgroupe.com/jobs", ""),
    # Confirmed iCIMS (subdomains pepsico.icims.com / uscareers-pepsico.icims.com).
    # Same JS-SPA-with-auth-walled-backend situation as Publicis above.
    # Covers Frito-Lay and Gatorade too — all three share the same PepsiCo careers site
    "PepsiCo (incl. Frito-Lay, Gatorade)": ("https://www.pepsicojobs.com/main", ""),
    # jobs.louisvuitton.com returns HTTP 403 from AkamaiGHost bot protection on a
    # plain request — could not fingerprint the ATS or confirm real job data without
    # a full browser session (cookies/JS challenge required).
    "Louis Vuitton":                     ("https://jobs.louisvuitton.com/en", ""),
    # Confirmed Avature (emiratesjobs.avature.net). Search results page is JS-rendered
    # (no SSR job cards in raw HTML); no public JSON search endpoint found.
    "Emirates":                          ("https://www.emiratesgroupcareers.com/search-and-apply/", "Dubai, United Arab Emirates"),
    # No ATS signature found in raw HTML (custom/JS SPA) — needs browser rendering to
    # identify the real job-listing source.
    "Lacoste":                           ("https://careers.lacoste.com/en", ""),
    # No ATS signature found; site returned HTTP 202 (async render placeholder) to a
    # plain request, confirming it's fully JS-driven with no SSR fallback.
    "Ralph Lauren":                      ("https://careers.ralphlauren.com/en_US/CareersCorporate/SearchJobsCorporate", ""),
    # kellanovacareers.com returns HTTP 405 to a plain GET (bot-detection style
    # rejection) — could not fingerprint the ATS without a browser session.
    "Kellanova":                         ("https://kellanovacareers.com", ""),
    # Confirmed PhenomPeople (assets/cdn.phenompeople.com references in page source).
    # The public Phenom search API (`/api/apply/v2/jobs?domain=...`) returned
    # "Tenant not identified" for every domain value tried — correct tenant id not
    # discoverable without inspecting the live JS bundle's network calls.
    "WK Kellogg Co":                     ("https://jobs.wkkellogg.com/us/en", ""),
    # Custom Next.js app (jobs.kraftheinz.com) — no recognizable third-party ATS
    # signature in the served HTML; likely calls an internal API from client JS that
    # wasn't discoverable via static asset inspection alone.
    "Kraft Heinz":                       ("https://careers.kraftheinzcompany.com", ""),
    # Confirmed iCIMS (dashboard-en-generalmills2.icims.com, a Jibe/iCIMS combo — same
    # situation as Publicis/PepsiCo above).
    "General Mills":                     ("https://careers.generalmills.com/careers", ""),
    # Confirmed Avature (lululemonincchina.avature.cn seen for the CN career flow);
    # the primary careers.lululemon.com flow is JS-rendered with no SSR job data.
    "Lululemon":                         ("https://careers.lululemon.com", ""),
    # Original URL (thejourney.lvmh.com) no longer resolves (DNS failure). Moët
    # Hennessy is NOT in the LVMH SmartRecruiters tenant already wired up in
    # SMARTRECRUITERS_COMPANIES (verified live — that tenant is LVMH Beauty/Perfumes
    # & Cosmetics only, no Moët Hennessy postings). Could not find the real live
    # careers site in the time available; left as-is pending a working URL.
    "Moet Hennessy":                     ("https://thejourney.lvmh.com/jobs", ""),
    # No ATS signature found (custom/JS SPA) — needs browser rendering to identify
    # the real job-listing source.
    "Universal Studios/Parks":           ("https://jobs.universalparks.com", ""),
    # Original URL was dead (404). Fixed to careers.pirelli.com, which redirects to
    # a live 200 page — but no third-party ATS signature found there either
    # (custom/JS SPA); job data source still unidentified.
    "Pirelli":                           ("https://careers.pirelli.com", ""),
    # Confirmed SAP SuccessFactors — career4.successfactors.com, company id
    # "Hersheys". Same client-side-only job list as Nestle/Ferrero/Paramount below.
    # career4.successfactors.com/career?company=Hersheys redirects into a
    # login/register wall for the actual job search (RCM redirect) — no
    # reachable unauthenticated job list found.
    "Hershey":                           ("https://careers.thehersheycompany.com", ""),
}
