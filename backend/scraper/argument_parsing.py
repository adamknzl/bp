"""
@file    argument_parsing.py
@brief   Command-line argument parsing for the scraping pipeline.
@author  Adam Kinzel (xkinzea00)
"""

import argparse

def parse():
    """
    Parse command-line flags controlling pipeline behavior.

    Returns:
        argparse.Namespace: with ``Branches`` (bool) and ``limit`` (int | None).
    """
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--Branches', help='Search for non-profit branches using Open Street Map', action='store_true')
    parser.add_argument('-l', '--limit', help='Limit the number of non-profits to process', type=int, default=None)
    
    return parser.parse_args()