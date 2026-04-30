"""
@file    main.py
@brief   Pipeline entry point: data acquisition, transformation, enrichment, and persistence.
@author  Adam Kinzel (xkinzea00)

This module orchestrates the full ETL pipeline. Source data is ingested from
the official ČSÚ register, augmented with web search and LLM-based enrichment,
and persisted to a relational database.
"""

import os
import random
import re
from datetime import datetime

import pandas as pd
import requests
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

import argument_parsing
import llm_gen
from categories import size_category as size_category_dict
from database import (
    Base,
    Category,
    DataSource,
    LegalForm,
    Organization,
    OrganizationCategory,
    Session,
    SizeCategory,
    engine,
)
from osm_api import fetch_branches
from search_api import get_url
from utils import (
    fetch_contact_page,
    format_address,
    get_emails,
    get_gps,
    get_html,
    get_tel_numbers,
    log_url,
)


_CSV_SOURCE_URL = 'https://opendata.csu.gov.cz/soubory/od/od_org03/res_data.csv'
_CSV_LOCAL_FILENAME = "res_data.csv"

# Legal form codes considered as nonprofit organizations (ČSÚ codebook).
_NPO_LEGAL_FORM_CODES = (117, 118, 141, 161, 706, 721, 722, 736)

# Code 736 = "Pobočný spolek" (branch entity), processed in a second pass after parents.
_BRANCH_LEGAL_FORM_CODE = 736

# Static codebook content uploaded into the database during setup.
_LEGAL_FORMS_DATA = {
    "117": "Nadace",
    "118": "Nadační fond",
    "141": "Obecně prospěšná společnost",
    "161": "Ústav",
    "706": "Spolek",
    "721": "Církevní organizace",
    "722": "Evidované církevní právnické osoby",
    "736": "Pobočný spolek",
}

_THEMATIC_CATEGORIES = (
    "Social services", "Education", "Healthcare", "Culture", "Environment",
    "Sports", "Youth", "Senior support", "Disability support",
    "Community development", "Human rights", "Charity & fundraising",
    "Arts & creative activities", "Animal welfare", "Other",
)


def _parse_zfilled_code(raw_value, width: int) -> str | None:
    """
    Parse a numeric ČSÚ code into a zero-padded string of given width.

    Returns None for missing or invalid values.
    """
    if pd.isna(raw_value) or raw_value == "":
        return None
    try:
        return str(int(float(raw_value))).zfill(width)
    except (ValueError, TypeError):
        return None


def _parse_size_bounds(label: str) -> tuple[int | None, int | None]:
    """Extract (min_emp, max_emp) from a size-category label such as '1 - 5 zaměstnanců'."""
    if "Bez" in label:
        return 0, 0
    if "Neuvedeno" in label:
        return None, None

    nums = [int(s) for s in re.findall(r'\d+', label.replace(" ", ""))]
    if len(nums) >= 2:
        return nums[0], nums[1]
    if len(nums) == 1:
        return nums[0], None
    return None, None


def upsert_codebooks() -> None:
    """Populate the legal-form and size-category codebook tables."""
    session = Session()
    try:
        # Legal forms
        for code, name in _LEGAL_FORMS_DATA.items():
            stmt = insert(LegalForm).values(code=code, name=name)
            stmt = stmt.on_conflict_do_nothing(index_elements=['code'])
            session.execute(stmt)

        # Size categories
        for code, label in size_category_dict.items():
            min_e, max_e = _parse_size_bounds(label)
            stmt = insert(SizeCategory).values(
                code=code, label=label, min_emp=min_e, max_emp=max_e,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=['code'],
                set_={
                    'label': stmt.excluded.label,
                    'min_emp': stmt.excluded.min_emp,
                    'max_emp': stmt.excluded.max_emp,
                },
            )
            session.execute(stmt)

        session.commit()
        print("Codebooks were successfully uploaded to DB.")
    except Exception as e:
        session.rollback()
        print(f"Error during codebook upload: {e}")
    finally:
        session.close()


def upsert_categories() -> None:
    """Populate the thematic-category table."""
    session = Session()
    try:
        for category in _THEMATIC_CATEGORIES:
            insert_stmt = insert(Category).values(name=category)
            upsert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=['name'],
                set_={'name': insert_stmt.excluded.name},
            )
            session.execute(upsert_stmt)
        session.commit()
        print("Category import successful")
    except Exception as e:
        print(f"Error during category import: {e}")
    finally:
        session.close()


