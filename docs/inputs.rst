Input Data
==========

The extracted inputs used by the current case-study workflow are embedded as
typed Python fixtures outside the core package so tests and notebooks use the
same source of truth without making ``OpenUtility`` itself a data archive.

Primary input fixtures
----------------------

``case_study/jimenez_romero_utility_system_optimization/benchmarks.py``
   Source constants and extracted table rows for the Jimenez-Romero
   utility-system optimization replication scope.

``case_study/jimenez_romero_utility_system_optimization/style_stage1_hot_oil_and_steam_mains/``
   Descriptive aliases for the STYLE stage 1 hot-oil and steam-main targets.

``case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/``
   Descriptive aliases for the Contribution 2 integrated hot-oil, steam-main,
   gas-turbine, HRSG, and flash-steam-recovery case study.

``case_study/jimenez_romero_utility_system_optimization/contribution2_computational_performance/``
   Descriptive aliases for the Contribution 2 solver performance, model-size,
   and steam-property comparison rows.

``STYLE_CASE_STUDY_2_SITE_CONFIG``
   Site demand, export limit, operating hours, finance constants, cooling-water
   temperature rise, boiler-feedwater temperature, and VHP pressure.

``STYLE_CASE_STUDY_2_RESOURCES``
   Fuel, electricity, cooling-water, and treated-water costs.

``STYLE_CASE_STUDY_2_EQUIPMENT_COSTS``
   Linear equipment capital-cost coefficients from the source references.

``STYLE_CASE_STUDY_2_STREAMS``
   Process stream rows used to reconstruct the heat-interval profile.

``STYLE_CASE_STUDY_2_RESULTS``
   STYLE case-study 2 benchmark outputs.

``CONTRIBUTION2_CASE_STUDY_2_BEST_CONFIGURATIONS``
   Contribution 2 Table 2-9 best-configuration rows used by the notebook
   workflow.

Model construction
------------------

``case_study/jimenez_romero_utility_system_optimization/style_model_builders.py``
turns the benchmark fixtures into
``StyleModelData`` instances. The notebook workflow uses
``style_case_study_2_contribution2_physical_profile_catalog`` for the
physical-profile Table 2-9 scenarios.

OpenPinch reuse
---------------

The Contribution 2 process stream fixtures are real OpenPinch ``Stream``
objects, collected in an OpenPinch ``StreamCollection`` and grouped in an
OpenPinch ``Zone`` with process subzones ``A`` through ``E``. The extracted
``heat_load`` is mapped to OpenPinch ``heat_flow``. ``dt_cont`` is half the extracted minimum temperature difference.

OpenUtility uses OpenPinch-derived ``CP``, ``type``, ``t_min_star``, and
``t_max_star`` values when building shifted thermal intervals. The thermal
helpers accept an OpenPinch ``Stream``, ``StreamCollection``, ``Zone``, or other
iterable of OpenPinch streams.

Potential OpenPinch upstream helpers
------------------------------------

The case-study source literature uses heat-duty terminology, so a
``heat_duty`` alias for ``heat_flow`` or support for ``heat_duty=`` in
``Stream(...)`` would reduce mapping code. A ``metadata`` or ``tags`` mapping on
``Stream`` would also help preserve source-table provenance. Finally, a
``Zone.add_stream(stream)`` helper could route hot and cold process streams into
the appropriate collection based on ``stream.type``.

Generated outputs
-----------------

The CSV files under the case-study package ``outputs/`` folders are generated
outputs used as regression fixtures. They are useful for review, but they are
not the authoritative input data for the package.
