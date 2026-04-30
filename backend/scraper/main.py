import csv
from datetime import datetime
import time
import requests
import os
import random
import pandas as pd
from collections import defaultdict
from contextlib import contextmanager
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from geopy.geocoders import Nominatim

from database import Session, DataSource, Organization, Category, OrganizationCategory, SizeCategory, engine, Base, LegalForm
from search_api import get_url
from osm_api import fetch_branches
from utils import format_size_category, format_address, get_gps, log_url, get_tel_numbers, get_emails, get_web_content, fetch_contact_page, get_html
from categories import size_category as size_category_dict
import argument_parsing
import llm_gen

benchmark_stats = defaultdict(float)

@contextmanager
def measure_time(category_name):
    start = time.perf_counter()
    yield
    end = time.perf_counter()
    benchmark_stats[category_name] += (end - start)

def process_row_worker(row, source_id, parent_id_guess=None):
    local_session = Session()
    try:
        process_insert_org(row, source_id, local_session, parent_id_guess)
        local_session.commit()
    except Exception as e:
        local_session.rollback()
        print(f"Error in thread for {row.get('name')}: {e}")
    finally:
        local_session.close()

def upsert_codebooks():
    session = Session()

    # 1. Dáta pre Právne formy
    legal_forms_data = {
        "117": "Nadace",
        "118": "Nadační fond",
        "141": "Obecně prospěšná společnost",
        "161": "Ústav",
        "706": "Spolek",
        "721": "Církevní organizace",
        "722": "Evidované církevní právnické osoby",
        "736": "Pobočný spolek"
    }

    try:
        # Import Právnych foriem
        for code, name in legal_forms_data.items():
            stmt = insert(LegalForm).values(code=code, name=name)
            stmt = stmt.on_conflict_do_nothing(index_elements=['code'])
            session.execute(stmt)

        # Import Veľkostných kategórií
        import re
        for code, label in size_category_dict.items():
            # Určenie min a max zamestnancov
            if "Bez" in label:
                min_e, max_e = 0, 0
            elif "Neuvedeno" in label:
                min_e, max_e = None, None
            else:
                nums = [int(s) for s in re.findall(r'\d+', label.replace(" ", ""))]
                if len(nums) >= 2:
                    min_e, max_e = nums[0], nums[1]
                elif len(nums) == 1:
                    min_e, max_e = nums[0], None
                else:
                    min_e, max_e = None, None

            stmt = insert(SizeCategory).values(code=code, label=label, min_emp=min_e, max_emp=max_e)
            stmt = stmt.on_conflict_do_update(
                index_elements=['code'],
                set_={'label': stmt.excluded.label, 'min_emp': stmt.excluded.min_emp, 'max_emp': stmt.excluded.max_emp}
            )
            session.execute(stmt)

        session.commit()
        print("Číselníky boli úspešne nahraté do DB.")
    except Exception as e:
        session.rollback()
        print(f"Chyba pri nahrávaní číselníkov: {e}")
    finally:
        session.close()

def upsert_categories():
    session = Session()

    categories = [
        "Social services", "Education", "Healthcare",
        "Culture", "Environment", "Sports", "Youth",
        "Senior support", "Disability support", "Community development",
        "Human rights", "Charity & fundraising", "Arts & creative activities",
        "Animal welfare", "Other"
    ]

    try:
        for category in categories:
            category_data = {
                "name": category
            }
            insert_stmt = insert(Category).values(**category_data)
            upsert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=['name'],
                set_={
                    'name': insert_stmt.excluded.name
                }
            )

            session.execute(upsert_stmt)

        session.commit()
        print("Category import successful")

    except Exception as e:
        print(f"Error during category import: {e}")

    finally:
        session.close()

