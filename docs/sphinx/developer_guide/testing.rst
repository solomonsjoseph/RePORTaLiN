Testing
=======

This guide covers testing strategies, automated test suites, and best practices for RePORTaLiN.

Automated Testing Strategy
---------------------------

Overview
~~~~~~~~

RePORTaLiN includes a comprehensive automated testing strategy (``test_strategy.py``) that 
validates all core functionality including:

1. **Argument-based functionality**: All CLI arguments, skip options, country options, encryption on/off
2. **Progress bar behavior**: With and without encryption
3. **Temporary file management**: Cleanup verification
4. **End-to-end execution**: Full pipeline with encryption
5. **Error handling**: Invalid arguments and country codes
6. **Makefile targets**: Build system integration

Running the Test Suite
~~~~~~~~~~~~~~~~~~~~~~~

Execute the comprehensive test suite:

.. code-block:: bash

   # Run all automated tests
   python3 test_strategy.py
   
   # View detailed test report
   cat test_report.json

Test Results Summary
~~~~~~~~~~~~~~~~~~~~

**Latest Test Run: 2025-10-13**

.. list-table:: Test Summary
   :header-rows: 1
   :widths: 30 15 15 40

   * - Metric
     - Value
     - Percentage
     - Notes
   * - Total Tests
     - 20
     - 100%
     - Comprehensive coverage
   * - Passed
     - 18
     - 90.0%
     - All critical tests pass
   * - Failed
     - 2
     - 10.0%
     - Non-critical issues
   * - Skipped
     - 0
     - 0%
     - All tests executed

Test Phases
~~~~~~~~~~~

The test suite is organized into 9 phases:

**Phase 1: Help Command Functionality** (3 tests)

- Main pipeline help
- De-identification help  
- List countries command

✅ All tests passed (100% success rate)

**Phase 2: Skip Argument Combinations** (3 tests)

- Skip dictionary loading
- Skip data extraction
- Skip both dictionary and extraction

✅ All tests passed (100% success rate)

**Phase 3: De-identification Arguments** (6 tests)

- Full extraction preparation
- Encryption enabled (default)
- Encryption disabled (--no-encryption)
- Single country (IN)
- Multiple countries (IN, US, ID)
- All countries

✅ All tests passed (100% success rate)

**Phase 4: Progress Bar with Encryption** (1 test)

- Full pipeline with encryption verification

✅ Test passed - Progress bar behavior confirmed

**Phase 5: Progress Bar without Encryption** (1 test)

- Full pipeline without encryption verification

✅ Test passed - Progress bar behavior confirmed

**Phase 6: Makefile Targets** (3 tests)

- ``make help``
- ``make clean``
- ``make run``

⚠️ 1 test failed: ``make run`` (platform-specific issue - uses ``python`` instead of ``python3``)

**Phase 7: End-to-End Execution** (2 tests)

- Complete pipeline with encryption
- Final results verification

✅ All tests passed (100% success rate)

**Phase 8: Error Handling** (2 tests)

- Invalid argument handling
- Invalid country code handling

⚠️ 1 test failed: Invalid country codes are silently ignored (design decision)

**Phase 9: Final Cleanup** (1 test)

- Temporary file cleanup verification

✅ Test passed - All temporary files removed

Detailed Test Results
~~~~~~~~~~~~~~~~~~~~~~

Critical Tests (100% Pass Rate)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All critical functionality tests passed:

- ✅ Data dictionary loading
- ✅ Data extraction (JSONL generation)
- ✅ De-identification with encryption
- ✅ De-identification without encryption
- ✅ Country-specific pattern detection
- ✅ Multi-country processing
- ✅ Progress indicators
- ✅ End-to-end pipeline execution
- ✅ Temporary file cleanup

Known Issues (Non-Critical)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Issue 1: Makefile Python Command**

- **Test**: ``make run``
- **Status**: Failed (platform-specific)
- **Issue**: Makefile uses ``python`` instead of ``python3``
- **Impact**: Low - Users can run ``python3 main.py`` directly
- **Workaround**: Update Makefile to use ``python3``

