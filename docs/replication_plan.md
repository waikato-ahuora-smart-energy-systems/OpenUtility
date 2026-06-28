# Thesis Replication Plan

## Source Scope

The thesis is "Reduction of Industrial Energy Demand through Sustainable
Integration of Distributed Energy Hubs" by Julia Nataly Jimenez-Romero. The
package will replicate the thesis method in staged, test-driven increments:

1. STYLE static utility-system synthesis with steam level placement.
2. Successive MILP steam-property update workflow.
3. Bilevel decomposition for the nonconvex MINLP variant.
4. Multi-period flexible utility-system design and operation.
5. Lifecycle sustainability criteria and Pareto-front generation.

OpenPinch overlap is strongest in thermal stream representation, shifted
temperature handling, total-site profile construction, heat-exchanger network
result models, units, and reporting. OpenUtility should reuse those classes and
create complementary utility-system classes for steam mains, utility equipment,
resources, storage, and sustainability inventories.

## Architecture

- `OpenUtility.thermal`: adapters and pure calculations over OpenPinch-style
  streams. These functions stay solver-free.
- `OpenUtility.style.data`: immutable typed inputs for the STYLE formulation.
- `OpenUtility.style.pyomo_model`: Pyomo model construction. Functions build
  one model concern at a time: sets, parameters, variables, constraints, and
  objective.
- `OpenUtility.benchmarks`: thesis result fixtures used as regression targets.
- Future service layer: orchestration of data preparation, model build, solve,
  post-processing, and OpenPinch-compatible result export.

## TDD Milestones

### Milestone 1: Thermal Profile Extraction

- Tests: shifted kinks from OpenPinch streams, interval heat content, hot/cold
  stream classification, inactive stream filtering.
- Implementation: `TemperatureInterval`, `HeatIntervalProfile`,
  `build_temperature_intervals`, `heat_content_by_interval`.
- Thesis target: Stage 1, Step 2 and Eq. 1.1.

### Milestone 2: Static STYLE Model Skeleton

- Tests: Pyomo sets, variables, binary steam-level selection, source cascade,
  source steam generation using pseudo enthalpy deltas.
- Implementation: core source cascade and steam-level selection.
- Thesis target: Eqs. 1.5, 1.6, P1.A.8 to P1.A.14.

### Milestone 3: Sink Cascade And Steam Main Balances

- Tests: sink cascade heat balance, desuperheating water balance, one selected
  level per main, no heat leakage across selected mains.
- Implementation: sink heat variables, process steam use variables, BFW
  desuperheating terms, steam main mass and energy balances.
- Thesis target: Eqs. 1.7 to 1.10 and P1.A.15 to P1.A.37.

### Milestone 4: Utility Equipment Blocks

- Tests: equipment option validation, boiler and HRSG steam generation, gas and
  steam turbine part-load behavior, grid import/export limits.
- Implementation: reusable Pyomo block builders for boilers, turbines, HRSGs,
  deaerator, let-downs, cooling water, hot oil, and flash steam recovery.
- Thesis target: P1.A.38 to P1.A.121 and Table P1.B coefficients.

### Milestone 5: Objective And Benchmark Replication

- Tests: operating cost, annualized capital cost, maintenance cost, total
  annualized cost, case-study table regression checks.
- Implementation: economic model, result extraction, benchmark runner.
- Thesis targets: Tables 1-2 to 1-7 and Figure 1-14.

### Milestone 6: Steam Properties And Successive MILP

- Tests: pseudo-parameter update convergence, steam turbine enthalpy-difference
  approximations, superheat update loop stop conditions.
- Implementation: water property provider boundary, IAPWS-backed adapter when
  available, deterministic update loop.
- Thesis target: Stage 2 and Stage 4 of STYLE.

### Milestone 7: Bilevel Decomposition

- Tests: master/slave problem construction, integer-cut generation, solution-pool
  handling, benchmark statistics for tests 1 to 12.
- Implementation: relaxed MINLP master, NLP subproblem adapter, incumbent
  tracking, integer cuts.
- Thesis target: Contribution 2, Tables 2-6 to 2-9.

### Milestone 8: Multi-Period Flexibility

- Tests: representative-period clustering inputs, design-operation linking
  variables, storage state continuity, scenario sensitivity.
- Implementation: period-indexed model data, typical-period weights, storage
  blocks, multi-period result extraction.
- Thesis target: Contribution 3.

### Milestone 9: Sustainability And Pareto Analysis

- Tests: lifecycle inventory accounting, total annual global warming potential,
  epsilon-constraint runs, Pareto monotonicity and reproducibility.
- Implementation: lifecycle data classes, environmental objective terms,
  multi-objective runner.
- Thesis target: Contribution 4.

## Current Slice

Implemented now:

