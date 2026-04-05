import requests
import re
import csv
import os
from bs4 import BeautifulSoup
from trafilatura import fetch_url, extract
from urllib.parse import urljoin

def log_url(name: str, best_url: str, filename="fetched_urls.csv"):
    file_exists = os.path.isfile(filename)

    with open(filename, mode='a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')

        if not file_exists:
            writer.writerow(['name', 'best_url'])

        writer.writerow([name, best_url if best_url else ""])

def clean_npo_name(name):
    clean = name.strip()
    legal_forms = r'''(?ix)
        \b(
            z\.?\s?s\.|o\.?\s?p\.?\s?s\.|spolek|ústav|nadace|nadační\s+fond|
            pobočný\s+spolek|obecně\s+prospěšná\s+společnost|
            zapsaný\s+spolek|zapsaná\s+pobočka|z\.?\s?ú\.|
            s\.?\s?r\.?\s?o\.|a\.?\s?s\.
        )[\s,\-]*$
    '''
    clean = re.sub(legal_forms, '', clean)
    clean = re.sub(r'(?i)se\s+sídlem.*', '', clean)
    clean = re.sub(r'\s*[,]\s*', ' ', clean)
    return " ".join(clean.split()).strip()

def format_size_category(raw: str) -> dict:
    """
    Formats the size category description from original format to a dictionary
    consisting of a label, minimum and maximum number of employees.
    """
    if not raw or "Neuvedeno" in raw:
        return {
            "label": "Unknown",
            "min_emp": None,
            "max_emp": None
        }

    numbers = [int(s) for s in re.findall(r'\d+', raw)]

    if len(numbers) >= 2:
        min_emp = numbers[0]
        max_emp = numbers[1]
        label = f"{min_emp}-{max_emp} employees"
    elif len(numbers) == 1:
        min_emp = numbers[0]
        max_emp = None
        label = f"{min_emp}+ employees"
    else:
        return {"label": "Unknown", "min_emp": None, "max_emp": None}

    return {
        "label": label,
        "min_emp": min_emp,
        "max_emp": max_emp
    }

def get_html(html_string: str) -> str:
    if not html_string:
        return ""
    
    soup = BeautifulSoup(html_string, 'html.parser')

    for element in soup.find_all(['script', 'style', 'head']):
        element.decompose()

    return soup.get_text(separator=' ')

def fetch_contact_page(url):
    if not url:
        return None

    try:
        r = requests.get(url)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            contact_regex = re.compile(r'(kontakty?|spojen[ií]|napi[sš]te|kde n[aá]s)', re.IGNORECASE)

            for a_tag in soup.find_all('a', href=True):
                link_text = a_tag.get_text(strip=True)
                href = a_tag['href'].strip()
                
                if contact_regex.search(link_text):
                    if href.lower().startswith(('mailto:', 'tel:', 'javascript:', '#')):
                        continue
                        
                    full_url = urljoin(url, href)
                    return full_url
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch contact page for {url}: {e}")

    return None

def get_emails(page):
    if not page:
        return []
    res = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page)
    res = list(dict.fromkeys(res))
    return res

def get_tel_numbers(page):
    if not page:
        return []
    res = re.findall(r'(?:\+420|\+421)?[\s/]*\d{3}[\s/]*\d{3}[\s/]*\d{3}', page)
    res = list(dict.fromkeys(res))
    return res

def get_web_content(url: str) -> str:
    """
    Extracts and returns the content of a webpage located at 'url' using trafilatura library.
    """
    return extract(fetch_url(url))

if __name__ == "__main__":
    url = "https://bratri-capkove.cz/"
    res = fetch_contact_page(url)

    print(f"URL of contact page for {url} is: {res}")

    target_url = res if res else url
    
    r = requests.get(target_url)
    
    raw_text_for_contacts = get_html(r.text)

    emails = get_emails(raw_text_for_contacts)
    tel_numbers = get_tel_numbers(raw_text_for_contacts)

    print("Emails:")
    for email in emails:
        print(email)

    print("Telephone numbers:")
    for tel_number in tel_numbers:
        print(tel_number)