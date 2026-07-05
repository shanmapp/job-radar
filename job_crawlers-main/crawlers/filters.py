ROLE_KEYWORDS = ["strategy", "brand", "partnerships", "sponsorship", "licensing", "sport"]

LOCATION_TERMS = ["united kingdom", "uk", "england", "scotland", "wales", "london",
                  "italy", "italia", "maranello", "milan", "rome", "turin",
                  "switzerland", "swiss", "geneva", "zurich", "basel"]

# Titles containing these words are senior/experienced roles — skip them
EXCLUDE_TITLE_WORDS = [
    "senior", " sr ", "sr.", "manager", "director", "head of", "head,",
    "lead", "principal", "vice president", "vp ", " vp", "chief", "president",
    "global", "group", "regional", "svp", "evp", "cmo", "ceo", "cco",
]


def matches_keywords(title):
    return any(k in title.lower() for k in ROLE_KEYWORDS)


def is_entry_level(title):
    t = title.lower()
    is_junior_or_assistant = "junior" in t or "assistant" in t
    for w in EXCLUDE_TITLE_WORDS:
        if w in t:
            if w == "manager" and is_junior_or_assistant:
                continue
            return False
    return True


def is_relevant(title):
    """True if title matches a role keyword AND is not a senior role."""
    return matches_keywords(title) and is_entry_level(title)


def matches_location(location_str):
    if not location_str:
        return False
    return any(term in location_str.lower() for term in LOCATION_TERMS)
