.. _country_regulations:

=======================================
Country-Specific Data Privacy Regulations
=======================================

Overview
========

The RePORTaLiN de-identification system supports country-specific data privacy regulations to ensure compliance with local laws when processing patient data. This feature enables automatic detection and de-identification of country-specific identifiers based on the applicable regulatory framework.

.. important::
   Always ensure you understand and comply with the specific regulations applicable to your jurisdiction. This tool provides technical capabilities but does not constitute legal advice.

Supported Countries and Regulations
====================================

The system currently supports **14 countries** across North America, Europe, Asia-Pacific, and Africa:

North America
-------------

United States (US)
~~~~~~~~~~~~~~~~~~

:Regulation: HIPAA (Health Insurance Portability and Accountability Act)
:Enhancement: HITECH Act (strengthens enforcement and penalties)
:Key Requirements:
   - Privacy Rule: Remove all 18 HIPAA identifiers
   - Security Rule: Administrative, physical, and technical safeguards
   - Breach Notification Rule: Notify within 60 days
   - Ages over 89 must be aggregated
   - Geographic subdivisions smaller than state must be removed

:Identifiers Detected:
   - Social Security Number (SSN)
   - Medical Record Number (MRN)
   - Insurance ID
   - Phone numbers, emails, dates, addresses

Canada (CA)
~~~~~~~~~~~

:Regulation: PIPEDA (Personal Information Protection and Electronic Documents Act)
:Provincial Laws: Ontario PHIPA, Alberta HIA, BC PIPA/eHealth Act
:Key Requirements:
   - Consent required for collection, use, and disclosure
   - Individual access and correction rights
   - Security safeguards proportionate to sensitivity
   - Breach notification to Privacy Commissioner

:Identifiers Detected:
   - Social Insurance Number (SIN)
   - Provincial Health Card Numbers
   - Standard identifiers (name, phone, email, etc.)

Europe
------

European Union (EU)
~~~~~~~~~~~~~~~~~~~

:Regulation: GDPR (General Data Protection Regulation)
:Scope: EU/EEA member states
:Notable Examples: Germany (BDSG/SGB), France (Code de la santé publique), Netherlands (WGBO/AVG)
:Key Requirements:
   - Special-category health data requires explicit consent/legal basis
   - Data minimization and purpose limitation
   - Right to erasure (right to be forgotten)
   - Data portability
   - Privacy by design and default
   - Breach notification within 72 hours
   - DPIA for high-risk processing

:Identifiers Detected:
   - National ID Numbers (varies by country)
   - European Health Insurance Card (EHIC)
   - Standard identifiers

United Kingdom (GB)
~~~~~~~~~~~~~~~~~~~

:Regulation: UK GDPR + Data Protection Act 2018
:Framework: Caldicott Principles, NHS information governance
:Key Requirements:
   - Health data treated as special category
   - Lawful basis and special category condition required
   - ICO breach notification within 72 hours
   - Privacy by design and default

:Identifiers Detected:
   - NHS Number
   - National Insurance Number
   - Standard identifiers

Asia-Pacific
------------

India (IN)
~~~~~~~~~~

:Regulation: DPDPA (Digital Personal Data Protection Act) 2023
:Key Requirements:
   - Obtain consent for data processing
   - Data minimization and purpose limitation
   - Storage limitation
   - Right to erasure and correction

:Identifiers Detected:
   - Aadhaar Number (12-digit unique ID)
   - PAN Number (Permanent Account Number)
   - Voter ID
   - Passport Number
   - Standard identifiers

Indonesia (ID)
~~~~~~~~~~~~~~

:Regulation: UU PDP (Personal Data Protection Law No. 27 of 2022)
:Key Requirements:
   - Consent-based data processing
   - Data protection officer required for large processors
   - Cross-border transfer restrictions
   - Breach notification within 72 hours