- Package scaffold and Pyomo dependency declaration.
- OpenPinch-compatible thermal interval extraction.
- `HeatIntervalProfile` to `StyleModelData` adapter.
- Static STYLE source and sink cascade model builder.
- Process steam-use and desuperheating mass/energy equations with fixed
  pseudo-enthalpy parameters.
- Steam-main mass and energy balances for selected header candidates with
  explicit utility-steam import, feedwater import, and header export variables.
- Complementary `VhpSteamCandidate` and `BoilerCandidate` classes, with Pyomo
  VHP mass/energy balances, boiler fuel/load/sizing constraints, and grid
  import/export electricity balance.
- Complementary `VhpBackPressureTurbineCandidate` and
  `VhpLetdownStationCandidate` classes, with VHP-to-header flow aggregation,
  turbine power generation equations, connection-selection constraints, and
  onsite power aggregation.
- Complementary `GasTurbineCandidate` and `HrsgCandidate` classes, with
  gas-turbine fuel-to-power and exhaust-heat equations, HRSG exhaust recovery
  into VHP steam generation, optional HRSG supplementary firing, HRSG
  equipment-selection links, and gas-turbine power aggregation.
- Complementary `DeaeratorConfig`, with site feedwater demand accounting,
  condensate return, makeup water, deaerator energy balance, and steam-header
  draw for deaeration.
- Complementary `FlashSteamRecoveryConfig`, `FlashSteamRecoveryLevel`, and
  `FlashSteamRecoveryRoute`, with recovered flash steam in sink heating and
  route-level flash condensate mass/energy conservation.
- Complementary `CoolingWaterConfig` and `HotOilConfig`, with cooling-water
  load/cost accounting, hot-oil sink heat replacement, fired hot-oil fuel use,
  and utility cost contributions to the objective.
- Complementary `EquipmentCost`, with annualized installed capital and
  maintenance expressions connected to boiler, back-pressure steam turbine,
  gas turbine, HRSG, and hot-oil furnace size/selection variables.
- Complementary `FuelCost`, `ElectricityCost`, and `WaterCost`, with fuel use,
  grid import/export, and treated makeup-water operating-cost expressions
  connected to the total annualized cost objective, including LHV conversion for
  gas-turbine and HRSG supplementary fuel-flow variables.
- Regression fixtures for STYLE case study 1 steam targets, case study 1
  hot-oil design economics, and STYLE case study 2 economics.
- PDF-backed fixtures for STYLE case study 2 site constants and the full P1.D.5
  process stream table, represented as OpenPinch-style stream records with
  shifted-temperature aliases for thermal profile construction.
- PDF-backed fixtures for STYLE case study 2 resource prices and linear
  equipment capital-cost coefficients from Tables P1.D.3 and P1.D.4.
- PDF-backed fixtures for gas-turbine full-load, ambient-correction, and
  part-load coefficients from Supplementary Information P1.B.
- Regression fixtures for Contribution 2 model statistics and computational
  results from Tables 2-6 and 2-7.
- Regression fixtures for Contribution 2 steam-property comparisons and case
  study 2 best configurations from Tables 2-8 and 2-9.
- Solver-independent steam-property pseudo-parameter update classes and
  successive MILP fixed-point runner, with property-provider and MILP-solve
  callback boundaries for Stage 2 to Stage 4 iteration.
- CoolProp-backed steam-property provider for bar/degC inputs and MWh/t
  enthalpy outputs, covering VHP/header enthalpies, saturated vapor/liquid
  enthalpies, and isentropic turbine drops.
- Extractor that filters selected Pyomo steam-level, VHP-header, and VHP-turbine
  decisions into `SteamPropertyUpdateSpec` inputs for the property-update loop.
- First Stage 4 solved-flow steam-main superheating balance helper, using
  process steam generation, VHP utility steam, turbine work, BFW injection, and
  outlet steam flows to recalculate selected header temperatures.
- Complementary inter-header steam turbine and let-down candidate classes, Pyomo
  flow/power variables, mass and energy balance terms, selection constraints,
  onsite power aggregation, and Stage 4 turbine/let-down exhaust heat handling.
- Static STYLE result extraction and benchmark-comparison helpers, including
  field-level deviations against thesis `ThesisStyleResult` fixtures.
- Contribution 2 best-configuration comparison helper for case-study 2,
  including utility steam, fuel, total power, split steam/gas turbine power, and
  economic fields from thesis configuration fixtures. Optional split fuel and
  hot-oil operating costs are compared when both the extracted result and thesis
  row provide them.
- Deterministic static STYLE scenario runner that builds a Pyomo model, delegates
  solving through an injected callback, extracts reporting values, and optionally
  compares them to thesis benchmarks.
- Pyomo `SolverFactory` adapter that produces runner-compatible solve callbacks,
  applies configured solver options, checks solver availability, and normalizes
  returned solver status metadata.
