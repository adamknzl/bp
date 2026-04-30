"""
@file    osm_api.py
@brief   Branch discovery via OpenStreetMap Overpass API with endpoint rotation and retries.
@author  Adam Kinzel (xkinzea00)
"""

import random
import time
import uuid
from collections import defaultdict

import requests
from sqlalchemy.dialects.postgresql import insert

from database import Branch
from utils import clean_npo_name


ENDPOINTS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
)

_endpoint_failures: defaultdict = defaultdict(int)
MAX_ENDPOINT_FAILURES = 3


def _get_healthy_endpoints() -> list[str]:
    """
    Return endpoints whose failure count is below the threshold.

    If all endpoints are saturated, the failure counters are reset and the
    full list is returned.
    """
    healthy = [e for e in ENDPOINTS if _endpoint_failures[e] < MAX_ENDPOINT_FAILURES]
    if not healthy:
        print("All endpoints exceeded failure limit, resetting counters...")
        _endpoint_failures.clear()
        return list(ENDPOINTS)
    return healthy


def _build_query(search_term: str, timeout_sec: int) -> str:
    """Build an Overpass QL query searching nodes and ways inside the Czech Republic."""
    return f"""
    [out:json][timeout:{timeout_sec}];
    area["ISO3166-1"="CZ"][admin_level=2]->.searchArea;
    (
      node["name"~"{search_term}",i](area.searchArea);
      way["name"~"{search_term}",i](area.searchArea);
    );
    out center;
    """


def _backoff_sleep(base: int, attempt: int, jitter_max: float = 0.0) -> float:
    """Compute and apply an exponential-backoff sleep, returning the slept duration."""
    wait = (2 ** attempt) * base + random.uniform(0, jitter_max)
    time.sleep(wait)
    return wait


def _fetch_from_endpoint(endpoint: str, params: dict, timeout_sec: int, max_retries: int = 3) -> requests.Response | None:
    """
    Query a single endpoint with exponential backoff and explicit handling of 429 / 504.

    Returns:
        requests.Response | None: None if all retries are exhausted.
    """
    for attempt in range(max_retries):
        try:
            # Allow the server slightly more time than the Overpass timeout itself.
            response = requests.get(endpoint, params=params, timeout=timeout_sec + 5)

            if response.status_code == 429:
                wait = _backoff_sleep(base=10, attempt=attempt, jitter_max=5)
                print(
                    f"  429 Too Many Requests on {endpoint} – waited {wait:.1f}s "
                    f"(attempt {attempt + 1}/{max_retries})..."
                )
                continue

            if response.status_code == 504:
                wait = _backoff_sleep(base=3, attempt=attempt, jitter_max=2)
                print(
                    f"  504 Gateway Timeout on {endpoint} – waited {wait:.1f}s "
                    f"(attempt {attempt + 1}/{max_retries})..."
                )
                continue

            response.raise_for_status()
            return response

        except requests.exceptions.ReadTimeout:
            wait = _backoff_sleep(base=2, attempt=attempt)
            print(
                f"  Read timeout on {endpoint} (attempt {attempt + 1}/{max_retries}) "
                f"– waited {wait}s..."
            )

        except Exception as e:
            print(f"  Unexpected error on {endpoint} (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(2)

    return None


def _extract_branch_record(element: dict, org_id: uuid.UUID) -> dict | None:
    """Project a single Overpass element into a Branch row, or None if it lacks usable data."""
    tags = element.get("tags", {})

    city = tags.get("addr:city")
    street = tags.get("addr:street", "")
    street_num = tags.get("addr:housenumber", "")
    full_street = f"{street} {street_num}".strip() if street or street_num else None

    email = tags.get("contact:email") or tags.get("email")
    phone = tags.get("contact:phone") or tags.get("phone")

    lat = element.get("lat") or element.get("center", {}).get("lat")
    lon = element.get("lon") or element.get("center", {}).get("lon")

    # Skip elements with neither a city name nor any coordinates.
    if not city and not lat:
        return None

    return {
        "organization_id": org_id,
        "city": city,
        "street": full_street,
        "email": email,
        "tel_num": phone,
        "lat": lat,
        "lon": lon,
    }


def _save_branches(elements: list, org_id: uuid.UUID, session) -> int:
    """
    Persist branch records using ON CONFLICT DO NOTHING to handle re-runs safely.

    Requires a unique constraint on (organization_id, lat, lon).

    Returns:
        int: Number of branch records submitted to the database.
    """
    saved_cnt = 0
    for element in elements:
        record = _extract_branch_record(element, org_id)
        if record is None:
            continue

        stmt = insert(Branch).values(**record).on_conflict_do_nothing(
            index_elements=["organization_id", "lat", "lon"],
        )
        session.execute(stmt)
        saved_cnt += 1
    return saved_cnt


def fetch_branches(npo_name: str, org_id: uuid.UUID, session) -> None:
    """
    Search OSM for branches of an organization and persist them to the database.

    Iterates through healthy endpoints and stops as soon as one returns a valid
    response. Endpoints that repeatedly fail are skipped on subsequent calls.
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

        # Throttle subsequent calls to respect the public Overpass rate limits.
        time.sleep(5)
        return

    print(f"  All endpoints failed for '{search_term}'. Skipping organization.")