import csv
import re
from urllib.parse import urlparse


def normalize_name(name):
    """Normalize organization name format (fix missing spaces after commas)."""
    name = re.sub(r',\s*', ', ', name)
    return name.strip()


def load_csv_to_dict(filename, url_column_name):
    """Load a CSV file into a dictionary of format { 'Name': 'URL' }."""
    data = {}
    with open(filename, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            clean_name = normalize_name(row['name'])
            data[clean_name] = row[url_column_name]
    return data


def normalize_url(url):
    """Normalize a URL for fair comparison (strip www., protocol, and query params)."""
    if not url:
        return ""

    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    parsed = urlparse(url.strip())
    netloc = parsed.netloc.replace('www.', '').lower()
    path = parsed.path.rstrip('/').lower()

    return netloc + path


def run_evaluation():
    ground_truth_file = 'ground_truth_urls.csv'
    fetched_file = 'fetched_urls.csv'

    try:
        truth_data = load_csv_to_dict(ground_truth_file, 'expected_url')
        fetched_data = load_csv_to_dict(fetched_file, 'best_url')
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

        norm_expected = normalize_url(expected_url)
        norm_actual = normalize_url(actual_url)

        if norm_expected == norm_actual:
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