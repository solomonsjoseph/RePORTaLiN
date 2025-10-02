Installation
============

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

It's recommended to use a virtual environment to avoid conflicts with other Python packages:

.. code-block:: bash

   # Create virtual environment
   python -m venv .venv

   # Activate on macOS/Linux
   source .venv/bin/activate

   # Activate on Windows
   .venv\Scripts\activate

Step 3: Install Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install all required packages using pip:

.. code-block:: bash

   pip install -r requirements.txt

This will install:

- **pandas**: Data manipulation and Excel reading
- **openpyxl**: Excel file handling
- **numpy**: Numerical operations
- **tqdm**: Progress bars
- **sphinx** and related packages: Documentation generation

Verifying Installation
----------------------

To verify the installation was successful:

.. code-block:: bash

   # Check if main modules can be imported
   python -c "import pandas, openpyxl, numpy, tqdm; print('All dependencies installed!')"

   # Try running the help command
   python main.py --help

You should see the usage information without any errors.

Directory Structure
-------------------

After installation, your project structure should look like:

.. code-block:: text

   RePORTaLiN/
   ├── main.py                 # Main entry point
   ├── config.py               # Configuration
   ├── requirements.txt        # Dependencies
   ├── Makefile               # Build commands
   ├── scripts/               # Core modules
   │   ├── extract_data.py
   │   ├── load_dictionary.py
   │   └── utils/
   ├── data/                  # Your data files go here
   │   ├── dataset/
   │   └── data_dictionary_and_mapping_specifications/
   ├── results/               # Output files (created automatically)
   ├── docs/                  # Documentation
   └── .venv/                 # Virtual environment

Troubleshooting Installation
-----------------------------

Problem: "pip: command not found"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution**: Install pip or use ``python -m pip`` instead:

.. code-block:: bash

   python -m pip install -r requirements.txt

Problem: "Permission denied" errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution**: Use the ``--user`` flag or ensure you're in a virtual environment:

.. code-block:: bash

   pip install --user -r requirements.txt

Problem: Import errors after installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution**: Ensure you're in the correct directory and virtual environment:

.. code-block:: bash

   # Check current directory
   pwd

   # Ensure virtual environment is activated
   which python

   # Reinstall dependencies
   pip install --force-reinstall -r requirements.txt

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

Next Steps
----------

Now that RePORTaLiN is installed, proceed to:

- :doc:`quickstart`: Run your first data extraction
- :doc:`configuration`: Learn about configuration options
- :doc:`usage`: Explore advanced usage patterns
