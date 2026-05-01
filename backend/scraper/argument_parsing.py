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
        argparse.Namespace: with limit (int | None).
    """
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--limit', help='Limit the number of non-profits to process', type=int, default=None)
    
    return parser.parse_args()