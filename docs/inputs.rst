Input Data
==========

OpenUtility accepts typed Python objects rather than prescribing a file format.
Callers can load data from CSV, databases, spreadsheets, or generated workflows
and then construct ``UtilitySystemModelData``.

Model data
----------

``UtilitySystemModelData`` is the top-level input object. It contains steam
levels, optional VHP headers and equipment candidates, power import/export
limits, cost settings, and reporting adjustments. Model construction is
deterministic: the same input object produces the same Pyomo variables,
constraints, and objective.

Plain thermal data
------------------

Thermal helpers accept any stream-like object exposing ``CP``, ``type``,
``t_min_star``, and ``t_max_star`` values. OpenPinch can export compatible
values, but OpenUtility does not import OpenPinch.

HPR data
--------

HPR is the umbrella term for heat pump and refrigeration assets. OpenUtility
uses versioned ``HprPerformanceMap`` data with temperature coordinates,
part-load points, units, thermodynamic backend metadata, model identity, and
provenance. OpenPinch remains the preferred place to generate those maps from
CoolProp-backed HPR targeting or explicit TESPy workflows.

``HprCandidate`` combines a physical map with OpenUtility-owned optimization
data: thermal-node assignments, fixed-capacity candidate size, costs, and
selection policy. The Pyomo model only interpolates within the one ordered
part-load curve that matches a candidate's period source and sink temperatures.
