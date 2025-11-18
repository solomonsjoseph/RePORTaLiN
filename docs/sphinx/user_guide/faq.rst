Frequently Asked Questions
===========================

General Questions
-----------------

What is RePORTaLiN?
~~~~~~~~~~~~~~~~~~~

RePORTaLiN (Regional Prospective Observational Research for Tuberculosis Analysis in India) is a comprehensive data extraction and harmonization pipeline for tuberculosis research studies. It automates the extraction, validation, and de-identification of clinical trial data from PDF forms and Excel datasets.

Who should use RePORTaLiN?
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Clinical research teams conducting TB studies
* Data managers handling multi-center trials
* Researchers requiring de-identified datasets
* Organizations needing regulatory-compliant data processing

What data formats does it support?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Input**: PDF (annotated case report forms), Excel (.xlsx, .xls), CSV
* **Output**: Excel, CSV, JSON, Parquet

Installation & Setup
--------------------

What are the system requirements?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Python 3.8 or higher
* 8GB RAM minimum (16GB recommended)
* 2GB disk space for application and dependencies
* macOS, Linux, or Windows operating system

How do I install RePORTaLiN?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/your-org/RePORTaLiN.git
   cd RePORTaLiN
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

See :doc:`installation` for detailed instructions.

Do I need an API key?
~~~~~~~~~~~~~~~~~~~~~

Yes, you need an API key for the LLM provider (OpenAI, Anthropic, etc.) to use the data extraction features. Add your key to the `.env` file:

.. code-block:: bash

   OPENAI_API_KEY=your_api_key_here

Using the Pipeline
------------------

How do I run the pipeline?
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python main.py

Or run individual stages:

.. code-block:: bash

   python scripts/load_dictionary.py
   python scripts/extract_data.py
   python scripts/deidentify.py

Can I run only part of the pipeline?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! Each stage can be run independently. Use the Makefile for convenience:

.. code-block:: bash

   make load-dict    # Load dictionary only
   make extract      # Extract data only
   make deidentify   # De-identify only

How long does processing take?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Processing time depends on:

* Number of documents (PDF pages or Excel rows)
* LLM provider and model speed
* System resources

Typical processing rates:

* Dictionary loading: <1 minute for most studies
* Data extraction: 1-5 seconds per PDF page
* De-identification: <1 second per record

Data Extraction
---------------

What types of data can be extracted?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Structured form fields (text, numbers, dates)
* Checkboxes and radio buttons
* Tables and grids
* Free-text responses

How accurate is the extraction?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Accuracy depends on:

* PDF quality (searchable vs. scanned)
* Form complexity
* LLM model used

Typical accuracy:

* Structured fields: 95%+ with GPT-4
* Free text: 90%+ with proper validation
* Handwritten (with OCR): 70-90%

Can I validate extraction results?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! The pipeline includes:

* Automatic validation against data dictionary
* Manual review reports
* Error logs for problematic records

.. code-block:: python

   from scripts.extract_data import validate_extraction
   
   validation_report = validate_extraction(extracted_data, dictionary)

De-identification
-----------------

What privacy regulations are supported?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **HIPAA** (USA): Health Insurance Portability and Accountability Act
* **GDPR** (EU): General Data Protection Regulation
* **PDPA** (Singapore): Personal Data Protection Act

Configure the region in `config.py`:

.. code-block:: python

   COMPLIANCE_REGION = "USA"  # or "EU", "Singapore"

What PII is removed?
~~~~~~~~~~~~~~~~~~~~

Direct identifiers:

* Names
* ID numbers
* Contact information
* Geographic locations (below region level)

Quasi-identifiers:

* Dates (shifted by random offset)
* Ages (binned)
* Detailed locations (generalized)

Can I customize de-identification rules?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! Add custom patterns:

.. code-block:: python

   from scripts.deidentify import add_custom_pattern
   
   add_custom_pattern(
       name="custom_id",
       pattern=r"ID-\\d{6}",
       replacement="[REDACTED]"
   )

Is de-identification reversible?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No, by design. De-identification is one-way to ensure privacy. The mapping between original and de-identified data is stored securely and separately from the de-identified dataset.

Vector Database
---------------

What is the vector database used for?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Semantic search across documents
* Finding relevant CRF sections
* Similarity-based retrieval
* Context for LLM extraction

How do I ingest documents?
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.vector_db.ingest_pdfs import ingest_pdfs
   
   ingest_pdfs(
       pdf_dir="data/Indo-VAP/annotated_pdfs",
       collection_name="crf_documents"
   )

How do I query the vector store?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.vector_db.vector_store import VectorStore
   
   store = VectorStore(collection_name="crf_documents")
   results = store.query("tuberculosis screening", n_results=5)

Can I use custom embeddings?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! Configure the embedding model in `config.py`:

.. code-block:: python

   EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Default
   # Or use: "all-mpnet-base-v2", "paraphrase-multilingual-mpnet-base-v2", etc.

Troubleshooting
---------------

The pipeline fails with "API key not found"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add your API key to the `.env` file:

.. code-block:: bash

   OPENAI_API_KEY=your_key_here

Extraction is very slow
~~~~~~~~~~~~~~~~~~~~~~~~

Try:

* Use a faster LLM model (e.g., GPT-3.5 instead of GPT-4)
* Increase batch size: ``EXTRACTION_BATCH_SIZE = 100``
* Enable caching for repeated extractions

I'm getting validation errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check:

* Data dictionary field definitions
* Source data quality
* Field type mappings

Review the validation report:

.. code-block:: bash

   cat output/validation_report.txt

Memory errors during processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Try:

* Reduce batch size: ``EXTRACTION_BATCH_SIZE = 50``
* Process in smaller chunks
* Increase available system RAM

Development & Contributing
--------------------------

How can I contribute?
~~~~~~~~~~~~~~~~~~~~~

See :doc:`../developer_guide/contributing` for contribution guidelines.

How do I report bugs?
~~~~~~~~~~~~~~~~~~~~~~

Open an issue on GitHub with:

* Detailed description
* Steps to reproduce
* Error messages and logs
* System information

Where can I get help?
~~~~~~~~~~~~~~~~~~~~~

* **Documentation**: https://reportalin.readthedocs.io
* **GitHub Issues**: https://github.com/your-org/RePORTaLiN/issues
* **Email**: support@reportalin.org

Performance & Scaling
---------------------

Can it handle large datasets?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! The pipeline is designed for:

* Hundreds of PDF forms
* Thousands of Excel records
* Multi-gigabyte databases

Use batch processing and parallel execution for large datasets.

Can I run it on a server?
~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! RePORTaLiN can run:

* On local machines
* On remote servers (via SSH)
* In Docker containers
* On cloud platforms (AWS, GCP, Azure)

Is there a GUI?
~~~~~~~~~~~~~~~

Not currently. RePORTaLiN is a command-line tool. A web interface is planned for future releases.

Licensing & Usage
-----------------

What license is RePORTaLiN under?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check the LICENSE file in the repository for licensing information.

Can I use it for commercial purposes?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check the specific license terms. Contact the maintainers for commercial licensing inquiries.

Can I modify the code?
~~~~~~~~~~~~~~~~~~~~~~~

Yes, if permitted by the license. Contributions back to the project are welcome!

Next Steps
----------

* Read the :doc:`quickstart` guide
* Explore :doc:`data_pipeline` for detailed pipeline documentation
* Check :doc:`configuration` for all configuration options
