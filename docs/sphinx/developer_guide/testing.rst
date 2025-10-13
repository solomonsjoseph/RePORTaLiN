Testing
=======

This guide covers testing strategies and best practices for RePORTaLiN.

Overview
--------

RePORTaLiN currently uses manual testing approaches for validation:

1. **Manual Testing**: Running the pipeline on real data
2. **Integration Testing**: Testing module interactions manually
3. **Validation Testing**: Verifying de-identification output

.. note::
   Automated unit tests are not currently implemented. Future versions may include
   a comprehensive automated testing suite using pytest.

Manual Testing
--------------

Basic Pipeline Test
~~~~~~~~~~~~~~~~~~~

Test the full pipeline with real data:

.. code-block:: bash

   # Run complete pipeline
   python main.py
   
   # Check outputs
   ls -la results/dataset/*/original/
   ls -la results/dataset/*/cleaned/
   ls -la results/data_dictionary_mappings/
   
   # Check deidentified outputs (if enabled)
   ls -la results/deidentified/*/original/
   ls -la results/deidentified/*/cleaned/
   ls -la results/deidentified/mappings/
   
   # Check logs
   cat .logs/reportalin_*.log

Partial Pipeline Test
~~~~~~~~~~~~~~~~~~~~~~

Test individual steps:

.. code-block:: bash

   # Test only dictionary loading
   python main.py --skip-extraction
   
   # Test only data extraction
   python main.py --skip-dictionary

Single File Test
~~~~~~~~~~~~~~~~

Test with a single file:

.. code-block:: python

   from scripts.extract_data import process_excel_file
   from pathlib import Path
   
   test_file = Path("data/dataset/Indo-vap/10_TST.xlsx")
   output_dir = Path("test_output")
   output_dir.mkdir(exist_ok=True)
   
   result = process_excel_file(str(test_file), str(output_dir))
   print(f"Processed {result.get('records', 0)} records")

Testing Individual Components
------------------------------

Test Configuration Module
~~~~~~~~~~~~~~~~~~~~~~~~~~

Verify configuration is correctly loaded:

.. code-block:: python

   import config
   from pathlib import Path
   
   # Verify paths exist
   assert Path(config.ROOT_DIR).exists()
   assert Path(config.DATA_DIR).exists()
   
   # Verify dataset detection
   print(f"Dataset: {config.DATASET_NAME}")
   print(f"Input: {config.DATASET_DIR}")
   print(f"Output: {config.CLEAN_DATASET_DIR}")

Test Data Extraction Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test individual functions in the extract_data module:

.. code-block:: python

   import pandas as pd
   from scripts.extract_data import (
       clean_record_for_json,
       is_dataframe_empty,
       find_excel_files
   )
   
   # Test JSON serialization cleaning
   record = {
       'date': pd.Timestamp('2025-01-01'),
       'number': 42,
       'text': 'hello',
       'missing': pd.NA
   }
   cleaned = clean_record_for_json(record)
   print(f"Cleaned record: {cleaned}")
   
   # Test empty dataframe detection
   empty_df = pd.DataFrame()
   full_df = pd.DataFrame({'a': [1, 2, 3]})
   print(f"Empty: {is_dataframe_empty(empty_df)}")  # Should be True
   print(f"Full: {is_dataframe_empty(full_df)}")    # Should be False
   
   # Test Excel file discovery
   files = find_excel_files("data/dataset/Indo-vap_csv_files")
   print(f"Found {len(files)} Excel files")

Test Dictionary Loading
~~~~~~~~~~~~~~~~~~~~~~~

Test the dictionary loading module:

.. code-block:: python

   from scripts.load_dictionary import _deduplicate_columns
   
   # Test column deduplication with unique columns
   columns1 = ['a', 'b', 'c']
   result1 = _deduplicate_columns(columns1)
   print(f"Unique columns: {result1}")  # ['a', 'b', 'c']
   
   # Test column deduplication with duplicates
   columns2 = ['a', 'b', 'a', 'c', 'a']
   result2 = _deduplicate_columns(columns2)
   print(f"Deduplicated: {result2}")  # ['a', 'b', 'a_1', 'c', 'a_2']

Test Logging System
~~~~~~~~~~~~~~~~~~~

Verify the logging system works correctly:

.. code-block:: python

   from scripts.utils import logging_utils as log
   import logging
   
   # Setup logger
   log.setup_logger(name="test_logger", log_level=logging.DEBUG)
   
   # Test all log levels
   log.debug("Debug message")
   log.info("Info message")
   log.success("Success message")  # Custom SUCCESS level
   log.warning("Warning message")
   log.error("Error message")
   
   # Verify log file was created
   import os
   log_files = os.listdir(".logs/")
   print(f"Log files: {log_files}")

Integration Testing
-------------------

Test Complete Workflow
~~~~~~~~~~~~~~~~~~~~~~

Test the full pipeline with sample data:
       
       # Verify output
       jsonl_file = output_dir / "sample.jsonl"
       assert jsonl_file.exists()
       
       # Read and verify content
       with open(jsonl_file, 'r') as f:
           records = [json.loads(line) for line in f]
       
       assert len(records) == 3
       assert records[0]['name'] == 'Alice'

Test with Edge Cases
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def test_empty_excel_file(tmp_path):
       """Test handling of empty Excel file."""
       input_dir = tmp_path / "input"
       output_dir = tmp_path / "output"
       input_dir.mkdir()
       output_dir.mkdir()
       
       # Create empty DataFrame
       df = pd.DataFrame()
       excel_file = input_dir / "empty.xlsx"
       df.to_excel(excel_file, index=False)
       
       # Run extraction (should not create output file)
       extract_excel_to_jsonl(str(input_dir), str(output_dir))
       
       jsonl_file = output_dir / "empty.jsonl"
       # File should not be created for empty DataFrame
       assert not jsonl_file.exists()

