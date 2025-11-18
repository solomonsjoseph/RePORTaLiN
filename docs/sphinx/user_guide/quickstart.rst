Quick Start
===========

This guide will walk you through your first data extraction with RePORTaLiN.

Basic Usage
-----------

Running the Full Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest way to run the complete pipeline:

.. code-block:: bash

   python main.py

This executes all three stages:

1. Dictionary loading
2. Data extraction
3. De-identification

Pipeline Configuration
~~~~~~~~~~~~~~~~~~~~~~

Configure the pipeline by editing `config.py` or using environment variables:

.. code-block:: python

   from config import Config
   
   # View current configuration
   config = Config()
   print(f"Input path: {config.INPUT_PATH}")
   print(f"Output path: {config.OUTPUT_PATH}")

Step-by-Step Execution
----------------------

Load Data Dictionary
~~~~~~~~~~~~~~~~~~~~

Extract data dictionary definitions from Excel files:

.. code-block:: bash

   python scripts/load_dictionary.py

This will:

* Read Excel files from the configured dictionary path
* Parse field definitions, validation rules, and mappings
* Save structured dictionary data for downstream processing

Extract Data from PDFs
~~~~~~~~~~~~~~~~~~~~~~~

Extract data from annotated PDF case report forms:

.. code-block:: bash

   python scripts/extract_data.py

The extraction process:

* Reads PDF forms from the input directory
* Uses LLM to extract structured data
* Validates against the data dictionary
* Saves extracted data in the specified format

De-identify Extracted Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Remove personally identifiable information:

.. code-block:: bash

   python scripts/deidentify.py

De-identification includes:

* Date shifting
* Name removal/pseudonymization
* Location generalization
* Identifier hashing

Working with Vector Database
-----------------------------

Ingest PDF Documents
~~~~~~~~~~~~~~~~~~~~

Add PDF documents to the vector database:

.. code-block:: python

   from scripts.vector_db.ingest_pdfs import ingest_pdfs
   
   # Ingest PDFs from a directory
   ingest_pdfs(
       pdf_dir="data/Indo-VAP/annotated_pdfs",
       collection_name="crf_documents"
   )

Query the Vector Store
~~~~~~~~~~~~~~~~~~~~~~

Search for relevant information:

.. code-block:: python

   from scripts.vector_db.vector_store import VectorStore
   
   # Initialize vector store
   store = VectorStore(collection_name="crf_documents")
   
   # Perform semantic search
   results = store.query(
       query_text="tuberculosis screening criteria",
       n_results=5
   )
   
   for result in results:
       print(f"Document: {result['metadata']['source']}")
       print(f"Content: {result['text']}")

Common Tasks
------------

Viewing Logs
~~~~~~~~~~~~

All pipeline operations are logged to `logs/` directory:

.. code-block:: bash

   # View recent log entries
   tail -f logs/reportalin_YYYYMMDD.log

Handling Errors
~~~~~~~~~~~~~~~

If the pipeline encounters errors:

1. Check the log files for detailed error messages
2. Verify your configuration in `config.py`
3. Ensure all required input files are present
4. Check that dependencies are correctly installed

Advanced Options
~~~~~~~~~~~~~~~~

Use the Makefile for common tasks:

.. code-block:: bash

   # Run all stages
   make all
   
   # Run dictionary loading only
   make load-dict
   
   # Run extraction only
   make extract
   
   # Run de-identification only
   make deidentify
   
   # Run tests
   make test

Next Steps
----------

* Explore :doc:`configuration` for detailed configuration options
* Read :doc:`data_pipeline` for in-depth pipeline documentation
* See :doc:`../developer_guide/api_reference` for API details
