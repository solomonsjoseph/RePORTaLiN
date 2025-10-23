GitHub Pages Automatic Deployment
===================================

**For Developers: Setting up Continuous Documentation Deployment**

This guide explains how the documentation is automatically built and deployed to GitHub Pages,
and how to troubleshoot deployment issues.

**Last Updated:** October 23, 2025  
**Version:** |version|  
**Status:** Production-Ready

Overview
--------

The documentation deployment system uses GitHub Actions to automatically:

1. Build Sphinx documentation on every push
2. Deploy to GitHub Pages via ``gh-pages`` branch
3. Make documentation live at ``https://username.github.io/repo-name``

This is a **hands-off** continuous deployment system requiring zero manual intervention
after initial setup.

Architecture
------------

Deployment Flow
~~~~~~~~~~~~~~~

.. code-block:: text

   Developer Push Code
         ↓
   GitHub Detects Changes
         ↓
   GitHub Actions Triggered (.github/workflows/deploy-docs.yml)
         ↓
   [BUILD JOB]
   • Setup Python 3.13
   • Install dependencies
   • Run: cd docs/sphinx && make clean html
   • Upload artifact (7-day retention)
         ↓
   [DEPLOY JOB]
   • Download build artifact
   • Configure GitHub Pages
   • Upload to gh-pages branch
   • Live at: https://username.github.io/repo-name
         ↓
   Documentation Available (1-2 minutes)

Build & Deploy Jobs
~~~~~~~~~~~~~~~~~~~

The workflow has two separate jobs following professional CI/CD patterns:

**Build Job** (``ubuntu-latest``)
   - Setup: Python 3.13, system dependencies (``make``)
   - Install: All packages from ``requirements.txt``
   - Build: Sphinx documentation with caching
   - Output: Artifacts stored 7 days (debugging support)
   - Runs on: Every push, pull requests, manual trigger

**Deploy Job** (``ubuntu-latest``)
   - Dependency: Requires build job to succeed
   - Condition: Only runs on ``main``, ``master`` branches
   - Action: Uploads to ``gh-pages`` branch
   - Result: GitHub Pages auto-deploys from ``gh-pages``

Why Separate Jobs?
   - ✅ Reliability: Retry deploy without rebuilding
   - ✅ Debugging: Keep build artifacts for investigation
   - ✅ Safety: Deploy only on main branches (PR builds safe)
   - ✅ Scalability: Easy to add additional deployment targets
   - ✅ Performance: Can parallelize in future

Configuration Files
-------------------

``.github/workflows/deploy-docs.yml``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Main GitHub Actions workflow file.

**Triggers:**

.. code-block:: yaml

   on:
     push:
       branches:
         - main
         - master
         - develop
       paths:
         - 'docs/**'
         - 'scripts/**'
         - '__version__.py'
         - 'main.py'
         - 'config.py'
         - 'requirements.txt'
         - '.github/workflows/deploy-docs.yml'
     pull_request:
       branches:
         - main
         - master
     workflow_dispatch:  # Manual trigger

**Build Job Steps:**

.. code-block:: yaml

   - Checkout repository (with full history)
   - Set up Python 3.13
   - Install system dependencies (make)
   - Install Python dependencies (cached pip)
   - Build documentation: cd docs/sphinx && make clean html
   - Upload build artifact (7-day retention)

**Deploy Job Steps:**

.. code-block:: yaml

   - Download build artifact
   - Setup GitHub Pages
   - Upload to GitHub Pages
   - Deploy to gh-pages branch
   - Success notification

See ``.github/workflows/deploy-docs.yml`` for complete configuration.

``.nojekyll``
~~~~~~~~~~~~~

Empty file that tells GitHub Pages to serve content as-is without Jekyll processing.

**Why needed:** Sphinx generates HTML structure that Jekyll would incorrectly process,
breaking links and styling. This file disables Jekyll.

**Location:** Repository root (automatically served by GitHub Pages)

**Content:** Empty or comment-only

``requirements.txt``
~~~~~~~~~~~~~~~~~~~~

All Python dependencies including Sphinx packages:

.. code-block:: text

   sphinx>=7.0.0                      # Documentation generator
   sphinx-rtd-theme>=1.3.0            # Read the Docs theme
   sphinx-autodoc-typehints>=1.24.0   # Type hints rendering
   sphinx-autobuild>=2021.3.14        # Auto-rebuild on file changes

**.gitignore**

Already configured to exclude:

.. code-block:: text

   docs/sphinx/_build/                # Built HTML (not committed)

Setup Instructions
------------------

One-Time Setup
~~~~~~~~~~~~~~

**Step 1: Verify Files Exist**

.. code-block:: bash

   # Check workflow file
   ls -la .github/workflows/deploy-docs.yml

   # Check GitHub Pages config
   ls -la .nojekyll

   # Check dependencies
   grep sphinx requirements.txt

**Step 2: Commit Files**

.. code-block:: bash

   git add .github .nojekyll
   git commit -m "Add automatic GitHub Pages deployment"
   git push origin main

**Step 3: Watch Workflow Run**

