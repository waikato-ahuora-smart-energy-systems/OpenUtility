OpenUtility
===========

OpenUtility is a Pyomo-based utility-system optimization package with thermal
profile handling and HPR investment/dispatch optimization. HPR is the umbrella
term for heat pump and refrigeration assets.

The reusable package exposes typed model inputs, Pyomo model construction,
solver adapters, reporting helpers, and bilevel decomposition utilities.
OpenUtility does not import OpenPinch or TESPy; it consumes plain data that
upstream targeting or thermodynamic tools can export.
Private replication workflows are intentionally outside the public package and
are not part of the release test boundary.

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
   release_strategy
