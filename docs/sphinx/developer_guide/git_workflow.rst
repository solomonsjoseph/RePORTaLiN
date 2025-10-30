Git Workflow and Version Management
=====================================

**For Developers:** This guide explains the automated version management system
and git workflow used in the RePORTaLiN project.

Overview
--------

RePORTaLiN uses an **automated version bumping system** that works seamlessly with:

- ✅ **VS Code Source Control** panel (recommended for most developers)
- ✅ **Terminal git commands** (for advanced users)
- ✅ **Any git client** (GitKraken, SourceTree, Tower, etc.)
- ✅ **CI/CD pipelines** (automated deployments)

The system follows `Semantic Versioning <https://semver.org/>`_ and
`Conventional Commits <https://www.conventionalcommits.org/>`_ standards.

How It Works
------------

Version Bumping Analogy
~~~~~~~~~~~~~~~~~~~~~~~

Think of the version bumping system like an **automatic receipt printer** at a restaurant:

- **You (Developer):** Place an order (make a commit)
- **Commit Message:** The order details ("fix: burger" vs "feat: new menu item")
- **Git Hooks:** The kitchen staff that automatically categorize and process orders
- **Version Number:** The receipt number that increments based on order type

Just like the receipt printer automatically assigns the next number based on what you ordered,
the git hooks automatically bump the version based on your commit message.

Conventional Commits Format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Commit messages follow this format:
::

    <type>[optional scope]: <description>
    
    [optional body]
    
    [optional footer(s)]

**Type** determines the version bump:

.. list-table::
   :header-rows: 1
   :widths: 20 30 25 25

   * - Commit Type
     - Version Change
     - Example Before
     - Example After
   * - ``fix:``
     - Patch bump
     - 0.8.6
     - 0.8.7
   * - ``feat:``
     - Minor bump
     - 0.8.6
     - 0.9.0
   * - ``feat!:`` or ``BREAKING CHANGE:``
     - Major bump
     - 0.8.6
     - 1.0.0
   * - Other (docs, chore, etc.)
     - Patch bump
     - 0.8.6
     - 0.8.7

Case Sensitivity
~~~~~~~~~~~~~~~~

The system is **case-insensitive**. All these work the same:

- ``feat:`` → Minor bump
- ``Feat:`` → Minor bump
- ``FEAT:`` → Minor bump
- ``fix:`` → Patch bump
- ``Fix:`` → Patch bump
- ``FIX:`` → Patch bump

Using VS Code (Recommended)
---------------------------

This is the simplest way to commit with automatic version bumping.

Step-by-Step Guide
~~~~~~~~~~~~~~~~~~

1. **Make your changes** in VS Code as normal

2. **Stage your files** using the Source Control panel (``Cmd+Shift+G`` on macOS)

3. **Write your commit message** in the text box at the top:
   ::

       feat: add new data extraction feature

4. **Click the "Commit" button** (or press ``Cmd+Enter``)

5. **✨ Magic happens automatically:**
   
   - Git hook detects "feat:" in your message
   - Version bumps from 0.8.6 → 0.9.0
   - ``__version__.py`` is updated and staged
   - Commit includes both your changes AND the version bump
   - Logs are written to ``.logs/prepare_commit_msg.log``

6. **Push your changes** when ready

Example VS Code Workflow
~~~~~~~~~~~~~~~~~~~~~~~~

**Scenario: Bug Fix**
::

    Message: fix: correct data parsing error
    
    Result:
    ✓ Version bumped: 0.8.6 → 0.8.7
    ✓ Files committed: your_file.py, __version__.py
    ✓ Log entry created

**Scenario: New Feature**
::

    Message: feat: implement PDF annotation extraction
    
    Result:
    ✓ Version bumped: 0.8.6 → 0.9.0
    ✓ Files committed: extract_data.py, __version__.py
    ✓ Log entry created

**Scenario: Breaking Change**
::

    Message: feat!: redesign configuration API
    
    Result:
    ✓ Version bumped: 0.8.6 → 1.0.0
    ✓ Files committed: config.py, __version__.py
    ✓ Log entry created

Using Terminal (Advanced)
--------------------------

For power users who prefer the command line.

Option 1: Smart Commit Script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the enhanced ``smart-commit.sh`` script for more control:
::

    # Navigate to repository root
    cd /path/to/RePORTaLiN
    
    # Make your changes
    git add file1.py file2.py
    
    # Commit with automatic version bumping
    ./scripts/utils/smart-commit.sh "feat: add new feature"

**Features:**

- Validates changes before committing
- Detailed terminal output with colors
- Comprehensive error handling
- Logs to ``.logs/smart_commit.log``

