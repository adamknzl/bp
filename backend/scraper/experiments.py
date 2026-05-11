"""
@file    experiments.py
@brief   Logic and execution of experiments for ETL pipeline evaluation.
@author  Adam Kinzel (xkinzea00)
"""

import csv
import os
import random
import re
from collections import Counter
from urllib.parse import urlparse


# ─── Configuration ────────────────────────────────────────────────────────────

GROUND_TRUTH_FILE = 'data/ground_truth_urls.csv'
LLM_EVAL_FILE     = 'data/llm_eval.csv'


# ─── Shared URL normalization ─────────────────────────────────────────────────

def _normalize_url(url: str) -> str:
    """Reduce a URL to netloc + path for canonical comparison.

    Strips protocol, www prefix, and trailing slash.
    """
    if not url:
        return ""
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    parsed = urlparse(url.strip())
    netloc = parsed.netloc.replace('www.', '').lower()
    path   = parsed.path.rstrip('/').lower()
    return netloc + path


# ─── Experiment 1: URL accuracy ───────────────────────────────────────────────

def get_ground_truth_sample(
    output: str = GROUND_TRUTH_FILE,
    n: int = 100,
    seed: int = 42,
) -> None:
    """Sample organizations from the database for URL discovery evaluation.

    Samples both organizations with and without a discovered URL, writing
    the pipeline's best_url result alongside an empty expected_url column
    for manual verification.

    Sampling from the database (rather than re-running get_url() live) ensures
    the experiment reflects what the final system actually produced, and
    includes the full distribution — organizations with and without websites.

    Args:
        output: Path to write the ground truth CSV.
        n:      Number of organizations to sample.
        seed:   Random seed for reproducibility.
    """
    from database import Session, Organization
    from sqlalchemy import select

    random.seed(seed)

    session = Session()
    try:
        rows = session.execute(
            select(Organization.name, Organization.web_url)
        ).all()
    finally:
        session.close()

    sample = random.sample(rows, min(n, len(rows)))
    print(f"Sampled {len(sample)} organizations from the database.")

    with_url    = sum(1 for r in sample if r.web_url)
    without_url = sum(1 for r in sample if not r.web_url)
    print(f"  - {with_url} with a discovered URL")
    print(f"  - {without_url} without a URL")

    with open(output, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['name', 'best_url', 'expected_url'],
            delimiter=';',
        )
        writer.writeheader()
        for row in sample:
            writer.writerow({
                'name':         row.name,
                'best_url':     row.web_url or '',
                'expected_url': '',
            })

    print(f"\nWritten to '{output}'.")
    print("Fill in the 'expected_url' column manually, then re-run to evaluate.")
    print("Leave expected_url empty for organizations that have no website.")


