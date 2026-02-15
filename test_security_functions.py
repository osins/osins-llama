"""Simple test script for security functions."""
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from llama.cli.start import validate_host, parse_api_keys


def test_validate_host():
    """Test the validate_host function."""
    print("Testing validate_host function...")
    
    # Test valid IPv4 address
    try:
        result = validate_host(None, None, '192.168.1.1')
        print(f"✓ Valid IPv4: {result}")
    except Exception as e:
        print(f"✗ Valid IPv4 failed: {e}")
    
    # Test valid IPv6 address
    try:
        result = validate_host(None, None, '2001:0db8:85a3:0000:0000:8a2e:0370:7334')
        print(f"✓ Valid IPv6: {result}")
    except Exception as e:
        print(f"✗ Valid IPv6 failed: {e}")
    
    # Test valid hostname
    try:
        result = validate_host(None, None, 'example.com')
        print(f"✓ Valid hostname: {result}")
    except Exception as e:
        print(f"✗ Valid hostname failed: {e}")
    
    # Test invalid format (starts with hyphen)
    try:
        result = validate_host(None, None, '-invalid-hostname')
        print(f"✗ Invalid format (starts with hyphen) passed: {result}")
    except Exception as e:
        print(f"✓ Invalid format (starts with hyphen) correctly rejected: {e}")
    
    # Test invalid format (contains consecutive dots)
    try:
        result = validate_host(None, None, 'invalid..hostname')
        print(f"✗ Invalid format (consecutive dots) passed: {result}")
    except Exception as e:
        print(f"✓ Invalid format (consecutive dots) correctly rejected: {e}")


def test_parse_api_keys():
    """Test the parse_api_keys function."""
    print("\nTesting parse_api_keys function...")
    
    # Test valid keys
    try:
        keys = parse_api_keys('key123456789012345,keyabcdefghijklmnop')
        print(f"✓ Valid keys: {keys}")
    except Exception as e:
        print(f"✗ Valid keys failed: {e}")
    
    # Test invalid key format
    try:
        keys = parse_api_keys('invalid_key,validkey123456789012345')
        print(f"✗ Invalid key format passed: {keys}")
    except Exception as e:
        print(f"✓ Invalid key format correctly rejected: {e}")
    
    # Test duplicate keys
    try:
        keys = parse_api_keys('key123456789012345,key123456789012345,keyabcdefghijklmnop')
        print(f"✓ Duplicate keys removed: {keys}")
    except Exception as e:
        print(f"✗ Duplicate keys failed: {e}")


if __name__ == "__main__":
    print("Running security functions tests...")
    print("=" * 50)
    
    test_validate_host()
    test_parse_api_keys()
    
    print("\n" + "=" * 50)
    print("Tests completed!")
