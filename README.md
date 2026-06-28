# OpenUtility

OpenUtility is a Pyomo-based package for replicating the utility-system
optimization methods and benchmark results from Julia Jimenez-Romero's thesis,
starting with the STYLE static synthesis framework and growing toward the
multi-period and sustainability extensions.

## Notebook Quick Start

The primary workflow is a small Jupyter notebook. Open the checked example at
`examples/notebooks/thesis_table_2_9_case_study.ipynb`, or start with:

```python
from OpenUtility import run_thesis_table_2_9_case_study

case_study = run_thesis_table_2_9_case_study(
    catalog="physical-profile",
    apply_fuel_targets=True,
    apply_operating_targets=True,
)

summary = case_study.summary_table()
comparison = case_study.comparison_table()
axes = case_study.plot_field_comparison("total_annualized_cost")
```

The first implementation slice contains:

- OpenPinch-compatible stream interval extraction for total site profiles.
- Optional conversion of thesis process stream fixtures into real OpenPinch
  `Stream` and `StreamCollection` objects for case-study heat-profile
  construction and notebook exploration when OpenPinch is installed, with a
  fixture fallback when it is not.
- Regression fixtures for STYLE case studies 1 and 2 plus Contribution 2
  benchmark tables reported in the thesis.
- PDF-backed case-study 2 site constants and process stream fixtures from
  Supplementary Information P1.D, exposed as OpenPinch-style shifted-temperature
  stream records for reuse by thermal profile builders.
- PDF-backed case-study 2 resource prices and linear equipment capital-cost
  coefficient fixtures from Supplementary Information P1.D.
- PDF-backed gas-turbine performance coefficient fixtures from Supplementary
  Information P1.B.
- A maintainable Pyomo model-building boundary for the static STYLE source and
  sink cascades, steam-use/desuperheating equations, steam-main mass/energy
  balances, VHP boiler generation, VHP turbine/let-down connections,
  gas-turbine/HRSG generation with supplementary firing, electricity balance,
  cooling-water, hot-oil, fuel, electricity, and makeup-water utility cost
  terms, energy-basis gas-turbine and supplementary-firing fuel accounting,
  equipment capital/maintenance cost expressions, deaerator feedwater accounting,
  flash-steam recovery, and steam-level selection structure.
- A solver-independent successive MILP steam-property update workflow for
  recalculating fixed pseudo-parameters between STYLE optimization iterations.
- A CoolProp-backed steam-property provider using bar, degrees Celsius, and
  MWh/t units for VHP/header enthalpies, saturated vapor/liquid enthalpies, and
  isentropic turbine drops.
- A solved-model extraction helper that filters selected Pyomo steam levels,
  VHP headers, and VHP turbines into property-update inputs.
- A first Stage 4 solved-flow superheating balance helper that recalculates
  selected steam-main temperatures from Pyomo mass and energy flows.
- Inter-header steam turbine and let-down candidates with Pyomo mass/energy
  balances and Stage 4 exhaust heat accounting.
- Static STYLE result extraction and benchmark-comparison helpers for solved
  Pyomo models.
- Contribution 2 case-study 2 best-configuration comparison helpers that check
  extracted utility steam, fuel, total power, split steam/gas turbine power, and
  cost values against thesis fixtures, including optional split fuel and hot-oil
  operating costs when the thesis row reports them.
- A deterministic static STYLE scenario runner that builds the Pyomo model,
  delegates solving through an injected callback, extracts results, and compares
  them with thesis benchmark fixtures when provided.
- A Pyomo `SolverFactory` adapter that turns configured MILP solvers into
  runner-compatible solve callbacks while normalizing solver status metadata.
- A SciPy/HiGHS MILP adapter for linear Pyomo models, including solution
  write-back into Pyomo variables and runner-compatible status reporting when
  external solvers such as GLPK or CBC are not installed.
- A static STYLE scenario catalog boundary for registering, listing, and looking
  up benchmark scenario definitions by `(case_study, scenario)` key.
- Case-study 2 builder helpers that reconstruct the shifted heat-interval
  profile from extracted streams and create baseline `StyleModelData` with site
  power, export, electricity, cooling-water, and treated-water inputs.
- Case-study 2 mapping helpers for capital recovery, resource costs, piecewise
  equipment capital-cost coefficients, and explicit benchmark scenario wrappers.
- Gas-turbine candidate derivation from P1.B full-load coefficients, ambient
  correction factors, and case-study 2 fuel data.
