import time
import sys
import os
from pathlib import Path
from simple_example import calculate_fibonacci

def benchmark_fibonacci_python():
    """Benchmark the Fibonacci function in Python."""
    print("Running Python Fibonacci benchmark...")
    
    # Test parameters
    test_values = [5, 10, 15, 20, 25, 30, 35]
    iterations = 100000
    
    # Warmup
    calculate_fibonacci(10)
    
    # Benchmark
    results = {}
    for n in test_values:
        start_time = time.perf_counter()
        for _ in range(iterations):
            calculate_fibonacci(n)
        end_time = time.perf_counter()
        
        duration_ms = (end_time - start_time) * 1000
        per_call_us = (duration_ms * 1000) / iterations
        results[n] = per_call_us
    
    return results

def benchmark_fibonacci_cpp(output_dir):
    """Benchmark the Fibonacci function in C++."""
    print("Running C++ Fibonacci benchmark...")
    
    output_path = Path(output_dir)
    
    # Check if python_wrapper directory exists
    python_wrapper_path = output_path / "python_wrapper"
    if not python_wrapper_path.exists():
        print(f"Error: Python wrapper directory not found at {python_wrapper_path}")
        return None
    
    # Make sure the python module is in the Python path
    sys.path.insert(0, str(output_path))
    
    # Check if the module files exist
    cpp_module_files = list(python_wrapper_path.glob("cpp_impl*.so"))
    if not cpp_module_files:
        print(f"Error: No C++ module found in {python_wrapper_path}")
        
        # Check build directory as fallback
        build_path = output_path / "build"
        if build_path.exists():
            build_module_files = list(build_path.glob("cpp_impl*.so"))
            if build_module_files:
                print(f"Found module in build directory: {build_module_files}")
                print("Module needs to be copied to python_wrapper directory")
    else:
        print(f"Found C++ module files: {cpp_module_files}")
    
    # Try to import the C++ module
    try:
        from python_wrapper import calculate_fibonacci as calculate_fibonacci_cpp
        print("Successfully imported C++ module")
    except ImportError as e:
        print(f"Error importing C++ module: {e}")
        print(f"Paths searched: {sys.path}")
        print(f"Files in {output_path}: {os.listdir(output_path)}")
        if (output_path / "python_wrapper").exists():
            print(f"Files in python_wrapper: {os.listdir(output_path / 'python_wrapper')}")
            
            # Try direct import as a last resort
            try:
                import importlib.util
                for module_file in cpp_module_files:
                    print(f"Attempting direct import of {module_file}")
                    spec = importlib.util.spec_from_file_location("cpp_impl", module_file)
                    if spec:
                        cpp_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(cpp_module)
                        print("Direct import successful")
                        
                        # Create a wrapper function with the same signature
                        def calculate_fibonacci_cpp(n, use_cpp=True):
                            return cpp_module.calculate_fibonacci(n)
                        
                        break
                else:
                    print("Direct import failed")
                    return None
            except Exception as import_err:
                print(f"Direct import failed: {import_err}")
                return None
        else:
            return None
    
    # Test parameters
    test_values = [5, 10, 15, 20, 25, 30, 35]
    iterations = 100000
    
    # Warmup
    calculate_fibonacci_cpp(10, True)  # Use C++ implementation
    
    # Benchmark
    results = {}
    for n in test_values:
        start_time = time.perf_counter()
        for _ in range(iterations):
            calculate_fibonacci_cpp(n, True)  # Use C++ implementation
        end_time = time.perf_counter()
        
        duration_ms = (end_time - start_time) * 1000
        per_call_us = (duration_ms * 1000) / iterations
        results[n] = per_call_us
    
    return results

def print_comparison(py_results, cpp_results):
    """Print a comparison of Python and C++ benchmark results."""
    if not cpp_results:
        print("\nC++ benchmark failed or not available.")
        print("\nPython benchmark results:")
        print("-" * 50)
        print(f"{'n':<10} {'Time (μs)':<15}")
        print("-" * 50)
        for n, time_us in sorted(py_results.items()):
            print(f"{n:<10} {time_us:.3f}")
        return
    
    # Print comparison table
    print("\nBenchmark Results (time per call in microseconds):")
    print("-" * 70)
    print(f"{'n':<8} {'Python (μs)':<15} {'C++ (μs)':<15} {'Ratio':<10} {'Speedup':<10}")
    print("-" * 70)
    
    for n in sorted(py_results.keys()):
        py_time = py_results[n]
        cpp_time = cpp_results.get(n, 0)
        
        if cpp_time > 0:
            ratio = py_time / cpp_time
            speedup = f"{ratio:.2f}x"
        else:
            ratio = "N/A"
            speedup = "N/A"
        
        print(f"{n:<8} {py_time:.3f}        {cpp_time:.3f}        {ratio:<10} {speedup:<10}")

def main():
    """Run benchmarks and display results."""
    # Get the output directory from command line if provided
    output_dir = "./generated"
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    
    # Run Python benchmark
    py_results = benchmark_fibonacci_python()
    
    # Try to run C++ benchmark if output directory exists
    cpp_results = None
    if os.path.exists(output_dir):
        cpp_results = benchmark_fibonacci_cpp(output_dir)
    else:
        print(f"Output directory not found: {output_dir}")
    
    # Print comparison
    print_comparison(py_results, cpp_results)

if __name__ == "__main__":
    main()