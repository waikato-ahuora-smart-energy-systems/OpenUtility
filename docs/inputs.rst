Input Data
==========

The thesis inputs used by the current case-study workflow are embedded as typed
Python fixtures so tests and notebooks use the same source of truth.

Primary input fixtures
----------------------

``OpenUtility/benchmarks.py``
   Thesis constants and extracted table rows.

``STYLE_CASE_STUDY_2_SITE_CONFIG``
   Site demand, export limit, operating hours, finance constants, cooling-water
   temperature rise, boiler-feedwater temperature, and VHP pressure.

``STYLE_CASE_STUDY_2_RESOURCES``
   Fuel, electricity, cooling-water, and treated-water costs.

``STYLE_CASE_STUDY_2_EQUIPMENT_COSTS``
   Linear equipment capital-cost coefficients from the thesis references.

``STYLE_CASE_STUDY_2_STREAMS``
   Process stream rows used to reconstruct the heat-interval profile.

``STYLE_CASE_STUDY_2_RESULTS``
   STYLE case-study 2 benchmark outputs.

``CONTRIBUTION2_CASE_STUDY_2_BEST_CONFIGURATIONS``
   Contribution 2 Table 2-9 best-configuration rows used by the notebook
   workflow.

Model construction
------------------

``OpenUtility/style/case_studies.py`` turns the benchmark fixtures into
``StyleModelData`` instances. The notebook workflow uses
``style_case_study_2_contribution2_physical_profile_catalog`` for the
physical-profile Table 2-9 scenarios.

OpenPinch reuse
---------------

When OpenPinch is installed, ``style_case_study_2_heat_interval_profile`` first
converts the thesis stream fixtures into real OpenPinch ``Stream`` objects using
``openpinch_streams_from_thesis_streams``. Notebook users can also request an
OpenPinch ``StreamCollection`` with
``openpinch_stream_collection_from_thesis_streams``. These conversions reuse
OpenPinch's hot/cold stream classification, collection container, and
shifted-temperature properties while preserving the explicit thesis
heat-capacity-flow values used by the STYLE heat profile. If OpenPinch is
unavailable, the case-study builder falls back to the OpenPinch-compatible
fixture objects.

Generated outputs
-----------------

The CSV files under ``examples/`` are generated outputs used as regression
fixtures. They are useful for review, but they are not the authoritative input
data for the package.