def _resolve_url(row: dict, ico_val: str, parent_id, session) -> str | None:
    """
    Determine the website URL of an organization, reusing cached values when possible.

    If the organization is already in the database, its stored URL is reused.
    Otherwise a fresh search is issued. As a fallback, branches inherit the URL
    of their parent organization.
    """
    existing_url = session.execute(
        select(Organization.web_url).where(ico_val == Organization.ico)
    ).scalar()
    if existing_url is not None:
        print(f"Organization {row.get('FIRMA')} has a URL in database, skipping search...")
        url = existing_url
    else:
        url = get_url(row.get('FIRMA'))

    # Branch fallback: inherit the parent's URL if we did not find anything.
    if not url and parent_id is not None:
        parent_url = session.execute(
            select(Organization.web_url).where(Organization.organization_id == parent_id)
        ).scalar()
        if parent_url:
            print(f"Branch inherits URL from parent: {parent_url}")
            url = parent_url

    return url


def _resolve_description(row: dict, ico_val: str, branch_url: str, session) -> tuple[str | None, list | None]:
    """
    Generate or retrieve description and category list for an organization.

    Returns:
        tuple: (description, categories). categories is None when the
        record already has a description in the database (i.e. nothing to upsert).
    """
    existing_desc = session.execute(
        select(Organization.description).where(Organization.ico == ico_val)
    ).scalar()

    if existing_desc is None:
        print(f"Organization {row.get('FIRMA')} has no description, generating...")
        gen_res = llm_gen.generate(row.get('FIRMA'), branch_url)
        return gen_res.get('description'), gen_res.get('categories', [])

    print(f"Organization {row.get('FIRMA')} already has a description, skipping generation.")
    return existing_desc, None


def _extract_contact_info(branch_url: str) -> tuple[list[str], list[str]]:
    """Fetch the organization's contact page and extract emails and phone numbers."""
    contact_page_url = fetch_contact_page(branch_url)
    target_url = contact_page_url or branch_url
    if not target_url:
        return [], []

    try:
        r = requests.get(target_url, timeout=10)
        if r.status_code != 200:
            return [], []
        contact_html = get_html(r.text)
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch contact HTML for {target_url}: {e}")
        return [], []

    return get_emails(contact_html), get_tel_numbers(contact_html)


def _upsert_organization(org_data: dict, session) -> str | None:
    """Insert or update an organization record and return its primary key."""
    insert_stmt = insert(Organization).values(**org_data)
    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=['ico'],
        set_={
            col: insert_stmt.excluded[col]
            for col in (
                'parent_id', 'name', 'legal_form_code', 'hq_address',
                'emails', 'tel_numbers', 'size_category_code', 'web_url',
                'source_id', 'description', 'lat', 'lon',
            )
        },
    ).returning(Organization.organization_id)
    return session.execute(upsert_stmt).scalar()


def _link_categories(org_id, categories: list[str], session) -> None:
    """Attach a list of category names to an organization (no-op for unknown names)."""
    for category_name in categories:
        cat_id = session.execute(
            select(Category.category_id).where(Category.name == category_name)
        ).scalar()
        if not cat_id:
            continue

        stmt = insert(OrganizationCategory).values(
            organization_id=org_id, category_id=cat_id,
        ).on_conflict_do_nothing(index_elements=['organization_id', 'category_id'])
        session.execute(stmt)


