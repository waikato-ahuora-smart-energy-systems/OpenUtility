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
uses alpha ``schema_version="1.0"`` ``HprPerformanceMap`` data with temperature
coordinates, part-load points, units, thermodynamic backend metadata, model
identity, and structured JSON provenance. OpenPinch remains the preferred place
to generate those maps from CoolProp-backed HPR targeting or explicit TESPy
workflows, but OpenUtility accepts only plain Python/JSON-like data and does not
import those packages.

Schema ``1.0`` is fixed-capacity and single-source/single-sink per curve. It
uses external thermal service temperatures in ``degC`` and duties and power in
``kW``. The final producer-facing field names are:

* ``schema_version``: currently only ``"1.0"`` is accepted.
* ``map_id``: stable map identifier referenced by ``HprCandidate.map_id``.
* ``mode``: ``"heat_pump"`` or ``"refrigeration"``.
* ``units``: exact unit mapping for ``source_temperature``,
  ``sink_temperature``, ``q_source``, ``q_sink``, and ``electric_power``.
* ``reference_capacity``: absolute useful duty for full load.
* ``reference_capacity_basis``: ``"q_sink"`` for heat pumps and ``"q_source"``
  for refrigeration.
* ``interpolation_topology``: currently ``"ordered_part_load_curve"``.
* ``thermodynamic_backend``: producer-declared backend, such as ``"coolprop"``
  or explicit TESPy workflow identifiers.
* ``model_id``: producer model or calculation identifier.
* ``provenance``: structured JSON-like object preserved without string
  coercion.
* ``cop_convention``: ``"heating"`` for heat pumps and ``"cooling"`` for
  refrigeration.
* ``energy_balance_tolerance``: optional tolerance for duty, power, capacity,
  and COP consistency checks.
* ``temperature_match_tolerance``: optional tolerance for matching period node
  temperatures to map curve coordinates.

``HprCandidate`` combines a physical map with OpenUtility-owned optimization
data: thermal-node assignments, fixed-capacity candidate size, costs, and
selection policy. The Pyomo model only interpolates within the one ordered
part-load curve that matches a candidate's period source and sink temperatures.
For ``schema_version="1.0"``, map points are absolute duties at the map
reference capacity. If ``HprCandidate.fixed_capacity`` differs from
``reference_capacity``, OpenUtility applies one constant scale factor to
``q_source``, ``q_sink``, and ``electric_power``.

Ordered part-load curves are encoded with lambda variables plus segment binary
variables so dispatch can interpolate only between adjacent load-fraction
breakpoints. Nonadjacent global convex mixing is prohibited.

HPR electricity
---------------

The current HPR implementation uses a period-indexed HPR electricity overlay:
``hpr_power`` is balanced against ``hpr_grid_power_import`` and
``hpr_grid_power_export`` for each operating period. The original utility-system
power balance remains a static scalar balance for non-HPR equipment and onsite
generation. This is a deliberate alpha limitation; OpenUtility should not be
described as having one fully integrated period-indexed electricity balance
until the non-HPR power generation and grid variables are converted to the same
multi-period topology.
