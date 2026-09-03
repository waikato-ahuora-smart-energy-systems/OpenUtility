Notebook Workflow
=================

OpenUtility is designed to work cleanly from a small notebook or script. The
public package does not ship replication notebooks; test coverage uses a
minimal reproducible example that builds package-owned model data directly.

Minimal notebook
----------------

.. code-block:: python

   from OpenUtility import (
       SteamLevelCandidate,
       UtilitySystemModelData,
       build_utility_system_model,
       pyomo_utility_system_solver,
   )

   data = UtilitySystemModelData(
       steam_mains=("MP",),
       steam_levels=(
           SteamLevelCandidate(
               name="MP_100",
               steam_main="MP",
               temperature=100.0,
               source_heat_available=5.0,
               sink_heat_demand=5.0,
               generation_enthalpy_delta=1.0,
               use_enthalpy_delta=1.0,
               source_heat_upper_bound=5.0,
               sink_heat_upper_bound=5.0,
           ),
       ),
       power_demand=0.0,
       grid_import_limit=0.0,
       grid_export_limit=0.0,
   )
   model = build_utility_system_model(data)
   status = pyomo_utility_system_solver("appsi_highs")(model)

   status.termination_condition
