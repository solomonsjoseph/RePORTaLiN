Extending RePORTaLiN
=====================

This guide explains how to extend and customize RePORTaLiN for your specific needs.

.. versionchanged:: 0.0.3
   Added configuration module utilities (``ensure_directories()``, ``validate_config()``).
   See `Working with Configuration Module`_ for new features.

.. versionchanged:: 0.0.4
   Logging module enhanced with better type hints, optimized performance, and explicit public API.

.. versionchanged:: 0.0.7
   Data extraction module enhanced with explicit public API (6 exports), comprehensive usage examples,
   and verified type safety. See `Working with Data Extraction Module`_ for public API details.

.. versionchanged:: 0.0.8
   Data dictionary module enhanced with explicit public API (2 exports), comprehensive usage examples,
   and algorithm documentation. See `Working with Data Dictionary Module`_ for public API details.

Working with Data Dictionary Module
------------------------------------

.. versionadded:: 0.0.8

The ``scripts/load_dictionary.py`` module provides a well-defined public API for processing data dictionary Excel files.

Using the Public API
~~~~~~~~~~~~~~~~~~~~

The module exports 2 functions via ``__all__``:

1. **load_study_dictionary** - High-level function using config defaults
2. **process_excel_file** - Low-level function for custom workflows

**Best Practice: Use the public API**

.. code-block:: python

   # Recommended: Use public API
   from scripts.load_dictionary import (
       load_study_dictionary,
       process_excel_file
   )
   
   # High-level usage with config defaults
   success = load_study_dictionary()
   
   # Custom file processing
   success = process_excel_file(
       excel_path="data/custom_dictionary.xlsx",
       output_dir="results/custom_output",
       preserve_na=True
   )

**Extending with Custom Processing**

.. code-block:: python

   from scripts.load_dictionary import process_excel_file
   import pandas as pd
   
   def custom_dictionary_processor(
       excel_path: str,
       output_dir: str,
       custom_validation: callable = None
   ) -> bool:
       """Process dictionary with custom validation."""
       
       # Process with standard function
       success = process_excel_file(excel_path, output_dir)
       
       if success and custom_validation:
           # Apply custom post-processing
           custom_validation(output_dir)
       
       return success
   
   # Use custom processor
   def validate_output(output_dir: str):
       """Custom validation logic."""
       print(f"Validating output in {output_dir}")
       # Add your validation logic here
   
   custom_dictionary_processor(
       "data/dictionary.xlsx",
       "results/output",
       validate_output
   )

**Understanding Multi-Table Detection**

The module's table detection algorithm:

1. Identifies horizontal strips (separated by empty rows)
2. Within each strip, identifies vertical sections (separated by empty columns)
3. Extracts each non-empty section as a separate table
4. Deduplicates column names by appending numeric suffixes
5. Checks for "ignore below" markers and segregates subsequent tables
6. Adds metadata fields (``__sheet__``, ``__table__``)
7. Saves to JSONL with proper directory structure

**Type Safety Benefits**

The module has return type hints on all functions:

- All functions have return type annotations
- IDEs provide better autocomplete and error detection
- Static analysis tools can verify return types
- Documentation is clear about expected outputs

See :doc:`../api/scripts.load_dictionary` for complete API reference.

Working with Data Extraction Module
------------------------------------

.. versionadded:: 0.0.7

The ``scripts/extract_data.py`` module provides a well-defined public API for Excel to JSONL conversion.

Using the Public API
~~~~~~~~~~~~~~~~~~~~

The module exports 6 functions via ``__all__``:

1. **extract_excel_to_jsonl** - Batch process all Excel files
2. **process_excel_file** - Process a single Excel file
3. **find_excel_files** - Find Excel files in a directory
4. **convert_dataframe_to_jsonl** - Convert DataFrame to JSONL
5. **clean_record_for_json** - Clean record for JSON serialization
6. **clean_duplicate_columns** - Remove duplicate columns

