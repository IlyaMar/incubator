#!/usr/bin/env python3
"""
Script to sort numbers in text files.
Numbers are read from a file (one per line), sorted, and written to an output file.
"""

import argparse
import sys
from pathlib import Path


def read_numbers_from_file(file_path):
    """
    Read numbers from a file, one per line.
    
    Args:
        file_path (str): Path to the input file
        
    Returns:
        list: List of numbers read from the file
    """
    numbers = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line.lower() == 'inf':
                    numbers.append(float('inf'))
                elif line.lower() == '-inf':
                    numbers.append(float('-inf'))
                elif line:  # Skip empty lines
                    try:
                        numbers.append(float(line))
                    except ValueError:
                        print(f"Warning: Could not convert '{line}' to a number. Skipping.")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    return numbers


def write_numbers_to_file(numbers, file_path):
    """
    Write numbers to a file, one per line.
    
    Args:
        numbers (list): List of numbers to write
        file_path (str): Path to the output file
    """
    try:
        with open(file_path, 'w') as file:
            for number in numbers:
                if number == float('inf'):
                    file.write("inf\n")
                elif number == float('-inf'):
                    file.write("-inf\n")
                else:
                    file.write(f"{number}\n")
        print(f"Successfully wrote sorted numbers to '{file_path}'")
    except Exception as e:
        print(f"Error writing to file: {e}")
        sys.exit(1)


def main():
    """Main function to parse arguments and sort numbers."""
    parser = argparse.ArgumentParser(description='Sort numbers in a text file.')
    parser.add_argument('-i', '--input', default='buckets.txt',
                        help='Input file path (default: buckets.txt)')
    parser.add_argument('-o', '--output', default='sorted_buckets.txt',
                        help='Output file path (default: sorted_buckets.txt)')
    parser.add_argument('-d', '--descending', action='store_true',
                        help='Sort in descending order (default: ascending)')
    
    args = parser.parse_args()
    
    # Ensure input file exists
    input_path = Path(args.input)
    if not input_path.is_file():
        print(f"Error: Input file '{args.input}' not found.")
        sys.exit(1)
    
    # Read numbers from input file
    numbers = read_numbers_from_file(args.input)
    
    if not numbers:
        print("No numbers found in the input file.")
        sys.exit(1)
    
    # Sort numbers
    numbers.sort(reverse=args.descending)
    
    # Write sorted numbers to output file
    write_numbers_to_file(numbers, args.output)


if __name__ == "__main__":
    main()