1. Go to GitHub repository
2. Click **Actions** tab
3. Look for **"Build and Deploy Documentation"**
4. Should show: ⏳ In Progress → ✅ Passed

**Step 4: Configure GitHub Pages**

1. Go to **Settings** → **Pages** (left sidebar)
2. Under **Build and deployment**:
   - Source: **Deploy from a branch**
   - Branch: **gh-pages** (appears after first build)
   - Folder: **/root**
3. Click **Save**

**Step 5: Access Documentation**

After ~1-2 minutes:

.. code-block:: text

   URL: https://your-username.github.io/repo-name
   Example: https://myusername.github.io/RePORTaLiN

Local Testing
~~~~~~~~~~~~~

Before pushing to GitHub, verify locally:

.. code-block:: bash

   # Test 1: Build documentation
   make clean-docs
   make docs

   # Test 2: Check output exists
   ls -la docs/sphinx/_build/html/index.html

   # Test 3: View locally
   make docs-open

   # Test 4: Live reload development
   make docs-watch
   # Then visit: http://127.0.0.1:8000

Performance
-----------

Build Times
~~~~~~~~~~~

============================  ==================
Build Type                    Expected Time
============================  ==================
First build (fresh install)   2-3 minutes
Subsequent builds (cached)    30-60 seconds
Cache retention               5 days
============================  ==================

**Why slow first time:** Downloads and installs all pip dependencies

**Why fast after:** Pip dependencies cached in GitHub Actions

Bandwidth & Quota
~~~~~~~~~~~~~~~~~

**GitHub Pages:**
   - Unlimited bandwidth for public repositories
   - No strict size limits for reasonable sizes

**GitHub Actions:**
   - Public repos: Unlimited free usage
   - Private repos: 2,000 minutes/month free
   - Current build: ~30-60 seconds per build
   - Monthly estimate: Minimal quota usage

Troubleshooting
---------------

Workflow Shows Red (Failed)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Step 1: Check Error Logs**

1. Go to **Actions** tab
2. Click the failed workflow run
3. Click **build** job
4. Scroll down to find error message

**Step 2: Common Issues**

+-------------------------------------------+---------------------------------------------+
| Error                                     | Solution                                    |
+===========================================+=============================================+
| ``ModuleNotFoundError: No module named``  | Add package to ``requirements.txt``         |
|                                           | Then run: ``make docs`` locally             |
+-------------------------------------------+---------------------------------------------+
| Sphinx build fails (warnings as errors)   | Fix ``.rst`` syntax errors in docs          |
|                                           | Run: ``make docs`` locally to debug         |
+-------------------------------------------+---------------------------------------------+
| ``make: command not found``               | Workflow installs ``make`` automatically    |
|                                           | Only happens if Ubuntu image changes        |
+-------------------------------------------+---------------------------------------------+
| Import errors in conf.py                  | Check ``sys.path.insert()`` in ``conf.py``  |
|                                           | Verify ``__version__.py`` exists            |
+-------------------------------------------+---------------------------------------------+

**Step 3: Debug Locally**

.. code-block:: bash

   # Build exactly like the workflow does
   cd docs/sphinx
   make clean html

   # If that works, problem is environment-specific
   # If that fails, you found the issue to fix

Documentation Not Updating
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Check 1: Verify Workflow Ran**

1. Go to **Actions** tab
2. Find latest "Build and Deploy Documentation" run
3. Check status (should be ✅ Passed)

**Check 2: Clear Browser Cache**

.. code-block:: text

   macOS: Cmd+Shift+R
   Windows/Linux: Ctrl+Shift+R

**Check 3: Verify GitHub Pages Settings**

1. Go to **Settings** → **Pages**
2. Verify:
   - Source: **Deploy from a branch**
   - Branch: **gh-pages** (not main)
   - Folder: **/root**
3. Click **Save** again

**Check 4: Wait for Propagation**

GitHub Pages takes 1-3 minutes to propagate. Wait and refresh.

Build Succeeds But Docs Don't Appear
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Issue:** Workflow shows ✅ Passed but docs not live

**Solution:**

1. Go to **Settings** → **Pages**
2. Verify ``gh-pages`` branch is selected
3. Verify folder is ``/root``
4. Click **Save**
5. Wait 2-3 minutes
6. Visit URL again

**If still not working:**

1. Delete ``gh-pages`` branch locally and remote
2. Run workflow again (or push code)
3. Workflow recreates ``gh-pages`` branch
4. Reconfigure Settings → Pages

Manual Deployment
-----------------

Trigger Build Manually
~~~~~~~~~~~~~~~~~~~~~~

To rebuild docs without pushing code:

1. Go to GitHub repository
2. Click **Actions** tab
3. Click **Build and Deploy Documentation**
4. Click **Run workflow** button
5. Select branch (usually **main**)
6. Click **Run workflow**

Wait ~1-2 minutes for build to complete.

Redeploy Old Version
~~~~~~~~~~~~~~~~~~~~

To re-deploy a previous version:

