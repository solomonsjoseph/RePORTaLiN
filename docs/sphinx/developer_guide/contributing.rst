Contributing
============

We welcome contributions to RePORTaLiN! This guide will help you get started.

Getting Started
---------------

1. **Fork the Repository**

   Visit the GitHub repository and click "Fork"

2. **Clone Your Fork**

   .. code-block:: bash

      git clone https://github.com/YOUR_USERNAME/RePORTaLiN.git
      cd RePORTaLiN

3. **Set Up Development Environment**

   .. code-block:: bash

      # Create virtual environment
      python -m venv .venv
      source .venv/bin/activate  # On Windows: .venv\Scripts\activate
      
      # Install dependencies
      pip install -r requirements.txt

4. **Create a Branch**

   .. code-block:: bash

      git checkout -b feature/your-feature-name

Development Workflow
--------------------

Making Changes
~~~~~~~~~~~~~~

1. Make your changes in your feature branch
2. Follow the :ref:`coding-standards` below
3. Add or update tests as needed
4. Update documentation if needed
5. Ensure all tests pass

.. code-block:: bash

   # Run tests (if available)
   make test
   
   # Clean build artifacts
   make clean
   
   # Test the pipeline
   python main.py

Commit Guidelines
~~~~~~~~~~~~~~~~~

Use clear, descriptive commit messages:

.. code-block:: text

   # Good commit messages
   ✅ Add support for CSV output format
   ✅ Fix date conversion bug in extract_data.py
   ✅ Update documentation for configuration options
   ✅ Refactor table detection algorithm for clarity

   # Bad commit messages
   ❌ Update
   ❌ Fix bug
   ❌ Changes

Commit Message Format:

.. code-block:: text

   <type>: <subject>

   <body>

   <footer>

Types:

- ``feat``: New feature
- ``fix``: Bug fix
- ``docs``: Documentation changes
- ``style``: Code style changes (formatting, etc.)
- ``refactor``: Code refactoring
- ``test``: Adding or updating tests
- ``chore``: Maintenance tasks

Example:

.. code-block:: text

   feat: Add CSV export option
   
   - Add convert_to_csv() function in extract_data.py
   - Add --format csv command-line option
   - Update documentation with CSV examples
   
   Closes #42

.. _coding-standards:

Coding Standards
----------------

Python Style
~~~~~~~~~~~~

Follow PEP 8 guidelines:

- Use 4 spaces for indentation
- Max line length: 100 characters (flexible for readability)
- Use descriptive variable names
- Add docstrings to all public functions

Example:

.. code-block:: python

   def process_data(input_file: str, output_dir: str) -> dict:
       """
       Process a single data file.
       
       Args:
           input_file: Path to input Excel file
           output_dir: Directory for output JSONL file
       
       Returns:
           Dictionary with processing results
       
       Raises:
           FileNotFoundError: If input_file doesn't exist
       """
       # Implementation here
       pass

Documentation
~~~~~~~~~~~~~

Use Google-style docstrings:

.. code-block:: python

   def my_function(param1: str, param2: int = 0) -> bool:
       """
       Brief description of function.
       
       Longer description with more details about what the function
       does and why it exists.
       
       Args:
           param1 (str): Description of param1
           param2 (int, optional): Description of param2. Defaults to 0.
       
       Returns:
           bool: Description of return value
       
       Raises:
           ValueError: When param1 is empty
           TypeError: When param2 is negative
       
       Example:
           >>> result = my_function("test", 5)
           >>> print(result)
           True
       
       Note:
           Any important notes about usage
       
       See Also:
           :func:`related_function`: Related functionality
       """
       pass

Type Hints
~~~~~~~~~~

Use type hints for function parameters and return values:

.. code-block:: python

   from typing import List, Dict, Optional
   from pathlib import Path

   def find_files(
       directory: Path,
       pattern: str = "*.xlsx"
   ) -> List[Path]:
       """Find files matching pattern."""
       return list(directory.glob(pattern))

   def process_record(
       record: Dict[str, any],
       config: Optional[Dict] = None
   ) -> Dict[str, any]:
       """Process a single record."""
       pass

Code Organization
~~~~~~~~~~~~~~~~~

- One class/major function per file (for large implementations)
- Related utility functions can be grouped
- Keep functions focused (single responsibility)
- Limit function length (prefer < 50 lines)

Example structure:

.. code-block:: python

   # module.py
   """
   Module docstring explaining purpose.
   """
   
   import standard_library
   import third_party
   import local_modules
   
   # Constants
   MAX_RETRIES = 3
   DEFAULT_TIMEOUT = 30
   
   # Main functions
   def public_function():
       """Public API function."""
       pass
   
   def _private_helper():
       """Private helper function."""
       pass

Error Handling
~~~~~~~~~~~~~~

Use appropriate exception handling:

.. code-block:: python

   # Good: Specific exception handling
   try:
       data = read_file(path)
   except FileNotFoundError:
       log.error(f"File not found: {path}")
       raise
   except PermissionError:
       log.error(f"Permission denied: {path}")
       raise
   
   # Avoid: Generic catch-all
   try:
       data = read_file(path)
   except Exception as e:  # Too broad
       pass

Logging
~~~~~~~

Use the centralized logging system:

.. code-block:: python

   from scripts.utils import logging_utils as log
   
   # Use appropriate log levels
   log.debug("Detailed diagnostic information")
   log.info("General information")
   log.success("Operation completed successfully")
   log.warning("Warning message")
   log.error("Error occurred", exc_info=True)

Testing Guidelines
------------------

.. note::
   Automated unit tests are not currently implemented. Manual testing is required
   for all new functionality. See :doc:`testing` for manual testing strategies.

Manual Testing
~~~~~~~~~~~~~~

Test new functionality manually:

.. code-block:: python

   # Test your function interactively
   from scripts.my_module import my_function
   
   # Basic test
   result = my_function("input")
   print(f"Result: {result}")
   assert result == "expected", "Test failed"
   
   # Edge case test
   try:
       my_function("")
   except ValueError:
       print("ValueError raised as expected")
   
   # Test with options
   result = my_function("input", option=True)
   assert result is not None, "Result should not be None"
   print("All manual tests passed!")

Running the Pipeline
~~~~~~~~~~~~~~~~~~~~

Test integration by running the full pipeline:

.. code-block:: bash

   # Run complete pipeline
   python main.py
   
   # Run with de-identification
   python main.py --enable-deidentification --countries US
   
   # Check output files
   ls -la results/dataset/*/cleaned/
   ls -la results/data_dictionary_mappings/

Documentation
-------------

Updating Documentation
~~~~~~~~~~~~~~~~~~~~~~

When adding features, update:

1. **Code docstrings**: In the Python files
2. **User guide**: In ``docs/sphinx/user_guide/``
3. **Developer guide**: In ``docs/sphinx/developer_guide/``
4. **API docs**: Auto-generated from docstrings

Building Documentation
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cd docs/sphinx
   make clean
   make html
   
   # View documentation
   open _build/html/index.html

Pull Request Process
--------------------

1. **Update Your Branch**

   .. code-block:: bash

      git fetch upstream
      git rebase upstream/main

2. **Push to Your Fork**

   .. code-block:: bash

      git push origin feature/your-feature-name

3. **Create Pull Request**

   - Go to GitHub and create a pull request
   - Provide clear description of changes
   - Reference any related issues
   - Wait for review

4. **Address Review Comments**

   - Make requested changes
   - Push updates to your branch
   - Respond to reviewer questions

5. **Merge**

   - Once approved, your PR will be merged
   - Delete your feature branch after merge

Pull Request Template
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: markdown

   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Refactoring
   
   ## Changes Made
   - List of specific changes
   - Another change
   
   ## Testing
   - [ ] All existing tests pass
   - [ ] Added new tests for new functionality
   - [ ] Manually tested the changes
   
   ## Documentation
   - [ ] Updated code docstrings
   - [ ] Updated user documentation
   - [ ] Updated developer documentation
   
   ## Related Issues
   Closes #123

Code Review Guidelines
----------------------

For Reviewers
~~~~~~~~~~~~~

When reviewing code:

- Be respectful and constructive
- Focus on the code, not the person
- Explain the "why" behind suggestions
- Approve when code meets standards

For Authors
~~~~~~~~~~~

When receiving reviews:

- Be open to feedback
- Ask questions if unclear
- Don't take criticism personally
- Thank reviewers for their time

Areas of Contribution
---------------------

We welcome contributions in several areas:

Features
~~~~~~~~

- New output formats (CSV, Parquet, etc.)
- Database integration
- Parallel processing
- Data validation rules
- Custom transformation functions

Bug Fixes
~~~~~~~~~

- Check GitHub issues for bugs
- Fix and add tests to prevent regression
- Document the fix in commit message

Documentation
~~~~~~~~~~~~~

- Improve existing documentation
- Add examples and use cases
- Fix typos and clarify confusing sections
- Add troubleshooting tips

Testing
~~~~~~~

- Add test coverage
- Add edge case tests
- Improve test documentation

Performance
~~~~~~~~~~~

- Optimize slow operations
- Reduce memory usage
- Profile and benchmark changes

Questions?
----------

If you have questions:

1. Check existing documentation
2. Search GitHub issues
3. Ask in discussions
4. Open a new issue

Thank you for contributing to RePORTaLiN!

See Also
--------

- :doc:`architecture`: System architecture
- :doc:`testing`: Testing guide
- :doc:`extending`: Extending the pipeline
- GitHub: https://github.com/solomonsjoseph/RePORTaLiN
