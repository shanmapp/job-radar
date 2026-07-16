"""Source-health check for all crawler URLs.

Why this exists: a crawler pointed at a dead site fails *silently* — its
exception is caught, printed to stdout, and it returns [], which is
indistinguishable from "site is up, no matching jobs". That is exactly how
the Moët Hennessy entry (thejourney.lvmh.com, DNS-dead) sat broken for weeks
until a matching London posting was missed.

This module scans every crawlers/*.py source file for https:// string
literals (skipping comment lines), dedupes to hostnames, and probes each one.
Self-discovery means a newly added crawler is monitored automatically — there
is no registry to forget to update.

A host is only flagged DEAD on DNS failure or connection failure. HTTP-level
rejections (403/405/503) are NOT flagged: several tracked sites are
bot-walled and reject plain requests while working fine under Selenium.
DNS/connection failure is the class of breakage that can never succeed from
any client, so it never false-alarms.
"""
import concurrent.futures
import os
import re
import socket
from urllib.parse import urlparse

_CRAWLERS_DIR = os.path.dirname(os.path.abspath(__file__))
_URL_RE = re.compile(r"https://[a-zA-Z0-9.\-]+")

# Hosts that appear in source but are not crawl targets (API endpoints of
# already-probed services, doc links, etc.) can be listed here.
IGNORED_HOSTS = set()


def discover_hosts():
    """Collect every https:// hostname from non-comment lines of crawlers/*.py."""
    hosts = set()
    for fname in os.listdir(_CRAWLERS_DIR):
        if not fname.endswith(".py"):
            continue
        with open(os.path.join(_CRAWLERS_DIR, fname), encoding="utf-8") as f:
            for line in f:
                if line.lstrip().startswith("#"):
                    continue
                for url in _URL_RE.findall(line):
                    host = urlparse(url).netloc
                    if host and host not in IGNORED_HOSTS:
                        hosts.add(host)
    return sorted(hosts)


def _probe(host):
    """Return an error string if the host is dead, else None."""
    try:
        addr = socket.gethostbyname(host)
    except Exception as e:
        return f"DNS failure ({e})"
    try:
        with socket.create_connection((addr, 443), timeout=10):
            return None
    except Exception as e:
        return f"connection failure ({e})"


def check_sources():
    """Probe all discovered hosts; return {host: error} for dead ones."""
    hosts = discover_hosts()
    dead = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for host, err in zip(hosts, ex.map(_probe, hosts)):
            if err:
                dead[host] = err
    print(f"Source health: {len(hosts) - len(dead)}/{len(hosts)} hosts reachable")
    return dead
