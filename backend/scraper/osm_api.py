import random
import time
from collections import defaultdict

import requests
from sqlalchemy.dialects.postgresql import insert

from database import Branch
from utils import clean_npo_name


ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
]

# Tracks consecutive failures per endpoint across calls; resets when all are exhausted
_endpoint_failures = defaultdict(int)
MAX_ENDPOINT_FAILURES = 3


def _get_healthy_endpoints() -> list[str]:
    healthy = [e for e in ENDPOINTS if _endpoint_failures[e] < MAX_ENDPOINT_FAILURES]
    if not healthy:
        print("All endpoints exceeded failure limit, resetting counters...")
        _endpoint_failures.clear()
        return list(ENDPOINTS)
    return healthy


def _build_query(search_term: str, timeout_sec: int) -> str:
    return f"""
    [out:json][timeout:{timeout_sec}];
    area["ISO3166-1"="CZ"][admin_level=2]->.searchArea;
    (
      node["name"~"{search_term}",i](area.searchArea);
      way["name"~"{search_term}",i](area.searchArea);
    );
    out center;
    """


def _fetch_from_endpoint(
    endpoint: str, params: dict, timeout_sec: int, max_retries: int = 3
) -> requests.Response | None:
    """
    Attempts a query against the given endpoint using exponential backoff with jitter.
    Returns the response on success, or None if all retries are exhausted.
    """
    for attempt in range(max_retries):
        try:
            # Give the server slightly more time than the Overpass timeout to return its own error
            response = requests.get(endpoint, params=params, timeout=timeout_sec + 5)

            if response.status_code == 429:
                wait = (2 ** attempt) * 10 + random.uniform(0, 5)
                print(f"  429 Too Many Requests on {endpoint} – waiting {wait:.1f}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait)
                continue

            if response.status_code == 504:
                wait = (2 ** attempt) * 3 + random.uniform(0, 2)
                print(f"  504 Gateway Timeout on {endpoint} – waiting {wait:.1f}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait)
                continue

            response.raise_for_status()
            return response

        except requests.exceptions.ReadTimeout:
            wait = (2 ** attempt) * 2
            print(f"  Read timeout on {endpoint} (attempt {attempt + 1}/{max_retries}) – waiting {wait}s...")
            time.sleep(wait)

        except Exception as e:
            print(f"  Unexpected error on {endpoint} (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(2)

    return None


def _save_branches(elements: list, org_id: int, session) -> int:
    """
    Persists branch records to the database.
    Uses ON CONFLICT DO NOTHING to safely handle re-runs without creating duplicates.
    Requires a unique constraint on (organization_id, lat, lon) in the Branch table.
    Returns the number of records processed.
    """
    saved_cnt = 0

    for element in elements:
        tags = element.get("tags", {})

        city = tags.get("addr:city")
        street = tags.get("addr:street", "")
        street_num = tags.get("addr:housenumber", "")
        full_street = f"{street} {street_num}".strip() if street or street_num else None

        email = tags.get("contact:email") or tags.get("email")
        phone = tags.get("contact:phone") or tags.get("phone")

        lat = element.get("lat") or element.get("center", {}).get("lat")
        lon = element.get("lon") or element.get("center", {}).get("lon")

        # Skip elements with no useful location data
        if not city and not lat:
            continue

        branch_data = {
            "organization_id": org_id,
            "city": city,
            "street": full_street,
            "email": email,
            "tel_num": phone,
            "lat": lat,
            "lon": lon,
        }

        stmt = insert(Branch).values(**branch_data).on_conflict_do_nothing(
            index_elements=["organization_id", "lat", "lon"]
        )
        session.execute(stmt)
        saved_cnt += 1

    return saved_cnt


def fetch_branches(npo_name: str, org_id: int, session) -> None:
    """
    Searches OpenStreetMap via Overpass API for branches of the given organization
    and stores the results in the database. Iterates through healthy endpoints and
    stops as soon as one succeeds.
    """
    search_term = clean_npo_name(npo_name)

    if len(search_term) < 4:
        print(f"Skipping OSM search for '{npo_name}' (search term too short: '{search_term}')")
        return

    timeout_sec = 75
    params = {"data": _build_query(search_term, timeout_sec)}

    healthy_endpoints = _get_healthy_endpoints()
    print(f"Searching branches for: '{search_term}' (available endpoints: {len(healthy_endpoints)})...")

    for endpoint in healthy_endpoints:
        response = _fetch_from_endpoint(endpoint, params, timeout_sec)

        if response is None:
            _endpoint_failures[endpoint] += 1
            print(f"  Endpoint {endpoint} marked as unreliable (failures: {_endpoint_failures[endpoint]}).")
            continue

        try:
            data = response.json()
        except Exception as e:
            print(f"  Invalid JSON from {endpoint}: {e}")
            _endpoint_failures[endpoint] += 1
            continue

        elements = data.get("elements", [])
        saved_cnt = _save_branches(elements, org_id, session)

        try:
            session.commit()
        except Exception as e:
            print(f"  Database commit failed: {e}")
            session.rollback()
            return

        if saved_cnt > 0:
            print(f"  Success: saved {saved_cnt} branches for '{search_term}'.")
        else:
            print(f"  No branches found on OSM for '{search_term}'.")

        # Throttle requests to avoid hitting rate limits for subsequent organizations
        time.sleep(5)
        return

    print(f"  All endpoints failed for '{search_term}'. Skipping organization.")