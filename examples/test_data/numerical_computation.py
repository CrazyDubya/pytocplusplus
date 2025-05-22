import numpy as np
from typing import List

def matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """Multiply two matrices using nested loops."""
    rows_a = len(a)
    cols_a = len(a[0])
    cols_b = len(b[0])
    
    result = [[0.0 for _ in range(cols_b)] for _ in range(rows_a)]
    
    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += a[i][k] * b[k][j]
    
    return result

def compute_statistics(data: List[float]) -> dict:
    """Compute basic statistics on a list of numbers."""
    if not data:
        return {}
    
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std_dev = variance ** 0.5
    
    return {
        "mean": mean,
        "variance": variance,
        "std_dev": std_dev,
        "min": min(data),
        "max": max(data)
    }

def main():
    # Test matrix multiplication
    a = [[1.0, 2.0, 3.0],
         [4.0, 5.0, 6.0]]
    b = [[7.0, 8.0],
         [9.0, 10.0],
         [11.0, 12.0]]
    
    result = matrix_multiply(a, b)
    print("Matrix multiplication result:")
    for row in result:
        print(row)
    
    # Test statistics computation
    data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    stats = compute_statistics(data)
    print("\nStatistics:")
    for key, value in stats.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main() 