:Identifiers Detected:
   - NIK (National Identity Number - 16 digits)
   - KK Number (Family Card)
   - NPWP (Tax ID)
   - Standard identifiers

Philippines (PH)
~~~~~~~~~~~~~~~~

:Regulation: Data Privacy Act of 2012 (Republic Act No. 10173)
:Key Requirements:
   - Consent or legitimate interest required
   - Privacy policy must be provided
   - Breach notification to NPC within 72 hours
   - Security measures proportionate to risk

:Identifiers Detected:
   - PhilHealth Number
   - UMID Number
   - SSS Number
   - Standard identifiers

Australia (AU)
~~~~~~~~~~~~~~

:Regulation: Privacy Act 1988 + Australian Privacy Principles (APPs)
:Additional: My Health Records Act 2012
:Key Requirements:
   - Health data is sensitive information
   - Consent or legal authority required
   - Security safeguards for personal information
   - Notifiable Data Breaches scheme

:Identifiers Detected:
   - Medicare Number
   - Individual Healthcare Identifier (IHI)
   - Tax File Number (TFN)
   - Standard identifiers

Latin America
-------------

Brazil (BR)
~~~~~~~~~~~

:Regulation: LGPD (Lei Geral de Proteção de Dados - Law 13.709/2018)
:Key Requirements:
   - Legal basis required for processing
   - Data protection impact assessment for high-risk processing
   - Data protection officer for public bodies and large processors
   - Sensitive data requires specific consent

:Identifiers Detected:
   - CPF (Individual Taxpayer Registry)
   - RG (General Registry/ID card)
   - SUS Number (Unified Health System)
   - Standard identifiers

Africa
------

South Africa (ZA)
~~~~~~~~~~~~~~~~~

:Regulation: POPIA (Protection of Personal Information Act - Act 4 of 2013)
:Key Requirements:
   - Process information lawfully and reasonably
   - Collect for specific purpose with consent
   - Adequate security measures
   - Data subject participation rights

:Identifiers Detected:
   - South African ID Number (13 digits)
   - Passport Number
   - Standard identifiers

Kenya (KE)
~~~~~~~~~~

:Regulation: Data Protection Act 2019
:Additional: Health Act 2017 (patient confidentiality)
:Key Requirements:
   - Sensitive health data requires explicit consent
   - Data Protection Commissioner oversight
   - Cross-border transfer restrictions
   - Breach notification obligations

:Identifiers Detected:
   - National ID Number
   - NHIF Number (National Hospital Insurance Fund)
   - Standard identifiers

Nigeria (NG)
~~~~~~~~~~~~

:Regulation: Nigeria Data Protection Act 2023 (NDPA)
:Enforcement: Nigeria Data Protection Commission (NDPC)
:Key Requirements:
   - Health data treated as sensitive
   - Explicit consent for sensitive data processing
   - Data localization requirements
   - Breach notification within 72 hours
   - Data Protection Officer required

:Identifiers Detected:
   - NIN (National Identification Number - 11 digits)
   - NHIS Number (National Health Insurance Scheme)
   - Standard identifiers

Ghana (GH)
~~~~~~~~~~

:Regulation: Data Protection Act 2012
:Framework: Ghana Health Service confidentiality rules
:Key Requirements:
   - Health data classified as sensitive
   - Consent required for sensitive data processing
   - Data Protection Commission oversight
   - Cross-border transfer restrictions

:Identifiers Detected:
   - Ghana Card Number
   - NHIS Number
   - Standard identifiers

Uganda (UG)
~~~~~~~~~~~

:Regulation: Data Protection and Privacy Act 2019 (DPPA 2019)
:Additional: Public Health Act (medical records confidentiality)
:Key Requirements:
   - Health data treated as sensitive
   - Explicit consent for sensitive data processing
   - Personal Data Protection Office oversight
   - Breach notification obligations

:Identifiers Detected:
   - National ID Number
   - NSSF Number (National Social Security Fund)
   - Standard identifiers

