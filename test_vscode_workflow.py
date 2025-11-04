"""
Test file for VS Code Source Control workflow verification.

This file is used to test the pre-commit hook when committing through VS Code's
Source Control panel.

Instructions for Testing
------------------------
1. Open VS Code Source Control panel (Cmd+Shift+G or click Source Control icon)
2. You should see this file as an untracked change
3. Stage this file by clicking the '+' icon next to it
4. Enter a commit message using conventional commit format:
   - For patch bump (0.8.11 → 0.8.12): "fix: Test VS Code workflow"
   - For minor bump (0.8.11 → 0.9.0): "feat: Test VS Code workflow"
   - For major bump (0.8.11 → 1.0.0): "feat!: Test VS Code workflow"
5. Click the checkmark to commit
6. Observe the pre-commit hook output in the terminal
7. Verify that __version__.py is automatically included in the commit

Expected Results
----------------
- The pre-commit hook should run automatically
- Version should be bumped based on your commit message
- Both this test file AND __version__.py should be in the same commit
- No uncommitted changes should remain
- Working tree should be clean

Current State
-------------
- Current version: 0.8.11
- Ready for testing through VS Code Source Control
"""


def vscode_workflow_test():
    """
    Simple test function to demonstrate VS Code integration.
    
    This function exists to make this a valid Python file.
    """
    print("Testing VS Code Source Control workflow with pre-commit hook")
    print("Current version should be: 0.8.11")
    print("After commit, check if version was bumped correctly")


if __name__ == "__main__":
    vscode_workflow_test()