- A first case-study 2 scenario data assembly path with a derived gas turbine,
  matching fuel cost, capital-cost input, benchmark result, and scenario catalog.
- HRSG candidate derivation from the derived gas-turbine exhaust-heat envelope
  and explicit VHP steam-property inputs, with buildable gas-turbine/HRSG case
  study data.
- HRSG exhaust-flow calculation from P1.B air-flow coefficients and conversion
  of P1.D HRSG capital-cost coefficients onto the model heat-input size basis.
- Boiler candidate derivation from explicit thermal efficiency plus P1.D
  capital/fuel cost mapping, with buildable boiler plus gas-turbine/HRSG VHP
  generation data.
- Case-study 2 VHP enthalpy helper that computes steam and boiler-feedwater
  enthalpy inputs from the thesis VHP pressure/feedwater temperature and a
  selected VHP steam temperature.
- Contribution 2 case-study 2 best-configuration property-spec helper that
  converts reported steam-main pressures/temperatures and VHP conditions into
  `SteamPropertyUpdateSpec` targets for the CoolProp update workflow.
- Contribution 2 case-study 2 reported-flow model-data helper that creates a
  buildable one-level-per-reported-main `StyleModelData` scaffold with
  CoolProp-derived enthalpies and site economics, including an optional
  per-level enthalpy heat basis for solveable calibration scaffolds.
- Reported VHP turbine helper that converts best-configuration utility steam
  generation and total steam-turbine power into an explicit VHP turbine
  candidate and steam-turbine capital-cost input.
- Reported boiler helper that converts best-configuration boiler flowrate into
  an explicit boiler candidate with matching fuel and capital-cost inputs.
- Reported gas-turbine/HRSG helpers that convert best-configuration gas-turbine
  power and HRSG steam flow into explicit gas-turbine, HRSG, fuel, and
  capital-cost inputs.
- Auxiliary VHP steam-source candidates for reported calibration rows where the
  thesis utility-steam total exceeds reported boiler and HRSG generation, with
  optional fuel accounting hooks.
- A reported-fuel-consumption calibration helper that derives the HRSG
  supplementary-firing factor needed to match fixed-load thesis rows.
- A combined Contribution 2 best-configuration model-data helper that composes
  reported flows, boiler, gas turbine, HRSG, and VHP turbine candidates into one
  buildable scaffold for calibration.
- Adjacent inter-main let-down helpers that derive reported steam transfers
  from best-configuration main balances and wire them into the Pyomo model.
- Optional reported HRSG supplementary-firing sizing for cases where the
  reported HRSG steam flow exceeds the derived gas-turbine exhaust envelope.
- Reported-equipment calibration controls for fixed reported loads, reported
  maintenance, reported power revenue, unpaid export allowance, auxiliary
  operating cost, and annualized capital scaling. These reproduce the
  utility-system microgrid best configuration's utility steam, power, operating
  cost, maintenance, capital, and total annualized cost while leaving the
  current fuel-consumption discrepancy explicit.
- Reported hot-oil and flash-steam recovery helpers for Contribution 2
  hot-oil/FSR best-configuration rows, including thermodynamic condensate
  recovery sizing from saturated enthalpies. Reported fuel consumption follows
  the thesis process-utility convention and excludes hot-oil fuel, while hot-oil
  cost remains available as a separate operating-cost component.
- A reported-hot-oil-cost calibration helper that derives the thermal efficiency
  needed to match the thesis hot-oil operating-cost row.
- A reported-economics calibration flag for Contribution 2 fixed-load rows that
  applies reported fuel cost, hot-oil cost, power revenue, maintenance, capital,
  and residual auxiliary operating cost.
- A ready-to-run Contribution 2 case-study 2 best-configuration scenario catalog
  covering the four reported rows from Table 2-9.
- A first physical-profile bridge that keeps the extracted P1.D process stream
  heat loads while applying reported Contribution 2 steam-property and equipment
  targets to physical steam-level candidates, including HP/MP/LP candidate sets
  for the reported mains. For multi-main reported configurations, the extracted
  process heat is carried once on the selected target steam main instead of
  being duplicated across every reported main.
- Solver-backed coverage for the multi-main physical-profile best-configuration
  bridge, including enthalpy-basis pseudo-deltas on the selected reported target
  level so the physical heat-profile data is feasible under the SciPy MILP
  runner. The current result remains an uncalibrated physical-profile solve,
  with Table 2-9 field deltas reported through the existing best-configuration
  comparison helper.