Common Data Fields
==================

All country configurations include these common data fields:

Personal Information
--------------------

- **First Name** (HIGH privacy)
- **Last Name** (HIGH privacy)
- **Middle Name** (MEDIUM privacy)
- **Date of Birth** (CRITICAL privacy)

Contact Information
-------------------

- **Phone Number** (HIGH privacy)
- **Email Address** (HIGH privacy)
- **Street Address** (HIGH privacy)
- **City** (MEDIUM privacy)
- **Postal/ZIP Code** (MEDIUM privacy)

Demographic Information
-----------------------

- **Gender** (LOW privacy)

Usage Examples
==============

Command-Line Interface
----------------------

Single Country
~~~~~~~~~~~~~~

De-identify data according to US regulations (default)::

   python -m scripts.utils.deidentify \
       --input-dir results/dataset/Indo-vap \
       --output-dir results/deidentified/Indo-vap

Specify a different country::

   python -m scripts.utils.deidentify \
       --countries IN \
       --input-dir results/dataset/Indo-vap \
       --output-dir results/deidentified/Indo-vap

Multiple Countries
~~~~~~~~~~~~~~~~~~

Process data that may contain identifiers from multiple countries::

   python -m scripts.utils.deidentify \
       --countries US IN ID BR \
       --input-dir results/dataset/Indo-vap \
       --output-dir results/deidentified/Indo-vap

All Countries
~~~~~~~~~~~~~

Enable detection for all supported countries::

   python -m scripts.utils.deidentify \
       --countries ALL \
       --input-dir results/dataset/Indo-vap \
       --output-dir results/deidentified/Indo-vap

List Supported Countries
~~~~~~~~~~~~~~~~~~~~~~~~

View all supported countries and their regulations::

   python -m scripts.utils.deidentify --list-countries

Python API
----------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from scripts.utils.deidentify import DeidentificationEngine, DeidentificationConfig
   
   # Configure for India
   config = DeidentificationConfig(
       countries=["IN"],
       enable_country_patterns=True
   )
   
   # Create engine
   engine = DeidentificationEngine(config=config)
   
   # De-identify text
   text = "Patient Rajesh Kumar, Aadhaar: 1234 5678 9012"
   deidentified = engine.deidentify_text(text)
   print(deidentified)
   # Output: "Patient [PATIENT-...], Aadhaar: [SSN-...]"

Multiple Countries
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.utils.deidentify import DeidentificationEngine, DeidentificationConfig
   
   # Configure for multiple countries
   config = DeidentificationConfig(
       countries=["US", "IN", "BR", "ID"],
       enable_country_patterns=True
   )
   
   engine = DeidentificationEngine(config=config)
   
   # Process mixed international data
   texts = [
       "US Patient: John Doe, SSN: 123-45-6789",
       "India Patient: Rajesh Kumar, Aadhaar: 1234 5678 9012",
       "Brazil Patient: Maria Silva, CPF: 123.456.789-01"
   ]
   
   for text in texts:
       deidentified = engine.deidentify_text(text)
       print(deidentified)

Working with Country Regulations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.utils.country_regulations import CountryRegulationManager
   
   # Create manager for specific countries
   manager = CountryRegulationManager(countries=["US", "IN"])
   
   # Get all data fields
   all_fields = manager.get_all_data_fields()
   print(f"Total fields: {len(all_fields)}")
   
   # Get country-specific fields
   country_fields = manager.get_country_specific_fields()
   for field in country_fields:
       print(f"{field.display_name}: {field.description}")
   
   # Get regulatory requirements
   requirements = manager.get_requirements_summary()
   for country, reqs in requirements.items():
       print(f"\n{country} Requirements:")
       for req in reqs:
           print(f"  - {req}")
   
   # Export configuration
   manager.export_configuration("config/country_regulations.json")

Integration with Main Pipeline
-------------------------------

