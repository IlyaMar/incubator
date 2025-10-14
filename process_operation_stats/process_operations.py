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
                operation = row['operation']
                bucket = float(row['le'])
                last_value = __convert_to_float(row['last'])
                
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


def main():
    """Main function to run the script."""
    if len(sys.argv) < 2:
        # print("Usage: python process_operations.py <csv_file_path>")
        # sys.exit(1)
        # # 26.08 - 15.09.2025 iam-cp-vla1
        file_path = "input/iam-qm.csv"
    else:
        file_path = sys.argv[1]


    result = process_operations_file(file_path)
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