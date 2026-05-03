"""
@file   dataset_extract.py
@brief  Extract a random sample of nonprofit organizations from the ČSÚ source CSV,
        or sample fetched URLs for ground truth evaluation.
@author Adam Kinzel (xkinzea00)
"""

import argparse
import pandas as pd

_NPO_LEGAL_FORM_CODES = (117, 118, 141, 161, 706, 721, 722, 736)


def sample_source(args) -> None:
    """Sample organizations from the full ČSÚ source CSV."""
    print("Reading res_data.csv...")
    chunks = []
    for chunk in pd.read_csv('data/res_data.csv', chunksize=10000, sep=',', low_memory=False):
        if(not 'v likvidaci' in chunk[chunk['FIRMA']]):
            chunks.append(chunk[chunk['FORMA'].isin(_NPO_LEGAL_FORM_CODES)])

    if not chunks:
        print("No data found.")
        exit(1)

    npos  = pd.concat(chunks)
    count = min(args.count, len(npos))
    sample = npos.sample(n=count, random_state=args.seed)

    sample.to_csv(args.output, index=False, sep=',')
    print(f"Saved {count} organizations to '{args.output}'.")


def sample_ground_truth(args) -> None:
    """Sample from fetched_urls.csv to create a ground truth evaluation set."""
    df = pd.read_csv('data/fetched_urls.csv', delimiter=';')

    # Stratify: mostly found URLs, some empty (pipeline returned nothing)
    found     = df[df['best_url'] != ''].sample(
        min(args.count - 10, len(df[df['best_url'] != ''])),
        random_state=args.seed
    )
    not_found = df[df['best_url'] == ''].sample(
        min(10, len(df[df['best_url'] == ''])),
        random_state=args.seed
    )

    sample = pd.concat([found, not_found])

    # Add empty expected_url column for manual filling
    sample = sample.copy()
    sample['expected_url'] = ''
    sample[['name', 'expected_url']].to_csv(args.output, index=False, sep=';')

    print(f"Saved {len(sample)} entries to '{args.output}'.")
    print("Open the file and fill in the 'expected_url' column manually.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['source', 'ground-truth'],
                        help="'source' to sample from res_data.csv, "
                             "'ground-truth' to sample from fetched_urls.csv")
    parser.add_argument('-n', '--count',  type=int, default=500,
                        help='Number of records to sample (default: 500)')
    parser.add_argument('-o', '--output', type=str, default=None,
                        help='Output file path')
    parser.add_argument('-s', '--seed',   type=int, default=42,
                        help='Random seed for reproducibility (default: 42)')
    args = parser.parse_args()

    # Set sensible output defaults per mode
    if args.output is None:
        args.output = {
            'source':       'data/res_data_sample.csv',
            'ground-truth': 'data/ground_truth_urls.csv',
        }[args.mode]

    if args.mode == 'source':
        sample_source(args)
    else:
        sample_ground_truth(args)