- A fixed reported-load option for the physical-profile bridge that pins
  reported boiler and VHP turbine loads and requires reported boiler,
  gas-turbine, HRSG, and VHP turbine selection, reducing the physical-profile
  utility-system microgrid deltas while preserving the calibrated reported-row
  catalog.
- Reported maintenance and capital calibration inputs for physical-profile
  bridge runs, keeping the remaining mismatch focused on physical fuel
  consumption and fuel-cost basis.
- Physical-profile fuel-cost basis calibration that matches the thesis fuel-cost
  row while leaving the physical fuel-consumption deviation visible in result
  comparison output.
- Residual auxiliary operating-cost calibration for physical-profile bridge
  runs, allowing fixed-load utility-system microgrid physical-profile results to
  match Table 2-9 operating and total costs without changing physical fuel use.
- Unpaid export handling for fixed-load physical-profile stand-alone rows, so
  the utility-system stand-alone Table 2-9 physical-profile run can match
  reported utility steam, power, fuel cost, maintenance, and capital while
  keeping residual fuel and operating-cost deltas explicit.
- Physical-profile hot-oil and flash-steam recovery build support for Table 2-9
  hot-oil/FSR rows, including reported hot-oil loads and flash-recovery routes
  mapped onto selected physical interval steam-level candidates.
- Solver-backed calibrated physical-profile regressions for both Table 2-9
  hot-oil/FSR rows, including physical-basis hot-oil cost calibration,
  reported power-revenue pricing, and auxiliary VHP source support for the
  stand-alone row while keeping physical fuel-consumption deltas explicit.
- A public Contribution 2 physical-profile scenario catalog covering all four
  Table 2-9 rows, with calibrated and uncalibrated variants runnable through the
  static STYLE scenario runner.
- A `openutility-style-table2-9` CLI/reporting entry point that runs the
  reported-equipment or physical-profile Table 2-9 catalogs with the SciPy MILP
  solver and exports benchmark deviations as CSV or JSON.
- Contribution 2 steam-property comparison report helpers and CLI output for
  the IAPWS-versus-model turbine enthalpy-drop and power-generation rows,
  including a computed mode that recomputes IAPWS-side values through the steam
  property provider.
- Contribution 2 model-statistics and computational-result report helpers and
  CLI output, including optimality-gap rows where the thesis reports a bound
  plus aggregate best-method and method-level summary views.
- Solver-independent bilevel decomposition bookkeeping helpers for binary
  master assignments, no-good cuts, incumbent tracking, and conversion of
  captured Contribution 2 computational rows into incumbent records.
- A Pyomo-facing no-good-cut helper that attaches incumbent-exclusion
  constraints to synthetic master models as the first bilevel master-builder
  boundary.
- STYLE master-binary extraction helpers that expose canonical Pyomo selection
  variables and read solved/fixed binary values into bilevel assignments.
- A fixed-assignment helper that applies a complete bilevel master assignment
  back onto a built Pyomo STYLE model for subproblem evaluation.
- A static STYLE fixed-assignment subproblem evaluator that builds a scenario
  model, fixes master binaries from a bilevel assignment, solves with the
  configured solver callback, and emits a `BilevelSubproblemResult`.
- A static STYLE fixed-assignment decomposition smoke workflow that runs the
  generic bounded bilevel loop with a real Pyomo STYLE master and fixed
  subproblem evaluator.
- Solver-backed coverage for that decomposition workflow on calibrated
  Contribution 2 physical-profile catalog cases, with all-scenario CLI
  trajectory rows carrying catalog, case-study, and scenario metadata.
- A binary-only STYLE selection master that is built from canonical Pyomo STYLE
  selection variable names and can drive fixed-assignment subproblem evaluation
  through the generic bounded decomposition loop.
- A deterministic binary-selection candidate solver callback that applies the
  first assignment satisfying the current no-good cuts.
- Two-iteration smoke coverage showing the binary-only master advances to a
  second feasible STYLE fixed-assignment subproblem after the first assignment
  is excluded by a no-good cut.
- A solved-scenario candidate extractor that runs a static STYLE scenario and
  turns its solved Pyomo binary selections into a binary-selection master
  candidate.
- Ordered candidate-pool helpers that deduplicate solved scenario assignments,
  filter candidates to a target master's exact binary variable set, and drive a
  real physical-profile binary-selection master past a no-good cut.
