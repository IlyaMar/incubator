def calculate_percentiles(bucket_counts, percentiles=[99, 99.9]):
    """
    Calculate specified percentiles from a dictionary of bucket counts.
    
    Args:
        bucket_counts (dict): Dictionary where keys are bucket values (float) and 
                             values are counts of measurements in each bucket.
                             Example: {0.1: 5, 0.05: 3, 0.01: 10, 0.005: 8}
        percentiles (list): List of percentiles to calculate (default: [99, 99.9])
    
    Returns:
        dict: Dictionary with percentile values as keys and their corresponding values
              Example: {99: 0.01, 99.9: 0.005}
    """
    # Sort buckets by value (ascending)
    sorted_buckets = sorted(bucket_counts.keys())
    
    # Calculate total count
    total_count = sum(bucket_counts.values())
    
    if total_count == 0:
        return {p: None for p in percentiles}
    
    # Calculate percentiles
    result = {}
    for p in percentiles:
        # Convert percentile to a fraction (e.g., 99 -> 0.99)
        percentile_fraction = p / 100
        
        # Calculate the count threshold for this percentile
        threshold = total_count * percentile_fraction
        
        # Iterate through sorted buckets and sum counts until threshold is reached
        cumulative_count = 0
        for bucket in sorted_buckets:
            cumulative_count += bucket_counts[bucket]
            if cumulative_count >= threshold:
                result[p] = bucket
                break
        else:
            # If no bucket is found, use the highest bucket
            result[p] = sorted_buckets[-1] if sorted_buckets else None
    
    return result


# Example usage
if __name__ == "__main__":
    # Example data
    example_buckets = {0.1: 5, 0.05: 999, 0.01: 10, 0.005: 8}
    
    # Calculate p99 and p999 (default)
    percentile_values = calculate_percentiles(example_buckets)
    
    print(f"p99: {percentile_values[99]}")
    print(f"p999: {percentile_values[99.9]}")