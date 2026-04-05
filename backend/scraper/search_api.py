import time
import re
from urllib.parse import urlparse
from difflib import SequenceMatcher

from ddgs import DDGS
from unidecode import unidecode

from utils import clean_npo_name

def name_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def normalize_url(url: str) -> str:
    """Normalize URL to its root (strip path, keep scheme + domain)."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"

def score_url(url, npo_name, title):
    score = 0
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.lower()
    query_string = parsed.query.lower()

    domain_blacklist = [
        'facebook.com', 'instagram.com', 'wikipedia.org', 'google.com', 'youtube.com', 'linkedin.com',
        'seznam.cz', 'kurzy.cz', 'finance.cz', 'penize.cz', 'podnikatel.cz', 'zlatestranky.cz',
        'firmy.cz', 'justice.cz', 'detail.cz', 'najisto.cz', 'merk.cz', 'euro.cz', 'statnisprava.cz',
        'firmy-lide.cz', '123firmy.cz', 'katalog-firem.cz', 'finstat.sk', 'kupi.cz', 'heureka.cz', 'mapy.cz',
        'jasnadata.cz', 'mapy.com', 'dnb.com',

        'praha.eu', 'stredoceskykraj.cz', 'plzensky-kraj.cz', 'kr-karlovarsky.cz', 'khk.cz', 'kraj-lbc.cz',
        'kr-ustecky.cz', 'kraj-jihocesky.cz', 'pardubickykraj.cz', 'kr-vysocina.cz', 'jmk.cz', 'msk.cz',
        'zlinskykraj.cz', 'olkraj.cz'
    ]

    url_context = unidecode(domain + path)

    if any(b in domain for b in domain_blacklist):
        return -100
    
    if 'rejstrik' in url_context or 'databaze' in url_context:
        return -100
    
    if query_string:
        score -= 20

    if re.search(r'\d{6,}', path):
        score -= 50

    clean_npo_lower = unidecode(npo_name.lower())
    title_lower = unidecode((title or "").lower())
    domain_no_tld = domain.split('.')[-2] if '.' in domain else domain

    branch_indicators = ['mistni organizace', 'okresni organizace', 'pobocka', 'oddil', 'stredisko']

    is_branch = False
    location_words = []

    for bi in branch_indicators:
        if bi in clean_npo_lower:
            is_branch = True
            parts = clean_npo_lower.split(bi)
            loc_part = parts[-1].replace(',', '').replace('-', '').strip()
            location_words = [w for w in loc_part.split() if len(w) > 2]
            break

    if is_branch and location_words:
        loc_match = any(lw in domain_no_tld or lw in title_lower or lw in path for lw in location_words)

        if not loc_match:
            return -100
    
    if path == '' or path == '/':
        score += 15
    elif len(path.strip('/').split('/')) == 1:
        score += 5
    else:
        score -= 15

    if domain.endswith('.cz') or domain.endswith('.eu'):
        score += 5
    elif domain.endswith('.org'):
        score += 2

    clean_name = unidecode(clean_npo_name(npo_name).lower())
    keywords = [w for w in clean_name.split() if len(w) > 3]
    domain_no_tld = domain.split('.')[-2] if '.' in domain else domain
    title_lower = unidecode((title or "").lower())

    word_match = False
    for kw in keywords:
        if kw in domain_no_tld:
            score += 25
            word_match = True
        elif name_similarity(kw, domain_no_tld) > 0.8:
            score += 15
            word_match = True
        if kw in title_lower:
            score += 10
            word_match = True

    acronym = "".join([w[0] for w in keywords if w]).lower()
    if len(acronym) >= 3 and acronym in domain_no_tld:
        score += 20
        word_match = True

    if not word_match:
        score -= 20

    return score

def get_url(npo_name: str):
    search_name = clean_npo_name(npo_name)
    
    queries = [
        f"{search_name} oficiální stránky",
        f"{search_name} web",
        search_name,
    ]

    best_url = None
    best_score = 10

    try:
        with DDGS() as ddgs:
            for query in queries:
                print(f"Searching DuckDuckGo: '{query}'")

                try:
                    results = ddgs.text(query, region='cz-cs', max_results=15)
                except Exception as e:
                    print(f"  Query failed: {e}, trying next...")
                    time.sleep(2)
                    continue

                if not results:
                    print(f"  No results returned, trying next query...")
                    time.sleep(2)
                    continue

                urls = []
                domains_seen = {}

                for item in results:
                    url = item.get('href')
                    title = item.get('title')
                    current_score = score_url(url, npo_name, title)
                    urls.append({"url": url, "score": current_score})

                    domain_parsed = urlparse(url).netloc.lower()
                    if domain_parsed not in domains_seen or current_score > domains_seen[domain_parsed][0]:
                        domains_seen[domain_parsed] = (current_score, url)

                for domain_key, (score, url) in domains_seen.items():
                    if score > best_score:
                        best_score = score
                        best_url = normalize_url(url)

                print(f"\n--- Results for '{npo_name}' (query: '{query}') ---")
                for i in sorted(urls, key=lambda x: x['score'], reverse=True):
                    print(f"  [{i['score']:+d}] {i['url']}")
                print("-----------------------------------")

                if best_url:
                    print(f"Found after query '{query}': '{best_url}' (score: {best_score})")
                    break

                print(f"No sufficient URL found, trying next query...")
                time.sleep(1.5)

        if not best_url:
            print(f"No URL found for '{npo_name}' across all queries.")

        return best_url

    except Exception as e:
        print(f"Unexpected error while searching for '{npo_name}': {e}")
        time.sleep(5)

    return None