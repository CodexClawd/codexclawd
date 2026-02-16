"""
Simple Python Fibonacci sequence calculator
"""

def fibonacci(n):
    """
    Calculate the nth Fibonacci number using iterative approach
    
    Args:
        n (int): The position in the Fibonacci sequence (0-indexed)
    
    Returns:
        int: The nth Fibonacci number
    """
    if n < 0:
        raise ValueError("Fibonacci is not defined for negative numbers")
    elif n == 0:
        return 0
    elif n == 1:
        return 1
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def fibonacci_sequence(length):
    """
    Generate a Fibonacci sequence of given length
    
    Args:
        length (int): Number of Fibonacci numbers to generate
    
    Returns:
        list: List containing the Fibonacci sequence
    """
    if length <= 0:
        return []
    
    sequence = []
    a, b = 0, 1
    
    for _ in range(length):
        sequence.append(a)
        a, b = b, a + b
    
    return sequence


# Example usage
if __name__ == "__main__":
    # Calculate individual Fibonacci numbers
    print("Fibonacci numbers:")
    for i in range(10):
        print(f"fib({i}) = {fibonacci(i)}")
    
    # Generate a sequence
    print("\nFirst 10 Fibonacci numbers:")
    sequence = fibonacci_sequence(10)
    print(sequence)
    
    # Test edge cases
    print("\nEdge cases:")
    print(f"fib(0) = {fibonacci(0)}")
    print(f"fib(1) = {fibonacci(1)}")
    print(f"fib(10) = {fibonacci(10)}")
    print(f"fib(20) = {fibonacci(20)}")