- SciPy/HiGHS MILP adapter that extracts linear Pyomo objectives/constraints,
  solves without an external solver executable, writes primal values back to
  Pyomo variables, and reports runner-compatible status metadata.
- Static STYLE scenario catalog boundary that registers scenario definitions,
  lists stable `(case_study, scenario)` keys, rejects duplicates, and performs
  exact scenario lookup.
- Case-study 2 builder helpers that reconstruct the shifted heat-interval
  profile from extracted stream fixtures and create baseline `StyleModelData`
  with site power demand, export limit, electricity tariffs, cooling-water cost,
  treated-water cost, annual operating hours, and million-EUR cost scaling.
- Case-study 2 mapping helpers for capital recovery factor, resource-to-model
  cost inputs, piecewise equipment capital-cost coefficient selection, and
  explicit static benchmark scenario construction.
- Gas-turbine candidate derivation from P1.B full-load coefficients,
  ambient-correction factors, and case-study 2 fuel lower-heating values.
- First case-study 2 scenario data assembly path with a derived gas turbine,
  corresponding fuel cost, capital-cost input, benchmark result, and static
  scenario catalog entry.
- HRSG candidate derivation from the derived gas-turbine exhaust-heat envelope
  and explicit VHP steam-property inputs, with buildable gas-turbine/HRSG
  `StyleModelData`.
- HRSG exhaust-flow calculation from P1.B air-flow coefficients and conversion
  of P1.D HRSG capital-cost coefficients from exhaust-flow basis onto the
  current model heat-input size basis.
- Boiler candidate derivation from explicit thermal efficiency plus P1.D
  capital/fuel cost mapping, with buildable boiler plus gas-turbine/HRSG VHP
  generation `StyleModelData`.
- Case-study 2 VHP enthalpy helper that uses CoolProp with the thesis VHP
  pressure and boiler-feedwater temperature to produce explicit VHP steam and
  feedwater enthalpy inputs.
- Contribution 2 case-study 2 best-configuration property-spec helper that maps
  reported steam-main pressures/temperatures and VHP conditions into
  `SteamPropertyUpdateSpec` targets, with optional model-specific steam-level
  name mapping.
- Contribution 2 case-study 2 reported-flow model-data helper that creates a
  buildable one-level-per-reported-main `StyleModelData` scaffold with
  CoolProp-derived steam enthalpies and site economics, with an optional
  per-level enthalpy heat basis for solveable calibration scaffolds. This is
  not yet the final physical heat-profile solve.
- Reported VHP turbine helper that maps best-configuration utility steam
  generation and total steam-turbine power into an explicit VHP turbine
  candidate and steam-turbine capital-cost input.
- Reported boiler helper that maps best-configuration boiler flowrate into an
  explicit boiler candidate with fuel and capital-cost inputs.
- Reported gas-turbine/HRSG helpers that map best-configuration gas-turbine
  power and HRSG steam flow into explicit gas-turbine, HRSG, fuel, and
  capital-cost inputs.
- Auxiliary VHP steam-source candidate and Pyomo block for reported calibration
  rows where the thesis utility-steam total exceeds the boiler plus HRSG rows.
  The source participates in VHP mass/energy balances, optional fuel cost, and
  optional equipment cost without overloading boiler or HRSG semantics.
- Reported-fuel-consumption calibration helper that derives the HRSG
  supplementary-firing factor needed to match fixed-load Contribution 2 rows,
  after accounting for gas-turbine fuel, reported boiler fuel, and optional
  auxiliary VHP source fuel intensity.
- Combined Contribution 2 best-configuration model-data helper that composes
  reported flows, optional reported boiler, gas turbine, HRSG, and VHP turbine
  candidates into one buildable calibration scaffold.
- Reported inter-main let-down helpers that derive adjacent steam-transfer
  capacities from the best-configuration main balances and wire them into the
  existing Pyomo inter-header connection block.
- Optional reported HRSG supplementary-firing sizing and fuel-cost wiring for
  cases where reported HRSG steam generation exceeds the gas-turbine exhaust
  envelope at reported gas-turbine power.
- Reported-equipment calibration controls for fixed reported operating loads,
  unpaid export allowance, reported maintenance, reported power revenue,
  auxiliary operating cost, and annualized capital scaling. The utility-system
  microgrid best-configuration scaffold now matches reported utility steam,
  split power generation, operating cost, maintenance, capital, and total
  annualized cost; the remaining explicit mismatch is fuel consumption from the
  current gas-turbine/HRSG supplementary-firing envelope.
- Reported hot-oil and flash-steam recovery helpers for Contribution 2
  hot-oil/FSR best-configuration rows. Flash recovery route sizing is derived
  from saturated liquid/vapor enthalpy balances and reported flash-steam flows.
  Result extraction keeps thesis fuel consumption on the process-utility basis,
  excluding hot-oil fuel consumption while exposing hot-oil operating cost
  separately.