**Best Practice: Use the public API**

.. code-block:: python

   # Recommended: Use public API
   from scripts.extract_data import (
       extract_excel_to_jsonl,
       process_excel_file,
       find_excel_files
   )
   
   # Batch processing
   extract_excel_to_jsonl(
       input_dir="data/dataset/Indo-vap",
       output_dir="results/dataset/Indo-vap"
   )
   
   # Single file processing
   result = process_excel_file(
       "data/file.xlsx",
       "results/output"
   )
   print(f"Processed {result['records']} records")

**Extending with Custom Conversions**

.. code-block:: python

   import pandas as pd
   from scripts.extract_data import (
       clean_record_for_json,
       convert_dataframe_to_jsonl
   )
   
   def custom_dataframe_processor(df: pd.DataFrame) -> pd.DataFrame:
       """Apply custom transformations before conversion."""
       # Custom logic here
       df = df.dropna(subset=['required_column'])
       df['new_column'] = df['old_column'] * 2
       return df
   
   # Use with standard conversion
   df = pd.read_excel("input.xlsx")
   df = custom_dataframe_processor(df)
   convert_dataframe_to_jsonl(df, "output.jsonl", "input.xlsx")

**Type Safety Benefits**

The module has complete type hint coverage:

- All functions have parameter and return type annotations
- IDEs provide better autocomplete and error detection
- Static analysis tools (mypy, pyright) can verify correctness
- Documentation is clear about expected inputs/outputs

See :doc:`../api/scripts.extract_data` for complete API reference.

Working with Configuration Module
----------------------------------

.. versionadded:: 0.0.3

The enhanced ``config.py`` module provides utilities for robust configuration management.

Using Configuration Utilities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Best Practice: Validate at startup**

.. code-block:: python

   # main.py or your script
   
   from config import validate_config, ensure_directories
   import logging
   
   def main():
       # Validate configuration first
       warnings = validate_config()
       if warnings:
           logging.warning("Configuration issues detected:")
           for warning in warnings:
               logging.warning(f"  {warning}")
       
       # Ensure directories exist
       ensure_directories()
       
       # Continue with your pipeline...

**Adding Custom Configuration Validation**

.. code-block:: python

   # custom_validator.py
   
   from typing import List
   from config import validate_config
   import os
   
   def validate_custom_config() -> List[str]:
       """Extend configuration validation with custom checks."""
       warnings = validate_config()  # Get base warnings
       
       # Add custom checks
       custom_paths = [
           "/path/to/custom/resource",
           "/path/to/another/file"
       ]
       
       for path in custom_paths:
           if not os.path.exists(path):
               warnings.append(f"Custom resource not found: {path}")
       
       return warnings

**Using Constants in Extensions**

.. code-block:: python

   from config import DEFAULT_DATASET_NAME, DATASET_SUFFIXES
   
   def process_dataset(folder_name: str = None):
       """Process a dataset with fallback to default."""
       name = folder_name or DEFAULT_DATASET_NAME
       print(f"Processing dataset: {name}")
       
   # Check if folder has recognized suffix
   def has_dataset_suffix(folder_name: str) -> bool:
       """Check if folder name has a dataset suffix."""
       return any(folder_name.endswith(suffix) for suffix in DATASET_SUFFIXES)

Adding New Output Formats
--------------------------

Example: Adding CSV Export
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Create the conversion function**:

.. code-block:: python

   # scripts/extract_data.py
   
   def convert_dataframe_to_csv(
       df: pd.DataFrame,
       output_file: str,
       **kwargs
   ) -> None:
       """
       Convert DataFrame to CSV format.
       
       Args:
           df: DataFrame to convert
           output_file: Path to output CSV file
           **kwargs: Additional arguments for to_csv()
       """
       df.to_csv(output_file, index=False, **kwargs)

2. **Add command-line option**:

.. code-block:: python

   # main.py
   
   def main():
       parser = argparse.ArgumentParser()
       parser.add_argument(
           '--format',
           choices=['jsonl', 'csv', 'parquet'],
           default='jsonl',
           help='Output format'
       )
       args = parser.parse_args()
       
       # Use format in extraction
       if args.format == 'csv':
           extract_excel_to_csv(...)
       elif args.format == 'jsonl':
           extract_excel_to_jsonl(...)

3. **Update documentation**:

Add usage examples and update user guide.

Adding Data Transformations
----------------------------

Example: Adding Data Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # scripts/validators.py
   
   from typing import List, Dict
   import pandas as pd
   from scripts.utils import logging as log
   
   class DataValidator:
       """Validate data against rules."""
       
       def __init__(self, rules: Dict[str, any]):
           """
           Initialize validator with rules.
           
           Args:
               rules: Dictionary of validation rules
           """
           self.rules = rules
       
       def validate_dataframe(self, df: pd.DataFrame) -> List[str]:
           """
           Validate DataFrame against rules.
           
           Args:
               df: DataFrame to validate
           
           Returns:
               List of validation errors
           """
           errors = []
           
           # Check required columns
           if 'required_columns' in self.rules:
               missing = set(self.rules['required_columns']) - set(df.columns)
               if missing:
                   errors.append(f"Missing columns: {missing}")
           
           # Check data types
           if 'column_types' in self.rules:
               for col, dtype in self.rules['column_types'].items():
                   if col in df.columns:
                       if not pd.api.types.is_dtype_equal(df[col].dtype, dtype):
                           errors.append(
                               f"Column {col} has wrong type: "
                               f"{df[col].dtype} (expected {dtype})"
                           )
           
           # Check value ranges
           if 'value_ranges' in self.rules:
               for col, (min_val, max_val) in self.rules['value_ranges'].items():
                   if col in df.columns:
                       if df[col].min() < min_val or df[col].max() > max_val:
                           errors.append(
                               f"Column {col} has values outside range "
                               f"[{min_val}, {max_val}]"
                           )
           
           return errors

**Usage**:

.. code-block:: python

   # In extract_data.py
   from scripts.validators import DataValidator
   
   def process_excel_file_with_validation(input_file, output_dir, rules):
       """Process file with validation."""
       df = pd.read_excel(input_file)
       
       # Validate
       validator = DataValidator(rules)
       errors = validator.validate_dataframe(df)
       
       if errors:
           log.warning(f"Validation errors in {input_file}:")
           for error in errors:
               log.warning(f"  - {error}")
       
       # Continue with extraction
       convert_dataframe_to_jsonl(df, output_file, input_file)

Adding Custom Logging
----------------------

.. versionchanged:: 0.0.4
   Logging module enhanced with better type hints, optimized performance, and explicit public API.

Understanding the Logging Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``scripts.utils.logging`` module provides a robust logging infrastructure with:

- **Thread-safe**: No shared mutable state
- **Optimized**: No unnecessary record copying
- **Type-safe**: Comprehensive type hints throughout
- **Well-defined API**: Explicit ``__all__`` declaration

**Public API** (v0.0.4):

.. code-block:: python

   from scripts.utils.logging import (
       # Setup functions (3)
       setup_logger,      # Initialize logging system
       get_logger,        # Get logger instance
       get_log_file_path, # Get current log file path
       
       # Logging functions (6)
       debug,             # Log debug messages
       info,              # Log info messages
       warning,           # Log warnings
       error,             # Log errors
       critical,          # Log critical errors
       success,           # Log success messages (custom level)
       
       # Constants (1)
       SUCCESS,           # SUCCESS level constant (25)
   )

Best Practices for Extensions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Use the public API only**:

   .. code-block:: python

      # Good: Use public API
      from scripts.utils.logging import info, success, error
      
      info("Processing data")
      success("Processing complete")
      
      # Avoid: Don't access private internals
      from scripts.utils.logging import _logger  # Don't do this

