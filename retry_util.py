"""
Retry utility with exponential backoff for handling transient failures.
"""

import time
import random
from functools import wraps
from typing import Callable, TypeVar, ParamSpec, Tuple, Union

P = ParamSpec('P')
T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[type[Exception], ...] = (ConnectionError, TimeoutError),
    jitter: bool = False
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator that retries a function with exponential backoff.
    
    Retries the decorated function up to max_retries times when specified
    exceptions are raised. Delay between retries follows exponential backoff:
    base_delay * (backoff_factor ** attempt).
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        backoff_factor: Multiplier for exponential backoff (default: 2.0)
        exceptions: Tuple of exception types to catch and retry (default: ConnectionError, TimeoutError)
        jitter: Add random jitter to delays to prevent thundering herd (default: False)
    
    Returns:
        Decorated function that implements retry logic
    
    Example:
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        def call_api():
            # May raise ConnectionError or TimeoutError
            pass
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: Union[Exception, None] = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (backoff_factor ** attempt)
                        if jitter:
                            delay *= (0.5 + random.random())
                        print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
                        time.sleep(delay)
                    else:
                        print(f"All {max_retries + 1} attempts failed. Giving up.")
            
            if last_exception:
                raise last_exception
            
            raise RuntimeError("Unexpected error: no exception captured but all retries exhausted")
        
        return wrapper
    return decorator


# Test function simulating a flaky API
def test_retry_with_backoff():
    """Test the retry_with_backoff decorator with a simulated flaky API."""
    
    call_count = 0
    fail_count = 2  # Fail first 2 calls, succeed on 3rd
    
    @retry_with_backoff(max_retries=3, base_delay=1.0, exceptions=(ConnectionError,))
    def flaky_api_call() -> str:
        nonlocal call_count
        call_count += 1
        
        if call_count <= fail_count:
            raise ConnectionError(f"Network error on attempt {call_count}")
        
        return f"Success after {call_count} attempts!"
    
    print("=" * 50)
    print("Testing retry_with_backoff decorator")
    print("=" * 50)
    print(f"Setup: Will fail {fail_count} times, then succeed\n")
    
    try:
        result = flaky_api_call()
        print(f"\nResult: {result}")
        print(f"Total calls made: {call_count}")
        assert call_count == 3, f"Expected 3 calls, got {call_count}"
        print("\nTest PASSED!")
    except Exception as e:
        print(f"\nTest FAILED with exception: {e}")
        raise


def test_retry_exhaustion():
    """Test that retry gives up after max_retries."""
    
    call_count = 0
    
    @retry_with_backoff(max_retries=2, base_delay=0.5, exceptions=(TimeoutError,))
    def always_fails() -> str:
        nonlocal call_count
        call_count += 1
        raise TimeoutError(f"Timeout on attempt {call_count}")
    
    print("\n" + "=" * 50)
    print("Testing retry exhaustion (should fail after 3 attempts)")
    print("=" * 50)
    
    try:
        always_fails()
        print("Test FAILED: Should have raised TimeoutError")
    except TimeoutError as e:
        print(f"Caught expected exception: {e}")
        print(f"Total calls made: {call_count}")
        assert call_count == 3, f"Expected 3 calls, got {call_count}"
        print("\nTest PASSED!")


if __name__ == "__main__":
    test_retry_with_backoff()
    test_retry_exhaustion()
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)
