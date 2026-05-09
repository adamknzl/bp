"""
@file   dataset_extract.py
@brief  Extract a stratified sample of nonprofit organizations from the ČSÚ source CSV.
@author Adam Kinzel (xkinzea00)

The sample guarantees a minimum number of parent-branch pairs so that the
branch-linking feature is demonstrable. Each guaranteed pair contributes one
parent record and one branch record to the sample. The remaining slots are
filled with a random draw from the rest of the population.
"""

import argparse
import pandas as pd

_NPO_LEGAL_FORM_CODES = (117, 118, 141, 161, 706, 721, 722, 736)
_BRANCH_LEGAL_FORM_CODE = 736


def _find_pairs(parents: pd.DataFrame, branches: pd.DataFrame) -> list[tuple]:
    """
    Return a list of (parent_index, branch_index) pairs.

    For each branch, progressively strips the last comma-separated token from
    its name until a match is found in the parent name set. O(branches × depth)
    where depth is typically 2-3, making this effectively O(branches).

    Example:
        Branch: "Český svaz včelařů, z.s., základní organizace Pláně"
        Try:    "Český svaz včelařů, z.s." → found in parent set → pair!
    """
    # Build a name → index map for fast parent lookup
    parent_name_to_idx = {name: idx for idx, name in parents['FIRMA'].items()}

    pairs = []
    seen_parents = set()

    for branch_idx, branch_name in branches['FIRMA'].items():
        parts = [p.strip() for p in branch_name.split(',')]

        # Try every prefix from longest to shortest
        for i in range(len(parts) - 1, 0, -1):
            candidate = ', '.join(parts[:i])
            if candidate in parent_name_to_idx:
                parent_idx = parent_name_to_idx[candidate]
                # Only one branch per parent to keep the sample balanced
                if parent_idx not in seen_parents:
                    pairs.append((parent_idx, branch_idx))
                    seen_parents.add(parent_idx)
                break

    return pairs


def sample_source(args) -> None:
    """Sample organizations from the full ČSÚ source CSV."""
    print("Reading res_data.csv...")
    chunks = []
    for chunk in pd.read_csv('data/res_data.csv', chunksize=10000, sep=',', low_memory=False):
        filtered = chunk[
            chunk['FORMA'].isin(_NPO_LEGAL_FORM_CODES) &
            ~chunk['FIRMA'].str.contains('v likvidaci', case=False, na=False)
        ]
        chunks.append(filtered)

    if not chunks:
        print("No data found.")
        exit(1)

    npos = pd.concat(chunks)

    branches = npos[npos['FORMA'] == _BRANCH_LEGAL_FORM_CODE]
    parents  = npos[npos['FORMA'] != _BRANCH_LEGAL_FORM_CODE]

    # ── Find parent-branch pairs ──────────────────────────────────────────────
    print("Finding parent-branch pairs...")
    pairs = _find_pairs(parents, branches)
    print(f"  Found {len(pairs)} matchable parent-branch pairs.")

    # Sample the requested number of pairs
    n_pairs = min(args.guaranteed_pairs, len(pairs))
    selected_pairs = pd.Series(range(len(pairs))).sample(n=n_pairs, random_state=args.seed).tolist()
    selected_pairs = [pairs[i] for i in selected_pairs]

    guaranteed_idxs = set()
    for parent_idx, branch_idx in selected_pairs:
        guaranteed_idxs.add(parent_idx)
        guaranteed_idxs.add(branch_idx)

    guaranteed_sample = npos.loc[list(guaranteed_idxs)]
    print(f"  Guaranteeing {n_pairs} parent-branch pairs ({len(guaranteed_idxs)} records).")

    # ── Fill remaining slots randomly ─────────────────────────────────────────
    remaining_pool  = npos[~npos.index.isin(guaranteed_idxs)]
    remaining_count = min(args.count - len(guaranteed_idxs), len(remaining_pool))
    random_sample   = remaining_pool.sample(n=remaining_count, random_state=args.seed)

    # Shuffle so guaranteed entries aren't clustered at the top
    sample = pd.concat([guaranteed_sample, random_sample]).sample(frac=1, random_state=args.seed)

    sample.to_csv(args.output, index=False, sep=',')
    print(f"Saved {len(sample)} organizations to '{args.output}'.")
    print(f"  - {len(guaranteed_idxs)} guaranteed (parents + their branches)")
    print(f"  - {remaining_count} randomly sampled")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--count',  type=int, default=1000,
                        help='Number of organizations to sample (default: 1000)')
    parser.add_argument('-o', '--output', type=str, default='data/res_data_sample.csv',
                        help='Output file path (default: data/res_data_sample.csv)')
    parser.add_argument('-s', '--seed',   type=int, default=42,
                        help='Random seed for reproducibility (default: 42)')
    parser.add_argument('--guaranteed-pairs', type=int, default=20,
                        help='Number of parent-branch pairs to guarantee (default: 20)')
    args = parser.parse_args()

    sample_source(args)