- A candidate-driven binary-selection decomposition helper that cuts and skips
  fixed-assignment subproblem failures instead of aborting the run, with
  provenance labels for solved-catalog candidate records.
- Candidate CLI reports qualify solved-catalog provenance labels by calibrated
  versus uncalibrated source catalog when both source pools are combined.
- A deterministic single-iteration bilevel decomposition orchestrator that
  builds a cut master, solves it through callbacks, evaluates a fixed-assignment
  subproblem callback, records the incumbent, and rebuilds the next cut master.
- A bounded bilevel decomposition loop with explicit stop reasons for maximum
  iterations, duplicate incumbents, and absolute optimality-gap convergence.
- Bilevel trajectory reporting helpers that flatten decomposition runs into
  CSV/JSON-ready iteration rows, including skipped-candidate counts for
  candidate-driven runs and accepted candidate source labels when available,
  for comparison with Contribution 2 statistics.
- Contribution 2 bilevel benchmark trajectory reporting that maps captured
  Table 2-7 bilevel rows onto the decomposition trajectory schema.
- Contribution 2 bilevel trajectory comparison helpers for checking generated
  decomposition runs against reported objective, bound, gap, timing, and status
  fields.
- A synthetic Contribution 2 bilevel run helper that uses the bounded
  decomposition loop over a Pyomo binary master and fixture-backed subproblem,
  then exercises the trajectory and benchmark-comparison workflow end to end.
- Steam-main scoped source/sink cascades for physical candidate sets, so
  residual heat and hot-oil ordering reset at each steam main and cooling-water
  load collects the bottom residual from each main.
- The hot-oil/FSR stand-alone reported row can be solved with a derived
  auxiliary VHP source for the unassigned utility-steam generation; both
  hot-oil/FSR rows can optionally match the reported fuel-consumption and
  economic rows, with a 0.01 MEUR/yr rounding tolerance on the stand-alone total
  annualized cost row.
- Required-equipment selection flags for reported fixed-load calibration, so
  reported boilers, gas turbines, HRSGs, and VHP turbines cannot be optimized
  away when other utilities such as hot oil are available.
- VHP-to-steam-main let-down helpers that connect assembled VHP generation data
  to selected steam-level candidates.
- VHP-to-steam-main back-pressure turbine helpers that add explicit turbine
  performance and map the design power to the thesis steam-turbine capital-cost
  row.
- A public case-study 2 static scenario catalog helper that assembles the
  extracted heat profile, site economics, boiler, gas turbine, HRSG, VHP header,
  VHP let-down, optional VHP turbine, and thesis benchmark into one buildable
  Pyomo scenario.
- That assembled catalog can optionally match the benchmark total power
  generation by constraining grid export to the reported generation above site
  demand.
- It can also optionally match benchmark maintenance and capital costs through
  explicit fixed-maintenance and fixed-capital targets on the assembled VHP
  turbine cost record.
- Explicit utility-steam, fuel-consumption, and operating-cost accounting
  adjustments can be applied to the assembled catalog; with power, maintenance,
  capital, utility-steam, fuel, and operating controls enabled, the current
  smoke scenario closes every benchmark field on the reported comparison basis.
- Solver-backed regression coverage for that assembled case-study 2 scenario
  through the SciPy MILP runner. The current solve is intentionally transparent
  about opt-in accounting bridges until steam-main structure, fuel assumptions,
  and benchmark-specific physical choices are fully aligned to the thesis
  tables.
- Annual operating-hour and currency-scaling controls on `StyleModelData`, with
  case-study 2 configured from the thesis site constants.

See [docs/usage.md](docs/usage.md) for command-line and Python API usage,
[docs/developer_checklist.md](docs/developer_checklist.md) for reproduction
commands, and [docs/replication_plan.md](docs/replication_plan.md) for the full
build plan and milestones. See [CHANGELOG.md](CHANGELOG.md) for the current
working-product scope.

Example:

```bash
openutility-style-table2-9 --catalog physical-profile --format csv
```

Run the physical-profile decomposition smoke trajectory from the CLI:

```bash
openutility-style-table2-9 --report style-decomposition --catalog physical-profile --format csv
```

Compare those decomposition objectives against Table 2-9 total costs:

```bash
openutility-style-table2-9 --report style-decomposition --catalog physical-profile --view summary --format csv
```

Break down physical-profile fuel-consumption residuals by equipment family:

```bash
openutility-style-table2-9 --catalog physical-profile --view fuel-families --format csv
```

