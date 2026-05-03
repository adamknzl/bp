"""
@file    search_api.py
@brief   URL discovery for nonprofit organizations using the Serper API.
@author  Adam Kinzel (xkinzea00)
"""

import os
import re
from dotenv import load_dotenv
from difflib import SequenceMatcher
from urllib.parse import urlparse

import requests
from unidecode import unidecode

from utils import clean_npo_name

load_dotenv()


SERPER_API_URL = os.getenv("SERPER_API_URL")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")


# Domains never considered as the official website of an organization
# (aggregators, social networks, government registries, regional portals).
DOMAIN_BLACKLIST = (
    'facebook.com', 'instagram.com', 'wikipedia.org', 'google.com', 'youtube.com', 'linkedin.com',
    'seznam.cz', 'kurzy.cz', 'finance.cz', 'penize.cz', 'podnikatel.cz', 'zlatestranky.cz',
    'firmy.cz', 'justice.cz', 'detail.cz', 'najisto.cz', 'merk.cz', 'euro.cz', 'statnisprava.cz',
    'firmy-lide.cz', '123firmy.cz', 'katalog-firem.cz', 'finstat.sk', 'kupi.cz', 'heureka.cz',
    'mapy.cz', 'jasnadata.cz', 'mapy.com', 'dnb.com',
    # Regional government portals
    'praha.eu', 'stredoceskykraj.cz', 'plzensky-kraj.cz', 'kr-karlovarsky.cz', 'khk.cz',
    'kraj-lbc.cz', 'kr-ustecky.cz', 'kraj-jihocesky.cz', 'pardubickykraj.cz', 'kr-vysocina.cz',
    'jmk.cz', 'msk.cz', 'zlinskykraj.cz', 'olkraj.cz',
)

# Czech sub-organization indicators used to detect branch entities.
_BRANCH_INDICATORS = ('mistni organizace', 'okresni organizace', 'pobocka', 'oddil', 'stredisko')

_LONG_DIGIT_PATH_REGEX = re.compile(r'\d{6,}')


def _name_similarity(a: str, b: str) -> float:
    """Return a similarity ratio in [0, 1] between two strings."""
    return SequenceMatcher(None, a, b).ratio()


