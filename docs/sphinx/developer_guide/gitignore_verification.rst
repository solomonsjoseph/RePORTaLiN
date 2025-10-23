Git Ignore Policy Verification
================================

**For Developers: File Exclusion Compliance**

This document verifies that the `.gitignore` policy is properly enforced to ensure
only `README.md` is the sole `.md` file tracked by git, with all other documentation
in `.rst` format.

**Last Verified:** October 23, 2025  
**Status:** ✅ FULLY COMPLIANT

Verification Summary
--------------------

**Git Ignore Rules Status:**

✅ `docs/.vision/` folder is properly ignored  
✅ `docs/.vision/**` (all contents) are properly ignored  
✅ All `.md` files blocked except `README.md`  
✅ Temporary folders (`tmp/`, `.logs/`, `data/.backup/`) ignored  
✅ No untracked `.md` files in project (excluding ignored directories)

Git Tracked Files
-----------------

**Markdown Files Tracked by Git:**

.. code-block:: text

   README.md  ← Only allowed .md file ✅

**Total `.md` files tracked:** 1

Ignored Directories
-------------------

The following directories are completely ignored, including any `.md` files within:

1. **docs/.vision/** - AI/Editor cache and temporary files (docs-specific)
2. **tmp/** - Temporary files
3. **.logs/** - Log files (project root)
4. **data/.backup/** - Backup files (data-specific)
5. **.venv/** - Virtual environment
6. **build/** - Build artifacts
7. **docs/sphinx/_build/** - Documentation build output

Git Ignore Configuration
-------------------------

Enhanced `.gitignore` Rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   # AI/Editor cache and temporary files
   docs/.vision/
   docs/.vision/**

   # Documentation Policy: NO .md files except README.md
   # All documentation goes in docs/sphinx/*.rst files
   *.md
   !README.md

   # Temporary documentation files
   FIXES.md
   AUDIT.md
   VERIFICATION.md
   STATUS.md
   CHANGES.md
   NOTES.md
   *_VERIFICATION*.md
   *_AUDIT*.md
   *_REPORT*.md
   *_SUMMARY*.md

Testing Git Ignore
------------------

To verify that a file or directory is properly ignored:

.. code-block:: bash

   # Check if a file/directory is ignored
   git check-ignore -v docs/.vision/
   git check-ignore -v docs/.vision/context.md
   git check-ignore -v TERMINOLOGY_AUDIT_SUMMARY.md

   # List all tracked .md files (should only show README.md)
   git ls-files "*.md"

   # Find any .md files not in ignored directories
   find . -name "*.md" -not -path "./.git/*" -not -path "./.venv/*" \
          -not -path "./tmp/*" -not -path "./docs/.vision/*" | grep -v "README.md"

Documentation Policy Compliance
--------------------------------

**Policy:** All documentation must be in `.rst` format except `README.md`

**Enforcement Layers:**

1. **Git Ignore** - Blocks `.md` files from being committed
2. **Style Checker** - Validates documentation standards
3. **Policy Document** - Documents the requirements
4. **This Verification** - Regular compliance checks

**Compliant Documentation Structure:**

.. code-block:: text

   RePORTaLiN/
   ├── README.md                           ← Only .md file (allowed) ✅
   └── docs/
       └── sphinx/
           ├── user_guide/
           │   ├── introduction.rst        ← All .rst ✅
           │   ├── installation.rst        ← All .rst ✅
           │   ├── configuration.rst       ← All .rst ✅
           │   └── ...
           └── developer_guide/
               ├── architecture.rst        ← All .rst ✅
               ├── contributing.rst        ← All .rst ✅
               ├── documentation_policy.rst← All .rst ✅
               └── ...

Verification Checklist
----------------------

Manual Verification Steps
~~~~~~~~~~~~~~~~~~~~~~~~~

Run these commands to verify compliance:

.. code-block:: bash

   # 1. Check git tracked .md files (should only show README.md)
   git ls-files "*.md"
   
   # 2. Verify docs/.vision is ignored
   git check-ignore -v docs/.vision/
   
   # 3. Check for untracked .md files in project
   find . -name "*.md" -not -path "./.git/*" -not -path "./.venv/*" \
          -not -path "./tmp/*" -not -path "./docs/.vision/*" | grep -v "README.md"
   
   # 4. Run documentation style checker
   bash scripts/utils/check_docs_style.sh

Expected Results
~~~~~~~~~~~~~~~~

**All checks should pass with:**

1. Git tracked files: ``README.md`` only
2. `docs/.vision/` check: Returns gitignore rule match
3. Untracked `.md` files: None found (count = 0)
4. Style checker: All passed, 0 errors

Current Status
--------------

**Last Verification:** October 23, 2025

.. code-block:: text

   ✅ Git tracked .md files: 1 (README.md only)
   ✅ docs/.vision/ folder: Properly ignored
   ✅ docs/.vision/** contents: Properly ignored
   ✅ Untracked .md files: 0 found
   ✅ Style checker: All passed
   ✅ Documentation build: Success (0 warnings, 0 errors)

**Compliance Status:** ✅ FULLY COMPLIANT

Troubleshooting
---------------

If .md Files Appear in Git Status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** `.md` files (other than `README.md`) showing as untracked

**Solution:**

.. code-block:: bash

   # 1. Verify .gitignore is correct
   cat .gitignore | grep -A5 "Documentation Policy"
   
   # 2. Test if file is ignored
   git check-ignore -v filename.md
   
   # 3. If not ignored, check .gitignore syntax
   # Make sure *.md is not commented out
   # Make sure !README.md comes after *.md

If docs/.vision/ Files Are Tracked
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** `docs/.vision/` files showing in git status

**Solution:**

.. code-block:: bash

   # 1. Remove from git cache (if already tracked)
   git rm -r --cached docs/.vision/
   
   # 2. Verify ignore rule
   git check-ignore -v docs/.vision/
   
   # 3. Commit the removal
   git commit -m "Remove docs/.vision/ from git tracking"

If Documentation Build Fails
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Sphinx build fails after removing `.md` files

**Solution:**

.. code-block:: bash

   # 1. Verify all documentation is in .rst format
   find docs/sphinx -name "*.md" -not -name "README.md"
   
   # 2. Check for broken links in .rst files
   cd docs/sphinx && make linkcheck
   
   # 3. Rebuild clean
   make clean && make html

Best Practices
--------------

1. **Never commit `.md` files except `README.md`**
   
   - Use `.rst` format for all documentation
   - Run style checker before commits

2. **Keep .gitignore updated**
   
   - Add new ignored directories as needed
   - Test ignore rules with `git check-ignore`

3. **Regular verification**
   
   - Run verification checks periodically
   - Update this document after changes

4. **Use automated checks**
   
   - Run style checker in CI/CD
   - Add pre-commit hooks if needed

Related Documentation
---------------------

- :doc:`documentation_policy` - Documentation standards and enforcement
- :doc:`documentation_style_guide` - Style guide for .rst documentation
- :doc:`terminology_simplification` - Language simplification audit
- :doc:`documentation_audit` - Complete documentation audit

See Also
--------

**Git Documentation:**

- `git check-ignore <https://git-scm.com/docs/git-check-ignore>`_
- `gitignore patterns <https://git-scm.com/docs/gitignore>`_

**Project Documentation:**

- `.gitignore` - Complete ignore rules
- `scripts/utils/check_docs_style.sh` - Automated compliance checker
- `README.md` - The only allowed markdown file

---

**Maintained by:** Development Team  
**Next Review:** As needed when .gitignore changes  
**Automation:** Run `bash scripts/utils/check_docs_style.sh` for automated verification
