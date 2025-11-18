Configuration
=============

RePORTaLiN configuration is managed through the `config.py` file and environment variables.

Configuration Files
-------------------

config.py
~~~~~~~~~

The main configuration file contains all pipeline settings:

.. code-block:: python

   from config import Config
   
   config = Config()

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Sensitive information should be stored in a `.env` file (not committed to version control):

.. code-block:: bash

   # .env file
   OPENAI_API_KEY=your_api_key_here
   ANTHROPIC_API_KEY=your_api_key_here
   LLM_PROVIDER=openai

Configuration Options
---------------------

Path Configuration
~~~~~~~~~~~~~~~~~~

Configure input/output paths for the pipeline:

* ``INPUT_PATH``: Directory containing source data files
* ``OUTPUT_PATH``: Directory for processed output files
* ``LOG_PATH``: Directory for log files
* ``DICT_PATH``: Directory containing data dictionary files

Example:

.. code-block:: python

   INPUT_PATH = "data/Indo-VAP/datasets"
   OUTPUT_PATH = "output"
   LOG_PATH = "logs"
   DICT_PATH = "data/Indo-VAP/data_dictionary"

LLM Configuration
~~~~~~~~~~~~~~~~~

Configure the language model provider and settings:

* ``LLM_PROVIDER``: Provider name ("openai", "anthropic", etc.)
* ``LLM_MODEL``: Specific model to use
* ``LLM_TEMPERATURE``: Sampling temperature (0.0-1.0)
* ``LLM_MAX_TOKENS``: Maximum tokens in response

Example:

.. code-block:: python

   LLM_PROVIDER = "openai"
   LLM_MODEL = "gpt-4"
   LLM_TEMPERATURE = 0.0
   LLM_MAX_TOKENS = 4096

Vector Database Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure ChromaDB vector store settings:

* ``CHROMA_PERSIST_DIR``: Directory to persist vector database
* ``CHROMA_COLLECTION_NAME``: Name of the collection
* ``EMBEDDING_MODEL``: Sentence transformer model for embeddings
* ``CHUNK_SIZE``: Size of text chunks for embedding
* ``CHUNK_OVERLAP``: Overlap between chunks

Example:

.. code-block:: python

   CHROMA_PERSIST_DIR = "chroma_db"
   CHROMA_COLLECTION_NAME = "reportalin_docs"
   EMBEDDING_MODEL = "all-MiniLM-L6-v2"
   CHUNK_SIZE = 1000
   CHUNK_OVERLAP = 200

De-identification Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure PII removal and privacy settings:

* ``DEIDENTIFY_ENABLED``: Enable/disable de-identification
* ``COMPLIANCE_REGION``: Regulatory region ("USA", "EU", "Singapore")
* ``DATE_SHIFT_DAYS``: Number of days to shift dates
* ``HASH_SALT``: Salt for identifier hashing

Example:

.. code-block:: python

   DEIDENTIFY_ENABLED = True
   COMPLIANCE_REGION = "USA"
   DATE_SHIFT_DAYS = 365
   HASH_SALT = "secure_random_salt"

Logging Configuration
~~~~~~~~~~~~~~~~~~~~~

Configure logging behavior:

* ``LOG_LEVEL``: Logging level ("DEBUG", "INFO", "WARNING", "ERROR")
* ``LOG_FORMAT``: Format string for log messages
* ``LOG_TO_FILE``: Enable file logging
* ``LOG_TO_CONSOLE``: Enable console logging

Example:

.. code-block:: python

   LOG_LEVEL = "INFO"
   LOG_TO_FILE = True
   LOG_TO_CONSOLE = True

Advanced Configuration
----------------------

Custom Validators
~~~~~~~~~~~~~~~~~

Add custom validation rules for specific fields:

.. code-block:: python

   from scripts.load_dictionary import add_custom_validator
   
   def validate_tb_status(value):
       valid_statuses = ["active", "latent", "treated", "negative"]
       return value.lower() in valid_statuses
   
   add_custom_validator("tb_status", validate_tb_status)

Custom De-identification Rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add custom PII detection patterns:

.. code-block:: python

   from scripts.deidentify import add_custom_pattern
   
   # Add pattern for hospital ID format
   add_custom_pattern(
       name="hospital_id",
       pattern=r"HID-\\d{6}",
       replacement="[HOSPITAL_ID]"
   )

Environment-Specific Configuration
-----------------------------------

Development Environment
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # .env.development
   LOG_LEVEL=DEBUG
   LLM_PROVIDER=openai
   DEIDENTIFY_ENABLED=False

Production Environment
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # .env.production
   LOG_LEVEL=WARNING
   LLM_PROVIDER=openai
   DEIDENTIFY_ENABLED=True
   COMPLIANCE_REGION=USA

Testing Environment
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # .env.test
   LOG_LEVEL=DEBUG
   LLM_PROVIDER=mock
   INPUT_PATH=tests/fixtures
   OUTPUT_PATH=tests/output

Best Practices
--------------

1. **Never commit `.env` files**: Add `.env` to `.gitignore`
2. **Use environment-specific configs**: Maintain separate configs for dev/test/prod
3. **Document custom settings**: Add comments explaining non-obvious settings
4. **Validate on startup**: Check that required settings are present
5. **Use secure secrets**: Store API keys and sensitive data securely

Troubleshooting
---------------

Common Configuration Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Missing API Keys**

Error: "LLM_API_KEY not found in environment"

Solution: Add your API key to the `.env` file

**Invalid Paths**

Error: "Input directory not found"

Solution: Ensure all paths in `config.py` exist and are accessible

**Database Connection Errors**

Error: "Cannot connect to ChromaDB"

Solution: Check `CHROMA_PERSIST_DIR` permissions and available disk space