2. **Don't mutate log records**:

   .. code-block:: python

      # Good: Create custom formatter without mutation
      class MyFormatter(logging.Formatter):
          def format(self, record: logging.LogRecord) -> str:
              # Don't modify record; work with formatted string
              formatted = super().format(record)
              return f"[CUSTOM] {formatted}"
      
      # Bad: Mutating record (not thread-safe)
      class BadFormatter(logging.Formatter):
          def format(self, record: logging.LogRecord) -> str:
              record.msg = f"[CUSTOM] {record.msg}"  # Don't mutate!
              return super().format(record)

3. **Use proper exception handling**:

   .. code-block:: python

      from scripts.utils.logging import error, info
      
      try:
          risky_operation()
          info("Operation completed")
      except ValueError as e:
          error(f"Invalid value: {e}", exc_info=True)
      except Exception as e:
          error(f"Unexpected error: {e}", exc_info=True)
          raise

Example: Adding Email Notifications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # scripts/utils/notifications.py
   
   import smtplib
   from email.mime.text import MIMEText
   from email.mime.multipart import MIMEMultipart
   import logging
   
   class EmailHandler(logging.Handler):
       """Send log messages via email."""
       
       def __init__(
           self,
           smtp_server: str,
           from_addr: str,
           to_addrs: list,
           subject: str = "RePORTaLiN Log"
       ):
           """
           Initialize email handler.
           
           Args:
               smtp_server: SMTP server address
               from_addr: Sender email address
               to_addrs: List of recipient addresses
               subject: Email subject line
           """
           super().__init__()
           self.smtp_server = smtp_server
           self.from_addr = from_addr
           self.to_addrs = to_addrs
           self.subject = subject
       
       def emit(self, record):
           """Send log record via email."""
           try:
               msg = MIMEMultipart()
               msg['From'] = self.from_addr
               msg['To'] = ', '.join(self.to_addrs)
               msg['Subject'] = f"{self.subject} - {record.levelname}"
               
               body = self.format(record)
               msg.attach(MIMEText(body, 'plain'))
               
               server = smtplib.SMTP(self.smtp_server)
               server.send_message(msg)
               server.quit()
           except Exception as e:
               # Don't let email failure crash the app
               print(f"Failed to send email: {e}")

**Usage**:

.. code-block:: python

   # In logging.py or main.py
   from scripts.utils.notifications import EmailHandler
   
   # Add email handler for errors
   email_handler = EmailHandler(
       smtp_server='smtp.example.com',
       from_addr='reportalin@example.com',
       to_addrs=['admin@example.com'],
       subject='RePORTaLiN Error'
   )
   email_handler.setLevel(logging.ERROR)
   logger.addHandler(email_handler)

Adding Database Support
------------------------

Example: PostgreSQL Output
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # scripts/database.py
   
   import pandas as pd
   from sqlalchemy import create_engine
   from typing import Optional
   from scripts.utils import logging as log
   
   class DatabaseExporter:
       """Export data to database."""
       
       def __init__(self, connection_string: str):
           """
           Initialize database connection.
           
           Args:
               connection_string: SQLAlchemy connection string
           """
           self.engine = create_engine(connection_string)
       
       def export_dataframe(
           self,
           df: pd.DataFrame,
           table_name: str,
           if_exists: str = 'append'
       ) -> int:
           """
           Export DataFrame to database table.
           
           Args:
               df: DataFrame to export
               table_name: Target table name
               if_exists: What to do if table exists ('append', 'replace', 'fail')
           
           Returns:
               Number of rows exported
           """
           try:
               df.to_sql(
                   table_name,
                   self.engine,
                   if_exists=if_exists,
                   index=False
               )
               log.success(f"Exported {len(df)} rows to {table_name}")
               return len(df)
           except Exception as e:
               log.error(f"Failed to export to database: {e}")
               raise
       
       def close(self):
           """Close database connection."""
           self.engine.dispose()