def process_insert_org(row, source_id, session, parent_id=None):
    ico_raw = row.get('ICO')
    
    if pd.isna(ico_raw) or not ico_raw:
        return None

    ico_val = str(int(float(ico_raw))).zfill(8)

    forma_raw = row.get('FORMA')
    legal_form_code = str(int(float(forma_raw))).zfill(3) if pd.notna(forma_raw) and forma_raw != "" else None

    katpo_raw = row.get('KATPO') 
    size_cat_code = str(int(float(katpo_raw))).zfill(3) if pd.notna(katpo_raw) and katpo_raw != "" else None

    if "v likvidaci" in row.get('FIRMA'):
        return None

    with measure_time('URL search'):
        branch_url = session.execute(select(Organization.web_url).where(ico_val == Organization.ico)).scalar()
        if branch_url is not None:
            print(f"Organization {row.get('FIRMA')} has a URL in database, skipping...")
        else:
            branch_url = get_url(row.get('FIRMA'))

    if not branch_url and parent_id is not None:
        parent_url = session.execute(
            select(Organization.web_url).where(Organization.organization_id == parent_id)
        ).scalar()

        branch_url = parent_url
        print(f"Branch does not have its own web, inheriting URL from parent: {parent_url}")

    select_stmt = select(Organization.description).where(Organization.ico == ico_val)
    if(session.execute(select_stmt).scalar() == None):
        print(f"Organization {row.get('FIRMA')} does not have a description, generating one...")
        with measure_time('LLM generating'):
            gen_res = llm_gen.generate(row.get('FIRMA'), branch_url)

            description = gen_res.get('description')
            categories = gen_res.get('categories', [])

            if len(categories) == 0:
                return None
    else:
        print(f"Organization {row.get('FIRMA')} already has a description, skipping generating...")
        description = session.execute(select(Organization.description).where(Organization.ico == ico_val)).scalar()
        categories = None

    contact_page_url = fetch_contact_page(branch_url)
    target_url = contact_page_url if contact_page_url else branch_url

    contact_page_html = ""
    if target_url:
        try:
            r = requests.get(target_url, timeout=10)
            if r.status_code == 200:
                contact_page_html = get_html(r.text)
        except requests.exceptions.RequestException as e:
            print(f"Nepodarilo sa stiahnut HTML pre {target_url}: {e}")

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
        "emails": get_emails(contact_page_html),
        "tel_numbers": get_tel_numbers(contact_page_html),
        "web_url": branch_url,
        "created_at": datetime.now(),
        "size_category_code": size_cat_code,
        "description": description,
        "lat": lat,
        "lon": lon
    }

    log_url(row.get('FIRMA'), org_data["web_url"])

    with measure_time('Database insert:'):
        insert_stmt = insert(Organization).values(**org_data)

        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=['ico'],
            set_={
                'parent_id': insert_stmt.excluded.parent_id,
                'name': insert_stmt.excluded.name,
                'legal_form_code': insert_stmt.excluded.legal_form_code,
                'hq_address': insert_stmt.excluded.hq_address,
                'emails': insert_stmt.excluded.emails,
                'tel_numbers': insert_stmt.excluded.tel_numbers,
                'size_category_code': insert_stmt.excluded.size_category_code,
                'web_url': insert_stmt.excluded.web_url,
                'source_id': insert_stmt.excluded.source_id,
                'description': insert_stmt.excluded.description,
                'lat': insert_stmt.excluded.lat,
                'lon': insert_stmt.excluded.lon
            }
        ).returning(Organization.organization_id)

        org_id = session.execute(upsert_stmt).scalar()

        if org_id and categories:
            for category_name in categories:
                select_stmt = select(Category.category_id).where(Category.name == category_name)
                cat_id = session.execute(select_stmt).scalar()

                if cat_id:
                    org_cat_data = {
                        'organization_id': org_id,
                        'category_id': cat_id
                    }

                    insert_cat_stmt = insert(OrganizationCategory).values(org_cat_data)
                    upsert_cat_stmt = insert_cat_stmt.on_conflict_do_nothing(
                        index_elements=['organization_id', 'category_id']
                    )

                    session.execute(upsert_cat_stmt)

    return org_id

