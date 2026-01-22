import sys
from pathlib import Path

# Add the build directory to the Python path
build_dir = Path("generated/build")
sys.path.append(str(build_dir))

try:
    from cpp_impl import calculate_fibonacci as cpp_calculate_fibonacci
    print("Successfully imported C++ implementation")
except ImportError as e:
    print(f"Failed to import C++ implementation: {e}")
    cpp_calculate_fibonacci = None

def python_fibonacci(n: int) -> int:
    """Python implementation of Fibonacci."""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def test_fibonacci() -> None:
    # Test with Python implementation
    print("\nTesting Python implementation:")
    for n in [5, 10, 15]:
        result = python_fibonacci(n)
        print(f"Fibonacci({n}) = {result}")
    
    if cpp_calculate_fibonacci is not None:
        print("\nTesting C++ implementation:")
        for n in [5, 10, 15]:
            result = cpp_calculate_fibonacci(n)
            print(f"Fibonacci({n}) = {result}")

if __name__ == "__main__":
    test_fibonacci() 