Quick Reference - Version Bumping
==================================

**For Developers:** Quick reference card for the automated version bumping system.

Commit Message → Version Change
--------------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Commit Message
     - Version Change
     - Example
   * - ``fix: bug description``
     - Patch (0.8.6 → 0.8.7)
     - Bug fixes
   * - ``feat: feature description``
     - Minor (0.8.6 → 0.9.0)
     - New features
   * - ``feat!: breaking change`` or ``BREAKING CHANGE:``
     - Major (0.8.6 → 1.0.0)
     - API changes
   * - ``docs:``, ``chore:``, ``refactor:``, etc.
     - Patch (0.8.6 → 0.8.7)
     - Other changes

VS Code Workflow
----------------

**3-Step Process:**

1. Stage files (``Cmd+Shift+G``)
2. Write message: ``feat: description``
3. Click "Commit"

✨ **Version bumps automatically!**

Terminal Quick Commands
-----------------------

**Using smart-commit (recommended):**
::

    ./scripts/utils/smart-commit.sh "feat: description"

**Using standard git:**
::

    git add files
    git commit -m "feat: description"
    # Hook runs automatically

**Create git alias (one-time setup):**
::

    git config alias.sc '!bash scripts/utils/smart-commit.sh'
    git sc "feat: description"

Common Tasks
------------

**Check current version:**
::

    cat __version__.py | grep __version__

**View version history:**
::

    tail -20 .logs/version_updates.log

**Bypass version bump:**
::

    git commit --no-verify -m "message"

**Manual version bump:**
::

    .git/hooks/bump-version patch    # 0.8.6 → 0.8.7
    .git/hooks/bump-version minor    # 0.8.6 → 0.9.0
    .git/hooks/bump-version major    # 0.8.6 → 1.0.0

Troubleshooting One-Liners
---------------------------

**Version not bumping?**
::

    # Check hook is executable
    ls -la .git/hooks/prepare-commit-msg
    
    # Make executable if needed
    chmod +x .git/hooks/prepare-commit-msg

**Check for errors:**
::

    tail -30 .logs/prepare_commit_msg.log

**Reset if version file is stuck staged:**
::

    git reset __version__.py

Commit Message Examples
-----------------------

**Good Examples:**
::

    ✓ feat: implement PDF text extraction
    ✓ fix: correct validation logic
    ✓ feat(api): add new endpoint
    ✓ fix(parser): handle empty fields
    ✓ docs: update installation guide
    ✓ refactor: simplify data processing
    ✓ feat!: redesign configuration API

**Bad Examples:**
::

    ✗ update code
    ✗ fixes
    ✗ WIP
    ✗ small changes

Log Files Location
------------------

All logs in ``.logs/`` directory:

- ``version_updates.log`` - Version bump history
- ``prepare_commit_msg.log`` - VS Code commit logs
- ``smart_commit.log`` - Terminal smart-commit logs
- ``pre_commit_version.log`` - Pre-commit hook logs

Full Documentation
------------------

See :doc:`git_workflow` for complete details.

.. versionadded:: 0.9.0
   Quick reference guide for automated version bumping system.
