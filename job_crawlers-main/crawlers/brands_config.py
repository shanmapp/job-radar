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
    # Confirmed via the api.greenhouse.io reference inside wk.com/jobs's Gatsby
    # JS bundle; board "wk" verified live (Portland HQ + Slime Mold Productions).
    "Wieden+Kennedy":       "wk",
}

LEVER_COMPANIES = {
    "Spotify":   "spotify",
    "Arc'teryx": "arcteryx.com",
}

SMARTRECRUITERS_COMPANIES = {
    # LVMH removed: the "LVMH2" tenant only carried Beauty/Perfumes & Cosmetics.
    # crawl_lvmh (brands_selenium_crawler) now covers the whole group via the
    # lvmh.com job hub, and keeping both would double-notify beauty postings
    # under different job numbers.
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
    "Formula E": "formulae.teamtailor.com",
    # careers.juventus.com is a Teamtailor custom domain; /jobs.json confirmed live.
    "Juventus":  "careers.juventus.com",
}

# Breezy HR: {company name: subdomain slug}
BREEZY_COMPANIES = {
    "Siegel+Gale": "siegel-gale",
}

# Pinpoint (ATS): {company name: full postings.json host}
PINPOINT_COMPANIES = {
    "FIFA": "jobs.fifa.com",
    "Premier League": "premierleague.pinpointhq.com",
}

# Jobylon (ATS): {company name: (numeric company id, default country appended
# to city-only locations)}. The uefa.com jobs pages block plain HTTP clients
# (Akamai), but the jobs are served by Jobylon, whose CDN embed endpoint
# (cdn.jobylon.com/jobs/companies/<id>/embed/v1/) is open and curl-friendly.
# Company id found in the emp.jobylon.com job detail pages ("company_id = 2972").
JOBYLON_COMPANIES = {
    # UEFA postings list city only ("Nyon"); HQ country appended for filtering.
    "UEFA": ("2972", "Switzerland"),
}

# Phenom People careers sites: {company name: careers site base URL}.
# Phenom's /widgets endpoint accepts an unauthenticated JSON POST
# (ddoKey=refineSearch) and returns the full job index with pagination —
# unlike the WK Kellogg tenant noted in HEURISTIC_COMPANIES, these two were
# confirmed live returning real postings.
PHENOM_COMPANIES = {
    "Mars":        "https://careers.mars.com",
    "New Balance": "https://jobs.newbalance.com",
}

# SAP SuccessFactors Career Site Builder sites that server-render their job
# lists (unlike the login-walled career4/career5 tenants in HEURISTIC_COMPANIES,
# these public CSB front ends return parseable HTML to a plain GET).
# {company name: (host, listing path, markup style)}
# - "csb": stock CSB markup, paginated with ?startrow=N (10 rows/page).
# - "listing": Heineken has no /search/ (404); its custom /Job-Listing uses
#   job-list-item blocks and a composite ?page=0,0,N parameter.
SUCCESSFACTORS_COMPANIES = {
    "Under Armour": ("careers.underarmour.com", "/search/", "csb"),
    "Heineken":     ("careers.theheinekencompany.com", "/Job-Listing", "listing"),
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
    # Separate UK board on the same tenant — the Amplify U trainee postings
    # (Kings Cross, London) live here, not on UMGUS.
    "Universal Music UK":    "https://umusic.wd5.myworkdayjobs.com/UMGUK",
    "Diageo":           "https://diageo.wd3.myworkdayjobs.com/Diageo_Careers",
    # dentsu group global board (tenant name is the old Dentsu Aegis Network)
    "Dentsu":           "https://dentsuaegis.wd3.myworkdayjobs.com/DAN_GLOBAL",
    # IMG has no standalone board — it hires through parent Endeavor's WME/IMG tenant
    "IMG (Endeavor)":   "https://wmeimg.wd1.myworkdayjobs.com/WMEGRP",
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
# 2026-07 club/agency fingerprinting pass — requested companies with NO usable
# public job source (documented here so nobody re-fingerprints them; per the
# Moët Hennessy lesson, no dead config entries are kept for them):
# - Real Madrid: no public job portal at all — hires via LinkedIn/agencies only.
# - FC Barcelona: same; no careers portal on fcbarcelona.com (the "Job Center"
#   is an ex-players service).
# - AC Milan: acmilan.com/en/club/work-with-us is CV-by-email
#   (hrsupport@acmilan.com); no listings to crawl.
# - Pentagram: pentagram.com/careers is mailto-only per studio; no listings.
# - Omnicom: no group-wide job board; per-agency sites only (the main one,
#   us-careers.omnicommediagroup.com, is US-only — out of location scope).
# - AFC Ajax: werkenbij.ajax.nl is an AFAS InSite portal; the vacancy list is a
#   JS widget ("Geen gegevens om te tonen" without JS) and vacancy URLs use
#   /vacaturebeschrijvingen/... so the generic a[href*='job'] heuristic can't
#   see them either. Needs a bespoke AFAS crawler with a real browser session.
HEURISTIC_COMPANIES = {
    # McDonald's corporate roles are server-rendered at careers.mcdonalds.com
    # /jobs (links match a[href*='job']), but Akamai 403s plain HTTP clients so
    # it needs the browser tier. The McDonaldsCorporation SmartRecruiters
    # tenant (still configured above) is a near-dead shell carrying only a few
    # stray postings — the raw-pull audit caught it at 4 jobs total.
    "McDonald's (corporate site)":       ("https://careers.mcdonalds.com/jobs", ""),
    # Publicis: moved to the Jibe JSON API crawler (JIBE_COMPANIES in
    # brands_http_crawler) — careers.publicisgroupe.com/api/jobs is open JSON.
    # PepsiCo (incl. Frito-Lay, Gatorade, SodaStream): moved to crawl_pepsico in
    # brands_http_crawler — the Jibe front end's /api/jobs endpoint is plain
    # stable JSON (it was the HTML search page that was bot-flaky, not the API).
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
    # General Mills: moved to the Jibe JSON API crawler (JIBE_COMPANIES in
    # brands_http_crawler) — careers.generalmills.com/api/jobs is open JSON.
    # Confirmed Avature (lululemonincchina.avature.cn seen for the CN career flow);
    # the primary careers.lululemon.com flow is JS-rendered with no SSR job data.
    "Lululemon":                         ("https://careers.lululemon.com", ""),
    # Moët Hennessy: covered by crawl_lvmh (lvmh.com group job hub) — its old
    # standalone site (thejourney.lvmh.com) is DNS-dead and sat here erroring
    # silently on every run until a matching London posting was missed.
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
