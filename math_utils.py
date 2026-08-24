# fibonacci(n) - Fibonacci number generator

def fibonacci(n):
    if n < 0:
        raise ValueError("Negative numbers are not allowed")
    
    if n == 0:
        return 0
    
    if n == 1:
        return 1
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    
    return b

# Test cases

def test_fibonacci():
    # Test base cases
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    
    # Test larger values
    assert fibonacci(10) == 55
    
    # Test negative numbers raise ValueError
    try:
        fibonacci(-1)
        assert False, "Expected ValueError"
    except ValueError:
        pass

# Run tests
if __name__ == "__main__":
    test_fibonacci()
    print("All tests passed!")