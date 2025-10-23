File Reorganization: check_docs_style.sh
============================================

**For Developers: Script Location Update**

This document tracks the relocation of the documentation style checker script
to a more organized location within the utils folder.

**Date:** October 23, 2025  
**Status:** ✅ Complete

Change Summary
--------------

**File Moved:**

.. code-block:: text

   scripts/check_docs_style.sh  →  scripts/utils/check_docs_style.sh

**Reason:**

- Better organization: Utility scripts belong in the `utils/` folder
- Consistent with project structure (logging, colors, etc. are in utils)
- Clearer separation between core scripts and utility tools

Files Updated
-------------

The following files were updated with the new path:

Documentation Files (7 updates)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **scripts/utils/check_docs_style.sh**
   
   - Updated internal usage comment
   - New: ``./scripts/utils/check_docs_style.sh``

2. **docs/sphinx/developer_guide/documentation_style_guide.rst**
   
   - Updated execution example
   - Changed: ``./scripts/check_docs_style.sh`` → ``./scripts/utils/check_docs_style.sh``

3. **docs/sphinx/developer_guide/terminology_simplification.rst** (5 updates)
   
   - Updated script name references
   - Updated execution commands (2 instances)
   - Updated enforcement layer description
   - Updated testing procedure

4. **docs/sphinx/developer_guide/gitignore_verification.rst** (3 updates)
   
   - Updated verification checklist command
   - Updated documentation reference
   - Updated automation note

Cleanup Actions
~~~~~~~~~~~~~~~

- ✅ Removed: ``scripts/check_docs_style.sh`` (old location)
- ✅ Removed: ``TERMINOLOGY_AUDIT_SUMMARY.md`` (violates .md policy)
- ✅ Cleared: Sphinx build cache (doctrees with old references)

New Project Structure
---------------------

Updated File Organization
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   RePORTaLiN/
   ├── scripts/
   │   ├── __init__.py
   │   ├── load_dictionary.py      # Core script
   │   ├── extract_data.py         # Core script
   │   ├── deidentify.py          # Core script
   │   └── utils/                  # Utility scripts ✨
   │       ├── __init__.py
   │       ├── colors.py
   │       ├── country_regulations.py
   │       ├── logging.py
   │       ├── progress.py
   │       └── check_docs_style.sh  # ← Moved here ✅
   └── docs/
       └── sphinx/
           ├── user_guide/
           └── developer_guide/

**Benefits:**

- ✅ Consistent organization (all utilities in one place)
- ✅ Easier to find and maintain
- ✅ Clear separation of concerns
- ✅ Follows project structure conventions

How to Use
----------

From Project Root
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Run the style checker
   bash scripts/utils/check_docs_style.sh

From Scripts Directory
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Navigate to scripts folder
   cd scripts
   
   # Run from utils
   bash utils/check_docs_style.sh

Make It Executable
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Ensure execute permissions
   chmod +x scripts/utils/check_docs_style.sh
   
   # Run directly
   ./scripts/utils/check_docs_style.sh

Verification
------------

Post-Move Verification Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   ✅ File location: scripts/utils/check_docs_style.sh
   ✅ Old file removed: scripts/check_docs_style.sh (deleted)
   ✅ Script functional: All checks pass
   ✅ Documentation updated: 7 files
   ✅ Build cache cleared: No stale references
   ✅ All tests pass: Style checker runs successfully

Testing the Move
~~~~~~~~~~~~~~~~

Run these commands to verify everything works:

.. code-block:: bash

   # 1. Verify file exists in new location
   ls -lh scripts/utils/check_docs_style.sh
   
   # 2. Verify old file is gone
   ls scripts/check_docs_style.sh 2>&1 | grep "No such file"
   
   # 3. Test execution from project root
   bash scripts/utils/check_docs_style.sh
   
   # 4. Rebuild documentation
   cd docs/sphinx
   make clean && make html
   
   # 5. Search for old references (should be 0)
   grep -r "scripts/check_docs_style.sh" docs/sphinx/*.rst 2>/dev/null | wc -l

Documentation References
------------------------

All Documentation Now Points to New Location
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Correct Usage Everywhere:**

.. code-block:: bash

   bash scripts/utils/check_docs_style.sh

**Referenced In:**

- ``documentation_style_guide.rst`` - Shows how to run checker
- ``terminology_simplification.rst`` - Describes enhancement
- ``gitignore_verification.rst`` - Part of verification process
- ``check_docs_style.sh`` itself - Internal usage documentation

Migration Checklist
-------------------

Completed Steps
~~~~~~~~~~~~~~~

.. code-block:: text

   ✅ Move file to new location
   ✅ Update internal documentation (usage comment)
   ✅ Update all .rst file references (7 files)
   ✅ Remove old file from previous location
   ✅ Remove temporary .md files
   ✅ Clear Sphinx build cache
   ✅ Test script execution
   ✅ Verify all documentation builds
   ✅ Confirm no broken references
   ✅ Create this migration document

No Action Required
~~~~~~~~~~~~~~~~~~

The following already reference the correct location:

- Makefile (no references to check_docs_style.sh)
- Python scripts (no references)
- Git hooks (none exist yet)
- CI/CD config (none exists yet)

Future Considerations
---------------------

Integration Opportunities
~~~~~~~~~~~~~~~~~~~~~~~~~

Now that the script is properly organized in `utils/`, consider:

1. **Git Pre-Commit Hook**
   
   .. code-block:: bash
   
      # .git/hooks/pre-commit
      #!/bin/bash
      bash scripts/utils/check_docs_style.sh

2. **Makefile Target**
   
   .. code-block:: makefile
   
      .PHONY: check-docs
      check-docs:
          @bash scripts/utils/check_docs_style.sh

3. **CI/CD Pipeline**
   
   Add to GitHub Actions or similar:
   
   .. code-block:: yaml
   
      - name: Check Documentation Style
        run: bash scripts/utils/check_docs_style.sh

Consistency with Other Utils
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `scripts/utils/` directory now contains:

- **Python utilities**: `.py` files for code functionality
- **Shell utilities**: `.sh` files for automation
- **Clear naming**: All files describe their purpose

Related Documentation
---------------------

- :doc:`documentation_style_guide` - Style guide and standards
- :doc:`terminology_simplification` - Language simplification audit
- :doc:`gitignore_verification` - File exclusion compliance
- :doc:`documentation_policy` - Documentation enforcement policy

See Also
--------

**Script Location:**

- New: ``scripts/utils/check_docs_style.sh``
- Old: ~~``scripts/check_docs_style.sh``~~ (removed)

**Related Utils:**

- ``scripts/utils/logging.py`` - Logging utilities
- ``scripts/utils/colors.py`` - Terminal color codes
- ``scripts/utils/country_regulations.py`` - Privacy regulations
- ``scripts/utils/progress.py`` - Progress bar utilities

---

**Migration By:** AI Assistant  
**Completed:** October 23, 2025  
**Status:** ✅ All references updated, fully functional
