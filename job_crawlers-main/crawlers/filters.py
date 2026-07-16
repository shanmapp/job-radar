import re

# Matched as whole words only — plain substring matching let "sport" hit
# "tranSPORT"/"pasSPORT", so inflections are listed explicitly rather than
# relying on a stem matching its own plural.
ROLE_KEYWORDS = ["strategy", "brand", "brands", "branding",
                 "partnership", "partnerships", "sponsorship", "sponsorships",
                 "licensing", "sport", "sports",
                 "creative", "designer", "designers"]

_ROLE_RE = re.compile(r"\b(?:%s)\b" % "|".join(re.escape(k) for k in ROLE_KEYWORDS))

# Countries in scope. Display-cased so API-level crawlers (e.g. Jibe) can use
# them directly as server-side location queries; lowercased below for matching.
TARGET_COUNTRIES = [
    "United Kingdom", "Australia", "Austria", "Belgium", "Chile", "Costa Rica",
    "Croatia", "Czech Republic", "Denmark", "Estonia", "Finland", "France",
    "Germany", "Greece", "Hong Kong", "Iceland", "Ireland", "Italy", "Japan",
    "Korea", "Latvia", "Lithuania", "Luxembourg", "Netherlands", "New Zealand",
    "Norway", "Poland", "Portugal", "San Marino", "Slovakia", "Slovenia",
    "Spain", "Sweden", "Switzerland", "Taiwan",
]

# Matched as whole words/phrases within the location string.
LOCATION_TERMS = [c.lower() for c in TARGET_COUNTRIES] + [
    "uk", "england", "scotland", "wales", "czechia", "italia", "swiss",
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
    """True if title matches a role keyword AND is not a senior role."""
    return matches_keywords(title) and is_entry_level(title)


_LOCATION_RE = re.compile(r"\b(?:%s)\b" % "|".join(re.escape(t) for t in LOCATION_TERMS))

def matches_location(location_str):
    if not location_str:
        return False
    return _LOCATION_RE.search(location_str.lower()) is not None
