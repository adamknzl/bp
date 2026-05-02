"""
@file    eval_urls.py
@brief   Evaluation of URL discovery accuracy against a ground-truth dataset.
@author  Adam Kinzel (xkinzea00)
"""

import csv
import re
from urllib.parse import urlparse


def _normalize_name(name: str) -> str:
    """Standardize an organization name (consistent spacing around commas)."""
    return re.sub(r',\s*', ', ', name).strip()


def _normalize_url(url: str) -> str:
    """
    Reduce a URL to a canonical form for fair string comparison.

    Strips protocol, www. prefix, and trailing slash; lowercases everything.
    """
    if not url:
        return ""
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    parsed = urlparse(url.strip())
    netloc = parsed.netloc.replace('www.', '').lower()
    path = parsed.path.rstrip('/').lower()
    return netloc + path


def _load_csv_to_dict(filename: str, url_column: str) -> dict[str, str]:
    """Load a CSV mapping from organization name to URL."""
    data: dict[str, str] = {}
    with open(filename, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            data[_normalize_name(row['name'])] = row[url_column]
    return data


# ─── Evaluation entry point ───────────────────────────────────────────────────

def run_evaluation(ground_truth_file: str = 'ground_truth_urls.csv', fetched_file: str = 'fetched_urls.csv') -> None:
    """
    Compare fetched URLs against the ground-truth file and report accuracy.

    Prints per-entry success / failure indicators and a summary block at the end.
    """
    try:
        truth_data = _load_csv_to_dict(ground_truth_file, 'expected_url')
        fetched_data = _load_csv_to_dict(fetched_file, 'best_url')
    except FileNotFoundError as e:
        print(f"ERROR: File not found - {e}")
        return

    total = 0
    correct = 0

    print("\n--- Per-entry results ---\n")
    for i, (name, expected_url) in enumerate(truth_data.items(), start=1):
        if name not in fetched_data:
            print(f"URL {i}: Skipped — '{name}' not found in {fetched_file}.")
            continue

        total += 1
        actual_url = fetched_data[name]

        if _normalize_url(expected_url) == _normalize_url(actual_url):
            correct += 1
            print(f"URL {i}: Success ({name})")
        else:
            print(f"URL {i}: Fail ({name})")
            print(f"  Expected: {expected_url or 'None'}")
            print(f"  Got:      {actual_url or 'None'}")

    if total == 0:
        print("No data to compare.")
        return

    accuracy = (correct / total) * 100
    print("\n" + "=" * 40)
    print(" URL SEARCH EVALUATION RESULTS")
    print("=" * 40)
    print(f" Total tested:  {total}")
    print(f" Correct:       {correct}")
    print(f" Accuracy:      {accuracy:.2f}%")
    print("=" * 40)


if __name__ == "__main__":
    run_evaluation()