**Usage**:

.. code-block:: python

   # In extract_data.py
   from scripts.database import DatabaseExporter
   
   def extract_to_database(input_dir, connection_string):
       """Extract data directly to database."""
       db = DatabaseExporter(connection_string)
       
       for excel_file in find_excel_files(input_dir):
           df = pd.read_excel(excel_file)
           table_name = Path(excel_file).stem
           db.export_dataframe(df, table_name)
       
       db.close()

Adding Parallel Processing
---------------------------

Example: Process Files in Parallel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # scripts/parallel.py
   
   from concurrent.futures import ProcessPoolExecutor, as_completed
   from typing import List, Callable
   from pathlib import Path
   from tqdm import tqdm
   from scripts.utils import logging as log
   
   def process_files_parallel(
       files: List[Path],
       process_func: Callable,
       max_workers: int = 4,
       **kwargs
   ) -> List[dict]:
       """
       Process files in parallel.
       
       Args:
           files: List of files to process
           process_func: Function to apply to each file
           max_workers: Maximum number of parallel workers
           **kwargs: Additional arguments for process_func
       
       Returns:
           List of results from processing each file
       """
       results = []
       
       with ProcessPoolExecutor(max_workers=max_workers) as executor:
           # Submit all tasks
           future_to_file = {
               executor.submit(process_func, file, **kwargs): file
               for file in files
           }
           
           # Process completed tasks
           with tqdm(total=len(files), desc="Processing files") as pbar:
               for future in as_completed(future_to_file):
                   file = future_to_file[future]
                   try:
                       result = future.result()
                       results.append(result)
                       log.info(f"Completed {file}")
                   except Exception as e:
                       log.error(f"Failed to process {file}: {e}")
                   finally:
                       pbar.update(1)
       
       return results

**Usage**:

.. code-block:: python

   # In extract_data.py
   from scripts.parallel import process_files_parallel
   
   def extract_excel_to_jsonl_parallel(input_dir, output_dir, max_workers=4):
       """Extract files in parallel."""
       files = find_excel_files(input_dir)
       
       results = process_files_parallel(
           files,
           process_excel_file,
           max_workers=max_workers,
           output_dir=output_dir
       )
       
       total_records = sum(r.get('records', 0) for r in results)
       log.success(f"Processed {len(results)} files, {total_records} records")

Adding Custom Table Detection
------------------------------

Example: Custom Split Logic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # scripts/custom_split.py
   
   import pandas as pd
   from typing import List, Tuple
   
   class CustomTableSplitter:
       """Custom table splitting logic."""
       
       def split_by_header_rows(
           self,
           df: pd.DataFrame,
           header_pattern: str
       ) -> List[pd.DataFrame]:
           """
           Split DataFrame at rows matching header pattern.
           
           Args:
               df: DataFrame to split
               header_pattern: Pattern to identify header rows
           
           Returns:
               List of DataFrames split at header rows
           """
           tables = []
           current_table = []
           
           for idx, row in df.iterrows():
               # Check if row matches header pattern
               if any(header_pattern in str(val) for val in row):
                   if current_table:
                       # Save previous table
                       tables.append(pd.DataFrame(current_table))
                       current_table = []
                   # Start new table with this row as header
                   current_table = [row]
               else:
                   current_table.append(row)
           
           # Add last table
           if current_table:
               tables.append(pd.DataFrame(current_table))
           
           return tables

Adding Plugin System
--------------------

