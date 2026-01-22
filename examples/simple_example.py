def calculate_fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def main() -> None:
    # Test the Fibonacci calculation
    numbers = [5, 10, 15]
    results = []
    
    for num in numbers:
        result = calculate_fibonacci(num)
        results.append(result)
        print(f"Fibonacci({num}) = {result}")

if __name__ == "__main__":
    main() 