Testing
=======

This guide covers testing strategies and best practices for RePORTaLiN.

Overview
--------

RePORTaLiN uses a comprehensive testing approach with multiple levels:

1. **Manual Testing**: Running the pipeline on real data
2. **Integration Testing**: Testing module interactions
3. **Unit Testing**: Testing individual functions

Test Structure
--------------

Tests should be organized by module:

.. code-block:: text

   tests/
   ├── __init__.py
   ├── test_config.py              # Configuration tests
   ├── test_extract_data.py         # Data extraction tests
   ├── test_load_dictionary.py      # Dictionary loading tests
   ├── test_logging_utils.py        # Logging tests
   └── fixtures/                    # Test data
       ├── sample_data.xlsx
       └── sample_dictionary.xlsx

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

Unit Testing
------------

Test Configuration
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # tests/test_config.py
   import pytest
   from pathlib import Path
   import config
   
   def test_root_dir_exists():
       """Test that root directory is valid."""
       assert Path(config.ROOT_DIR).exists()
   
   def test_data_dir_path():
       """Test data directory path construction."""
       assert config.DATA_DIR.endswith("data")
   
   def test_dataset_detection():
       """Test automatic dataset detection."""
       assert config.DATASET_NAME is not None
       assert len(config.DATASET_NAME) > 0

Test Data Extraction
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # tests/test_extract_data.py
   import pytest
   import pandas as pd
   from scripts.extract_data import (
       clean_record_for_json,
       is_dataframe_empty,
       find_excel_files
   )
   
   def test_clean_record_for_json():
       """Test JSON serialization cleaning."""
       record = {
           'date': pd.Timestamp('2025-01-01'),
           'number': 42,
           'text': 'hello',
           'missing': pd.NA
       }
       
       cleaned = clean_record_for_json(record)
       
       assert cleaned['date'] == '2025-01-01 00:00:00'
       assert cleaned['number'] == 42
       assert cleaned['text'] == 'hello'
       assert cleaned['missing'] is None
   
   def test_is_dataframe_empty_true():
       """Test empty dataframe detection."""
       df = pd.DataFrame()
       assert is_dataframe_empty(df) is True
   
   def test_is_dataframe_empty_false():
       """Test non-empty dataframe."""
       df = pd.DataFrame({'a': [1, 2, 3]})
       assert is_dataframe_empty(df) is False
   
   def test_find_excel_files(tmp_path):
       """Test Excel file discovery."""
       # Create test files
       test_dir = tmp_path / "data"
       test_dir.mkdir()
       (test_dir / "file1.xlsx").touch()
       (test_dir / "file2.xlsx").touch()
       (test_dir / "not_excel.txt").touch()
       
       files = find_excel_files(test_dir)
       
       assert len(files) == 2
       assert all(f.endswith('.xlsx') for f in files)

Test Dictionary Loading
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # tests/test_load_dictionary.py
   import pytest
   import pandas as pd
   from scripts.load_dictionary import _deduplicate_columns
   
   def test_deduplicate_columns_no_duplicates():
       """Test column deduplication with unique columns."""
       columns = ['a', 'b', 'c']
       result = _deduplicate_columns(columns)
       assert result == ['a', 'b', 'c']
   
   def test_deduplicate_columns_with_duplicates():
       """Test column deduplication with duplicates."""
       columns = ['a', 'b', 'a', 'c', 'a']
       result = _deduplicate_columns(columns)
       assert result == ['a', 'b', 'a_2', 'c', 'a_3']
   
   def test_deduplicate_columns_mixed():
       """Test with unnamed columns and duplicates."""
       columns = ['a', 'Unnamed: 1', 'a', 'b']
       result = _deduplicate_columns(columns)
       assert 'a_2' in result

Test Logging
~~~~~~~~~~~~

.. code-block:: python

   # tests/test_logging_utils.py
   import pytest
   import logging
   from scripts.utils import logging_utils as log
   
   def test_success_level_exists():
       """Test that SUCCESS log level is defined."""
       assert hasattr(logging, 'SUCCESS')
       assert logging.SUCCESS == 25
   
   def test_logger_has_success_method():
       """Test that logger has success method."""
       logger = logging.getLogger('test')
       assert hasattr(logger, 'success')

Integration Testing
-------------------

Test End-to-End Workflow
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # tests/test_integration.py
   import pytest
   from pathlib import Path
   import json
   from scripts.extract_data import extract_excel_to_jsonl
   from scripts.load_dictionary import load_study_dictionary
   
   def test_full_pipeline(tmp_path):
       """Test complete pipeline with sample data."""
       # Set up test directories
       input_dir = tmp_path / "input"
       output_dir = tmp_path / "output"
       input_dir.mkdir()
       output_dir.mkdir()
       
       # Create sample Excel file
       import pandas as pd
       df = pd.DataFrame({
           'id': [1, 2, 3],
           'name': ['Alice', 'Bob', 'Charlie'],
           'age': [25, 30, 35]
       })
       excel_file = input_dir / "sample.xlsx"
       df.to_excel(excel_file, index=False)
       
       # Run extraction
       extract_excel_to_jsonl(str(input_dir), str(output_dir))
       
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