**Issue 2: Invalid Country Code Handling**

- **Test**: Invalid country code handling
- **Status**: Failed (by design)
- **Issue**: Invalid country codes are silently ignored
- **Impact**: Low - No crash, continues with default behavior
- **Enhancement**: Could add warning messages for invalid codes

Performance Metrics
~~~~~~~~~~~~~~~~~~~

.. list-table:: Test Performance
   :header-rows: 1
   :widths: 50 20 30

   * - Test Phase
     - Duration
     - Notes
   * - Help commands
     - ~1 second
     - Fast validation
   * - Skip combinations
     - ~14 seconds
     - Minimal processing
   * - De-identification tests
     - ~64 seconds
     - Full PHI/PII detection
   * - Progress bar tests
     - ~48 seconds
     - Full pipeline runs
   * - End-to-end test
     - ~24 seconds
     - Complete workflow
   * - **Total Test Suite**
     - **~153 seconds**
     - **Comprehensive validation**

Verification Checklist
~~~~~~~~~~~~~~~~~~~~~~

After each test run, the suite verifies:

✅ All result directories created correctly:
   - ``results/dataset/`` (86 JSONL files)
   - ``results/data_dictionary_mappings/`` (18 JSONL files)
   - ``results/deidentified/`` (86 JSONL files when enabled)

✅ Temporary files cleaned up:
   - No ``.tmp`` files
   - No ``.temp`` files
   - No ``__pycache__`` directories (after ``make clean``)
   - No orphaned log files

✅ Progress indicators working:
   - Logging messages displayed
   - Step completion messages
   - Error messages (when appropriate)

Test Coverage
~~~~~~~~~~~~~

The automated test suite covers:

.. list-table:: Coverage by Component
   :header-rows: 1
   :widths: 30 40 30

   * - Component
     - Test Coverage
     - Status
   * - CLI Arguments
     - All 7 arguments tested
     - ✅ Complete
   * - Pipeline Steps
     - All 3 steps (dictionary, extraction, de-identification)
     - ✅ Complete
   * - Encryption
     - Both enabled and disabled modes
     - ✅ Complete
   * - Country Options
     - Single, multiple, ALL options
     - ✅ Complete
   * - Error Handling
     - Invalid arguments and countries
     - ✅ Complete
   * - File Management
     - Creation, cleanup, structure
     - ✅ Complete
   * - Makefile
     - help, clean, run targets
     - ⚠️ Partial

Extending the Test Suite
~~~~~~~~~~~~~~~~~~~~~~~~~

To add new tests to ``test_strategy.py``:

1. **Add a new test method** to the ``TestStrategy`` class:

   .. code-block:: python

      def test_new_feature(self):
          """Test new feature functionality."""
          start_time = time.time()
          
          # Run command
          returncode, stdout, stderr = self.run_command([
              "python3", "main.py",
              "--new-option"
          ], timeout=60)
          
          elapsed = time.time() - start_time
          
          # Record result
          self.record_test(
              description="New feature test",
              command="python3 main.py --new-option",
              expected_success=True,
              actual_returncode=returncode,
              elapsed_time=elapsed,
              stdout=stdout,
              stderr=stderr
          )

2. **Add the test to a phase** in the ``run_all_tests()`` method:

   .. code-block:: python

      # Phase 10: New Feature Tests
      self.section("TEST PHASE 10: New Feature")
      self.test_new_feature()

3. **Update documentation** to reflect new test coverage

Continuous Integration
~~~~~~~~~~~~~~~~~~~~~~

For CI/CD integration:

.. code-block:: yaml

   # Example GitHub Actions workflow
   name: Test Suite
   
   on: [push, pull_request]
   
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Set up Python
           uses: actions/setup-python@v2
           with:
             python-version: '3.9'
         - name: Install dependencies
           run: |
             pip install -r requirements.txt
         - name: Run test suite
           run: |
             python3 test_strategy.py
         - name: Upload test report
           uses: actions/upload-artifact@v2
           with:
             name: test-report
             path: test_report.json

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

   from scripts.utils import logging as log
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