Example: Plugin Architecture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # scripts/plugins.py
   
   from abc import ABC, abstractmethod
   from typing import Dict, List
   import importlib
   import os
   
   class ProcessorPlugin(ABC):
       """Base class for processor plugins."""
       
       @abstractmethod
       def process(self, df: pd.DataFrame) -> pd.DataFrame:
           """
           Process DataFrame.
           
           Args:
               df: Input DataFrame
           
           Returns:
               Processed DataFrame
           """
           pass
   
   class PluginManager:
       """Manage and load plugins."""
       
       def __init__(self, plugin_dir: str = "plugins"):
           """
           Initialize plugin manager.
           
           Args:
               plugin_dir: Directory containing plugins
           """
           self.plugin_dir = plugin_dir
           self.plugins: Dict[str, ProcessorPlugin] = {}
       
       def load_plugins(self):
           """Load all plugins from plugin directory."""
           if not os.path.exists(self.plugin_dir):
               return
           
           for file in os.listdir(self.plugin_dir):
               if file.endswith('.py') and not file.startswith('_'):
                   module_name = file[:-3]
                   try:
                       module = importlib.import_module(
                           f"{self.plugin_dir}.{module_name}"
                       )
                       # Look for Plugin class
                       if hasattr(module, 'Plugin'):
                           plugin = module.Plugin()
                           self.plugins[module_name] = plugin
                   except Exception as e:
                       print(f"Failed to load plugin {module_name}: {e}")
       
       def apply_plugins(
           self,
           df: pd.DataFrame,
           plugin_names: List[str] = None
       ) -> pd.DataFrame:
           """
           Apply plugins to DataFrame.
           
           Args:
               df: DataFrame to process
               plugin_names: List of plugin names to apply (None = all)
           
           Returns:
               Processed DataFrame
           """
           if plugin_names is None:
               plugin_names = self.plugins.keys()
           
           for name in plugin_names:
               if name in self.plugins:
                   df = self.plugins[name].process(df)
           
           return df

**Example Plugin**:

.. code-block:: python

   # plugins/normalize_names.py
   
   import pandas as pd
   from scripts.plugins import ProcessorPlugin
   
   class Plugin(ProcessorPlugin):
       """Normalize column names."""
       
       def process(self, df: pd.DataFrame) -> pd.DataFrame:
           """Normalize column names to lowercase with underscores."""
           df.columns = [
               col.lower().replace(' ', '_')
               for col in df.columns
           ]
           return df

**Usage**:

.. code-block:: python

   from scripts.plugins import PluginManager
   
   # Load and apply plugins
   manager = PluginManager()
   manager.load_plugins()
   
   df = pd.read_excel('data.xlsx')
   df = manager.apply_plugins(df, ['normalize_names'])

Configuration File Support
---------------------------

Example: YAML Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # scripts/config_loader.py
   
   import yaml
   from pathlib import Path
   from typing import Dict, Any
   
   class ConfigLoader:
       """Load configuration from YAML file."""
       
       def __init__(self, config_file: str = "config.yaml"):
           """
           Initialize config loader.
           
           Args:
               config_file: Path to configuration file
           """
           self.config_file = Path(config_file)
           self.config: Dict[str, Any] = {}
       
       def load(self) -> Dict[str, Any]:
           """
           Load configuration from file.
           
           Returns:
               Configuration dictionary
           """
           if self.config_file.exists():
               with open(self.config_file, 'r') as f:
                   self.config = yaml.safe_load(f)
           return self.config
       
       def get(self, key: str, default: Any = None) -> Any:
           """
           Get configuration value.
           
           Args:
               key: Configuration key (supports dot notation)
               default: Default value if key not found
           
           Returns:
               Configuration value
           """
           keys = key.split('.')
           value = self.config
           
           for k in keys:
               if isinstance(value, dict) and k in value:
                   value = value[k]
               else:
                   return default
           
           return value

**Example config.yaml**:

.. code-block:: yaml

   # config.yaml
   
   pipeline:
     input_dir: data/dataset/Indo-vap
     output_dir: results/dataset/Indo-vap
     
   processing:
     parallel: true
     max_workers: 4
     
   validation:
     enabled: true
     rules:
       required_columns:
         - id
         - date
       column_types:
         id: int64
         date: datetime64
   
   logging:
     level: INFO
     file: .logs/reportalin.log

