scripts.utils.country\_regulations module
===========================================

.. automodule:: scripts.utils.country_regulations
   :members:
   :undoc-members:
   :show-inheritance:

.. versionchanged:: 0.0.5
   Added explicit public API definition via ``__all__`` (6 exports) and enhanced module
   docstring with usage examples.

Overview
--------

The ``country_regulations`` module provides comprehensive country-specific data privacy regulations for patient data de-identification. It supports 14 countries across North America, Europe, Asia-Pacific, and Africa, ensuring compliance with local privacy laws.

**Public API** (v0.0.5):

.. code-block:: python

   __all__ = [
       'DataFieldType',       # Enum for field types
       'PrivacyLevel',        # Enum for privacy levels
       'DataField',           # Dataclass for field definitions
       'CountryRegulation',   # Dataclass for regulations
       'CountryRegulationManager',  # Main manager class
       'get_common_fields',   # Helper function
   ]

.. note::
   When initializing ``CountryRegulationManager`` without specifying a country, it defaults to **India (IN)** to align with the RePORTaLiN project's primary focus on tuberculosis research in India.

Key Features
------------

- **Multi-Country Support**: HIPAA (US), PIPEDA (CA), GDPR (EU/GB), DPDPA (IN), LGPD (BR), DPA (PH, ID, ZA, AU), POPIA (ZA), and country-specific laws for KE, NG, GH, UG
- **Privacy Frameworks**: Structured privacy level definitions (PUBLIC to CRITICAL)
- **Data Field Management**: Categorized data fields with privacy characteristics
- **Identifier Detection**: Country-specific identifier patterns (SSN, Aadhaar, NIK, etc.)
- **Regulatory Requirements**: Built-in requirements for data retention, breach notification, and consent
- **Export/Import**: JSON-based configuration export and import

Supported Countries
-------------------

.. list-table:: Supported Privacy Regulations by Country
   :header-rows: 1
   :widths: 15 25 30 30

   * - Country
     - Code
     - Primary Regulation
     - Key Features
   * - United States
     - US
     - HIPAA/HITECH
     - 18 identifiers, ages >89 aggregation
   * - Canada
     - CA
     - PIPEDA + Provincial
     - Consent required, breach notification
   * - India
     - IN
     - DPDPA 2023
     - Aadhaar protection, children's data
   * - Indonesia
     - ID
     - Law No. 27/2022
     - NIK protection, consent requirements
   * - Brazil
     - BR
     - LGPD
     - CPF protection, data subject rights
   * - Philippines
     - PH
     - DPA 2012
     - SSS/GSIS protection, NPC registration
   * - South Africa
     - ZA
     - POPIA
     - ID protection, children's data
   * - European Union
     - EU
     - GDPR
     - Right to erasure, portability
   * - United Kingdom
     - GB
     - UK GDPR
     - ICO oversight, Brexit-adapted GDPR
   * - Australia
     - AU
     - Privacy Act
     - Medicare/TFN protection, OAIC
   * - Kenya
     - KE
     - DPA 2019
     - ID/Passport protection, ODPC
   * - Nigeria
     - NG
     - NDPR
     - NIN/BVN protection, NITDA
   * - Ghana
     - GH
     - DPA 2012
     - Ghana Card protection, DPC
   * - Uganda
     - UG
     - DPA 2019
     - NIN protection, NITA-U

Core Classes
------------

.. currentmodule:: scripts.utils.country_regulations

CountryRegulationManager
~~~~~~~~~~~~~~~~~~~~~~~~

Main manager class for country-specific regulations.

.. autoclass:: CountryRegulationManager
   :members:
   :special-members: __init__

Key Methods:

- :meth:`~CountryRegulationManager.get_supported_countries`: Get list of supported country codes
- :meth:`~CountryRegulationManager.get_country_info`: Get information about a country's regulation
- :meth:`~CountryRegulationManager.get_all_data_fields`: Get all data fields from loaded countries
- :meth:`~CountryRegulationManager.get_country_specific_fields`: Get country-specific fields
- :meth:`~CountryRegulationManager.get_high_privacy_fields`: Get HIGH/CRITICAL privacy fields
- :meth:`~CountryRegulationManager.get_detection_patterns`: Get regex patterns for identifiers
- :meth:`~CountryRegulationManager.export_configuration`: Export configuration to JSON
- :meth:`~CountryRegulationManager.get_requirements_summary`: Get regulatory requirements summary

CountryRegulation
~~~~~~~~~~~~~~~~~

Country-specific regulation configuration.

.. autoclass:: CountryRegulation
   :members:
   :special-members: __init__

DataField
~~~~~~~~~

Data field definition with privacy characteristics.

.. autoclass:: DataField
   :members:
   :special-members: __init__

Enums
-----

DataFieldType
~~~~~~~~~~~~~

Data field type categorization.

.. autoclass:: DataFieldType
   :members:
   :undoc-members:

