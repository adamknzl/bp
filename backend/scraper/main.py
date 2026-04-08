import csv
from datetime import datetime
import time
import requests
from collections import defaultdict
from contextlib import contextmanager
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
import concurrent.futures

from database import Session, DataSource, Organization, Category, OrganizationCategory, SizeCategory, engine, Base
from search_api import get_url
from osm_api import fetch_branches
from utils import format_size_category, log_url, get_tel_numbers, get_emails, get_web_content, fetch_contact_page, get_html
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
    #print(f"Entering process_insert_org with {row.get('name')}")

    ico_val = row.get('ico')
    if not ico_val:
        return None

    size_raw = row.get('size_category')
    size_category_id = None

    if size_raw:
        size_cat = format_size_category(size_raw)

        select_stmt = select(SizeCategory.cat_id).where(
            SizeCategory.min_emp == size_cat["min_emp"],
            SizeCategory.max_emp == size_cat["max_emp"]
        )
        size_category_id = session.execute(select_stmt).scalar()

    with measure_time('URL search'):
        branch_url = get_url(row.get('name'))

    if not branch_url and parent_id is not None:
        parent_url = session.execute(
            select(Organization.web_url).where(Organization.organization_id == parent_id)
        ).scalar()

        branch_url = parent_url
        print(f"Branch does not have its own web, inheriting URL from parent: {parent_url}")

    select_stmt = select(Organization.description).where(Organization.ico == ico_val)
    if(session.execute(select_stmt).scalar() == None):
        print(f"Organization {row.get('name')} does not have a description, generating one...")
        with measure_time('LLM generating'):
            gen_res = llm_gen.generate(row.get('name'), row.get('legal_form'), branch_url)

            description = gen_res.get('description')
            categories = gen_res.get('categories', [])
    else:
        print(f"Organization {row.get('name')} already has a description, skipping generating...")
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

    org_data = {
        "source_id": source_id,
        "parent_id": parent_id,
        "name": row.get('name'),
        "ico": ico_val,
        "legal_form": row.get('legal_form'),
        "hq_address": row.get('address'),
        "emails": get_emails(contact_page_html),
        "tel_numbers": get_tel_numbers(contact_page_html),
        "web_url": branch_url,
        "created_at": datetime.now(),
        "size_category_id": size_category_id,
        "description": description,
        "lat": row.get('X').replace(",", "."),
        "lon": row.get('Y').replace(",", ".")
    }

    log_url(row.get('name'), org_data["web_url"])

    with measure_time('Database insert:'):
        insert_stmt = insert(Organization).values(**org_data)

        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=['ico'],
            set_={
                'parent_id': insert_stmt.excluded.parent_id,
                'name': insert_stmt.excluded.name,
                'legal_form': insert_stmt.excluded.legal_form,
                'hq_address': insert_stmt.excluded.hq_address,
                'emails': insert_stmt.excluded.emails,
                'tel_numbers': insert_stmt.excluded.tel_numbers,
                'size_category_id': insert_stmt.excluded.size_category_id,
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

def import_csv_threaded(csv_filename, max_workers=5):
    main_session = Session()
    try:
        source = DataSource(name="Import CSV", url=csv_filename, last_scraped = datetime.now())
        main_session.add(source)
        main_session.flush()
        source_id = source.source_id
        main_session.commit()
    finally:
        main_session.close()

    with open(csv_filename, mode="r", encoding="utf-8") as file:
        csv_reader = list(csv.DictReader(file, delimiter=";"))

    root_orgs = [row for row in csv_reader if row.get('legal_form') != 'Pobočný spolek']

    print(f"Launching multithreading with {max_workers} threads for {len(root_orgs)} organizations...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for row in root_orgs:
            future = executor.submit(process_row_worker, row, source_id)
            futures.append(future)

        for count, future in enumerate(concurrent.futures.as_completed(futures), 1):
            print(f"[{count}/{len(root_orgs)}] Processing complete.")

    print("All threads completed tasks.")

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
    time_start = time.perf_counter()

    Base.metadata.create_all(engine)
    upsert_categories()
    import_csv('nonprofits_small.csv')

    time_end = time.perf_counter()
    program_duration = time_end - time_start

    #print("\n" + "=" * 50)
    #print(" Benchmark results")
    #print("=" * 50)
    #for category, duration in sorted(benchmark_stats.items()):
    #    percent = (duration / program_duration) * 100
    #    print(f" {category:<35} : {duration:>7.2f} s  ({percent:>5.1f} %)")
    #print("-" * 50)
    #print(f" {'Complete program duration':<35} : {program_duration:>7.2f} s")
    #print("=" * 50)