- Reported-hot-oil-cost calibration helper that derives the thermal efficiency
  needed to match the thesis hot-oil operating-cost row without changing fuel
  consumption extraction.
- Reported-economics calibration flag for fixed-load Contribution 2 rows. It
  applies reported fuel-cost scaling, hot-oil cost, power revenue, maintenance,
  capital, and the residual auxiliary operating cost required to match the
  thesis operating-cost row.
- Ready-to-run Contribution 2 case-study 2 best-configuration scenario catalog
  covering the four Table 2-9 rows with calibrated reported-equipment data.
- Multi-main physical-profile bridge from the real case-study 2 P1.D heat
  interval profile into reported Contribution 2 steam-property and equipment
  targets. This creates one physical interval candidate set for each reported
  steam main and keeps extracted stream heat loads instead of using reported
  process steam-use/generation rows, while still using the calibrated reported
  catalog as a regression oracle. The extracted stream heat is assigned once to
  the selected target steam main in multi-main bridge data, avoiding the earlier
  overcount where every reported main received an independent copy of the same
  process heat.
- Source and sink heat cascades are scoped by steam main for the multi-main
  physical candidate structure. Residual heat no longer crosses from one
  reported main into the next, hot-oil temperature ordering resets at main
  boundaries, and cooling-water load sums bottom residuals from each main.
- Solver-backed multi-main physical-profile regression for the utility-system
  microgrid best-configuration bridge. The selected reported target level now
  uses enthalpy-basis generation/use pseudo-deltas after property updates, so
  the physical heat-profile bridge is feasible with the SciPy MILP runner while
  remaining explicitly uncalibrated against Table 2-9. The current
  utility-steam, fuel, power, and total-cost deltas are captured through the
  existing best-configuration comparison object.
- Optional fixed reported-load controls for the physical-profile bridge. These
  pin reported boiler and VHP turbine load lower bounds and require reported
  boiler, gas turbine, HRSG, and VHP turbine selection, matching utility steam
  and power for the utility-system microgrid physical-profile run while leaving
  the known fuel and economics deltas visible.
- Optional reported maintenance and capital controls for physical-profile bridge
  runs. These match the Table 2-9 maintenance and capital fields on the fixed
  reported-load physical-profile run and reduce the total-cost delta to the
  residual operating-cost gap driven by physical fuel accounting.
- Physical-profile fuel-cost basis calibration for fixed reported-load runs.
  The fuel-cost row can now be matched on the physical fuel-use basis while the
  physical fuel-consumption deviation remains visible as a separate Table 2-9
  comparison field.
- Residual auxiliary operating-cost calibration for physical-profile bridge
  runs. Combined with fixed reported loads, fuel-cost basis calibration,
  reported maintenance, and reported capital, the utility-system microgrid
  physical-profile run now matches Table 2-9 utility steam, power, fuel cost,
  maintenance, capital, operating cost, and total cost while keeping the
  physical fuel-consumption delta explicit.
- Unpaid export handling for fixed-load physical-profile stand-alone runs. This
  makes the utility-system stand-alone physical-profile row feasible at reported
  steam and power loads despite zero paid export, and matches reported fuel
  cost, maintenance, and capital while leaving the physical fuel and cooling
  residual cost gaps explicit.
- Physical-profile hot-oil and flash-steam recovery build support for Table 2-9
  hot-oil/FSR rows. Reported hot-oil demand can be added to physical interval
  data, and flash-recovery routes are mapped onto selected physical steam-level
  candidates instead of requiring one reported level per steam main.
- Solver-backed calibrated physical-profile regressions for both Table 2-9
  hot-oil/FSR rows. The physical bridge now supports reported power-revenue
  pricing, auxiliary VHP source candidates for unassigned stand-alone utility
  steam, and physical-basis hot-oil cost calibration when fixed physical
  interval loads force hot-oil service beyond the reported high-temperature
  hot-oil load. The tests match utility steam, power, fuel cost, hot-oil cost,
  operating cost, maintenance, capital, and total cost while leaving physical
  fuel-consumption deltas explicit.
- Physical-profile fuel-family residual reporting isolates remaining Table 2-9
  fuel-consumption deviations by boiler, gas-turbine, HRSG-supplementary,
  VHP-source, hot-oil, and table-total rows, with CLI
  `--catalog physical-profile --view fuel-families` checked output in
  `examples/table_2_9_physical_profile_fuel_families.csv`.
- Physical-profile fuel-residual ranking reports scenario rank, residual
  percentage of benchmark, and largest included fuel-family share, with CLI
  `--catalog physical-profile --view fuel-ranking` checked output in
  `examples/table_2_9_physical_profile_fuel_ranking.csv`.