Test Fixtures
-------------

Creating Test Data
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # tests/conftest.py
   import pytest
   import pandas as pd
   from pathlib import Path
   
   @pytest.fixture
   def sample_dataframe():
       """Create sample DataFrame for testing."""
       return pd.DataFrame({
           'id': [1, 2, 3],
           'name': ['Alice', 'Bob', 'Charlie'],
           'date': pd.to_datetime(['2025-01-01', '2025-01-02', '2025-01-03']),
           'value': [10.5, 20.3, 30.1]
       })
   
   @pytest.fixture
   def temp_excel_file(tmp_path, sample_dataframe):
       """Create temporary Excel file."""
       excel_file = tmp_path / "test.xlsx"
       sample_dataframe.to_excel(excel_file, index=False)
       return excel_file
   
   @pytest.fixture
   def temp_output_dir(tmp_path):
       """Create temporary output directory."""
       output_dir = tmp_path / "output"
       output_dir.mkdir()
       return output_dir

Using Fixtures
~~~~~~~~~~~~~~

.. code-block:: python

   def test_with_fixtures(temp_excel_file, temp_output_dir):
       """Test using fixtures."""
       from scripts.extract_data import process_excel_file
       
       result = process_excel_file(
           str(temp_excel_file),
           str(temp_output_dir)
       )
       
       assert result is not None
       assert result['records'] == 3

Running Tests
-------------

Using pytest
~~~~~~~~~~~~

.. code-block:: bash

   # Install pytest if not already installed
   pip install pytest pytest-cov
   
   # Run all tests
   pytest tests/
   
   # Run specific test file
   pytest tests/test_extract_data.py
   
   # Run specific test
   pytest tests/test_extract_data.py::test_clean_record_for_json
   
   # Run with verbose output
   pytest -v tests/
   
   # Run with coverage report
   pytest --cov=scripts --cov-report=html tests/

Using Make
~~~~~~~~~~

.. code-block:: bash

   # If Makefile has test target
   make test

Test Coverage
-------------

Measuring Coverage
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Generate coverage report
   pytest --cov=scripts --cov-report=html tests/
   
   # View report
   open htmlcov/index.html

Coverage Goals
~~~~~~~~~~~~~~

Aim for:

- **Overall coverage**: > 80%
- **Critical functions**: 100%
- **Error handling**: Test all error paths

Mock Testing
------------

Mocking External Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from unittest.mock import Mock, patch
   
   @patch('scripts.extract_data.pd.read_excel')
   def test_with_mock_excel(mock_read_excel, sample_dataframe):
       """Test with mocked Excel reading."""
       # Set up mock
       mock_read_excel.return_value = sample_dataframe
       
       # Run test
       from scripts.extract_data import process_excel_file
       result = process_excel_file("fake_file.xlsx", "output")
       
       # Verify mock was called
       mock_read_excel.assert_called_once()

Performance Testing
-------------------

Benchmark Tests
~~~~~~~~~~~~~~~

.. code-block:: python

   import time
   import pytest
   
   def test_extraction_performance(temp_excel_file, temp_output_dir):
       """Test extraction performance."""
       from scripts.extract_data import process_excel_file
       
       start_time = time.time()
       process_excel_file(str(temp_excel_file), str(temp_output_dir))
       elapsed = time.time() - start_time
       
       # Should complete in less than 1 second for small files
       assert elapsed < 1.0

Memory Testing
~~~~~~~~~~~~~~

.. code-block:: python

   import tracemalloc
   
   def test_memory_usage():
       """Test memory usage during extraction."""
       tracemalloc.start()
       
       # Run operation
       from scripts.extract_data import extract_excel_to_jsonl
       extract_excel_to_jsonl(input_dir, output_dir)
       
       current, peak = tracemalloc.get_traced_memory()
       tracemalloc.stop()
       
       # Peak memory should be reasonable (< 500 MB for example)
       assert peak < 500 * 1024 * 1024

Continuous Integration
----------------------

GitHub Actions Example
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # .github/workflows/tests.yml
   name: Tests
   
   on: [push, pull_request]
   
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         
         - name: Set up Python
           uses: actions/setup-python@v2
           with:
             python-version: '3.13'
         
         - name: Install dependencies
           run: |
             pip install -r requirements.txt
             pip install pytest pytest-cov
         
         - name: Run tests
           run: pytest --cov=scripts tests/
         
         - name: Upload coverage
           uses: codecov/codecov-action@v1

Best Practices
--------------

1. **Test Isolation**
   
   Each test should be independent:
   
   .. code-block:: python
   
      # Good: Uses fixtures
      def test_function(temp_dir):
          result = my_function(temp_dir)
          assert result
   
      # Bad: Depends on previous test
      def test_function():
          result = my_function(GLOBAL_DIR)
          assert result

2. **Test Naming**
   
   Use descriptive names:
   
   .. code-block:: python
   
      # Good
      def test_extract_data_with_empty_dataframe():
          pass
   
      # Bad
      def test1():
          pass

3. **Arrange-Act-Assert**
   
   Structure tests clearly:
   
   .. code-block:: python
   
      def test_my_function():
          # Arrange: Set up test data
          input_data = create_test_data()
          
          # Act: Execute function
          result = my_function(input_data)
          
          # Assert: Verify results
          assert result == expected

4. **Test Documentation**
   
   Document what's being tested:
   
   .. code-block:: python
   
      def test_extract_handles_special_characters():
          """
          Test that extraction correctly handles special characters
          in column names and data values.
          """
          pass

See Also
--------

- :doc:`contributing`: Contributing guidelines
- :doc:`architecture`: System architecture
- pytest documentation: https://docs.pytest.org/
