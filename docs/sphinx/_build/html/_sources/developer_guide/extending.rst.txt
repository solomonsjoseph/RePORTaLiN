Extending RePORTaLiN
=====================

This guide explains how to extend and customize RePORTaLiN for your specific needs.

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
   from scripts.utils import logging_utils as log
   
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

   # In logging_utils.py or main.py
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
   from scripts.utils import logging_utils as log
   
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
   from scripts.utils import logging_utils as log
   
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
- :doc:`testing`: Testing guide
- :doc:`../api/modules`: API reference