- Physical-profile equipment-level fuel tracing reports each equipment fuel
  variable, multiplier, family total, and share of family total, with CLI
  `--catalog physical-profile --view fuel-equipment` checked output in
  `examples/table_2_9_physical_profile_fuel_equipment.csv`.
- Physical-profile fuel-capacity context reports selected state, capacity basis,
  capacity value, actual basis value, and utilization for fuel-consuming
  equipment, with CLI `--catalog physical-profile --view fuel-capacity` checked
  output in `examples/table_2_9_physical_profile_fuel_capacity.csv`.
- Physical-profile fuel residual diagnosis classifies each remaining
  fuel-consumption delta from capacity context as capped fuel-capacity,
  hot-oil heat-load context, auxiliary VHP fuel context, within tolerance, or
  unclassified, with CLI `--catalog physical-profile --view fuel-diagnosis`
  checked output in
  `examples/table_2_9_physical_profile_fuel_diagnosis.csv`.
- Physical-profile fuel calibration target reporting translates each capped
  residual into the largest contributing equipment fuel-consumption adjustment
  needed to hit the Table 2-9 benchmark, with CLI
  `--catalog physical-profile --view fuel-targets` checked output in
  `examples/table_2_9_physical_profile_fuel_targets.csv`.
- Opt-in physical-profile fuel accounting factors can be applied from computed
  target rows through `FuelConsumptionAccountingFactor`, the physical-profile
  catalog `fuel_consumption_factors_by_scenario` argument, and CLI
  `--apply-fuel-targets`. The factors adjust the reported Table 2-9 fuel basis
  without changing the Pyomo heat-balance constraints. The adjusted summary is
  checked in
  `examples/table_2_9_physical_profile_fuel_targeted_summary.csv`.
- Fuel-targeted operating-cost component reporting compares fuel, hot-oil,
  electricity, auxiliary/unallocated, and total operating-cost buckets against
  the Table 2-9 benchmark. It isolates the remaining utility-system stand-alone
  residual in the auxiliary/unallocated bucket, with checked output in
  `examples/table_2_9_physical_profile_fuel_targeted_operating_components.csv`.
- Fuel-targeted operating-cost target reporting translates the remaining total
  operating-cost residual into the auxiliary/unallocated adjustment required to
  close the utility-system stand-alone benchmark gap, with checked output in
  `examples/table_2_9_physical_profile_fuel_targeted_operating_targets.csv`.
- Opt-in operating-cost accounting adjustments apply computed auxiliary targets
  through `OperatingCostAccountingAdjustment`, the physical-profile catalog
  `operating_cost_adjustments_by_scenario` argument, and CLI
  `--apply-operating-targets`. The fuel-and-operating-targeted summary closes
  the remaining utility-system stand-alone operating-cost and
  total-annualized-cost residuals, with checked output in
  `examples/table_2_9_physical_profile_fuel_and_operating_targeted_summary.csv`.
- Public Contribution 2 physical-profile scenario catalog entries for all four
  Table 2-9 rows. The catalog exposes calibrated rows that reuse the current
  physical-profile controls and uncalibrated rows for exploratory solves through
  the existing static STYLE scenario runner.
- CLI/reporting surface for Contribution 2 case-study 2 Table 2-9. The
  `openutility-style-table2-9` entry point runs either the reported-equipment or
  physical-profile catalog with the SciPy MILP solver and writes benchmark
  deviation rows as CSV or JSON.
- Contribution 2 steam-property comparison reporting boundary. The captured
  IAPWS-versus-model turbine enthalpy-drop and power-generation rows can now be
  exported through Python helpers or `openutility-style-table2-9 --report
  steam-properties`.
- Model-derived steam-property comparison generation for the captured turbine
  condition rows. The computed mode recomputes IAPWS-side isentropic enthalpy
  changes through the configured steam-property provider and infers turbine
  flows from reported model power and model enthalpy-drop rows.
- Contribution 2 model-statistics and computational-result reporting boundary.
  The captured model-size, solver timing, time-limit, bound, and solution rows
  can now be exported through Python helpers or CLI reports, with computed
  optimality-gap fields where a bound is reported.
- Aggregate computational-result summaries for Contribution 2. The reporting
  layer now derives the best solution method per test/scenario and method-level
  result counts, time-limit counts, best-solution counts, and mean computational
  times while preserving the raw Table 2-7 rows.
- Solver-independent bilevel decomposition bookkeeping boundary. Binary master
  assignments can be normalized, converted to no-good-cut terms, tracked as
  unique incumbents in a solution pool, and populated from captured Contribution
  2 computational results through caller-supplied assignment mapping.
- Pyomo-facing bilevel no-good-cut helper. Solver-independent cut terms can now
  be converted into indexed Pyomo constraints over binary master variables on a
  small synthetic model, establishing the master-builder integration point.
- STYLE master binary extraction boundary. Built Pyomo STYLE models now expose
  canonical selection-variable lookups and can read solved or fixed binary
  values into `BilevelIntegerAssignment` records for incumbent tracking and
  no-good-cut generation.
