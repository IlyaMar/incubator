#!/usr/bin/env python3
"""
Script to parse CSV file with operation metrics and sum 'last' values by operation and bucket.
"""
import csv
import sys
import math
from collections import defaultdict
from typing import Dict, Any
from percentile import calculate_percentiles


def __convert_to_float(s):
    if not s:
        return 0
    try:
        value = float(s)
        if math.isnan(value):
            return 0
        return value
    except ValueError:
        return 0

def process_operations_file(file_path: str) -> Dict[str, Dict[float, float]]:
    """
    Process operations CSV file and return a dictionary with summed 'last' values
    grouped by operation and bucket.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Dictionary in the format {operation: {bucket: sum_of_last_values}}
    """
    # Initialize result dictionary
    result = defaultdict(lambda: defaultdict(float))
    
    try:
        with open(file_path, 'r') as f:
            # Create CSV reader
            reader = csv.DictReader(f)
            
            # Process each row
            for row in reader:
                operation = row.get('method', None)
                bucket = float(row['le'])
                last_value = __convert_to_float(row['integral'])
                
                # Add the last value to the appropriate bucket for this operation
                result[operation][bucket] += last_value
    
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Missing required column: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: Invalid data format: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")
        sys.exit(1)
    
    # Convert defaultdict to regular dict for cleaner output
    return {op: dict(buckets) for op, buckets in result.items()}


def process_operation_files(file_paths: list) -> Dict[str, Dict[float, float]]:
    """
    Process multiple operations CSV files and return a merged dictionary with summed 'last' values
    grouped by operation and bucket.
    
    Args:
        file_paths: List of paths to the CSV files
        
    Returns:
        Dictionary in the format {operation: {bucket: sum_of_last_values}}
    """
    # Initialize merged result dictionary with the same structure as the return type
    merged_result: Dict[str, Dict[float, float]] = {}
    
    # Process each file
    for file_path in file_paths:
        try:
            # Process the current file
            file_result = process_operations_file(file_path)
            
            # Merge the result with the overall result
            for operation, buckets in file_result.items():
                if operation not in merged_result:
                    merged_result[operation] = {}
                
                for bucket, value in buckets.items():
                    if bucket not in merged_result[operation]:
                        merged_result[operation][bucket] = 0.0
                    merged_result[operation][bucket] += value
        except Exception as e:
            print(f"Error processing file '{file_path}': {e}")
            # Continue processing other files instead of exiting
            continue
    
    return merged_result


def main():
    """Main function to run the script."""
    if len(sys.argv) < 2:
        # Default file if no arguments provided
        file_paths = ["input/iam-qm.csv"]
        print("Usage: python3 process_operations.py <csv_file_path1> [<csv_file_path2> ...]")
        print("Using default file: input/iam-qm.csv")
    else:
        # Get all files from command line arguments
        file_paths = sys.argv[1:]

    # Process all files and merge results
    result = process_operation_files(file_paths)
    percentiles = [50, 90, 99, 99.9]
    operations_low_counts = {}
    operations_stat = {}
    for operation, buckets in result.items():
        op_sum = sum(buckets.values())
        if op_sum < 100:
            operations_low_counts[operation] = op_sum
        operations_stat[operation] = {"p": calculate_percentiles(buckets, percentiles), "cnt": int(op_sum)}
        
    # Print the result
    print("Operation with stats: %d" % len(operations_stat))
    with open("operation_stat.csv", 'w') as f:
        f.write("operation,count,p50,p90,p99,p999\n")
        for operation, s in operations_stat.items():
            f.write(f"{operation},{s["cnt"]},{s["p"][50]},{s["p"][90]},{s["p"][99]},{s["p"][99.9]}\n")

    print("Operation low counts:")
    for operation, op_cnt in operations_low_counts.items():
        print(f"{operation}:  {op_cnt}")


if __name__ == "__main__":
    main()