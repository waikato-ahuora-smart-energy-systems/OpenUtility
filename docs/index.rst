OpenUtility
===========

OpenUtility is a Pyomo-based utility-system optimization package for
replicating selected methods and results from Julia Jimenez-Romero's thesis.
The current user path is a notebook-first workflow: import one helper, solve a
checked thesis case study, then inspect comparison tables and graphs.

Notebook-first workflow
-----------------------

Start with the checked example notebook:

``examples/notebooks/thesis_table_2_9_case_study.ipynb``

The notebook loads Contribution 2 case-study 2, solves the physical-profile
Table 2-9 scenarios with the SciPy/HiGHS Pyomo model path, and presents model
versus thesis outputs as pandas tables and matplotlib plots.

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