Enable country-specific de-identification in the main pipeline::

   # Edit main.py or use command-line arguments
   python main.py --enable-deidentification --countries US IN ID

Configuration Options
=====================

DeidentificationConfig Parameters
----------------------------------

When creating a ``DeidentificationConfig`` object, you can specify:

``countries``
   List of country codes (e.g., ``["US", "IN", "BR"]``) or ``None`` for default (US).
   Use ``["ALL"]`` to enable all supported countries.

``enable_country_patterns``
   Boolean. If ``True``, loads and uses country-specific detection patterns.
   Default: ``True``

Example::

   config = DeidentificationConfig(
       countries=["US", "IN", "ID", "BR"],
       enable_country_patterns=True,
       enable_encryption=True,
       enable_validation=True
   )

Best Practices
==============

1. **Know Your Data**: Understand which countries your data originates from to select appropriate regulations.

2. **Use Specific Countries**: Rather than using ``ALL``, specify only the countries relevant to your dataset for optimal performance.

3. **Validate Output**: Always verify that no PHI/PII remains after de-identification by reviewing the output files.

4. **Review Regulations**: Familiarize yourself with the specific requirements of each regulation you're working with.

5. **Keep Encryption Enabled**: Always keep mapping encryption enabled in production environments.

6. **Document Compliance**: Maintain records of which regulations you're complying with and how.

Legal Compliance Notes
======================

.. warning::
   This tool provides **technical capabilities** for de-identification but does not guarantee legal compliance. Always:
   
   - Consult with legal counsel familiar with applicable regulations
   - Conduct Data Protection Impact Assessments (DPIA) where required
   - Maintain documentation of your de-identification process
   - Regularly review and update your compliance procedures
   - Ensure proper Business Associate Agreements (BAAs) are in place
   - Implement appropriate security safeguards beyond de-identification

Cross-Border Data Transfers
----------------------------

When transferring data across borders, ensure compliance with:

- **EU/UK**: Adequacy decisions, Standard Contractual Clauses (SCCs), or Binding Corporate Rules (BCRs)
- **APEC**: Cross-Border Privacy Rules (CBPR) system
- **Africa**: African Union Convention on Cyber Security and Personal Data Protection
- **Country-specific**: Data localization requirements (e.g., Nigeria, Indonesia)

Retention and Deletion
-----------------------

Follow applicable retention requirements:

- **HIPAA (US)**: 6 years from creation or last effective date
- **GDPR (EU/UK)**: No longer than necessary for the purpose
- **State/Provincial Laws**: May have specific requirements

Breach Notification
-------------------

Understand breach notification timelines:

- **72 hours**: GDPR (EU), UK GDPR, Indonesia, Nigeria, Philippines
- **60 days**: HIPAA (US)
- **Varies**: Other jurisdictions - consult local regulations

Additional Resources
====================

Official Regulatory Bodies
--------------------------

**United States**
   - HHS Office for Civil Rights (OCR): https://www.hhs.gov/ocr/

**European Union**
   - European Data Protection Board: https://edpb.europa.eu/

**United Kingdom**
   - Information Commissioner's Office (ICO): https://ico.org.uk/

**Canada**
   - Office of the Privacy Commissioner: https://www.priv.gc.ca/

**Australia**
   - Office of the Australian Information Commissioner: https://www.oaic.gov.au/

**Individual Countries**
   - Consult national data protection authorities

Documentation
-------------

- :ref:`deidentification` - General de-identification guide
- :ref:`quickstart` - Getting started with RePORTaLiN
- :ref:`configuration` - Configuration options

API Reference
-------------

- ``scripts.utils.country_regulations`` - Country regulation management
- ``scripts.utils.deidentify`` - De-identification engine

See Also
========

- :doc:`deidentification` - Comprehensive de-identification documentation
- :doc:`usage` - General usage guide
- :doc:`troubleshooting` - Common issues and solutions
