Notebook Workflow
=================

OpenUtility is intended to be driven from small Jupyter notebooks. The public
workflow helper hides the catalog construction, calibration target application,
solver setup, and benchmark comparison plumbing.

Checked example
---------------

The runnable example notebook is checked in at:

``case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/notebooks/replication.ipynb``

Download it from the documentation build:

:download:`style_table_2_9_case_study.ipynb <../case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/notebooks/replication.ipynb>`

Minimal notebook
----------------

.. code-block:: python

   from case_study.jimenez_romero_utility_system_optimization.contribution2_integrated_hot_oil_fsr import run_contribution2_table_2_9_case_study

   case_study = run_contribution2_table_2_9_case_study(
       catalog="physical-profile",
       apply_fuel_targets=True,
       apply_operating_targets=True,
       solver_time_limit=20.0,
   )

   summary = case_study.summary_table()
   comparison = case_study.comparison_table()

The summary table contains one row per STYLE scenario and reports whether all
comparison fields are within tolerance. The comparison table contains one row
per scenario and output field.

Tables
------

.. code-block:: python

   summary

.. code-block:: python

   comparison

.. code-block:: python

   case_study.field_table("total_annualized_cost")

Graphs
------

.. code-block:: python

   axes = case_study.plot_field_comparison("total_annualized_cost")
   axes.figure.tight_layout()
   axes.figure

.. code-block:: python

   axes = case_study.plot_summary_deviations()
   axes.figure.tight_layout()
   axes.figure

The plotting methods return matplotlib axes so the notebook author can keep
customizing labels, limits, colours, and export settings.