def run_url_evaluation(ground_truth_file: str = GROUND_TRUTH_FILE) -> None:
    """Compare best_url against expected_url and report accuracy.

    Treats each row as one of three outcomes:
      - True positive:  org has a website, pipeline found the correct URL.
      - True negative:  org has no website, pipeline returned nothing.
      - Failure:        anything else (wrong URL found, or website missed).

    Rows where expected_url was not filled in are skipped.
    """
    def load_ground_truth(filename: str) -> list[dict]:
        rows = []
        with open(filename, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                rows.append({k: v.strip() for k, v in row.items() if k})
        return rows

    def normalize_name(name: str) -> str:
        return re.sub(r',\s*', ', ', name).strip()

    try:
        rows = load_ground_truth(ground_truth_file)
    except FileNotFoundError as e:
        print(f"ERROR: File not found - {e}")
        return

    total          = 0
    true_positives = 0
    true_negatives = 0

    print("\n--- Per-entry results ---\n")
    for i, row in enumerate(rows, start=1):
        name     = normalize_name(row.get('name', ''))
        expected = row.get('expected_url', '').strip()
        actual   = row.get('best_url', '').strip()

        # Skip rows not yet manually verified
        if not expected and not actual:
            print(f"[{i}] Skipped (not verified): {name}")
            continue

        total += 1

        # True negative: org has no website, pipeline correctly returned nothing
        if expected.lower() == 'none' and not actual:
            true_negatives += 1
            print(f"[{i}] True negative: {name}")

        # False positive: org has no website but pipeline returned something
        elif expected.lower() == 'none' and actual:
            print(f"[{i}] Fail (Wrong URL returned — org has no website): {name}")
            print(f"      Got: {actual}")

        # True positive: pipeline found the correct URL
        elif _normalize_url(expected) == _normalize_url(actual):
            true_positives += 1
            print(f"[{i}] True positive: {name}")

        # Failure: wrong URL returned, or website exists but wasn't found
        else:
            outcome = "Wrong URL returned" if actual else "Website missed"
            print(f"[{i}] Fail ({outcome}): {name}")
            print(f"      Expected: {expected}")
            print(f"      Got:      {actual or 'None'}")

    if total == 0:
        print("No verified rows to evaluate.")
        return

    correct  = true_positives + true_negatives
    accuracy = correct / total * 100

    print("\n" + "=" * 50)
    print(" URL DISCOVERY EVALUATION RESULTS")
    print("=" * 50)
    print(f" Total evaluated:   {total}")
    print(f" True positives:    {true_positives}  (correct URL found)")
    print(f" True negatives:    {true_negatives}  (no website, none returned)")
    print(f" Failures:          {total - correct}")
    print(f" Overall accuracy:  {accuracy:.2f}%")
    print("=" * 50)


# ─── Experiment 2: LLM quality ────────────────────────────────────────────────

def get_llm_eval_sample(
    output: str = LLM_EVAL_FILE,
    n: int = 100,
    seed: int = 42,
) -> None:
    """Sample organizations from the database for LLM output evaluation.

    Only samples organizations that have a generated description, since
    those are the only records where LLM output quality can be assessed.
    Writes a CSV with empty evaluation columns for manual assessment.

    Args:
        output: Path to write the evaluation CSV.
        n:      Number of organizations to sample.
        seed:   Random seed for reproducibility.
    """
    from database import Session, Organization
    from sqlalchemy import select

    random.seed(seed)

    session = Session()
    try:
        rows = session.execute(
            select(
                Organization.name,
                Organization.web_url,
                Organization.description,
            )
        ).all()
    finally:
        session.close()

    eligible = [r for r in rows if r.description]
    sample   = random.sample(eligible, min(n, len(eligible)))
    print(f"Sampled {len(sample)} records with descriptions from the database.")

    with open(output, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['name', 'web_url', 'description_eval', 'categories_eval'],
            delimiter=';',
        )
        writer.writeheader()
        for row in sample:
            writer.writerow({
                'name':             row.name,
                'web_url':          row.web_url or '',
                'description_eval': '',
                'categories_eval':  '',
            })

    print(f"Written to '{output}'.")
    print("Fill in 'description_eval' and 'categories_eval' manually, then re-run.")


def run_llm_evaluation(eval_file: str = LLM_EVAL_FILE) -> None:
    """Parse and summarize the manually filled LLM evaluation CSV.

    Computes accuracy rates for descriptions and categories,
    and breaks down failure modes for both.
    """
    def load_eval(filename: str) -> list[dict]:
        rows = []
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                rows.append({k: (v or '').strip().strip('"') for k, v in row.items() if k})
        return rows

    def classify(value: str) -> str:
        v = value.lower().strip()
        if v == 'valid':                 return 'valid'
        if v == 'n/a':                   return 'n/a'
        if 'categorized in others' in v: return 'others'
        if 'invalid description' in v:   return 'invalid_desc'
        if 'invalid category' in v:      return 'invalid_cat'
        return 'unknown'

    def compute_stats(statuses: list[str]) -> dict:
        counts = Counter(statuses)
        total  = len(statuses)
        return {k: {'count': v, 'pct': round(v / total * 100, 1)} for k, v in counts.items()}

    def print_report(label: str, statuses: list[str], rows: list[dict], col: str) -> None:
        stats   = compute_stats(statuses)
        total   = len(statuses)
        n_a     = stats.get('n/a',   {}).get('count', 0)
        valid   = stats.get('valid', {}).get('count', 0)
        invalid = total - n_a - valid
        eval_n  = total - n_a

        print(f"\n{'='*50}")
        print(f" {label}")
        print(f"{'='*50}")
        print(f" Total records:   {total}")
        print(f" N/A:             {n_a}  ({n_a/total*100:.1f}%)")
        print(f" Evaluable:       {eval_n}")
        print(f" Valid:           {valid}  ({valid/eval_n*100:.1f}% of evaluable)")
        print(f" Invalid:         {invalid}  ({invalid/eval_n*100:.1f}% of evaluable)")
        print(f"\n Failure breakdown:")

        for status, data in sorted(
            {k: v for k, v in stats.items() if k not in ('valid', 'n/a')}.items(),
            key=lambda x: -x[1]['count'],
        ):
            print(f"   {status:<25} {data['count']}  ({data['pct']}%)")

        print(f"\n Examples per failure type:")
        seen = set()
        for row in rows:
            status = classify(row.get(col, ''))
            if status not in ('valid', 'n/a') and status not in seen:
                seen.add(status)
                print(f"   [{row.get(col, '')}]  →  {row['name']}")

    rows          = load_eval(eval_file)
    desc_statuses = [classify(r.get('description_eval', '')) for r in rows]
    cat_statuses  = [classify(r.get('categories_eval',  '')) for r in rows]

    print_report('DESCRIPTION EVALUATION', desc_statuses, rows, 'description_eval')
    print_report('CATEGORY EVALUATION',    cat_statuses,  rows, 'categories_eval')

    both_valid = sum(
        1 for d, c in zip(desc_statuses, cat_statuses)
        if d == 'valid' and c == 'valid'
    )
    evaluable = sum(1 for d in desc_statuses if d != 'n/a')
    print(f"\n{'='*50}")
    print(f" JOINT ACCURACY (both valid)")
    print(f"{'='*50}")
    print(f" Both valid:   {both_valid}  ({both_valid/evaluable*100:.1f}% of evaluable)")


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == '__main__':

    # ── Experiment 1 ──────────────────────────────────────────────────────────
    if not os.path.exists(GROUND_TRUTH_FILE):
        print("Ground truth file not found. Generating URL discovery sample...")
        get_ground_truth_sample()
        print(f"\nFill in 'expected_url' in '{GROUND_TRUTH_FILE}', then re-run.")
    else:
        print(f"'{GROUND_TRUTH_FILE}' found. Running URL evaluation...")
        run_url_evaluation()

        # ── Experiment 2 ──────────────────────────────────────────────────────
        if not os.path.exists(LLM_EVAL_FILE):
            print(f"\nLLM eval file not found. Generating sample from database...")
            get_llm_eval_sample()
            print(f"\nFill in evaluation columns in '{LLM_EVAL_FILE}', then re-run.")
        else:
            print(f"\n'{LLM_EVAL_FILE}' found. Running LLM evaluation...")
            run_llm_evaluation()