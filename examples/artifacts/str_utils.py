# String utility module

def is_palindrome(s: str) -> bool:
    """
    Check if a string is a palindrome.
    
    Args:
        s: The input string to check
        
    Returns:
        True if the string is a palindrome, False otherwise
    """
    return s == s[::-1]


def test_palindrome():
    """Test cases for palindrome checking function."""
    # Test with 'racecar' - should be True
    assert is_palindrome('racecar') == True
    
    # Test with 'hello' - should be False
    assert is_palindrome('hello') == False
    
    # Test with empty string - should be True (empty string is a palindrome)
    assert is_palindrome('') == True


if __name__ == '__main__':
    test_palindrome()
    print("All tests passed!")