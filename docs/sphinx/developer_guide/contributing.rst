Contributing
============

We welcome contributions to RePORTaLiN! This guide will help you get started.

Getting Started
---------------

Setting Up Your Development Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Fork the repository** on GitHub

2. **Clone your fork:**

   .. code-block:: bash

      git clone https://github.com/your-username/RePORTaLiN.git
      cd RePORTaLiN

3. **Add the upstream remote:**

   .. code-block:: bash

      git remote add upstream https://github.com/original-org/RePORTaLiN.git

4. **Create a virtual environment:**

   .. code-block:: bash

      python -m venv venv
      source venv/bin/activate  # On Windows: venv\\Scripts\\activate

5. **Install development dependencies:**

   .. code-block:: bash

      pip install -r requirements.txt
      pip install -r requirements-dev.txt

6. **Verify installation:**

   .. code-block:: bash

      python -c "import scripts; print('Setup successful!')"
      pytest --version

Development Workflow
--------------------

Creating a Feature Branch
~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Update your main branch:**

   .. code-block:: bash

      git checkout main
      git pull upstream main

2. **Create a feature branch:**

   .. code-block:: bash

      git checkout -b feature/your-feature-name

   Use prefixes:
   
   * ``feature/`` - New features
   * ``bugfix/`` - Bug fixes
   * ``docs/`` - Documentation changes
   * ``refactor/`` - Code refactoring
   * ``test/`` - Test additions/changes

Making Changes
~~~~~~~~~~~~~~

1. **Write your code** following the :ref:`coding-standards`

2. **Add tests** for new functionality

3. **Update documentation** as needed

4. **Run tests:**

   .. code-block:: bash

      pytest tests/

5. **Check code quality:**

   .. code-block:: bash

      # Format code
      black scripts/
      
      # Check linting
      flake8 scripts/
      
      # Type checking
      mypy scripts/

6. **Verify no errors:**

   .. code-block:: bash

      python -m py_compile scripts/**/*.py

Committing Changes
~~~~~~~~~~~~~~~~~~

1. **Stage your changes:**

   .. code-block:: bash

      git add .

2. **Commit with a descriptive message:**

   .. code-block:: bash

      git commit -m "Add feature: brief description
      
      - Detailed change 1
      - Detailed change 2
      
      Closes #123"

   Follow commit message conventions:
   
   * First line: Brief summary (<50 chars)
   * Blank line
   * Detailed description
   * Reference issues/PRs

3. **Push to your fork:**

   .. code-block:: bash

      git push origin feature/your-feature-name

Submitting a Pull Request
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Go to GitHub** and create a pull request from your fork to the main repository

2. **Fill out the PR template:**
   
   * Description of changes
   * Related issues
   * Testing performed
   * Screenshots (if applicable)

3. **Wait for review** and address any feedback

4. **Ensure CI passes** (tests, linting, docs)

.. _coding-standards:

Coding Standards
----------------

Python Style Guide
~~~~~~~~~~~~~~~~~~

Follow **PEP 8** with these specifics:

* Line length: 88 characters (Black default)
* Indentation: 4 spaces
* Imports: Organized with ``isort``
* Quotes: Double quotes for strings

Example:

.. code-block:: python

   """Module docstring.
   
   This module does XYZ.
   """
   
   from typing import Dict, List, Optional
   
   import pandas as pd
   
   from scripts.utils import helper_function
   
   
   def process_data(
       data: pd.DataFrame,
       config: Dict[str, str],
       validate: bool = True,
   ) -> pd.DataFrame:
       """Process the input data.
       
       Args:
           data: Input DataFrame to process.
           config: Configuration dictionary.
           validate: Whether to validate results.
       
       Returns:
           Processed DataFrame.
       
       Raises:
           ValueError: If data is empty.
       
       Example:
           >>> df = pd.DataFrame({"col1": [1, 2, 3]})
           >>> result = process_data(df, {"key": "value"})
           >>> len(result)
           3
       """
       if data.empty:
           raise ValueError("Data cannot be empty")
       
       # Processing logic
       result = data.copy()
       
       if validate:
           _validate_result(result)
       
       return result

Documentation Standards
~~~~~~~~~~~~~~~~~~~~~~~

**All public functions, classes, and modules must have Google-style docstrings:**

.. code-block:: python

   def function_name(param1: str, param2: int = 10) -> bool:
       """One-line summary.
       
       Detailed description of what the function does.
       Can span multiple lines.
       
       Args:
           param1: Description of param1.
           param2: Description of param2. Defaults to 10.
       
       Returns:
           Description of return value.
       
       Raises:
           ValueError: When param1 is empty.
           TypeError: When param2 is not an integer.
       
       Example:
           >>> result = function_name("test", 20)
           >>> print(result)
           True
       
       Note:
           Additional notes about usage, edge cases, etc.
       """

Type Hints
~~~~~~~~~~

Use type hints for all function signatures:

.. code-block:: python

   from typing import Dict, List, Optional, Union
   
   def process_records(
       records: List[Dict[str, str]],
       max_count: Optional[int] = None,
   ) -> Union[pd.DataFrame, None]:
       """Process a list of records."""
       ...

Testing Standards
-----------------

Writing Tests
~~~~~~~~~~~~~

* **Location**: Tests in ``tests/`` directory mirror ``scripts/`` structure
* **Framework**: Use ``pytest``
* **Coverage**: Aim for >80% code coverage
* **Types**: Write unit tests, integration tests, and end-to-end tests