Rank physical-profile fuel residuals by scenario:

```bash
openutility-style-table2-9 --catalog physical-profile --view fuel-ranking --format csv
```

Trace physical-profile fuel consumption to equipment variables:

```bash
openutility-style-table2-9 --catalog physical-profile --view fuel-equipment --format csv
```

Compare physical-profile fuel equipment rows with capacity context:

```bash
openutility-style-table2-9 --catalog physical-profile --view fuel-capacity --format csv
```

Classify physical-profile fuel residual drivers from capacity context:

```bash
openutility-style-table2-9 --catalog physical-profile --view fuel-diagnosis --format csv
```

Compute physical-profile fuel adjustment targets for capped residuals:

```bash
openutility-style-table2-9 --catalog physical-profile --view fuel-targets --format csv
```

Apply the computed fuel target factors before reporting Table 2-9 deviations:

```bash
openutility-style-table2-9 --catalog physical-profile --apply-fuel-targets --view summary --format csv
```

Apply both computed fuel and operating-cost targets before reporting Table 2-9
deviations:

```bash
openutility-style-table2-9 --catalog physical-profile --apply-fuel-targets --apply-operating-targets --view summary --format csv
```

Break down fuel-targeted operating-cost residuals by component:

```bash
openutility-style-table2-9 --catalog physical-profile --apply-fuel-targets --view operating-components --format csv
```

Compute the remaining fuel-targeted operating-cost target adjustment:

```bash
openutility-style-table2-9 --catalog physical-profile --apply-fuel-targets --view operating-targets --format csv
```

Run the candidate-driven skipped-candidate trajectory from the CLI:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-trajectory --format csv
```

List the compatible solved-candidate pool before decomposition cuts:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-pool --format csv
```

Summarize solved candidate-source filtering before decomposition:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-source-summary --format csv
```

List detailed candidate-source compatibility before decomposition:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-source-detail --format csv
```

List variable-level incompatibility diagnostics for source candidates:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-source-variables --format csv
```

Compare compatible candidates with the accepted incumbent assignment:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-pool-comparison --format csv
```

List the binary choices that differ from the accepted candidate:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-selection-delta --format csv
```

Summarize those differences by binary component family:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-selection-summary --format csv
```

Join skipped-candidate failure diagnostics with grouped selection deltas:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-skip-delta-summary --format csv
```

Generate the consolidated candidate audit bundle:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-audit-bundle --format csv
```

Compare the candidate-driven decomposition objective against Table 2-9:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-summary --format csv
```

Audit the skipped failed candidate assignment:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-skips --format csv
```