Adding New Country Regulations
-------------------------------

RePORTaLiN supports country-specific data privacy regulations for de-identification. You can add support for new countries by extending the ``country_regulations`` module.

Example: Adding a New Country
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Define the regulation function**:

.. code-block:: python

   # scripts/utils/country_regulations.py
   
   def get_new_country_regulation() -> CountryRegulation:
       """New Country - Data Protection Act."""
       return CountryRegulation(
           country_code="XX",  # ISO 3166-1 alpha-2 code
           country_name="New Country",
           regulation_name="Data Protection Act",
           regulation_acronym="DPA",
           common_fields=get_common_fields(),
           specific_fields=[
               DataField(
                   name="national_id",
                   display_name="National ID Number",
                   field_type=DataFieldType.IDENTIFIER,
                   privacy_level=PrivacyLevel.CRITICAL,
                   required=False,
                   pattern=r'^\d{10}$',  # Regex pattern
                   description="10-digit National ID",
                   examples=["1234567890"],
                   country_specific=True
               ),
               DataField(
                   name="health_card",
                   display_name="Health Insurance Card",
                   field_type=DataFieldType.MEDICAL,
                   privacy_level=PrivacyLevel.CRITICAL,
                   required=False,
                   pattern=r'^HC-\d{8}$',
                   description="Health card number",
                   examples=["HC-12345678"],
                   country_specific=True
               ),
           ],
           description="Brief description of the regulation",
           requirements=[
               "Key requirement 1",
               "Key requirement 2",
               "Data protection impact assessment required",
               "Breach notification within X hours",
           ]
       )

2. **Register the country in the registry**:

.. code-block:: python

   # In CountryRegulationManager class
   _REGISTRY: Dict[str, callable] = {
       "US": get_us_regulation,
       "IN": get_india_regulation,
       # ... existing countries ...
       "XX": get_new_country_regulation,  # Add your country
   }

4. **Test the implementation**:
   }

4. **Update documentation**:

Add the new country to:
   - ``docs/sphinx/user_guide/country_regulations.rst``
   - ``README.md``
   - CLI help text in ``scripts/deidentify.py``

Field Types and Privacy Levels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When defining country-specific fields, use appropriate types:

**DataFieldType Options**:
   - ``PERSONAL_NAME``: First/last/middle names
   - ``IDENTIFIER``: National IDs, SSN, etc.
   - ``CONTACT``: Phone, email, address
   - ``DEMOGRAPHIC``: Age, gender, ethnicity
   - ``LOCATION``: City, state, postal code
   - ``MEDICAL``: Health card, MRN, insurance
   - ``FINANCIAL``: Tax IDs, bank accounts
   - ``BIOMETRIC``: Fingerprints, facial data
   - ``CUSTOM``: Other sensitive data

**PrivacyLevel Options** (1-5):
   - ``PUBLIC``: Publicly available information
   - ``LOW``: Low sensitivity (e.g., gender)
   - ``MEDIUM``: Medium sensitivity (e.g., city)
   - ``HIGH``: High sensitivity PII (e.g., phone)
   - ``CRITICAL``: Critical sensitive PII (e.g., SSN, health data)

Regex Pattern Guidelines
~~~~~~~~~~~~~~~~~~~~~~~~~

When defining detection patterns:

1. **Be Specific**: Avoid overly broad patterns that might cause false positives.

2. **Use Anchors**: Use ``^`` and ``$`` to match entire strings:

   .. code-block:: python
   
      pattern=r'^\d{3}-\d{2}-\d{4}$'  # US SSN
      pattern=r'^\d{12}$'              # Indian Aadhaar (without spaces)