Example Test:

.. code-block:: python

   # tests/test_extract_data.py
   
   import pytest
   from scripts.extract_data import extract_from_pdf
   
   
   def test_extract_from_pdf_success():
       """Test successful PDF extraction."""
       result = extract_from_pdf("tests/fixtures/sample.pdf")
       
       assert result is not None
       assert "patient_id" in result
       assert len(result) > 0
   
   
   def test_extract_from_pdf_invalid_file():
       """Test extraction with invalid file."""
       with pytest.raises(FileNotFoundError):
           extract_from_pdf("nonexistent.pdf")
   
   
   @pytest.mark.parametrize("pdf_path,expected_fields", [
       ("tests/fixtures/form1.pdf", ["name", "age"]),
       ("tests/fixtures/form2.pdf", ["id", "date"]),
   ])
   def test_extract_from_pdf_parametrized(pdf_path, expected_fields):
       """Test extraction with multiple inputs."""
       result = extract_from_pdf(pdf_path)
       
       for field in expected_fields:
           assert field in result

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

   # Run all tests
   pytest
   
   # Run with coverage
   pytest --cov=scripts --cov-report=html
   
   # Run specific test file
   pytest tests/test_extract_data.py
   
   # Run specific test
   pytest tests/test_extract_data.py::test_extract_from_pdf_success
   
   # Run with verbose output
   pytest -v

Documentation Standards
-----------------------

Updating Documentation
~~~~~~~~~~~~~~~~~~~~~~

When adding features:

1. **Update docstrings** in the code
2. **Update user guide** if user-facing
3. **Update API reference** if adding public APIs
4. **Update architecture docs** if changing structure

Building Documentation Locally
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Build HTML docs
   cd docs/sphinx
   make html
   
   # View docs
   open _build/html/index.html  # macOS
   # Or: xdg-open _build/html/index.html  # Linux

Documentation Guidelines
~~~~~~~~~~~~~~~~~~~~~~~~

* Use reStructuredText (.rst) for docs
* Include code examples
* Add cross-references with ``:doc:``, ``:ref:``, etc.
* Keep examples up-to-date with code

Code Review Process
-------------------

Reviewer Responsibilities
~~~~~~~~~~~~~~~~~~~~~~~~~

Reviewers should check:

* **Correctness**: Does the code work as intended?
* **Tests**: Are there adequate tests?
* **Documentation**: Is the code documented?
* **Style**: Does it follow coding standards?
* **Performance**: Are there efficiency concerns?
* **Security**: Are there security implications?

Author Responsibilities
~~~~~~~~~~~~~~~~~~~~~~~

Authors should:

* Respond promptly to feedback
* Make requested changes
* Explain design decisions
* Keep PRs focused and reasonably sized

Best Practices
--------------

Code Quality
~~~~~~~~~~~~

* **DRY** (Don't Repeat Yourself): Avoid code duplication
* **KISS** (Keep It Simple, Stupid): Prefer simple solutions
* **YAGNI** (You Aren't Gonna Need It): Don't add unused features
* **Single Responsibility**: Each function/class has one job

Git Practices
~~~~~~~~~~~~~

* **Atomic commits**: Each commit does one thing
* **Meaningful messages**: Explain what and why
* **Small PRs**: Easier to review (<400 lines preferred)
* **Rebase before merge**: Keep history clean

Performance Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~

* Profile before optimizing
* Use appropriate data structures
* Cache expensive operations
* Consider memory usage for large datasets

Security Practices
~~~~~~~~~~~~~~~~~~

* Never commit API keys or secrets
* Use environment variables for sensitive data
* Validate all user inputs
* Follow least privilege principle

Common Tasks
------------

Adding a New Pipeline Stage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Create module in ``scripts/``
2. Add configuration to ``config.py``
3. Update ``main.py`` to call the stage
4. Add tests in ``tests/``
5. Document in user guide
6. Update architecture docs

Adding LLM Provider Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Create adapter in ``scripts/llm/``
2. Inherit from ``BaseAdapter``
3. Implement required methods
4. Add provider to configuration
5. Add integration tests
6. Document in configuration guide

Adding De-identification Rule
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Add pattern to ``scripts/deidentify.py``
2. Update ``country_regulations.py`` if region-specific
3. Add test cases
4. Document in user guide

Issue Tracking
--------------

Finding Issues to Work On
~~~~~~~~~~~~~~~~~~~~~~~~~

Look for issues labeled:

* ``good first issue``: Beginner-friendly
* ``help wanted``: Contributions welcome
* ``bug``: Bug fixes needed
* ``enhancement``: New features

Creating Issues
~~~~~~~~~~~~~~~

When creating an issue:

1. **Search first**: Check if it already exists
2. **Use templates**: Follow the issue template
3. **Be specific**: Provide details and examples
4. **Add labels**: Help with organization

Communication
-------------

Channels
~~~~~~~~

* **GitHub Issues**: Bug reports, feature requests
* **Pull Requests**: Code discussions
* **Discussions**: General questions
* **Email**: For sensitive topics

Code of Conduct
~~~~~~~~~~~~~~~

* Be respectful and inclusive
* Provide constructive feedback
* Assume good intentions
* Focus on what is best for the project

Questions?
----------

If you have questions:

* Check :doc:`../user_guide/faq`
* Search existing issues
* Ask in GitHub Discussions
* Email the maintainers

Thank you for contributing to RePORTaLiN!
