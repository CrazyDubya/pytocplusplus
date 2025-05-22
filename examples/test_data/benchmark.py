import time
from numerical_computation import matrix_multiply, compute_statistics

def benchmark_matrix_multiply():
    # Create test matrices (same as C++ example)
    a = [[1.0, 2.0, 3.0],
         [4.0, 5.0, 6.0]]
    b = [[7.0, 8.0],
         [9.0, 10.0],
         [11.0, 12.0]]
    
    # Warm up
    result = matrix_multiply(a, b)
    
    # Benchmark
    iterations = 10000
    start_time = time.perf_counter()
    
    for _ in range(iterations):
        result = matrix_multiply(a, b)
    
    end_time = time.perf_counter()
    duration = (end_time - start_time) * 1_000_000  # Convert to microseconds
    
    # Print results
    print("Matrix Multiplication Benchmark:")
    print(f"Python Time (average of {iterations} runs): {duration/iterations:.3f} microseconds\n")
    
    print("Result Matrix:")
    for row in result:
        print(" ".join(f"{x:8.1f}" for x in row))
    print()

def benchmark_statistics():
    # Create test data (same as C++ example)
    data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    
    # Warm up
    stats = compute_statistics(data)
    
    # Benchmark
    iterations = 10000
    start_time = time.perf_counter()
    
    for _ in range(iterations):
        stats = compute_statistics(data)
    
    end_time = time.perf_counter()
    duration = (end_time - start_time) * 1_000_000  # Convert to microseconds
    
    # Print results
    print("Statistics Computation Benchmark:")
    print(f"Python Time (average of {iterations} runs): {duration/iterations:.3f} microseconds\n")
    
    print("Statistics Results:")
    for key, value in stats.items():
        print(f"{key:8}: {value:8.3f}")

def main():
    print("Running benchmarks...\n")
    benchmark_matrix_multiply()
    benchmark_statistics()

if __name__ == "__main__":
    main() 