3. **Handle Variations**: Account for different formats:

   .. code-block:: python
   
      # With or without separators
      pattern=r'^\d{3}-\d{2}-\d{4}$|^\d{9}$'
      
      # With or without spaces
      pattern=r'^\d{4}\s?\d{4}\s?\d{4}$'

4. **Use Character Classes**: Use ``\d`` for digits, ``[A-Z]`` for uppercase letters:

   .. code-block:: python
   
      pattern=r'^[A-Z]{2}\d{6}[A-D]$'  # UK National Insurance

5. **Test Thoroughly**: Test patterns with real and synthetic data:

   .. code-block:: python
   
      # Test the pattern
      import re
      pattern = re.compile(r'^\d{3}-\d{2}-\d{4}$')
      assert pattern.match("123-45-6789")
      assert not pattern.match("123456789")

Testing Your Country Regulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Unit Test**:

.. code-block:: python

   # test_country_regulations.py
   
   def test_new_country_regulation():
       """Test new country regulation."""
       manager = CountryRegulationManager(countries=["XX"])
       
       # Verify it loads
       assert "XX" in manager.regulations
       
       # Verify fields
       reg = manager.regulations["XX"]
       assert len(reg.specific_fields) > 0
       
       # Test detection patterns
       patterns = manager.get_detection_patterns()
       assert "national_id" in patterns

2. **Integration Test**:

.. code-block:: python

   def test_deidentification_with_new_country():
       """Test de-identification with new country."""
       config = DeidentificationConfig(
           countries=["XX"],
           enable_country_patterns=True,
           enable_encryption=False
       )
       
       engine = DeidentificationEngine(config=config)
       
       text = "Patient ID: 1234567890, Health Card: HC-12345678"
       deidentified = engine.deidentify_text(text)
       
       # Verify identifiers are removed
       assert "1234567890" not in deidentified
       assert "HC-12345678" not in deidentified

3. **Manual Testing**:

.. code-block:: bash

   # Test with command line
   python3 -m scripts.utils.country_regulations --countries XX --show-fields
   
   # Test de-identification with sample text
   python3 -c "from scripts.deidentify import DeidentificationEngine, DeidentificationConfig; \
   config = DeidentificationConfig(countries=['XX']); \
   engine = DeidentificationEngine(config=config); \
   print(engine.deidentify_text('Patient John Doe, ID: 1234567890'))"

Common Pitfalls
~~~~~~~~~~~~~~~

1. **Overlapping Patterns**: Ensure patterns don't conflict with other countries.

2. **Locale-Specific Formats**: Account for different date/number formats.

3. **Special Characters**: Properly escape regex special characters.

4. **Performance**: Avoid extremely complex regex patterns that slow processing.

5. **False Positives**: Test with diverse data to minimize false detections.

Regulatory Compliance Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When adding a new country:

1. **Research the Regulation**: Thoroughly understand the legal requirements.

2. **Consult Legal Experts**: Ensure your implementation meets legal standards.

3. **Document Requirements**: List all key requirements in the regulation object.

4. **Stay Updated**: Monitor for regulatory changes and updates.

5. **Provide References**: Link to official regulatory documentation.

.. warning::
   Adding country-specific regulations does not guarantee legal compliance. 
   Always consult with legal counsel familiar with the jurisdiction.

Best Practices for Extensions
------------------------------

1. **Follow Existing Patterns**
   
   Study existing code and follow the same patterns.

2. **Add Tests**
   
   Always add tests for new functionality.

3. **Update Documentation**
   
   Document new features in user and developer guides.

4. **Maintain Backward Compatibility**
   
   Don't break existing functionality.

5. **Use Type Hints**
   
   Add type hints to all new functions.

6. **Log Appropriately**
   
   Use the centralized logging system.

7. **Handle Errors Gracefully**
   
   Don't let errors crash the pipeline.

See Also
--------

- :doc:`architecture`: System architecture
- :doc:`contributing`: Contributing guidelines
- :doc:`../api/modules`: API reference
