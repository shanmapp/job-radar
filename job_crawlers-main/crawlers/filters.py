import re
import threading

# Matched as whole words only — plain substring matching let "sport" hit
# "tranSPORT"/"pasSPORT", so inflections are listed explicitly rather than
# relying on a stem matching its own plural.
ROLE_KEYWORDS = ["strategy", "brand", "brands", "branding",
                 "partnership", "partnerships", "sponsorship", "sponsorships",
                 "licensing", "sport", "sports",
                 # Added after Premier League "Commercial Projects Assistant"
                 # (London) was dropped — club/league boards use "commercial"
                 # for exactly the partnerships/sponsorship space in scope.
                 "commercial",
                 # Added after Universal Music UK "Content Sales Executive"
                 # (Kings Cross, London) was dropped — sales/marketing is the
                 # commercial space in scope; gated by location + entry-level.
                 "sales", "marketing",
                 # Generic early-career title levels — gated by location +
                 # entry-level so senior variants still drop.
                 "executive", "assistant", "coordinator", "specialist",
                 "creative", "designer", "designers",
                 # Early-career terms: added after the NBA "Europe and Middle
                 # East Internship Programme" posting (London) was crawled but
                 # dropped — its title contained no role keyword at all.
                 "intern", "interns", "internship", "internships",
                 "graduate", "graduates", "trainee", "trainees",
                 # UK spelling only, on purpose: "program"/"programs" would
                 # flood-match US software/program-manager titles.
                 "programme", "programmes"]

_ROLE_RE = re.compile(r"\b(?:%s)\b" % "|".join(re.escape(k) for k in ROLE_KEYWORDS))

# Countries in scope. Display-cased so API-level crawlers (e.g. Jibe) can use
# them directly as server-side location queries; lowercased below for matching.
TARGET_COUNTRIES = [
    "United Kingdom", "Australia", "Austria", "Denmark", "Finland", "France",
    "Germany", "Hong Kong", "Ireland", "Italy", "Japan", "Korea",
    "Netherlands", "Norway", "Poland", "Spain", "Sweden", "Switzerland",
]

# Matched as whole words/phrases within the location string.
LOCATION_TERMS = [c.lower() for c in TARGET_COUNTRIES] + [
    "uk", "england", "scotland", "wales", "italia", "swiss",
    "london", "maranello", "milan", "rome", "turin", "geneva", "zurich", "basel",
]

# Titles containing these words are senior/experienced roles — skip them.
# Also matched as whole words, so padding like " sr " / "vp " is unnecessary.
# "leader"/"leaders" are spelled out because whole-word "lead" no longer
# catches them; "leadership" is deliberately absent so it stays allowed.
EXCLUDE_TITLE_WORDS = [
    "senior", "sr", "manager", "director", "head",
    "lead", "leads", "leader", "leaders", "principal", "vice president", "vp",
    "chief", "president", "global", "group", "regional", "svp", "evp",
    "cmo", "ceo", "cco",
]

_EXCLUDE_RES = {w: re.compile(r"\b%s\b" % re.escape(w)) for w in EXCLUDE_TITLE_WORDS}

# Operational/manual roles at sports companies. On club boards, whole-word
# "sport"/"sports" appears in titles like "Sports Minibus Driver", which
# otherwise sails through the role-keyword filter and triggers an alert.
EXCLUDE_OPERATIONAL_WORDS = [
    "driver", "drivers", "driving", "chauffeur", "minibus", "transport",
    "cleaner", "cleaners", "cleaning", "steward", "stewards",
    "chef", "chefs", "catering", "kitchen", "warehouse", "groundsperson",
]

_OPERATIONAL_RE = re.compile(
    r"\b(?:%s)\b" % "|".join(re.escape(w) for w in EXCLUDE_OPERATIONAL_WORDS))


def matches_keywords(title):
    return _ROLE_RE.search(title.lower()) is not None


def is_entry_level(title):
    t = title.lower()
    is_junior_or_assistant = "junior" in t or "assistant" in t
    for w in EXCLUDE_TITLE_WORDS:
        if _EXCLUDE_RES[w].search(t):
            if w == "manager" and is_junior_or_assistant:
                continue
            return False
    return True


def is_relevant(title):
    """True if title matches a role keyword AND is not a senior or operational role."""
    return (matches_keywords(title) and is_entry_level(title)
            and not _OPERATIONAL_RE.search(title.lower()))


_LOCATION_RE = re.compile(r"\b(?:%s)\b" % "|".join(re.escape(t) for t in LOCATION_TERMS))

def matches_location(location_str):
    if not location_str:
        return False
    return _LOCATION_RE.search(location_str.lower()) is not None


# ── Near-miss capture ────────────────────────────────────────────────────────
# Every job the radar has missed so far was dropped *silently* — a filtered-out
# job looks identical to one that never existed (NBA internship, PL Kicks,
# Amplify U). passes_filters() is the single choke point for title+location
# filtering: when a job's location IS in scope but its title fails the role
# keywords, the (title, location) pair is recorded here. app.py drains the
# buffer on a weekly schedule and sends a Telegram digest for human review, so
# keyword-scope gaps surface instead of accumulating invisibly.

_near_miss_lock = threading.Lock()
_near_misses = {}   # (company, title, location) -> hit count since last drain
_NEAR_MISS_CAP = 2000  # hard bound on memory if the digest never drains


def passes_filters(title, location=None, company=None):
    """Combined title+location filter; records near-misses.

    location=None means the caller already knows the job is in scope (bespoke
    crawlers for single-site companies pre-check location themselves).
    company is only used to label near-miss digest entries.
    """
    loc_ok = matches_location(location) if location is not None else True
    if not loc_ok:
        return False
    if is_relevant(title):
        return True
    key = ((company or "").strip(), title.strip(), (location or "").strip())
    with _near_miss_lock:
        if len(_near_misses) < _NEAR_MISS_CAP or key in _near_misses:
            _near_misses[key] = _near_misses.get(key, 0) + 1
    return False


def drain_near_misses():
    """Return and clear the accumulated near-misses: [(company, title, location), ...]."""
    with _near_miss_lock:
        items = sorted(_near_misses)
        _near_misses.clear()
    return items
