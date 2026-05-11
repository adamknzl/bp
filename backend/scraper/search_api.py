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

# Configuration

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

# Used for penalizing URLs with long numerical sequences in their path
_LONG_DIGIT_PATH_REGEX = re.compile(r'\d{6,}')


def _name_similarity(a: str, b: str) -> float:
    """Return a similarity ratio in [0, 1] between two strings."""
    return SequenceMatcher(None, a, b).ratio()


def normalize_url(url: str) -> str:
    """Reduce a URL to its scheme and hostname root."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"


def _domain_no_tld(domain: str) -> str:
    """Return the most specific non-www domain part."""
    if domain.startswith('www.'):
        domain = domain[4:]
        
    parts = domain.split('.')
    # If a subdomain exists, it is more specific than the 2nd level domain
    if len(parts) >= 3:
        return parts[0]
    return parts[-2] if len(parts) >= 2 else domain


def _detect_branch_location(clean_name: str) -> list[str]:
    """
    If the cleaned NPO name indicates a branch, return strings from the suffix.

    Returns an empty list when the name does not contain a branch indicator.
    """
    for indicator in _BRANCH_INDICATORS:
        if indicator in clean_name:
            parts = clean_name.split(indicator)
            loc_part = parts[-1].replace(',', '').replace('-', '').strip()
            return [w for w in loc_part.split() if len(w) > 2]
    return []

def _no_website_flag(results: list, threshold: float = 0.8) -> bool:
    """
    Return True if the majority of results (set by threshold) are blacklisted domains.
    
    When most results are directories or aggregators, it indicates the
    organization likely has no official website worth discovering.
    """
    if not results:
        return True
    
    blacklisted = sum(
        1 for item in results
        if any(b in urlparse(item.get("link", "")).netloc.lower()
            for b in DOMAIN_BLACKLIST)
    )

    return (blacklisted / len(results)) >= threshold

def score_url(url: str, npo_name: str, title: str, debug: bool = False) -> int:
    """
    Score a candidate URL against an NPO name and search-result title.

    Higher scores indicate a more likely match for the organization's official website.
    The score combines blacklist filtering, URL structure analysis, domain/title
    keyword matching, and branch-location heuristics.

    Returns:
        int: Scoring value, -100 for results that should be excluded entirely.
    """
    
    def log(msg: str):
        """Used for debugging based on achieved scores."""
        if debug:
            print(f"    {msg}")

    score = 0
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.lower()
    query_string = parsed.query.lower()

    _SCORING_STOPWORDS = {
        'cesky', 'ceska', 'české', 'czech',
        'spolek', 'svaz', 'ustav', 'nadace',
        'zakladni', 'organizace', 'pobocka',
        'obecne', 'prospesna', 'spolecnost',
        'pod', 'nad', 'pro', 'pri',
    }

    log(f"-- {url}")

    # Hard exclusions
    if any(b in domain for b in DOMAIN_BLACKLIST):
        log("EXCLUDE: domain is blacklisted")
        return -100

    url_context = unidecode(domain + path)
    if 'rejstrik' in url_context or 'databaze' in url_context:
        log("EXCLUDE: rejstrik/databaze in URL")
        return -100

    # Penalties
    if query_string:
        score -= 20
        log("-20: has query string")
    if _LONG_DIGIT_PATH_REGEX.search(path):
        score -= 50
        log("-50: long digit sequence in path")

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
            log(f"EXCLUDE: branch location words {location_words} not found in domain/title/path")
            return -100
        else:
            log(f"OK: branch location words {location_words} matched")

    # URL structure bonuses
    if path in ('', '/'):
        score += 15
        log("+15: root path")
    elif len(path.strip('/').split('/')) == 1:
        score += 5
        log("+5: single-level path")
    else:
        score -= 15
        log(f"-15: deep path ({path})")

    # TLD preference
    if not (domain.endswith('.cz') or domain.endswith('.eu') or domain.endswith('.org')):
        score -= 20
        log("-20: non-preferred TLD")
    else:
        score += 10
        log("+10: preferred TLD")

    # Keyword and acronym matching
    clean_name = unidecode(clean_npo_name(npo_name).lower())
    keywords = [w for w in clean_name.split() if len(w) > 3 and w not in _SCORING_STOPWORDS]
    acronym = "".join(w[0] for w in clean_name.split() if len(w) >= 2).lower()

    log(f"keywords: {keywords}, acronym: {acronym}, domain_part: {domain_part}")

    word_match = False
    domain_word_match = False

    for kw in keywords:
        if kw in domain_part:
            score += 25
            word_match = True
            domain_word_match = True
            log(f"+25: keyword '{kw}' in domain")
        elif _name_similarity(kw, domain_part) > 0.8:
            score += 15
            word_match = True
            domain_word_match = True
            log(f"+15: keyword '{kw}' similar to domain (similarity={_name_similarity(kw, domain_part):.2f})")
        if kw in title_lower:
            bonus = 10 if domain_word_match else 3
            score += bonus
            word_match = True
            log(f"+{bonus}: keyword '{kw}' in title {'(domain matched)' if domain_word_match else '(no domain match)'}")

    # Acronym match against domain
    if len(acronym) >= 2 and acronym == domain_part:
        score += 20
        word_match = True
        domain_word_match = True
        log(f"+20: acronym '{acronym}' matches domain")

    if not word_match:
        score -= 20
        log("-20: no word match at all")
    if not domain_word_match:
        score -= 30
        log("-30: no domain word match")

    log(f"-- final score: {score}")
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

        current_score = score_url(url, npo_name, title, debug=False)
        all_scored.append({"url": url, "score": current_score})

        domain = urlparse(url).netloc.lower()
        if domain not in domains_seen or current_score > domains_seen[domain][0]:
            domains_seen[domain] = (current_score, url)

    best_url = None
    best_score = 10  # Score threshold below which resluts are discarded
    for _, (score, url) in domains_seen.items():
        if score > best_score:
            best_score = score
            best_url = normalize_url(url)

    return best_url, best_score, all_scored


def get_url(npo_name: str) -> tuple[str | None, int]:
    """
    Discover the official website URL of a Czech nonprofit organization.

    Issues a search query and returns the highest-scoring candidate (if there is one).

    Returns:
        str | None: The discovered URL (root form), or None if no satisfactory candidate was found.
    """
    # Search query is the cleaned org name
    query = clean_npo_name(npo_name)

    try:
        print(f"Searching Serper: '{query}'")

        results = serper_search(query)
        if not results:
            print("  No results returned, continuing...")

        if _no_website_flag(results):
            print(f"  Most results are blacklisted domains - likely no website exists.")
            return None, 0

        best_url, best_score, all_scored = _evaluate_results(results, npo_name)

        print(f"\n--- Results for '{npo_name}' ---")
        for entry in sorted(all_scored, key=lambda x: x["score"], reverse=True):
            print(f"  [{entry['score']:+d}] {entry['url']}")
        print("-----------------------------------")

        if best_url:
            print(f"Found after query '{query}': '{best_url}' (score: {best_score})")
            return best_url, best_score

        print(f"No URL found for '{npo_name}'.")
        return None, 0

    except Exception as e:
        print(f"Unexpected error while searching for '{npo_name}': {e}")
        return None, 0