def get_source():
    url = 'https://opendata.csu.gov.cz/soubory/od/od_org03/res_data.csv'
    filename = "res_data.csv"

    try:
        # 1. Kontrola, či už súbor existuje lokálne na disku
        if os.path.exists(filename):
            print(f"Súbor '{filename}' nájdený lokálne. Preskakujem sťahovanie...")
        else:
            # Súbor neexistuje, musíme ho stiahnuť
            print("Downloading source data...")
            
            r = requests.get(url, stream=True)
            r.raise_for_status()

            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print("Downloading completed.")

        # 2. Samotné filtrovanie (prebehne rovnako zo stiahnutého aj lokálneho súboru)
        print("Filtering non-profits...")
        npo_codes = [117, 118, 141, 161, 706, 721, 722, 736]
        filtered_data = []

        for chunk in pd.read_csv(filename, chunksize=10000, sep=',', low_memory=False):
            chunk_npo = chunk[chunk['FORMA'].isin(npo_codes)]
            filtered_data.append(chunk_npo)

        if filtered_data:
            npos = pd.concat(filtered_data)
            print(f"Success: Found {len(npos)} non-profits.")
            return npos
        else:
            print("No data found for desired legal forms.")
            return None

    except Exception as e:
        print(f"Error during accessing data source: {e}")
        return None
    
def init_pipeline(npo_data, args):
    if npo_data is None or npo_data.empty:
        print("No data to process.")
        return

    session = Session()

    try:
        source = DataSource(
            name="CSV import",
            url="https://opendata.csu.gov.cz/soubory/od/od_org03/res_data.csv",
            last_scraped=datetime.now()
        )
        session.add(source)
        session.flush()

        records = npo_data.to_dict(orient='records')

        if args.limit:
            print(f"Limiting execution to {args.limit} records.")
            
            final_limit = min(args.limit, len(records))
            records = random.sample(records, final_limit)

        for row in records:
            if row.get('FORMA') != 736: # Pobocny spolek
                process_insert_org(row, source.source_id, session)

        session.commit()

        for row in records:
            if row.get('FORMA') == 736:
                parent_name_guess = str(row.get('FIRMA')).split(',')[0].strip()

                parent_id = session.execute(
                    select(Organization.organization_id)
                    .where(Organization.name.ilike(f"{parent_name_guess}%"))
                    .where(Organization.parent_id == None)
                    .limit(1)
                ).scalar()

                process_insert_org(row, source.source_id, session, parent_id)
        
        session.commit()
        print("Data import successful.")

    except Exception as e:
        session.rollback()
        print(f"Error during import: {e}")
    finally:
        session.close()

def import_csv(csv_filename):
    session = Session()

    try:
        source = DataSource(
            name="Import CSV",
            url=csv_filename,
            last_scraped=datetime.now()
        )
        session.add(source)
        session.flush()

        with open(csv_filename, mode="r", encoding="utf-8") as file:
            csv_reader = list(csv.DictReader(file, delimiter=";"))

            for row in csv_reader:
                if row.get('legal_form') != 'Pobočný spolek':
                    process_insert_org(row, source.source_id, session)

            session.commit()

            for row in csv_reader:
                if row.get('legal_form') == 'Pobočný spolek':
                    parent_name_guess = row.get('name').split(',')[0].strip()
                    #print(f"Concat'd name for {row.get('name')} is {parent_name_guess}")

                    parent_id = session.execute(
                        select(Organization.organization_id)
                        .where(Organization.name.ilike(f"{parent_name_guess}%"))
                        .where(Organization.parent_id == None) # Rodič nesmie byť pobočka
                        .limit(1)
                    ).scalar()

                    #if parent_id:
                    #    print(f"Branch '{row.get('name')}' attached to parent (ID: {parent_id}).")
                    #else:
                    #    print(f"Parent for '{row.get('name')}' not found in DB.")

                    process_insert_org(row, source.source_id, session, parent_id)

            session.commit()

            if argument_parsing.parse():
                main_orgs = session.execute(
                    select(Organization).where(Organization.parent_id == None)
                ).scalars().all()

                for org in main_orgs:
                    has_children = session.execute(
                        select(Organization.organization_id)
                        .where(Organization.parent_id == org.organization_id)
                        .limit(1)
                    ).scalar()

                    if not has_children:
                        fetch_branches(org.name, org.organization_id, session)
                    else:
                        print(f"Skipping OSM for '{org.name}' (structure already loaded from CSV).")

            session.commit()
            print("Data import successful.")

    except Exception as e:
        session.rollback()
        print(f"Error during import: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    #time_start = time.perf_counter()

    args = argument_parsing.parse()

    Base.metadata.create_all(engine)
    upsert_categories()
    upsert_codebooks()
    #import_csv('nonprofits_small.csv')

    #time_end = time.perf_counter()
    #program_duration = time_end - time_start

    npo_data = get_source()
    init_pipeline(npo_data, args)