Checked example reports are available in
[examples/table_2_9_reported_equipment.csv](examples/table_2_9_reported_equipment.csv)
and
[examples/table_2_9_physical_profile.csv](examples/table_2_9_physical_profile.csv).
The physical-profile fuel-family residual report is checked in
[examples/table_2_9_physical_profile_fuel_families.csv](examples/table_2_9_physical_profile_fuel_families.csv).
The physical-profile fuel-residual ranking report is checked in
[examples/table_2_9_physical_profile_fuel_ranking.csv](examples/table_2_9_physical_profile_fuel_ranking.csv).
The physical-profile equipment-level fuel trace is checked in
[examples/table_2_9_physical_profile_fuel_equipment.csv](examples/table_2_9_physical_profile_fuel_equipment.csv).
The physical-profile fuel-capacity context report is checked in
[examples/table_2_9_physical_profile_fuel_capacity.csv](examples/table_2_9_physical_profile_fuel_capacity.csv).
The physical-profile fuel residual diagnosis report is checked in
[examples/table_2_9_physical_profile_fuel_diagnosis.csv](examples/table_2_9_physical_profile_fuel_diagnosis.csv).
The physical-profile fuel calibration target report is checked in
[examples/table_2_9_physical_profile_fuel_targets.csv](examples/table_2_9_physical_profile_fuel_targets.csv).
The fuel-targeted physical-profile summary is checked in
[examples/table_2_9_physical_profile_fuel_targeted_summary.csv](examples/table_2_9_physical_profile_fuel_targeted_summary.csv).
The fuel-and-operating-targeted physical-profile summary is checked in
[examples/table_2_9_physical_profile_fuel_and_operating_targeted_summary.csv](examples/table_2_9_physical_profile_fuel_and_operating_targeted_summary.csv).
The fuel-targeted operating-cost component report is checked in
[examples/table_2_9_physical_profile_fuel_targeted_operating_components.csv](examples/table_2_9_physical_profile_fuel_targeted_operating_components.csv).
The fuel-targeted operating-cost target report is checked in
[examples/table_2_9_physical_profile_fuel_targeted_operating_targets.csv](examples/table_2_9_physical_profile_fuel_targeted_operating_targets.csv).
The steam-property comparison example is
[examples/steam_property_comparisons.csv](examples/steam_property_comparisons.csv).
Model-size and computational-result examples are
[examples/model_statistics.csv](examples/model_statistics.csv) and
[examples/computational_results.csv](examples/computational_results.csv).
Aggregate computational-result examples are
[examples/computational_best_methods.csv](examples/computational_best_methods.csv)
and
[examples/computational_method_summary.csv](examples/computational_method_summary.csv).
The captured bilevel benchmark trajectory example is
[examples/computational_bilevel_trajectory.csv](examples/computational_bilevel_trajectory.csv).
An executable synthetic reported-run comparison workflow is available in
[examples/contribution2_bilevel_reported_comparison.py](examples/contribution2_bilevel_reported_comparison.py),
with checked output in
[examples/contribution2_bilevel_reported_comparison.csv](examples/contribution2_bilevel_reported_comparison.csv).
A real STYLE-master decomposition smoke workflow is available in
[examples/contribution2_physical_profile_decomposition_smoke.py](examples/contribution2_physical_profile_decomposition_smoke.py),
with checked output in
[examples/contribution2_physical_profile_decomposition_smoke.csv](examples/contribution2_physical_profile_decomposition_smoke.csv).
The all-scenario CLI trajectory and cost-comparison outputs are checked in
[examples/contribution2_physical_profile_decomposition_trajectories.csv](examples/contribution2_physical_profile_decomposition_trajectories.csv)
and
[examples/contribution2_physical_profile_decomposition_cost_comparison.csv](examples/contribution2_physical_profile_decomposition_cost_comparison.csv).
A candidate-driven decomposition example with a skipped failed candidate is
available in
[examples/contribution2_candidate_decomposition_skipped_candidate.py](examples/contribution2_candidate_decomposition_skipped_candidate.py),
with checked output in
[examples/contribution2_candidate_decomposition_skipped_candidate.csv](examples/contribution2_candidate_decomposition_skipped_candidate.csv).
The compatible candidate-pool inventory is checked in
[examples/contribution2_candidate_decomposition_pool.csv](examples/contribution2_candidate_decomposition_pool.csv).
The candidate source-filtering summary is checked in
[examples/contribution2_candidate_decomposition_source_summary.csv](examples/contribution2_candidate_decomposition_source_summary.csv).
The candidate source-filtering detail report is checked in
[examples/contribution2_candidate_decomposition_source_detail.csv](examples/contribution2_candidate_decomposition_source_detail.csv).
The candidate source-filtering variable diagnostics are checked in
[examples/contribution2_candidate_decomposition_source_variables.csv](examples/contribution2_candidate_decomposition_source_variables.csv).
The candidate-pool Hamming-distance comparison is checked in
[examples/contribution2_candidate_decomposition_pool_comparison.csv](examples/contribution2_candidate_decomposition_pool_comparison.csv).
The accepted-versus-candidate binary selection delta is checked in
[examples/contribution2_candidate_decomposition_selection_delta.csv](examples/contribution2_candidate_decomposition_selection_delta.csv).
The grouped selection-delta summary is checked in
[examples/contribution2_candidate_decomposition_selection_delta_summary.csv](examples/contribution2_candidate_decomposition_selection_delta_summary.csv).
The skipped-candidate failure delta summary is checked in
[examples/contribution2_candidate_decomposition_skip_delta_summary.csv](examples/contribution2_candidate_decomposition_skip_delta_summary.csv).
The consolidated candidate audit bundle is checked in
[examples/contribution2_candidate_decomposition_audit_bundle.csv](examples/contribution2_candidate_decomposition_audit_bundle.csv).
The candidate-driven objective comparison is checked in
[examples/contribution2_candidate_decomposition_cost_comparison.csv](examples/contribution2_candidate_decomposition_cost_comparison.csv).
The skipped-candidate audit output, including the rejected candidate source
scenario, is checked in
[examples/contribution2_candidate_decomposition_skipped_candidates.csv](examples/contribution2_candidate_decomposition_skipped_candidates.csv).
Use `--view summary` for one row per scenario with failing fields.
