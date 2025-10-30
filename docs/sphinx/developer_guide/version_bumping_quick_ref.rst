Quick Reference: Version Bumping
==================================

**For Developers:** Quick reference guide for automatic version bumping in VS Code and terminal.

TL;DR
-----

**Commit from VS Code:**

1. Stage files
2. Write message: ``feat: add feature`` or ``fix: bug fix``
3. Click Commit
4. ✓ Version auto-bumps!

**Commit from Terminal:**

.. code-block:: bash

    git commit -m "feat: add feature"  # Auto-bumps to 0.9.0
    git commit -m "fix: bug fix"       # Auto-bumps to 0.8.7

Version Bump Rules
------------------

.. code-block:: text

    Message Starting With       Version Change      Example
    ═══════════════════════════════════════════════════════════
    feat:                       0.8.6 → 0.9.0       feat: add export
    Feat: (any case)            0.8.6 → 0.9.0       Feat: new API
    fix:                        0.8.6 → 0.8.7       fix: bug fix
    Fix: (any case)             0.8.6 → 0.8.7       Fix: typo
    feat!:                      0.8.6 → 1.0.0       feat!: breaking
    BREAKING CHANGE:            0.8.6 → 1.0.0       (in message)
    docs:/style:/test:          0.8.6 → 0.8.7       (patch bump)

Common Tasks
------------

New Feature
~~~~~~~~~~~

.. code-block:: bash

    git add .
    git commit -m "feat: add user authentication"
    # Version: 0.8.6 → 0.9.0

Bug Fix
~~~~~~~

.. code-block:: bash

    git add .
    git commit -m "fix: correct validation logic"
    # Version: 0.9.0 → 0.9.1

Documentation
~~~~~~~~~~~~~

.. code-block:: bash

    git add docs/
    git commit --no-verify -m "docs: update README"
    # Version: stays 0.9.1 (--no-verify skips bump)

Breaking Change
~~~~~~~~~~~~~~~

.. code-block:: bash

    git add .
    git commit -m "feat!: redesign API

    BREAKING CHANGE: All endpoints changed"
    # Version: 0.9.1 → 1.0.0

Troubleshooting
---------------

Version Not Bumping?
~~~~~~~~~~~~~~~~~~~~

**Check message format:**

.. code-block:: bash

    # ✗ Wrong (no colon)
    git commit -m "feat add feature"
    
    # ✓ Correct
    git commit -m "feat: add feature"

**Check hook permissions:**

.. code-block:: bash

    chmod +x .git/hooks/prepare-commit-msg
    chmod +x .git/hooks/bump-version

**Check logs:**

.. code-block:: bash

    tail -20 .logs/prepare_commit_msg.log

Version Bumped Twice?
~~~~~~~~~~~~~~~~~~~~~

Don't manually stage ``__version__.py``:

.. code-block:: bash

    # ✗ Wrong
    git add __version__.py  # Don't do this!
    git commit -m "feat: feature"
    
    # ✓ Correct
    git commit -m "feat: feature"  # System auto-stages it

VS Code Usage
-------------

Step-by-Step
~~~~~~~~~~~~

1. **Make changes** in files
2. **Stage files** (+ button in Source Control)
3. **Write message** in commit box:

   .. code-block:: text
   
       feat: add data export
   
4. **Click Commit** button (✓)
5. **Done!** Version auto-bumps from 0.8.6 → 0.9.0

What You'll See
~~~~~~~~~~~~~~~

.. code-block:: text

    ╔══════════════════════════════════════════╗
    ║  Automatic Version Bumping               ║
    ╚══════════════════════════════════════════╝
    
    → Current version: 0.8.6
    → Analyzing commit message...
    ✓ Version bumped: 0.8.6 → 0.9.0
    ✓ Version file staged
    ✓ Ready to commit with version 0.9.0

Useful Commands
---------------

Check Current Version
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    python -c "from __version__ import __version__; print(__version__)"

View Version History
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Last 20 version changes
    tail -20 .logs/version_updates.log
    
    # All features added
    grep "type: minor" .logs/version_updates.log
    
    # All bug fixes
    grep "type: patch" .logs/version_updates.log

Skip Version Bump
~~~~~~~~~~~~~~~~~

.. code-block:: bash

    git commit --no-verify -m "docs: update"

Bypass for docs, configs, or when you need manual control.

Full Documentation
------------------

For complete details, see:

- :doc:`git_workflow` - Complete git workflow guide
- :doc:`logging_system` - Logging system documentation
- :mod:`__version__` - Version module reference

.. versionadded:: 0.8.6
   Quick reference guide for automatic version bumping.
