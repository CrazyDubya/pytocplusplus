def calculate_statistics(data: list[float]) -> dict[str, float]:
    """
    Calculate various statistics from a list of numbers.
    
    Args:
        data: List of numbers to analyze
        
    Returns:
        Dictionary containing mean, variance, and standard deviation
    """
    if not data:
        return {
            'mean': 0.0,
            'variance': 0.0,
            'std_dev': 0.0
        }
    
    # Calculate mean
    total = 0.0
    for x in data:
        total += x
    mean = total / len(data)
    
    # Calculate variance
    squared_diff_sum = 0.0
    for x in data:
        diff = x - mean
        squared_diff_sum += diff * diff
    variance = squared_diff_sum / len(data)
    
    # Calculate standard deviation
    std_dev = variance ** 0.5
    
    return {
        'mean': mean,
        'variance': variance,
        'std_dev': std_dev
    }

def find_common_elements(list1: list[int], list2: list[int]) -> set[int]:
    """
    Find common elements between two lists.
    
    Args:
        list1: First list of integers
        list2: Second list of integers
        
    Returns:
        Set of common elements
    """
    try:
        # Convert lists to sets for efficient intersection
        set1 = set(list1)
        set2 = set(list2)
        
        # Find intersection
        common = set1.intersection(set2)
        
        return common
    except Exception as e:
        print(f"Error finding common elements: {e}")
        return set()

def process_data(data: dict[str, list[float]]) -> tuple[float, float]:
    """
    Process a dictionary of data lists.
    
    Args:
        data: Dictionary mapping keys to lists of numbers
        
    Returns:
        Tuple of (min_value, max_value)
    """
    min_val = float('inf')
    max_val = float('-inf')
    
    with open('data.log', 'w') as f:
        for key, values in data.items():
            try:
                # Calculate statistics for this list
                stats = calculate_statistics(values)
                
                # Update min/max
                min_val = min(min_val, stats['mean'])
                max_val = max(max_val, stats['mean'])
                
                # Log results
                f.write(f"Key: {key}\n")
                f.write(f"Mean: {stats['mean']}\n")
                f.write(f"Std Dev: {stats['std_dev']}\n")
            except Exception as e:
                print(f"Error processing {key}: {e}")
    
    return min_val, max_val

if __name__ == "__main__":
    # Test calculate_statistics
    test_data = [1.0, 2.0, 3.0, 4.0, 5.0]
    stats = calculate_statistics(test_data)
    print("Statistics:", stats)
    
    # Test find_common_elements
    list1 = [1, 2, 3, 4, 5]
    list2 = [4, 5, 6, 7, 8]
    common = find_common_elements(list1, list2)
    print("Common elements:", common)
    
    # Test process_data
    data = {
        'group1': [1.0, 2.0, 3.0],
        'group2': [4.0, 5.0, 6.0],
        'group3': [7.0, 8.0, 9.0]
    }
    min_val, max_val = process_data(data)
    print(f"Min: {min_val}, Max: {max_val}") 