def process_insert_org(row: dict, source_id, session, parent_id=None):
    """
    Run the full per-organization pipeline (URL search, LLM, contacts, persistence).

    Skips organizations missing an IČO or in liquidation, or those for which the
    LLM step returned no categories.
    """
    ico_val = _parse_zfilled_code(row.get('ICO'), width=8)
    if ico_val is None:
        return None

    if "v likvidaci" in (row.get('FIRMA') or ""):
        return None

    legal_form_code = _parse_zfilled_code(row.get('FORMA'), width=3)
    size_cat_code = _parse_zfilled_code(row.get('KATPO'), width=3)

    branch_url = _resolve_url(row, ico_val, parent_id, session)
    description, categories = _resolve_description(row, ico_val, branch_url, session)

    # An organization without categories is not persisted.
    if categories is not None and len(categories) == 0:
        return None

    emails, tel_numbers = _extract_contact_info(branch_url)

    address = format_address(row)
    location = get_gps(address)
    lat = location.latitude if location else None
    lon = location.longitude if location else None

    org_data = {
        "source_id": source_id,
        "parent_id": parent_id,
        "name": row.get('FIRMA'),
        "ico": ico_val,
        "legal_form_code": legal_form_code,
        "hq_address": address,
        "emails": emails,
        "tel_numbers": tel_numbers,
        "web_url": branch_url,
        "created_at": datetime.now(),
        "size_category_code": size_cat_code,
        "description": description,
        "lat": lat,
        "lon": lon,
    }

    log_url(row.get('FIRMA'), branch_url)
    org_id = _upsert_organization(org_data, session)

    if org_id and categories:
        _link_categories(org_id, categories, session)

    return org_id


def _download_source_csv() -> None:
    """
    Download the source CSV from ČSÚ to the local filesystem.
    The size of the source CSV is ~500 MB.
    """
    print("Downloading source data...")
    r = requests.get(_CSV_SOURCE_URL, stream=True)
    r.raise_for_status()
    with open(_CSV_LOCAL_FILENAME, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Download completed.")


def get_source() -> pd.DataFrame | None:
    """
    Load the ČSÚ register and filter it down to nonprofit legal forms.

    Re-uses the locally cached file when present.
    """
    try:
        if os.path.exists(_CSV_LOCAL_FILENAME):
            print(f"Source file '{_CSV_LOCAL_FILENAME}' found locally. Skipping download.")
        else:
            _download_source_csv()

        print("Filtering nonprofits...")
        chunks = []
        for chunk in pd.read_csv(_CSV_LOCAL_FILENAME, chunksize=10000, sep=',', low_memory=False):
            chunks.append(chunk[chunk['FORMA'].isin(_NPO_LEGAL_FORM_CODES)])

        if chunks:
            npos = pd.concat(chunks)
            print(f"Success: Found {len(npos)} non-profits.")
            return npos
        print("No data found for desired legal forms.")
        return None
    except Exception as e:
        print(f"Error during accessing data source: {e}")
        return None


def _find_parent_for_branch(parent_name_guess: str, session):
    """Find the candidate parent organization for a branch entity by name prefix."""
    return session.execute(
        select(Organization.organization_id)
        .where(Organization.name.ilike(f"{parent_name_guess}%"))
        .where(Organization.parent_id.is_(None))
        .limit(1)
    ).scalar()


def init_pipeline(npo_data: pd.DataFrame | None, args) -> None:
    """Run the two-pass pipeline: parents first, then branches with parent linking."""
    if npo_data is None or npo_data.empty:
        print("No data to process.")
        return

    session = Session()
    try:
        source = DataSource(
            name="CSV import",
            url=_CSV_SOURCE_URL,
            last_scraped=datetime.now(),
        )
        session.add(source)
        session.flush()

        records = npo_data.to_dict(orient='records')

        if args.limit:
            print(f"Limiting execution to {args.limit} records.")
            final_limit = min(args.limit, len(records))
            records = random.sample(records, final_limit)

        # First pass - parent organizations.
        for row in records:
            if row.get('FORMA') != _BRANCH_LEGAL_FORM_CODE:
                process_insert_org(row, source.source_id, session)
        session.commit()

        # Second pass - branches linked to their parents.
        for row in records:
            if row.get('FORMA') == _BRANCH_LEGAL_FORM_CODE:
                parent_name_guess = str(row.get('FIRMA')).split(',')[0].strip()
                parent_id = _find_parent_for_branch(parent_name_guess, session)
                process_insert_org(row, source.source_id, session, parent_id)
        session.commit()

        print("Data import successful.")
    except Exception as e:
        session.rollback()
        print(f"Error during import: {e}")
    finally:
        session.close()

# Main entry point.
if __name__ == "__main__":
    args = argument_parsing.parse()

    Base.metadata.create_all(engine)
    upsert_categories()
    upsert_codebooks()

    npo_data = get_source()
    init_pipeline(npo_data, args)