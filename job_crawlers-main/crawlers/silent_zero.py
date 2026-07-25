"""Silent-zero detector: flags crawlers whose job board comes back empty.

Why this exists: a broken crawler returns [] (bad selector, dead board, ATS
migration) which is indistinguishable from "board is up but no in-scope roles"
if you only look at the *matched* count — in-scope roles are rare, so most
companies match 0 on any given day. The distinguishing signal is the RAW board
size (jobs seen before filtering). Crawlers call report(company, raw_count)
each run; run_daily_zero_check() rolls the day's counts into a per-company
consecutive-zero streak and returns the companies empty for >= 3 checks so
app.py can Telegram a single digest.

Only companies that actually report are tracked, so partial instrumentation
never produces false positives — an uninstrumented crawler is simply not
watched (host reachability is still covered by health.py).
"""
import json
import os
import threading

_STORE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "zero_streaks.json")
_ZERO_ALERT_DAYS = 3

_lock = threading.Lock()
_raw_max = {}   # company -> max raw board size seen since the last daily check


def report(company, raw_count):
    """Record how many jobs a crawler pulled from a company's board, pre-filter.
    Safe to call every crawl run; the daily check uses the max seen per company
    (so one good run in the window clears a transient empty run)."""
    if not company:
        return
    with _lock:
        if raw_count > _raw_max.get(company, -1):
            _raw_max[company] = raw_count


def _load():
    try:
        with open(_STORE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save(streaks):
    try:
        with open(_STORE, "w") as f:
            json.dump(streaks, f, indent=0, sort_keys=True)
    except Exception as e:
        print(f"silent_zero save error: {e}")


def run_daily_zero_check():
    """Fold the counts reported since the last check into per-company streaks.
    A company whose max raw board size was 0 gets its streak incremented; any
    non-zero resets it. Returns sorted companies at or past the alert threshold.
    Companies that did not report this window keep their streak unchanged."""
    with _lock:
        counts = dict(_raw_max)
        _raw_max.clear()
    if not counts:
        return []
    streaks = _load()
    flagged = []
    for company, raw in counts.items():
        streaks[company] = streaks.get(company, 0) + 1 if raw == 0 else 0
        if streaks[company] >= _ZERO_ALERT_DAYS:
            flagged.append(company)
    _save(streaks)
    return sorted(flagged)
