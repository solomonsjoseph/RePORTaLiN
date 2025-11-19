Developer Guide
===============

Welcome to the RePORTaLiN developer guide. This section provides technical documentation for developers who want to contribute to, extend, or integrate with RePORTaLiN.

.. note::
   This is the **technical documentation** for developers. If you're a user looking to use RePORTaLiN, see the :doc:`../user_guide/index`.

Overview
--------

RePORTaLiN is a data pipeline system for processing clinical trial data with AI-powered document analysis, privacy-preserving data deidentification, and vector database storage for semantic search.

**Target Audience**: Software developers, data engineers, and technical contributors.

**Key Technologies**:

- Python 3.8+
- ChromaDB (vector database)
- OpenAI/Anthropic/Ollama LLMs
- pandas, openpyxl (data processing)
- Sentence Transformers (embeddings)
- PyMuPDF (PDF processing)

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Developer Documentation

   architecture
   contributing
   testing
   api_reference

Quick Links for Developers
---------------------------

**Getting Started**

1. Read the :doc:`architecture` to understand system design
2. Follow :doc:`contributing` to set up your development environment
3. Review :doc:`testing` to write and run tests
4. Consult :doc:`api_reference` for module and function documentation

**Common Development Tasks**

- **Add a new data source**: Modify :py:mod:`scripts.extract_data` and update the data dictionary loader
- **Implement a new LLM adapter**: Extend :py:class:`scripts.llm.base_adapter.LLMAdapter`
- **Add privacy regulations**: Update :py:mod:`scripts.utils.country_regulations`
- **Customize chunking**: Modify :py:mod:`scripts.vector_db.pdf_chunking` or :py:mod:`scripts.vector_db.jsonl_chunking_nl`

Architecture Principles
-----------------------

RePORTaLiN follows these architectural principles:

**Modularity**
   Each component (data extraction, deidentification, vector storage) is a separate, testable module.

**Privacy-First**
   All data processing includes privacy checks and deidentification by default.

**Extensibility**
   LLM adapters, chunking strategies, and regulations are designed to be easily extended.

**Configuration-Driven**
   System behavior is controlled through ``config.py``, not hardcoded values.

**Documentation-First**
   All code includes comprehensive docstrings and examples that can be tested with Sphinx doctest.

Development Standards
---------------------

Code Quality
~~~~~~~~~~~~

- **Style Guide**: Google Python Style Guide + PEP 8
- **Docstrings**: Google-style docstrings for all public APIs
- **Type Hints**: Use type annotations for function signatures
- **Testing**: Maintain 80%+ code coverage
- **Documentation**: Follow Diátaxis framework (tutorials, how-to guides, reference, explanation)

Documentation Standards
~~~~~~~~~~~~~~~~~~~~~~~

All documentation must follow the **Diátaxis** framework:

- **Tutorials** (learning-oriented): Step-by-step lessons for beginners
- **How-to guides** (task-oriented): Solutions to specific problems
- **Reference** (information-oriented): Technical descriptions of APIs
- **Explanation** (understanding-oriented): Clarification of design decisions

See :doc:`../user_guide/overview` for examples of user-facing documentation and :doc:`architecture` for technical explanation.

Code Review Process
~~~~~~~~~~~~~~~~~~~

All code changes require:

1. Google-style docstrings with examples
2. Unit tests with 80%+ coverage
3. Updated documentation
4. Passing CI/CD checks
5. At least one approving review

Contributing
------------

Ready to contribute? Start with:

1. :doc:`contributing` - Set up your development environment
2. :doc:`testing` - Write and run tests
3. :doc:`architecture` - Understand the system design
4. :doc:`api_reference` - Browse the API documentation

Additional Resources
--------------------

- `Google Python Style Guide <https://google.github.io/styleguide/pyguide.html>`_
- `Diátaxis Documentation Framework <https://diataxis.fr/>`_
- `Sphinx Documentation <https://www.sphinx-doc.org/>`_
- `pytest Documentation <https://docs.pytest.org/>`_

Need Help?
----------

- Check the :doc:`../user_guide/faq` for common questions
- Review :doc:`architecture` for system design questions
- Open an issue on GitHub for bugs or feature requests
- Join discussions on GitHub Discussions for general questions