1. Go to **Actions** tab
2. Find successful workflow run (scroll through history)
3. Click the run
4. Click **Re-run failed jobs** or **Re-run all jobs**

Previous version rebuilds and redeploys.

Disable Auto-Deploy
~~~~~~~~~~~~~~~~~~~

To temporarily disable automatic deployment:

**Option 1: Disable workflow**

1. Go to **Actions** tab
2. Click **Build and Deploy Documentation**
3. Click **⋯** (three dots)
4. Select **Disable workflow**

**Option 2: Delete workflow file**

.. code-block:: bash

   git rm .github/workflows/deploy-docs.yml
   git commit -m "Disable automatic deployment"
   git push

**Re-enable:** Restore the workflow file or click **Enable workflow**

Custom Domain (Advanced)
~~~~~~~~~~~~~~~~~~~~~~~~

To use a custom domain (e.g., ``docs.mysite.com``):

**Step 1: Create DNS Record**

Create CNAME or A record pointing to GitHub Pages:

.. code-block:: text

   CNAME: docs.mysite.com → username.github.io

**Step 2: Configure GitHub Pages**

1. Go to **Settings** → **Pages**
2. Enter domain in **Custom domain** field
3. GitHub creates CNAME file automatically
4. Enable **Enforce HTTPS** when available

**Step 3: Wait for SSL Certificate**

GitHub provisions SSL certificate (takes 24 hours).

Monitoring & Maintenance
------------------------

View Build Artifacts
~~~~~~~~~~~~~~~~~~~~~

Build artifacts are stored 7 days for debugging:

1. Go to **Actions** tab
2. Click workflow run
3. Scroll to **Artifacts** section
4. Download ``documentation`` artifact

Useful for debugging failed builds.

Check GitHub Actions Quota
~~~~~~~~~~~~~~~~~~~~~~~~~~

For private repositories (public repos have unlimited):

1. Go to **Settings** → **Billing and plans**
2. Click **Actions** (left sidebar)
3. View usage for current month

Current build time (~30-60 sec) uses minimal quota.

Update Documentation
~~~~~~~~~~~~~~~~~~~~

Documentation updates automatically on every push:

.. code-block:: bash

   # Edit documentation files
   vim docs/sphinx/user_guide/quickstart.rst

   # Test locally
   make docs

   # Commit and push
   git add docs/
   git commit -m "Update documentation"
   git push origin main

   # Workflow automatically runs
   # Docs update live in 2-5 minutes

Modify Workflow
~~~~~~~~~~~~~~~

To modify the GitHub Actions workflow:

1. Edit ``.github/workflows/deploy-docs.yml``
2. Make changes
3. Test locally if possible: ``make docs``
4. Commit and push
5. Workflow uses new configuration

Common modifications:
   - Change trigger branches
   - Add path filters
   - Change Python version
   - Add build steps

Best Practices
--------------

✅ DO
~~~~

✅ Commit documentation changes with code changes
✅ Test documentation locally before pushing
✅ Use consistent RST formatting
✅ Update version in ``__version__.py`` for major changes
✅ Include examples in documentation
✅ Use descriptive commit messages

❌ DON'T
~~~~~~~

❌ Don't commit build artifacts (``_build/``)
❌ Don't manually edit ``gh-pages`` branch
❌ Don't bypass documentation review
❌ Don't leave broken links in documentation
❌ Don't mix Markdown and RST (use only RST)
❌ Don't modify workflow without testing locally

Verification Checklist
----------------------

Before considering setup complete:

Setup Verification
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # ✓ Check 1: Files exist
   [ -f .github/workflows/deploy-docs.yml ] && echo "✓ Workflow file exists"
   [ -f .nojekyll ] && echo "✓ GitHub Pages config exists"

   # ✓ Check 2: Dependencies in requirements.txt
   grep sphinx requirements.txt && echo "✓ Sphinx configured"

   # ✓ Check 3: Documentation builds
   make docs && echo "✓ Local build works"

   # ✓ Check 4: Files committed
   git log --oneline -n 5 | grep -i pages && echo "✓ Files committed"

Deployment Verification
~~~~~~~~~~~~~~~~~~~~~~~

After first push:

.. code-block:: text

   ✓ Workflow started (visible in Actions tab)
   ✓ Build succeeded (green checkmark)
   ✓ gh-pages branch created
   ✓ Settings → Pages shows gh-pages branch
   ✓ Documentation accessible at live URL
   ✓ Search functionality working
   ✓ Links not broken
   ✓ Styling displaying correctly

Related Documentation
---------------------

- :doc:`documentation_policy` - Documentation standards and guidelines
- :doc:`documentation_style_guide` - Formatting and style requirements
- :doc:`documentation_audit` - Complete documentation audit
- :doc:`production_readiness` - Production readiness checklist

See Also
--------

- `GitHub Pages Documentation <https://docs.github.com/en/pages>`__
- `GitHub Actions Documentation <https://docs.github.com/en/actions>`__
- `Sphinx Documentation <https://www.sphinx-doc.org/>`__
- `Read the Docs Theme <https://sphinx-rtd-theme.readthedocs.io/>`__
