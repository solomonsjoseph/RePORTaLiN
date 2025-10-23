Installation
============

**For Users: Getting Started**

This guide will help you install RePORTaLiN on your computer in just a few simple steps.

Prerequisites
-------------

Before installing RePORTaLiN, ensure you have:

- **Python 3.13 or higher** installed on your system
- **pip** package manager (comes with Python)
- **Git** (optional, for cloning the repository)

Checking Python Version
~~~~~~~~~~~~~~~~~~~~~~~~

To verify your Python version:

.. code-block:: bash

   python --version
   # or
   python3 --version

You should see output like: ``Python 3.13.5`` or higher.

Installation Steps
------------------

Step 1: Clone the Repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have Git installed:

.. code-block:: bash

   git clone https://github.com/solomonsjoseph/RePORTaLiN.git
   cd RePORTaLiN

Alternatively, download the ZIP file from GitHub and extract it.

Step 2: Create a Virtual Environment (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's **highly recommended** to use a virtual environment to avoid conflicts with other Python packages:

**macOS/Linux:**

.. code-block:: bash

   # Create virtual environment
   python3 -m venv .venv

   # Activate virtual environment
   source .venv/bin/activate

   # Your prompt should now show (.venv)

**Windows:**

.. code-block:: bash

   # Create virtual environment
   python -m venv .venv

   # Activate virtual environment (Command Prompt)
   .venv\Scripts\activate.bat

   # Or for PowerShell
   .venv\Scripts\Activate.ps1

   # Your prompt should now show (.venv)

**To deactivate the virtual environment later:**

.. code-block:: bash

   deactivate

Step 3: Install Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install all required packages using pip:

.. code-block:: bash

   pip install -r requirements.txt

This will install:

**Core Dependencies:**

- **pandas** (≥2.0.0): Data manipulation and Excel reading
- **openpyxl** (≥3.1.0): Excel file format support (.xlsx files)
- **numpy** (≥1.24.0): Numerical operations
- **tqdm** (≥4.66.0): **Required** - Progress bars and clean console output

**Security:**

- **cryptography** (≥41.0.0): Encryption for de-identification mappings

**Documentation (Optional):**

- **sphinx** (≥7.0.0): Documentation generation
- **sphinx-rtd-theme** (≥1.3.0): ReadTheDocs theme
- **sphinx-autodoc-typehints** (≥1.24.0): Type hints in docs

Verifying Installation
----------------------

To verify the installation was successful:

**Option 1: Quick Check**

.. code-block:: bash

   # Check if main modules can be imported
   python -c "import pandas, openpyxl, numpy, tqdm, cryptography; print('✅ All dependencies installed successfully!')"

**Option 2: Run Help Command**

.. code-block:: bash

   python main.py --help

You should see the usage information without any errors.

**Option 3: Test Run**

.. code-block:: bash

   # Run a quick test (make sure you have data in data/dataset/)
   python main.py

If you see progress bars and status messages without errors, the installation is successful!

Directory Structure
-------------------

After installation, your project structure should look like:

.. code-block:: text

   RePORTaLiN/
   ├── main.py                 # Main entry point
   ├── config.py               # Configuration
   ├── requirements.txt        # Dependencies
   ├── Makefile               # Build commands (optional)
   ├── README.md              # Project overview
   ├── scripts/               # Core modules
   │   ├── extract_data.py   # Excel to JSONL extraction
   │   ├── load_dictionary.py # Dictionary processor
   │   └── utils/
   │       ├── deidentify.py # De-identification script
   │       └── logging.py # Centralized logging
   ├── data/                  # Your data files go here
   │   ├── dataset/
   │   │   └── <dataset_name>/  # Excel files (e.g., Indo-vap_csv_files/)
   │   └── data_dictionary_and_mapping_specifications/
   │       └── RePORT_DEB_to_Tables_mapping.xlsx
   ├── results/               # Output files (created automatically)
   │   ├── dataset/           # Extracted JSONL files
   │   ├── deidentified/      # De-identified data (if enabled)
   │   └── data_dictionary_mappings/  # Dictionary outputs
   ├── docs/                  # Documentation
   │   └── sphinx/            # Sphinx documentation
   ├── .logs/                 # Execution logs (created automatically)
   └── .venv/                 # Virtual environment (if created)

Troubleshooting Installation
-----------------------------

Problem: "pip: command not found"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution**: Install pip or use ``python -m pip`` instead:

.. code-block:: bash

   # Try using python -m pip
   python -m pip install -r requirements.txt

   # Or on macOS/Linux
   python3 -m pip install -r requirements.txt

Problem: "Permission denied" errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution**: Use the ``--user`` flag or ensure you're in a virtual environment:

.. code-block:: bash

   # Option 1: Install with --user flag
   pip install --user -r requirements.txt

   # Option 2: Use virtual environment (recommended)
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   # .venv\Scripts\activate   # Windows
   pip install -r requirements.txt

Problem: Import errors after installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution**: Ensure you're in the correct directory and virtual environment:

.. code-block:: bash

   # 1. Check current directory
   pwd
   # Should show: .../RePORTaLiN

   # 2. Ensure virtual environment is activated
   which python
   # Should show: .../RePORTaLiN/.venv/bin/python

   # 3. Reinstall dependencies
   pip install --force-reinstall -r requirements.txt

Problem: "Package 'cryptography' not found"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution**: The cryptography package may need system dependencies:

**macOS:**

.. code-block:: bash

   # Install OpenSSL with Homebrew
   brew install openssl
   pip install cryptography

**Ubuntu/Debian:**

.. code-block:: bash

   sudo apt-get install build-essential libssl-dev libffi-dev python3-dev
   pip install cryptography

**Windows:**

.. code-block:: bash

   # Usually works with pip alone
   pip install cryptography
   # If issues persist, install Microsoft C++ Build Tools

Problem: Excel file reading errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution**: Ensure openpyxl is properly installed:

.. code-block:: bash

   pip install --upgrade openpyxl
   
   # Test it
   python -c "import openpyxl; print('openpyxl version:', openpyxl.__version__)"

Problem: Incompatible Python version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution**: Install Python 3.13 or higher:

- **macOS**: Use Homebrew: ``brew install python@3.13``
- **Ubuntu/Debian**: ``sudo apt-get install python3.13``
- **Windows**: Download from `python.org <https://www.python.org/downloads/>`_

Upgrading
---------

To upgrade to the latest version:

.. code-block:: bash

   # Pull latest changes (if using Git)
   git pull origin main

   # Upgrade dependencies
   pip install --upgrade -r requirements.txt

Setting Up Your Data
--------------------

Before running RePORTaLiN, ensure your data is properly organized:

**Step 1: Place Excel Files**

Put your Excel data files in:

.. code-block:: text

   data/dataset/<your_dataset_name>/

For example:

.. code-block:: text

   data/dataset/Indo-vap_csv_files/
   ├── 1A_ICScreening.xlsx
   ├── 1B_HCScreening.xlsx
   ├── 2A_Index_Baseline.xlsx
   └── ...

**Step 2: Add Data Dictionary**

Place your data dictionary Excel file in:

.. code-block:: text

   data/data_dictionary_and_mapping_specifications/
   └── RePORT_DEB_to_Tables_mapping.xlsx

**Step 3: Verify Setup**

.. code-block:: bash

   # Check if files are in place
   ls data/dataset/
   ls data/data_dictionary_and_mapping_specifications/

The pipeline will automatically detect your dataset folder name and process all Excel files within it.

Next Steps
----------

Now that RePORTaLiN is installed, proceed to:

- :doc:`quickstart`: Run your first data extraction
- :doc:`configuration`: Learn about configuration options
- :doc:`usage`: Explore advanced usage patterns
