OpenUtility
===========

OpenUtility is a Pyomo-based utility-system optimization package for
replicating selected Jimenez-Romero utility-system case-study methods and
results.
The current user path is a notebook-first workflow: import one helper, solve a
checked STYLE case study, then inspect comparison tables and graphs.

Notebook-first workflow
-----------------------

Start with the checked example notebook:

``case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/notebooks/replication.ipynb``

The notebook loads Contribution 2 case-study 2, solves the physical-profile
Table 2-9 scenarios with the Pyomo/HiGHS SolverFactory path, and presents model
versus benchmark outputs as pandas tables and matplotlib plots.

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   notebook_workflow
   inputs
   api

.. toctree::
   :maxdepth: 1
   :caption: Development

   developer_checklist