PrivacyLevel
~~~~~~~~~~~~

Privacy sensitivity levels.

.. autoclass:: PrivacyLevel
   :members:
   :undoc-members:

Usage Examples
--------------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from scripts.utils.country_regulations import CountryRegulationManager
   
   # Initialize manager (defaults to India if no country specified)
   manager = CountryRegulationManager()  # Uses IN (India) by default
   
   # Or explicitly specify a country
   manager_us = CountryRegulationManager("US")
   
   # Get all data fields
   fields = manager.get_all_data_fields()
   for field in fields:
       print(f"{field.name}: {field.privacy_level.name}")
   
   # Get detection patterns
   patterns = manager.get_detection_patterns()
   for name, pattern in patterns.items():
       print(f"{name}: {pattern.pattern}")

Multi-Country Setup
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Process data from multiple countries
   manager = CountryRegulationManager(["US", "IN", "BR"])
   
   # Get supported countries
   supported = CountryRegulationManager.get_supported_countries()
   print(f"Supported countries: {supported}")
   
   # Get info for each loaded country
   for country_code in manager.country_codes:
       info = CountryRegulationManager.get_country_info(country_code)
       print(f"\n{info['name']}")
       print(f"Regulation: {info['regulation']}")
       print(f"Acronym: {info['acronym']}")

Field Validation
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Initialize manager for India
   manager = CountryRegulationManager("IN")
   
   # Get a specific field and validate
   fields = manager.get_all_data_fields()
   aadhaar_field = next((f for f in fields if "AADHAAR" in f.name.upper()), None)
   
   if aadhaar_field:
       # Validate Aadhaar number using field's pattern
       is_valid = aadhaar_field.validate("1234 5678 9012")
       print(f"Valid Aadhaar: {is_valid}")

Field Privacy Analysis
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get high privacy fields
   manager = CountryRegulationManager(["US", "IN"])
   high_privacy_fields = manager.get_high_privacy_fields()
   
   for field in high_privacy_fields:
       print(f"{field.display_name}: {field.privacy_level.name}")
       if field.description:
           print(f"  Description: {field.description}")

Export Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Export configuration for offline use
   manager = CountryRegulationManager(["US", "IN"])
   manager.export_configuration("config/country_regulations.json")
   
   # Get requirements summary
   summary = manager.get_requirements_summary()
   for country, requirements in summary.items():
       print(f"\n{country}:")
       for req in requirements:
           print(f"  - {req}")

Integration with De-identification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.utils.deidentify import DeidentificationEngine
   from scripts.utils.country_regulations import CountryRegulationManager
   
   # Set up country-specific de-identification
   reg_manager = CountryRegulationManager("IN")
   
   # Get detection patterns for use in de-identification
   patterns = reg_manager.get_detection_patterns()
   
   # Initialize de-identification engine (passes country code to engine)
   engine = DeidentificationEngine(country_code="IN")
   
   # De-identify with country-specific patterns
   text = "Patient Aadhaar: 1234 5678 9012, PAN: ABCDE1234F"
   deidentified = engine.deidentify_text(text)
   print(deidentified)

Command-Line Interface
----------------------

The module can be used as a standalone script:

.. code-block:: bash

   # List all supported countries
   python -m scripts.utils.country_regulations --list
   
   # Show regulations for specific countries
   python -m scripts.utils.country_regulations -c US IN
   
   # Show all data fields
   python -m scripts.utils.country_regulations -c US --show-fields
   
   # Export configuration for multiple countries
   python -m scripts.utils.country_regulations -c US IN BR --export config/regulations.json
   
   # Show all countries at once
   python -m scripts.utils.country_regulations -c ALL

Privacy Levels
--------------

The module defines five privacy sensitivity levels:

1. **PUBLIC** (Level 1): Non-sensitive, publicly available data
2. **LOW** (Level 2): Low-risk identifiers (geographic regions, dates without times)
3. **MEDIUM** (Level 3): Moderate-risk identifiers (full dates, ages, zip codes)
4. **HIGH** (Level 4): High-risk identifiers (names, phone numbers, emails)
5. **CRITICAL** (Level 5): Critical identifiers (SSN, medical records, biometrics)

Regulatory Requirements
-----------------------

Each country regulation includes:

- **Retention Requirements**: Data retention periods (days)
- **Breach Notification**: Notification timelines and authorities
- **Consent Requirements**: Types of consent needed
- **Data Subject Rights**: Right to access, correction, erasure, portability
- **Cross-Border Transfer**: Rules for international data transfer
- **Special Categories**: Additional protections for sensitive data

See Also
--------

:doc:`scripts.utils.deidentify`
   De-identification engine that uses country regulations

:doc:`../user_guide/country_regulations`
   Detailed user guide on country-specific regulations

:doc:`../user_guide/deidentification`
   General de-identification documentation

:doc:`../developer_guide/extending`
   Guide for adding new countries