def normalize_url(url: str) -> str:
    """Reduce a URL to its scheme + hostname root."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"


def _domain_no_tld(domain: str) -> str:
    """Return the second-level domain part (example for www.example.cz)."""
    return domain.split('.')[-2] if '.' in domain else domain


def _detect_branch_location(clean_name: str) -> list[str]:
    """
    If the cleaned NPO name indicates a branch, return location words from the suffix.

    Returns an empty list when the name does not contain a branch indicator.
    """
    for indicator in _BRANCH_INDICATORS:
        if indicator in clean_name:
            parts = clean_name.split(indicator)
            loc_part = parts[-1].replace(',', '').replace('-', '').strip()
            return [w for w in loc_part.split() if len(w) > 2]
    return []


def score_url(url: str, npo_name: str, title: str) -> int:
    """
    Score a candidate URL against an NPO name and search-result title.

    Higher scores indicate a more likely match for the organization's official website.
    The score combines blacklist filtering, URL structure analysis, domain/title
    keyword matching, and branch-location heuristics.

    Returns:
        int: Scoring value, -100 for results that should be excluded entirely.
    """
    score = 0
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.lower()
    query_string = parsed.query.lower()

    # Hard exclusions
    if any(b in domain for b in DOMAIN_BLACKLIST):
        return -100

    url_context = unidecode(domain + path)
    if 'rejstrik' in url_context or 'databaze' in url_context:
        return -100

    # Soft penalties
    if query_string:
        score -= 20
    if _LONG_DIGIT_PATH_REGEX.search(path):
        score -= 50

    # Branch-location enforcement
    clean_npo_lower = unidecode(npo_name.lower())
    title_lower = unidecode((title or "").lower())
    domain_part = _domain_no_tld(domain)

    location_words = _detect_branch_location(clean_npo_lower)
    if location_words:
        loc_match = any(
            lw in domain_part or lw in title_lower or lw in path
            for lw in location_words
        )
        if not loc_match:
            return -100

    # URL structure bonuses
    if path in ('', '/'):
        score += 15
    elif len(path.strip('/').split('/')) == 1:
        score += 5
    else:
        score -= 15

    # TLD preference
    if domain.endswith('.cz') or domain.endswith('.eu'):
        score += 5
    elif domain.endswith('.org'):
        score += 2

    # Keyword matching against domain and title
    clean_name = unidecode(clean_npo_name(npo_name).lower())
    keywords = [w for w in clean_name.split() if len(w) > 3]

    word_match = False
    for kw in keywords:
        if kw in domain_part:
            score += 25
            word_match = True
        elif _name_similarity(kw, domain_part) > 0.8:
            score += 15
            word_match = True
        if kw in title_lower:
            score += 10
            word_match = True

    # Acronym match
    acronym = "".join(w[0] for w in keywords if w).lower()
    if len(acronym) >= 3 and acronym in domain_part:
        score += 20
        word_match = True

    if not word_match:
        score -= 20

    return score


def serper_search(query: str, country: str = "cz", language: str = "cs", num: int = 15) -> list:
    """
    Query the Serper API and return the list of organic search results.

    Returns:
        list: Organic results as returned by Serper, or an empty list on failure.
    """
    if not SERPER_API_KEY:
        print("  SERPER_API_KEY is not set, cannot perform search.")
        return []

    payload = {"q": query, "gl": country, "hl": language, "num": num}
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}

    try:
        response = requests.post(SERPER_API_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"  Serper request failed for '{query}': {e}")
        return []
    except ValueError as e:
        print(f"  Serper returned invalid JSON for '{query}': {e}")
        return []

    return data.get("organic", [])


def _evaluate_results(results: list, npo_name: str) -> tuple[str | None, int, list]:
    """
    Score all results, deduplicate by domain, and return the best candidate.

    Returns:
        tuple: (best_url, best_score, all_scored) where all_scored is a list
        of {"url", "score"} dicts useful for diagnostic output.
    """
    all_scored: list[dict] = []
    domains_seen: dict[str, tuple[int, str]] = {}

    for item in results:
        url = item.get("link")
        title = item.get("title")
        if not url:
            continue

        current_score = score_url(url, npo_name, title)
        all_scored.append({"url": url, "score": current_score})

        domain = urlparse(url).netloc.lower()
        if domain not in domains_seen or current_score > domains_seen[domain][0]:
            domains_seen[domain] = (current_score, url)

    best_url = None
    best_score = 10  # Score threshold below which we discard results
    for _, (score, url) in domains_seen.items():
        if score > best_score:
            best_score = score
            best_url = normalize_url(url)

    return best_url, best_score, all_scored


def get_url(npo_name: str) -> str | None:
    """
    Discover the official website URL of a Czech nonprofit organization.

    Issues a sequence of search queries with progressively broader phrasing and
    returns the highest-scoring candidate from the first query that yields one.

    Returns:
        str | None: The discovered URL (root form), or None if no satisfactory
        candidate was found across all queries.
    """
    search_name = clean_npo_name(npo_name)
    queries = [
        f"{search_name} oficiální stránky",
        f"{search_name} web",
        search_name,
    ]

    try:
        for query in queries:
            print(f"Searching Serper: '{query}'")

            results = serper_search(query)
            if not results:
                print("  No results returned, trying next query...")
                continue

            best_url, best_score, all_scored = _evaluate_results(results, npo_name)

            print(f"\n--- Results for '{npo_name}' (query: '{query}') ---")
            for entry in sorted(all_scored, key=lambda x: x["score"], reverse=True):
                print(f"  [{entry['score']:+d}] {entry['url']}")
            print("-----------------------------------")

            if best_url:
                print(f"Found after query '{query}': '{best_url}' (score: {best_score})")
                return best_url

            print("No sufficient URL found, trying next query...")

        print(f"No URL found for '{npo_name}' across all queries.")
        return None

    except Exception as e:
        print(f"Unexpected error while searching for '{npo_name}': {e}")
        return None