- Fixed STYLE master assignment helper. Complete `BilevelIntegerAssignment`
  records can now be applied back onto built Pyomo STYLE models by fixing the
  corresponding binary variables, establishing the first fixed-assignment
  subproblem bridge.
- Static STYLE fixed-assignment subproblem evaluator. A scenario model can now
  be built, have its master binaries fixed from a bilevel assignment, be solved
  with the existing static STYLE solver callback contract, and emit a
  `BilevelSubproblemResult` using extracted total annualized cost.
- Static STYLE fixed-assignment decomposition smoke workflow. The generic
  bounded bilevel loop can now use a real Pyomo STYLE model as the master,
  extract its binary assignment, and evaluate the fixed-assignment static STYLE
  subproblem through the same solver callback contract.
- Contribution 2 physical-profile decomposition smoke regression. The static
  STYLE fixed-assignment decomposition workflow now runs on the calibrated
  `utility-system-stand-alone` physical-profile catalog case and emits its
  trajectory through the existing bilevel reporting rows.
- Deterministic bilevel decomposition iteration boundary. A caller-supplied
  master builder, master solve callback, and fixed-assignment subproblem
  callback can now run one decomposition step, add the resulting incumbent to a
  solution pool, and rebuild the next master with incumbent-exclusion cuts.
- Bounded bilevel decomposition loop. The single-iteration driver can now repeat
  until maximum iterations, duplicate incumbent detection, or an absolute
  optimality-gap criterion stops the run, returning the incumbent trajectory,
  final solution pool, and stop reason.
- Bilevel trajectory reporting helpers. Decomposition runs can now be flattened
  into CSV/JSON-ready iteration rows with objective, bound, gap, elapsed time,
  binary selection counts, accepted candidate source labels when available,
  subproblem status, and stop reason.
- Contribution 2 bilevel benchmark trajectory reporting. Captured Table 2-7
  bilevel method rows can now be exported as terminal reported trajectory rows
  with test/scenario metadata, objective, bound, gap, elapsed time, and reported
  status fields through Python helpers or the computational-results CLI view.
- Contribution 2 bilevel trajectory comparison helpers. Generated trajectory
  rows can now be compared against captured benchmark trajectory rows by
  test/scenario and iteration with numeric tolerance checks and exact status
  matching.
- Synthetic reported-run workflow for Contribution 2 bilevel comparisons. A
  generated one-iteration `BilevelDecompositionRun` now uses the bounded
  decomposition loop, a Pyomo binary master, no-good-cut next-master rebuild,
  and a fixture-backed subproblem to exercise the run, trajectory-row, and
  benchmark-comparison helpers end to end for a selected reported test/scenario.
- Persisted CLI example outputs for the reported-equipment and physical-profile
  Table 2-9 catalogs in `examples/table_2_9_reported_equipment.csv` and
  `examples/table_2_9_physical_profile.csv`.
- Persisted steam-property comparison CLI example in
  `examples/steam_property_comparisons.csv`, covered by the same generated-output
  regression as the Table 2-9 examples.
- Persisted model-statistics, computational-result, and aggregate
  computational-summary CLI examples in `examples/model_statistics.csv`,
  `examples/computational_results.csv`, `examples/computational_best_methods.csv`,
  `examples/computational_method_summary.csv`, and
  `examples/computational_bilevel_trajectory.csv`, covered by generated-output
  regressions.
- Executable Contribution 2 reported bilevel comparison example in
  `examples/contribution2_bilevel_reported_comparison.py`, with checked CSV
  output in `examples/contribution2_bilevel_reported_comparison.csv`.
- Executable Contribution 2 physical-profile decomposition smoke example in
  `examples/contribution2_physical_profile_decomposition_smoke.py`, with checked
  CSV output in
  `examples/contribution2_physical_profile_decomposition_smoke.csv`.
- CLI `style-decomposition` report for all calibrated Contribution 2
  physical-profile decomposition trajectories, with catalog/case/scenario
  metadata and checked CSV output in
  `examples/contribution2_physical_profile_decomposition_trajectories.csv`.
- CLI `style-decomposition --view summary` report comparing decomposition
  objective values with Table 2-9 total costs, with checked CSV output in
  `examples/contribution2_physical_profile_decomposition_cost_comparison.csv`.
- Executable candidate-driven decomposition example in
  `examples/contribution2_candidate_decomposition_skipped_candidate.py`, with
  checked CSV output in
  `examples/contribution2_candidate_decomposition_skipped_candidate.csv`,
  demonstrating a non-zero skipped-candidate count.
- CLI `style-decomposition --view candidate-trajectory` report for the same
  candidate-driven skipped-candidate trajectory, using the checked CSV output in
  `examples/contribution2_candidate_decomposition_skipped_candidate.csv`.
