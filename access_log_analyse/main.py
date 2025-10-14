#!/usr/bin/env python3
import sys
import argparse
from log_parser import parse_log_file


def print_table(data, headers=None):
    """
    Print data in a tabular format.
    
    Args:
        data: List of dictionaries containing the data
        headers: List of column headers (defaults to dictionary keys)
    """
    if not data:
        print("No data to display")
        return
        
    if headers is None:
        headers = list(data[0].keys())
    
    # Calculate column widths
    col_widths = {header: len(header) for header in headers}
    for row in data:
        for header in headers:
            if header in row:
                col_widths[header] = max(col_widths[header], len(str(row[header])))
    
    # Print headers
    header_row = "  ".join(header.ljust(col_widths[header]) for header in headers)
    print(header_row)
    print("-" * len(header_row))
    
    # Print data rows
    for row in data:
        row_str = "  ".join(str(row.get(header, "")).ljust(col_widths[header]) for header in headers)
        print(row_str)


def main():
    parser = argparse.ArgumentParser(description='Parse log file and print table of extracted data')
    parser.add_argument('log_file', help='Path to the log file')
    args = parser.parse_args()
    
    # Parse the log file
    results = parse_log_file(args.log_file)
    
    if not results:
        print("No valid log entries found")
        return
    
    # Print the table with specific headers and order
    headers = ['subject_id', 'client_id', 'total_duration']
    print_table(results, headers)


if __name__ == "__main__":
    main()