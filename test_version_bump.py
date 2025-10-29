"""
Test file to demonstrate automatic version bumping.

This file will be committed with a conventional commit message
to trigger the automatic version bumping system, then reverted.
"""


def test_function():
    """
    Simple test function to demonstrate version bumping.
    
    Returns:
        str: A test message
    """
    return "Testing automatic version bumping system"


if __name__ == "__main__":
    print(test_function())
    print("Version bump test file created successfully!")
