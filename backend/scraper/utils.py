"""
@file    utils.py
@brief   Utility functions for HTML parsing, contact extraction, address formatting and geocoding.
@author  Adam Kinzel (xkinzea00)
"""

import requests
import re
import csv
import os
import time
from bs4 import BeautifulSoup
from trafilatura import fetch_url, extract
from urllib.parse import urljoin
from geopy.geocoders import Nominatim

from categories import size_category

# Regex patterns

# Czech legal-form suffixes commonly appearing at the end of an organization name.
_LEGAL_FORM_SUFFIX_REGEX = re.compile(
    r'''(?ix)
        \b(
            z\.?\s?s\.|o\.?\s?p\.?\s?s\.|spolek|ústav|nadace|nadační\s+fond|
            pobočný\s+spolek|obecně\s+prospěšná\s+společnost|
            zapsaný\s+spolek|zapsaná\s+pobočka|z\.?\s?ú\.|
            s\.?\s?r\.?\s?o\.|a\.?\s?s\.
        )[\s,\-]*$
    '''
)

_REGISTERED_OFFICE_REGEX = re.compile(r'(?i)se\s+sídlem.*')
_EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
_PHONE_REGEX = re.compile(r'(?:\+420|\+421)?[\s/]*\d{3}[\s/]*\d{3}[\s/]*\d{3}')
_CONTACT_LINK_REGEX = re.compile(r'(kontakty?|spojen[ií]|napi[sš]te|kde n[aá]s)', re.IGNORECASE)


def log_url(name: str, best_url: str, filename="data/fetched_urls.csv") -> None:
    """Append a (name, url) pair to a CSV file, creating it with a header if missing."""
    file_exists = os.path.isfile(filename)

    with open(filename, mode='a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')

        if not file_exists:
            writer.writerow(['name', 'best_url'])

        writer.writerow([name, best_url if best_url else ""])

def clean_npo_name(name: str) -> str:
    """
    Strip legal-form suffixes and registered-office clauses from an NPO name.

    Used to produce a cleaner search term for the URL discovery pipeline.
    """
    clean = name.strip()
    clean = _LEGAL_FORM_SUFFIX_REGEX.sub('', clean)
    clean = _REGISTERED_OFFICE_REGEX.sub('', clean)
    clean = re.sub(r'\s*[,]\s*', ' ', clean)
    return " ".join(clean.split()).strip()

def get_gps(address: str):
    """
    Geocode a postal address using Nominatim and return the location object.

    Sleeps for 1 second to comply with the public Nominatim usage policy.

    Returns:
        geopy.location.Location | None: None if the address could not be resolved.
    """
    geolocator = Nominatim(user_agent="npo_project")
    location = geolocator.geocode(address)
    time.sleep(1)
    return location

def _safe_csv_field(row: dict, key: str) -> str:
    """
    Return row[key] as a clean string; empty for missing/None values.

    Strips trailing .0 introduced by pandas when reading numeric columns.
    """
    val = row.get(key)
    val_str = str(val).strip()
    if not val or val_str.lower() in ('nan', 'none'):
        return ""
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    return val_str

def format_address(row: dict) -> str:
    """Compose a postal address string from individual ČSÚ CSV columns."""
    psc = _safe_csv_field(row, 'PSC')
    city = _safe_csv_field(row, 'OBEC_TEXT')
    city_district = _safe_csv_field(row, 'COBCE_TEXT')
    street = _safe_csv_field(row, 'ULICE_TEXT')
    cdom = _safe_csv_field(row, 'CDOM')
    cor = _safe_csv_field(row, 'COR')

    if cdom and cor:
        house_number = f"{cdom}/{cor}"
    elif cdom:
        house_number = cdom
    else:
        house_number = ""

    if street:
        street_part = f"{street} {house_number}".strip()
    elif city_district:
        street_part = f"{city_district} {house_number}".strip()
    else:
        street_part = house_number

    city_part = f"{psc} {city}".strip()
    return f"{street_part}, {city_part}".strip(', ')

def format_size_category(category_code: str) -> dict:
    """
    Convert a ČSÚ size-category code to a structured dict with min/max employee count.

    Returns:
        dict: with keys label, min_emp, max_emp. Missing or invalid
        codes gives an "Unknown" entry with None bounds.
    """
    raw = size_category.get(str(category_code))

    if not raw or raw == "Neuvedeno":
        return {"label": "Unknown", "min_emp": None, "max_emp": None}

    if raw == "Bez zaměstnanců":
        return {"label": "0 employees", "min_emp": 0, "max_emp": 0}

    numbers = [int(s) for s in re.findall(r'\d+', raw.replace(" ", ""))]

    if len(numbers) >= 2:
        min_emp, max_emp = numbers[0], numbers[1]
        return {"label": f"{min_emp}-{max_emp} employees", "min_emp": min_emp, "max_emp": max_emp}
    if len(numbers) == 1:
        min_emp = numbers[0]
        return {"label": f"{min_emp}+ employees", "min_emp": min_emp, "max_emp": None}

    return {"label": "Unknown", "min_emp": None, "max_emp": None}

def get_html(html_string: str) -> str:
    """Strip <script>, <style> and <head> and return plain visible text."""
    if not html_string:
        return ""
    soup = BeautifulSoup(html_string, 'html.parser')
    for element in soup.find_all(['script', 'style', 'head']):
        element.decompose()
    return soup.get_text(separator=' ')

def fetch_contact_page(url: str) -> str | None:
    """
    Locate the contact page of a website by scanning hyperlinks for Czech contact keywords.

    Returns:
        str | None: Absolute URL of the discovered contact page, or None if
        no link matched or the request failed.
    """
    if not url:
        return None

    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, 'html.parser')
        for a_tag in soup.find_all('a', href=True):
            link_text = a_tag.get_text(strip=True)
            href = a_tag['href'].strip()

            if _CONTACT_LINK_REGEX.search(link_text):
                # Skip non-navigational hrefs (mailto, tel, JS handlers, anchors).
                if href.lower().startswith(('mailto:', 'tel:', 'javascript:', '#')):
                    continue
                return urljoin(url, href)
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch contact page for {url}: {e}")

    return None

def _extract_unique(pattern: re.Pattern, page: str) -> list[str]:
    """Find all regex matches in page and return them deduplicated, preserving order."""
    if not page:
        return []
    return list(dict.fromkeys(pattern.findall(page)))


def get_emails(page: str) -> list[str]:
    """Extract a deduplicated list of e-mail addresses from text content."""
    return _extract_unique(_EMAIL_REGEX, page)


def get_tel_numbers(page: str) -> list[str]:
    """Extract a deduplicated list of phone numbers (Czech / Slovak format) from text content."""
    return _extract_unique(_PHONE_REGEX, page)


def get_web_content(url: str) -> str:
    """Fetch the URL and return the main content using the trafilatura library."""
    return extract(fetch_url(url))