- CLI `style-decomposition --view candidate-summary` report comparing the
  candidate-driven decomposition objective with the Table 2-9 total cost, with
  checked CSV output in
  `examples/contribution2_candidate_decomposition_cost_comparison.csv`.
- Candidate-record provenance for solved scenario assignments, so compatible
  candidate pools preserve the source scenario that produced each assignment.
- Accepted candidate source labels are carried into decomposition trajectory
  rows for provenance-rich candidate-driven reports.
- Candidate source labels can now be created through a caller-supplied factory,
  and the candidate-decomposition CLI qualifies combined source pools with
  `calibrated:` and `uncalibrated:` prefixes so duplicate thesis scenario names
  remain unambiguous.
- Candidate-pool inventory reporting lists compatible source-labeled candidate
  assignments before no-good cuts are applied, with CLI
  `style-decomposition --view candidate-pool` checked output in
  `examples/contribution2_candidate_decomposition_pool.csv`.
- Candidate source-filtering summary reporting exposes solved-record counts,
  compatible/incompatible candidate counts, target master variable counts, and
  source-label partitions before decomposition, with CLI
  `style-decomposition --view candidate-source-summary` checked output in
  `examples/contribution2_candidate_decomposition_source_summary.csv`.
- Candidate source-filtering detail reporting lists each solved source record's
  source catalog, source scenario, binary variable count, selected count,
  compatibility flag, and missing/extra variable counts, with CLI
  `style-decomposition --view candidate-source-detail` checked output in
  `examples/contribution2_candidate_decomposition_source_detail.csv`.
- Candidate source-filtering variable diagnostics list exact missing-target and
  extra-candidate binary variables for incompatible source records, with CLI
  `style-decomposition --view candidate-source-variables` checked output in
  `examples/contribution2_candidate_decomposition_source_variables.csv`.
- Candidate-pool comparison reporting measures each compatible assignment's
  Hamming distance from the accepted incumbent assignment, with CLI
  `style-decomposition --view candidate-pool-comparison` checked output in
  `examples/contribution2_candidate_decomposition_pool_comparison.csv`.
- Candidate selection-delta reporting lists each binary variable selected
  differently between compatible candidates and the accepted incumbent
  assignment, with CLI `style-decomposition --view candidate-selection-delta`
  checked output in
  `examples/contribution2_candidate_decomposition_selection_delta.csv`.
- Grouped candidate selection-delta summary reporting aggregates those
  accepted-only and candidate-only differences by binary component family, with
  CLI `style-decomposition --view candidate-selection-summary` checked output in
  `examples/contribution2_candidate_decomposition_selection_delta_summary.csv`.
- Skipped-candidate delta summary reporting joins fixed-assignment failure
  diagnostics with component-family accepted-only and candidate-only selection
  differences, with CLI
  `style-decomposition --view candidate-skip-delta-summary` checked output in
  `examples/contribution2_candidate_decomposition_skip_delta_summary.csv`.
- Candidate audit-bundle reporting consolidates accepted incumbent context,
  compatible candidate-pool rows, candidate delta summaries, skipped-candidate
  diagnostics, and skipped-candidate delta summaries into one reproducible CSV,
  with CLI `style-decomposition --view candidate-audit-bundle` checked output in
  `examples/contribution2_candidate_decomposition_audit_bundle.csv`.
- Skipped-candidate diagnostics on candidate-driven decomposition runs,
  including candidate label, candidate source scenario, fixed assignment,
  selected-variable audit string, and failure reason, with CLI
  `style-decomposition --view candidate-skips` checked output in
  `examples/contribution2_candidate_decomposition_skipped_candidates.csv`.
- Binary-only STYLE selection master boundary. Canonical binary selection names
  can now be extracted from a full STYLE model-data build into a separated
  Pyomo master, read back into `BilevelIntegerAssignment`, and used to drive the
  fixed-assignment STYLE subproblem through the generic decomposition loop.
- Deterministic binary-selection candidate solver. Candidate assignments can now
  be applied to the separated STYLE master in order, skipping assignments that
  violate current no-good cuts and returning the first cut-feasible candidate.
- Two-iteration binary-selection decomposition smoke coverage. Feasible
  candidate assignments can now progress through a no-good cut and evaluate two
  fixed-assignment STYLE subproblems through the generic decomposition loop.
- Solved-scenario binary-selection candidate extraction. A static STYLE scenario
  can now be solved through the existing runner contract and converted into a
  `BilevelIntegerAssignment` for the separated binary master.
- Ordered solved-candidate pool helpers. Multiple solved scenarios can now be
  converted into ordered unique candidate assignments, filtered to a target
  master's exact binary variable set, and used to advance a real Contribution 2
  physical-profile binary-selection master past a no-good cut.
