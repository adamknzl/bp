import argparse

def parse():
    searchBranches = False

    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--Branches', help='Search for non-profit branches using Open Street Map', action='store_true')
    args = parser.parse_args()

    if args.Branches:
        searchBranches = True

    return searchBranches