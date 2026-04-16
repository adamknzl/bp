import argparse

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--Branches', help='Search for non-profit branches using Open Street Map', action='store_true')
    parser.add_argument('-l', '--limit', help='Limit the number of non-profits to process', type=int, default=None)
    
    return parser.parse_args()