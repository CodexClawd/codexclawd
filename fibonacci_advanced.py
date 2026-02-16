"""
Advanced Fibonacci implementations with different approaches
"""

import functools
import time

# 1. Recursive approach (inefficient for large n)
def fibonacci_recursive(n):
    """
    Calculate nth Fibonacci number using recursion
    Warning: O(2^n) time complexity - slow for n > 30
    """
    if n < 0:
        raise ValueError("Fibonacci is not defined for negative numbers")
    if n <= 1:
        return n
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)

# 2. Memoized recursion (efficient)
@functools.lru_cache(maxsize=None)
def fibonacci_memoized(n):
    """
    Calculate nth Fibonacci number using memoization
    O(n) time complexity due to caching
    """
    if n < 0:
        raise ValueError("Fibonacci is not defined for negative numbers")
    if n <= 1:
        return n
    return fibonacci_memoized(n - 1) + fibonacci_memoized(n - 2)

# 3. Iterative approach (most efficient)
def fibonacci_iterative(n):
    """
    Calculate nth Fibonacci number using iteration
    O(n) time complexity, O(1) space complexity
    """
    if n < 0:
        raise ValueError("Fibonacci is not defined for negative numbers")
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

# 4. Using matrix exponentiation (O(log n))
def fibonacci_matrix(n):
    """
    Calculate nth Fibonacci number using matrix exponentiation
    O(log n) time complexity - fastest for very large n
    """
    def matrix_mult(A, B):
        """Multiply two 2x2 matrices"""
        return [
            [A[0][0] * B[0][0] + A[0][1] * B[1][0],
             A[0][0] * B[0][1] + A[0][1] * B[1][1]],
            [A[1][0] * B[0][0] + A[1][1] * B[1][0],
             A[1][0] * B[0][1] + A[1][1] * B[1][1]]
        ]
    
    def matrix_pow(matrix, power):
        """Raise matrix to power using binary exponentiation"""
        if power == 0:
            return [[1, 0], [0, 1]]  # Identity matrix
        if power == 1:
            return matrix
        
        if power % 2 == 0:
            half = matrix_pow(matrix, power // 2)
            return matrix_mult(half, half)
        else:
            return matrix_mult(matrix, matrix_pow(matrix, power - 1))
    
    if n < 0:
        raise ValueError("Fibonacci is not defined for negative numbers")
    if n <= 1:
        return n
    
    fib_matrix = [[1, 1], [1, 0]]
    result = matrix_pow(fib_matrix, n - 1)
    return result[0][0]

# 5. Generator for sequence
def fibonacci_generator(n):
    """
    Generate Fibonacci sequence up to n terms
    """
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

def benchmark_methods(n=20):
    """Benchmark different methods"""
    methods = [
        ("Iterative", fibonacci_iterative),
        ("Memoized", fibonacci_memoized),
        ("Matrix", fibonacci_matrix),
    ]
    
    print(f"Benchmarking Fibonacci({n}):")
    for name, func in methods:
        start = time.time()
        result = func(n)
        elapsed = time.time() - start
        print(f"{name:12}: {result:15} in {elapsed*1000:.3f} ms")

# Example usage and tests
if __name__ == "__main__":
    print("=== Fibonacci Sequence Generator ===")
    
    n = 15
    print(f"\nFirst {n} Fibonacci numbers:")
    for i, val in enumerate(fibonacci_generator(n)):
        print(f"  {i:2d}: {val}")
    
    print(f"\nFibonacci(20) using different methods:")
    print(f"  Recursive:      {fibonacci_recursive(20)}")
    print(f"  Iterative:      {fibonacci_iterative(20)}")
    print(f"  Memoized:       {fibonacci_memoized(20)}")
    print(f"  Matrix method:  {fibonacci_matrix(20)}")
    
    # Benchmark for larger n
    print(f"\nBenchmarking for n=30:")
    benchmark_methods(30)
    
    # Verify consistency
    print(f"\nVerification for n=25:")
    methods = [fibonacci_iterative, fibonacci_memoized, fibonacci_matrix]
    results = [method(25) for method in methods]
    print(f"  All methods equal: {len(set(results)) == 1}")
    print(f"  Value: {results[0]}")