scripts.utils subpackage
========================

.. automodule:: scripts.utils
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The ``utils`` subpackage provides utility functions used throughout RePORTaLiN,
with a focus on centralized logging infrastructure.

Modules
-------

logging_utils
~~~~~~~~~~~~~

.. automodule:: scripts.utils.logging_utils
   :members:
   :undoc-members:
   :show-inheritance:

Centralized logging system with custom SUCCESS level.

Custom Log Levels
-----------------

SUCCESS Level
~~~~~~~~~~~~~

The logging system adds a custom SUCCESS level:

.. code-block:: python

   # SUCCESS level is between INFO and WARNING
   logging.INFO = 20
   logging.SUCCESS = 25  # Custom
   logging.WARNING = 30

This level is used to highlight successful completion of major operations.

**Example**:

.. code-block:: python

   from scripts.utils import logging_utils as log
   
   log.info("Starting processing...")
   log.success("Processing completed successfully!")
   log.warning("Warning: some records skipped")
   log.error("Error occurred")

Logging Functions
-----------------

The module provides standard logging functions:

info
~~~~

.. code-block:: python

   log.info(message, *args, **kwargs)

Log an informational message.

**Example**:

.. code-block:: python

   log.info("Processing 43 files...")
   log.info(f"Found {count} records in {file}")

success
~~~~~~~

.. code-block:: python

   log.success(message, *args, **kwargs)

Log a success message (custom level).

**Example**:

.. code-block:: python

   log.success("Step 1: Data extraction completed successfully")
   log.success(f"Processed {total} records from {file_count} files")

warning
~~~~~~~

.. code-block:: python

   log.warning(message, *args, **kwargs)

Log a warning message.

**Example**:

.. code-block:: python

   log.warning("Empty dataframe detected, skipping file")
   log.warning(f"Duplicate column name: {col_name}")

error
~~~~~

.. code-block:: python

   log.error(message, *args, **kwargs)

Log an error message.

**Example**:

.. code-block:: python

   log.error("Failed to read Excel file", exc_info=True)
   log.error(f"File not found: {file_path}")

debug
~~~~~

.. code-block:: python

   log.debug(message, *args, **kwargs)

Log a debug message (only when LOG_LEVEL = DEBUG).

**Example**:

.. code-block:: python

   log.debug(f"Processing row {row_num}")
   log.debug(f"Column types: {df.dtypes}")

Logging Configuration
---------------------

Setup
~~~~~

The logging system is configured in ``config.py``:

.. code-block:: python

   # config.py
   import logging
   
   LOG_LEVEL = logging.INFO
   LOG_NAME = "reportalin"

Log File Format
~~~~~~~~~~~~~~~

Log files are created in ``.logs/`` with timestamps:

.. code-block:: text

   .logs/
   └── reportalin_YYYYMMDD_HHMMSS.log

Example log file: ``reportalin_20251002_143052.log``

Log Message Format
~~~~~~~~~~~~~~~~~~

Messages are formatted as:

.. code-block:: text

   YYYY-MM-DD HH:MM:SS - LEVEL - Message

Example:

.. code-block:: text

   2025-10-02 14:30:52 - INFO - Starting data extraction
   2025-10-02 14:30:52 - SUCCESS - Step 0 completed successfully
   2025-10-02 14:31:10 - WARNING - Empty dataframe in file 99B_FSB.xlsx
   2025-10-02 14:31:15 - ERROR - Failed to process file: permission denied

Output Handlers
---------------

The logging system uses two handlers:

Console Handler
~~~~~~~~~~~~~~~

- **Output**: stderr
- **Format**: Simple message format
- **Colors**: May use colors if terminal supports

File Handler
~~~~~~~~~~~~

- **Output**: Timestamped file in ``.logs/``
- **Format**: Full format with timestamp and level
- **Encoding**: UTF-8 for international characters

Usage Examples
--------------

Basic Logging
~~~~~~~~~~~~~

.. code-block:: python

   from scripts.utils import logging_utils as log
   
   def process_data():
       log.info("Starting data processing")
       
       try:
           # Process data
           result = do_processing()
           log.success("Processing completed successfully")
           return result
       
       except Exception as e:
           log.error(f"Processing failed: {e}", exc_info=True)
           raise

Structured Logging
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.utils import logging_utils as log
   
   log.info(f"Processing {file_count} files")
   
   for file in files:
       log.debug(f"Processing file: {file}")
       
       try:
           result = process_file(file)
           log.info(f"Processed {result['records']} records from {file}")
       
       except Exception as e:
           log.error(f"Failed to process {file}: {e}")

Conditional Logging
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.utils import logging_utils as log
   import logging
   
   # Only log if DEBUG level
   if log.getEffectiveLevel() <= logging.DEBUG:
       log.debug(f"Detailed state: {complex_object}")

Context Logging
~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.utils import logging_utils as log
   
   def process_with_context(file):
       log.info(f"--- Processing {file} ---")
       
       try:
           result = do_processing(file)
           log.success(f"Completed {file}: {result['records']} records")
       
       except Exception as e:
           log.error(f"Error in {file}: {e}", exc_info=True)
       
       finally:
           log.info(f"--- Finished {file} ---")

Logging Best Practices
----------------------

1. **Use Appropriate Levels**:

   .. code-block:: python

      log.debug("Detailed diagnostic info")      # Development
      log.info("General progress updates")       # Normal operation
      log.success("Major milestones")            # Success confirmation
      log.warning("Potential issues")            # Non-critical problems
      log.error("Errors requiring attention")    # Critical problems

2. **Include Context**:

   .. code-block:: python

      # Good: Includes context
      log.error(f"Failed to read {file}: {error}")
      
      # Bad: Missing context
      log.error("Failed to read file")

3. **Use Exceptions**:

   .. code-block:: python

      # Include exception details
      try:
          process_file(file)
      except Exception as e:
          log.error(f"Error processing {file}", exc_info=True)

4. **Don't Over-Log**:

   .. code-block:: python

      # Good: Log summary
      log.info(f"Processed {count} records")
      
      # Bad: Log every record
      for record in records:
          log.info(f"Processing record {record['id']}")  # Too verbose

See Also
--------

:mod:`config`
   Configuration including LOG_LEVEL

:doc:`../user_guide/usage`
   Usage examples with logging

:doc:`../developer_guide/contributing`
   Logging guidelines for contributors