Option 2: Standard Git Commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Regular git commands work too (hooks run automatically):
::

    # Stage your changes
    git add file1.py file2.py
    
    # Commit with conventional message
    git commit -m "fix: correct validation logic"
    
    # Hook runs automatically:
    # ✓ Version bumped: 0.8.6 → 0.8.7
    # ✓ __version__.py staged and included in commit

Git Alias (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~

Create a git alias for convenience:
::

    # Setup (one time only)
    git config alias.sc '!bash scripts/utils/smart-commit.sh'
    
    # Usage
    git add my_changes.py
    git sc "feat: implement new algorithm"

Bypassing Version Bumping
--------------------------

Sometimes you need to commit without bumping the version.

Use the ``--no-verify`` Flag
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This skips all git hooks:
::

    # VS Code: Not directly supported, use terminal
    
    # Terminal
    git commit --no-verify -m "docs: update README"

**When to bypass:**

- Documentation-only changes
- Fixing typos in comments
- Updating ``.gitignore``
- Work-in-progress commits (use carefully)

.. warning::
   Bypassing hooks means version won't be bumped. Use only when truly necessary.

Manual Version Bumping
~~~~~~~~~~~~~~~~~~~~~~~

If you bypassed the hooks and want to bump manually:
::

    # Patch bump (0.8.6 → 0.8.7)
    .git/hooks/bump-version patch
    
    # Minor bump (0.8.6 → 0.9.0)
    .git/hooks/bump-version minor
    
    # Major bump (0.8.6 → 1.0.0)
    .git/hooks/bump-version major
    
    # Then stage and commit
    git add __version__.py
    git commit -m "chore: manual version bump"

Version History Tracking
-------------------------

All version changes are automatically logged for audit trails.

Log Files
~~~~~~~~~

The system maintains several log files in the ``.logs/`` directory:

**version_updates.log**
::

    [2025-10-29 18:22:19] Version bumped: 0.8.5 → 0.8.6 (type: patch) | Commit: fix: correct parsing
    [2025-10-29 19:30:45] Version bumped: 0.8.6 → 0.9.0 (type: minor) | Commit: feat: add extraction

**prepare_commit_msg.log**
::

    [2025-10-29 19:30:45] [INFO] Prepare-commit-msg hook started
    [2025-10-29 19:30:45] [SUCCESS] Version bumped: 0.8.6 → 0.9.0
    [2025-10-29 19:30:46] [INFO] Version file staged for commit

**smart_commit.log** (when using smart-commit.sh)
::

    [2025-10-29 19:15:30] [INFO] Smart commit initiated with message: feat: add feature
    [2025-10-29 19:15:31] [SUCCESS] Version bumped: 0.8.5 → 0.9.0

Viewing Version History
~~~~~~~~~~~~~~~~~~~~~~~~

Check recent version changes:
::

    # Last 10 version bumps
    tail -10 .logs/version_updates.log
    
    # Find all feature additions (minor bumps)
    grep "type: minor" .logs/version_updates.log
    
    # Find all bug fixes (patch bumps)
    grep "type: patch" .logs/version_updates.log
    
    # Search by date
    grep "2025-10-29" .logs/version_updates.log

Git History
~~~~~~~~~~~

View version changes in git history:
::

    # Show commits that modified version file
    git log --follow --oneline __version__.py
    
    # Detailed version change history
    git log -p __version__.py
    
    # Find specific version
    git log --all --grep="0.9.0"

Troubleshooting
---------------

Version Not Bumping
~~~~~~~~~~~~~~~~~~~

**Symptom:** Version stays the same after commit.

**Solutions:**

1. **Check commit message format:**
   ::

       # Wrong (no colon)
       feat add new feature
       
       # Correct
       feat: add new feature

2. **Verify hooks are executable:**
   ::

       ls -la .git/hooks/prepare-commit-msg
       # Should show: -rwxr-xr-x (executable)
       
       # Fix if needed:
       chmod +x .git/hooks/prepare-commit-msg

3. **Check logs for errors:**
   ::

       tail -20 .logs/prepare_commit_msg.log

4. **Verify __version__.py is not staged:**
   ::

       git status
       # If __version__.py is already staged, unstage it:
       git reset __version__.py

Version Bumped Twice
~~~~~~~~~~~~~~~~~~~~

**Symptom:** Version jumps two numbers (e.g., 0.8.6 → 0.8.8).

**Cause:** Running both smart-commit.sh AND having hooks enabled.

**Solution:** Choose one approach:

- **Either:** Use VS Code + hooks (automatic)
- **Or:** Use smart-commit.sh manually

Hook Conflicts
~~~~~~~~~~~~~~

**Symptom:** Error about hooks during commit.

**Solution:**

1. Check for conflicting hooks:
   ::

       ls -la .git/hooks/ | grep -v sample

2. Review hook logs:
   ::

       tail -50 .logs/prepare_commit_msg.log
       tail -50 .logs/pre_commit_version.log

3. Temporarily disable hooks:
   ::

       # Rename to disable
       mv .git/hooks/prepare-commit-msg .git/hooks/prepare-commit-msg.disabled
       
       # Commit without hooks
       git commit -m "message"
       
       # Re-enable
       mv .git/hooks/prepare-commit-msg.disabled .git/hooks/prepare-commit-msg

Best Practices
--------------

Commit Message Guidelines
~~~~~~~~~~~~~~~~~~~~~~~~~

**Good commit messages:**
::

    ✓ feat: implement PDF text extraction
    ✓ fix: correct validation logic in deidentify module
    ✓ feat(api): add new endpoint for data export
    ✓ fix(parser): handle edge case with empty fields
    ✓ feat!: redesign configuration API (breaking change)

**Bad commit messages:**
::

    ✗ update code
    ✗ fixes
    ✗ WIP
    ✗ asdfasdf
    ✗ changes

Branching Strategy
~~~~~~~~~~~~~~~~~~

**Feature branches:**
::

    # Create feature branch
    git checkout -b feature/new-extraction-method
    
    # Make commits (versions bump automatically)
    git commit -m "feat: add extraction skeleton"  # 0.8.6 → 0.9.0
    git commit -m "feat: implement core logic"     # 0.9.0 → 0.10.0
    git commit -m "fix: handle edge cases"         # 0.10.0 → 0.10.1
    
    # Merge to main
    git checkout main
    git merge feature/new-extraction-method

**Hotfix branches:**
::

    git checkout -b hotfix/critical-bug
    git commit -m "fix: resolve data corruption issue"  # Patch bump
    git checkout main
    git merge hotfix/critical-bug

Version Reset
~~~~~~~~~~~~~

If you need to reset version (use carefully):
::

    # Edit __version__.py manually
    vim __version__.py
    # Change: __version__ = "0.8.6"
    
    # Commit with bypass
    git add __version__.py
    git commit --no-verify -m "chore: reset version to 0.8.6"

Team Workflow
~~~~~~~~~~~~~

**For team collaboration:**

1. **Pull before committing:**
   ::

       git pull origin main
       # Resolve any version conflicts if needed

2. **Use descriptive commit messages:**
   - Helps team understand changes
   - Ensures correct version bumping

3. **Review version changes in PRs:**
   - Check that version bump makes sense
   - Verify ``__version__.py`` changes

4. **Communicate breaking changes:**
   - Use ``feat!:`` prefix
   - Add detailed explanation in commit body

Configuration
-------------

Customizing Version Bump Behavior
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Edit ``.git/hooks/bump-version`` to customize:
::

    # Line ~65-75: Modify bump type detection
    if echo "$COMMIT_MSG_LOWER" | grep -qE "^feat(\(.+\))?:"; then
        BUMP_TYPE="minor"
    elif echo "$COMMIT_MSG_LOWER" | grep -qE "^fix(\(.+\))?:"; then
        BUMP_TYPE="patch"
    # Add custom rules here
    fi

Disabling Automatic Bumping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To temporarily disable automatic version bumping:
::

    # Rename the hook
    mv .git/hooks/prepare-commit-msg .git/hooks/prepare-commit-msg.disabled
    
    # Commits won't bump version
    git commit -m "any message"
    
    # Re-enable later
    mv .git/hooks/prepare-commit-msg.disabled .git/hooks/prepare-commit-msg

Integration with CI/CD
----------------------

The version bumping system integrates seamlessly with CI/CD pipelines.

GitHub Actions Example
~~~~~~~~~~~~~~~~~~~~~~

::

    name: Build and Test
    on: [push]
    
    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v2
          
          - name: Get version
            id: version
            run: |
              VERSION=$(python -c "from __version__ import __version__; print(__version__)")
              echo "::set-output name=version::$VERSION"
          
          - name: Build with version
            run: |
              echo "Building version ${{ steps.version.outputs.version }}"
              # Your build commands here

GitLab CI Example
~~~~~~~~~~~~~~~~~

::

    build:
      script:
        - export VERSION=$(python -c "from __version__ import __version__; print(__version__)")
        - echo "Building version $VERSION"
        - # Your build commands

See Also
--------

- :doc:`logging_system` - Logging infrastructure and log file locations
- :doc:`testing` - Testing procedures
- :doc:`contributing` - Contribution guidelines
- :mod:`__version__` - Version module documentation

External Resources
------------------

- `Semantic Versioning 2.0.0 <https://semver.org/>`_
- `Conventional Commits <https://www.conventionalcommits.org/>`_
- `Git Hooks Documentation <https://git-scm.com/docs/githooks>`_

.. versionadded:: 0.9.0
   Automatic version bumping system with VS Code integration via git hooks.

.. note::
   The version bumping system is designed to work transparently. Most developers
   can simply write good commit messages and let the automation handle versioning.
