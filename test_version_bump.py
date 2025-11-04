"""
Test File for Version Bump Fix Verification
============================================

This file is used to test the double-bump fix in the prepare-commit-msg hook.

Test Instructions:
1. This file should be committed via VS Code Source Control
2. Use commit message: "fix: test double-bump prevention"
3. Expected result: Version should bump from 0.8.10 to 0.8.11 (single bump)
4. Check .logs/prepare_commit_msg.log for lock file messages
5. This file will be deleted after testing

Created: November 4, 2025
Purpose: Verify lock file mechanism prevents double version bumps
"""

def test_version_bump():
    """
    Simple test function to verify version bump works correctly.
    
    This function does nothing but exist to make this a valid Python file.
    """
    return "Version bump test - single bump expected"


if __name__ == "__main__":
    result = test_version_bump()
    print(result)
    print("Current test: Double-bump prevention via lock file mechanism")
