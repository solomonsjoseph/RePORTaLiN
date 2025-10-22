scripts.deidentify module
================================

.. automodule:: scripts.deidentify
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

.. versionchanged:: 0.0.6
   Added explicit public API definition via ``__all__`` (10 exports), enhanced module
   docstring with comprehensive usage examples (48 lines), and added complete return type annotations.

Overview
--------

The ``deidentify`` module provides robust HIPAA/GDPR-compliant de-identification for medical datasets,
supporting 14 countries with country-specific regulations, encrypted mapping storage, and comprehensive validation.

**Public API** (v0.0.6):

.. code-block:: python

   __all__ = [
       'PHIType',                    # Enum for PHI types
       'DetectionPattern',           # Dataclass for patterns
       'DeidentificationConfig',     # Dataclass for configuration
       'PatternLibrary',             # Pattern library class
       'PseudonymGenerator',         # Pseudonym generation
       'DateShifter',                # Date shifting
       'MappingStore',               # Secure mapping storage
       'DeidentificationEngine',     # Main engine class
       'deidentify_dataset',         # Top-level function
       'validate_dataset',           # Validation function
   ]

Key Features
------------

- **Multi-Country Support**: HIPAA (US), GDPR (EU/GB), DPDPA (IN), and 11 other countries
- **PHI/PII Detection**: 21 PHI types with country-specific patterns
- **Pseudonymization**: Consistent, reversible pseudonyms with encrypted mapping
- **Date Shifting**: Preserves time intervals while shifting dates
- **Encrypted Storage**: Fernet encryption for mapping files
- **Validation**: Comprehensive validation to ensure de-identification quality
- **Audit Trails**: Export mappings for compliance audits

Classes
-------

DeidentificationEngine
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: scripts.deidentify.DeidentificationEngine
   :members:
   :undoc-members:
   :show-inheritance:

PseudonymGenerator
~~~~~~~~~~~~~~~~~~

.. autoclass:: scripts.deidentify.PseudonymGenerator
   :members:
   :undoc-members:
   :show-inheritance:

DateShifter
~~~~~~~~~~~

.. autoclass:: scripts.deidentify.DateShifter
   :members:
   :undoc-members:
   :show-inheritance:

MappingStore
~~~~~~~~~~~~

.. autoclass:: scripts.deidentify.MappingStore
   :members:
   :undoc-members:
   :show-inheritance:

PatternLibrary
~~~~~~~~~~~~~~

.. autoclass:: scripts.deidentify.PatternLibrary
   :members:
   :undoc-members:
   :show-inheritance:

Enumerations
------------

PHIType
~~~~~~~

.. autoclass:: scripts.deidentify.PHIType
   :members:
   :undoc-members:
   :show-inheritance:

Data Classes
------------

DetectionPattern
~~~~~~~~~~~~~~~~

.. autoclass:: scripts.deidentify.DetectionPattern
   :members:
   :undoc-members:
   :show-inheritance:

DeidentificationConfig
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: scripts.deidentify.DeidentificationConfig
   :members:
   :undoc-members:
   :show-inheritance:

Functions
---------

deidentify_dataset
~~~~~~~~~~~~~~~~~~

.. autofunction:: scripts.deidentify.deidentify_dataset

validate_dataset
~~~~~~~~~~~~~~~~

.. autofunction:: scripts.deidentify.validate_dataset
