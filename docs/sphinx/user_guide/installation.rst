Installation
============

Prerequisites
-------------

Before installing RePORTaLiN, ensure you have:

* Python 3.8 or higher
* pip package manager
* Git (for cloning the repository)

System Requirements
~~~~~~~~~~~~~~~~~~~

* **Operating System**: macOS, Linux, or Windows
* **Memory**: Minimum 8GB RAM (16GB recommended for large datasets)
* **Disk Space**: 2GB for the application and dependencies

Installation Steps
------------------

1. Clone the Repository
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/your-org/RePORTaLiN.git
   cd RePORTaLiN

2. Create a Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate

3. Install Dependencies
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install -r requirements.txt

Required Dependencies
~~~~~~~~~~~~~~~~~~~~~

The main dependencies include:

* **pandas**: Data manipulation and analysis
* **openpyxl**: Excel file reading/writing
* **chromadb**: Vector database for semantic search
* **sentence-transformers**: Text embeddings
* **PyPDF2/pypdf**: PDF processing
* **python-dotenv**: Environment variable management

Optional Dependencies
~~~~~~~~~~~~~~~~~~~~~

For development:

.. code-block:: bash

   pip install -r requirements-dev.txt

This includes:

* pytest: Testing framework
* sphinx: Documentation generation
* black: Code formatting
* flake8: Linting

4. Verify Installation
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python -c "import scripts; print('Installation successful!')"

Configuration
-------------

After installation, you'll need to configure:

1. **Environment Variables**: Copy `.env.example` to `.env` and set your API keys
2. **Config File**: Adjust `config.py` for your specific needs
3. **Data Paths**: Update paths in config to point to your data directories

Next Steps
----------

* See :doc:`configuration` for detailed configuration options
* See :doc:`quickstart` for your first data extraction