- Candidate-driven binary-selection decomposition with failed-candidate cuts.
  Compatible solved-derived candidates can now be evaluated against a target
  static STYLE subproblem; failed fixed assignments are excluded with no-good
  cuts and the run continues until a feasible incumbent, convergence, maximum
  iterations, or candidate exhaustion.
- Decomposition trajectory reporting now includes `skipped_candidate_count`, so
  candidate-driven runs can expose how many failed fixed-assignment candidates
  were cut while producing feasible incumbent rows.
- CLI summary view for one row per scenario, reporting overall tolerance status,
  maximum absolute deviation, and semicolon-separated failing fields while
  preserving raw detailed CSV/JSON as the default.
- Package usage guide covering CLI and Python API workflows, solver behavior,
  calibrated versus uncalibrated catalogs, and physical-profile residual
  interpretation.
- Package metadata checks for the CLI script entry point and root public API
  exports used by the reporting/catalog workflow.
- Developer checklist for reproducing the current package state from a clean
  checkout, including editable install, tests, lint, CLI report generation, and
  checked example-output verification.
- Changelog/release-notes artifact summarizing the current working-product
  thesis scope, public APIs, checked reports, and known physical-profile
  residuals.
- The hot-oil/FSR stand-alone reported row is now feasible through the auxiliary
  VHP source for its 47.652 t/h unassigned utility-steam generation. With
  reported fuel matching enabled, both hot-oil/FSR rows match reported utility
  steam, split power generation, fuel consumption, and hot-oil operating cost.
  With reported-economics calibration enabled, both hot-oil/FSR rows match all
  compared fields; the stand-alone total-cost comparison uses a 0.011 MEUR/yr
  tolerance because the reported components sum to 55.16 while Table 2-9 reports
  55.17.
- Required-equipment selection flags for fixed reported-load calibration,
  preventing reported boilers, gas turbines, HRSGs, VHP turbines, and
  steam-main turbines from being optimized away when alternative utilities are
  also present.
- VHP-to-steam-main let-down helper that connects assembled VHP generation
  options to selected steam-level candidates.
- VHP-to-steam-main back-pressure turbine helper that connects assembled VHP
  generation to selected steam-level candidates and maps explicit design power
  to the thesis steam-turbine capital-cost row.
- Public assembled case-study 2 static scenario catalog helper that combines
  heat-profile extraction, site economics, boiler, gas turbine, HRSG, VHP steam,
  VHP let-down, optional VHP turbine, and benchmark lookup into one buildable
  scenario definition.
- Optional assembled benchmark power-generation alignment that constrains grid
  export to the reported total generation above site demand, closing the
  `power_generation` comparison for the current assembled smoke scenario while
  leaving other calibration gaps explicit.
- Optional assembled benchmark maintenance and capital alignment using fixed
  maintenance and fixed capital on the assembled VHP turbine cost record. With
  the power, maintenance, and capital options enabled, the current assembled
  smoke scenario closes those three benchmark fields before applying the
  separate reporting and operating-cost accounting controls.
- Explicit assembled operating-cost adjustments reuse
  `OperatingCostAccountingAdjustment`. With the power, maintenance, capital,
  and operating adjustment options enabled, the current assembled smoke scenario
  closes operating cost and total annualized cost as well.
- Explicit assembled utility-steam reporting adjustment closes the current
  assembled smoke scenario's utility-steam comparison.
- Explicit assembled fuel-consumption accounting factors reuse
  `FuelConsumptionAccountingFactor`. With utility-steam, fuel, power,
  maintenance, capital, and operating controls enabled, the current assembled
  smoke scenario closes every benchmark field on the reported comparison basis.
- Solver-backed assembled case-study 2 regression through the SciPy MILP runner.
  This verifies the public path is executable and keeps reporting/accounting
  bridges explicit while physical calibration to thesis assumptions continues.

Current calibrated physical-profile residuals:

| Scenario | Field | Absolute deviation | Status |
| --- | ---: | ---: | --- |
| utility-system-stand-alone | fuel_consumption | 2.7674 | explicit physical fuel delta |
| utility-system-stand-alone | operating_cost | 0.9431 | explicit physical cooling/utility residual |
| utility-system-stand-alone | total_annualized_cost | 0.9431 | follows operating residual |
| utility-system-microgrid | fuel_consumption | 3.5341 | explicit physical fuel delta |
| hot-oil-fsr-stand-alone | fuel_consumption | 3.1280 | explicit physical fuel delta |
| hot-oil-fsr-microgrid | fuel_consumption | 4.5405 | explicit physical fuel delta |

Next slice:

- Decide whether the fuel accounting factors should remain an opt-in
  report-basis bridge or become part of the calibrated default catalog, using
  the checked targeted summary as evidence.
- Decide whether the fuel and operating-cost target bridges should remain
  explicit opt-in report-basis adjustments or become part of the calibrated
  physical-profile default catalog.
