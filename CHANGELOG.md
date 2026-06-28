# Changelog

## 0.1.0 - Current Working Product

This release establishes a tested Python package for the static STYLE/Contribution
2 replication scope implemented so far.

Supported thesis scope:

- Contribution 2 case-study 2 Table 2-9 reported-equipment rows.
- Contribution 2 case-study 2 Table 2-9 physical-profile rows using extracted
  P1.D heat interval data.
- Physical-profile fuel-family residual reporting for remaining Table 2-9
  fuel-consumption deviations.
- Physical-profile fuel-residual ranking by scenario, including benchmark
  residual percent and largest included fuel-family share.
- Physical-profile equipment-level fuel tracing from residual rows back to
  Pyomo fuel variables and multipliers.
- Physical-profile fuel-capacity context for selected state, capacity basis, and
  utilization of fuel-consuming equipment.
- Physical-profile fuel residual diagnosis over capacity rows, classifying each
  scenario by capped fuel capacity, hot-oil heat-load context, auxiliary VHP
  fuel context, within-tolerance, or unclassified residual drivers.
- Physical-profile fuel calibration target reporting that computes the
  largest-equipment fuel adjustment needed to close capped residuals.
- Opt-in physical-profile fuel accounting factors for applying computed fuel
  target factors while leaving Pyomo heat-balance constraints unchanged.
- Checked fuel-targeted physical-profile summary showing closed fuel residuals
  with the remaining operating-cost residual still explicit.
- Fuel-targeted operating-cost component reporting that isolates remaining
  residuals by fuel, hot-oil, electricity, auxiliary/unallocated, and total
  operating-cost buckets.
- Fuel-targeted operating-cost target reporting that translates unresolved total
  operating-cost residuals into component adjustments required to close Table
  2-9 benchmark gaps.
- Opt-in operating-cost accounting adjustments for applying computed target
  adjustments while leaving Pyomo heat-balance constraints unchanged.
- Checked fuel-and-operating-targeted physical-profile summary showing closed
  Table 2-9 residuals for the current physical-profile bridge.
- Contribution 2 steam-property comparison rows for IAPWS-versus-model turbine
  enthalpy drops and power generation.
- Contribution 2 model-statistics and computational-result rows, including
  reportable model size, solver timing, time-limit, bound, optimality-gap,
  best-method, and method-summary fields.
- Solver-independent bilevel decomposition bookkeeping for binary assignments,
  no-good cuts, incumbent pools, and captured computational-result incumbents.
- Pyomo no-good-cut constraint attachment for binary master variables.
- STYLE master-binary extraction from built Pyomo models into bilevel assignment
  records.
- Fixed STYLE master-assignment application onto built Pyomo models for
  fixed-assignment subproblem evaluation.
- Static STYLE fixed-assignment subproblem evaluator that emits
  `BilevelSubproblemResult` from a solved Pyomo STYLE scenario model.
- Static STYLE fixed-assignment decomposition smoke workflow using the generic
  bounded bilevel loop with a real Pyomo STYLE master and fixed subproblem.
- Solver-backed Contribution 2 physical-profile catalog smoke regression for
  the static STYLE fixed-assignment decomposition workflow.
- Assembled case-study 2 static scenario catalog option for matching benchmark
  total power generation by constraining grid export to reported generation
  above site demand.
- Assembled case-study 2 static scenario catalog options for matching benchmark
  maintenance and capital costs through fixed VHP turbine cost targets.
- Assembled case-study 2 static scenario catalog support for explicit
  operating-cost adjustments, enabling the current smoke scenario to close total
  annualized cost when combined with benchmark power, maintenance, and capital
  options.
- Assembled case-study 2 utility-steam and fuel-consumption reporting adjustment
  support, allowing the current assembled smoke scenario to close every
  benchmark field when combined with benchmark power, maintenance, capital, and
  operating controls.
- CLI `style-decomposition` report for all calibrated physical-profile
  decomposition trajectories with catalog/case/scenario metadata.
- CLI `style-decomposition --view summary` cost-comparison report that compares
  decomposition objectives with Table 2-9 total costs.
- Binary-only STYLE selection master boundary and decomposition helper for
  separating master binary selection from fixed-assignment STYLE subproblem
  evaluation.
- Deterministic binary-selection candidate solver that skips assignments
  excluded by no-good cuts.
- Two-iteration binary-selection decomposition smoke coverage with feasible
  fixed-assignment STYLE subproblem evaluations after no-good-cut exclusion.
- Solved-scenario binary-selection candidate extraction from static STYLE
  scenario runs.
- Ordered solved-candidate pool helpers with exact target-master compatibility
  filtering and real physical-profile no-good-cut master progression coverage.
- Provenance-preserving solved-candidate records and compatibility filtering for
  source-labeled candidate pools.
- Caller-supplied solved-candidate source label factories, with the
  candidate-decomposition CLI qualifying combined calibrated and uncalibrated
  source pools.
- Candidate-pool inventory reporting for compatible source-labeled assignments
  before no-good cuts are applied.
- Candidate-pool comparison reporting using Hamming distance from the accepted
  incumbent assignment.
- Candidate selection-delta reporting for binary variables whose accepted and
  compatible candidate values differ.
- Grouped candidate selection-delta summary reporting by binary component
  family.
- Candidate source-filtering summary reporting for solved-record counts,
  compatible/incompatible candidate counts, target master variable counts, and
  source-label partitions before candidate-driven decomposition.
- Candidate source-filtering detail reporting for each solved source record's
  source catalog, source scenario, binary variable count, selected count,
  compatibility flag, and missing/extra variable counts.
- Candidate source-filtering variable diagnostics for exact missing-target and
  extra-candidate binary variables on incompatible source records.
- Skipped-candidate delta summary reporting that combines fixed-assignment
  failure reasons with grouped accepted-only and candidate-only binary
  selection deltas.
- Candidate audit-bundle reporting that consolidates accepted incumbent context,
  compatible pool rows, candidate delta summaries, skipped diagnostics, and
  skipped-candidate delta summaries into one reproducible view.
- Candidate-driven binary-selection decomposition that cuts and skips failed
  fixed-assignment subproblem candidates, stopping cleanly on candidate
  exhaustion when no cut-feasible candidates remain.
- Decomposition trajectory rows include `skipped_candidate_count` for
  candidate-driven runs and `candidate_source` for accepted solved-catalog
  candidates when provenance is available.
- Executable candidate-driven decomposition example with checked output showing
  a non-zero skipped-candidate count.
- CLI `style-decomposition --view candidate-trajectory` report for the
  candidate-driven skipped-candidate trajectory.
- CLI `style-decomposition --view candidate-summary` cost-comparison report for
  the candidate-driven decomposition target scenario.
- CLI `style-decomposition --view candidate-pool` inventory report for the
  compatible solved-candidate pool.
- CLI `style-decomposition --view candidate-source-summary` report for
  candidate source-filtering counts.
- CLI `style-decomposition --view candidate-source-detail` report for
  per-source candidate compatibility diagnostics.
- CLI `style-decomposition --view candidate-source-variables` report for
  variable-level source incompatibility diagnostics.
- CLI `--catalog physical-profile --view fuel-families` report for
  fuel-consumption residuals by equipment family.
- CLI `--catalog physical-profile --view fuel-ranking` report for
  scenario-level fuel-consumption residual ranking.
- CLI `--catalog physical-profile --view fuel-equipment` report for
  equipment-level fuel-consumption traceability.
- CLI `--catalog physical-profile --view fuel-capacity` report for
  equipment-level fuel-capacity context.
- CLI `--catalog physical-profile --view fuel-diagnosis` report for
  scenario-level residual-driver classification.
- CLI `--catalog physical-profile --view fuel-targets` report for capped fuel
  residual calibration targets.
- CLI `--catalog physical-profile --apply-fuel-targets` option for applying
  computed fuel target factors before Table 2-9 reports.
- CLI `--catalog physical-profile --apply-fuel-targets --view
  operating-components` report for operating-cost component residuals.
- CLI `--catalog physical-profile --apply-fuel-targets --view
  operating-targets` report for remaining operating-cost target adjustments.
- CLI `--catalog physical-profile --apply-fuel-targets
  --apply-operating-targets` option sequence for applying computed fuel and
  operating-cost targets before Table 2-9 reports.
- CLI `style-decomposition --view candidate-pool-comparison` report for
  accepted-versus-compatible candidate distances.
- CLI `style-decomposition --view candidate-selection-delta` report for
  accepted-versus-compatible binary selection deltas.
- CLI `style-decomposition --view candidate-selection-summary` report for
  grouped accepted-versus-compatible selection deltas.
- CLI `style-decomposition --view candidate-skip-delta-summary` report joining
  skipped-candidate diagnostics with grouped accepted-versus-skipped selection
  deltas.
- CLI `style-decomposition --view candidate-audit-bundle` report for the
  consolidated candidate audit bundle.
- CLI `style-decomposition --view candidate-skips` audit report for
  fixed-assignment subproblem candidates skipped after failure, including the
  source scenario that produced each rejected assignment.
- Deterministic single-iteration bilevel decomposition orchestration with
  caller-supplied master and subproblem callbacks.
- Bounded bilevel decomposition runs with explicit stop reasons and incumbent
  trajectory retention.
- Bilevel decomposition run trajectory rows with CSV/JSON formatting.
- Contribution 2 bilevel benchmark trajectory report rows and CLI output.
- Contribution 2 bilevel trajectory comparison rows for generated-versus-reported
  objective, bound, gap, timing, and status fields.
- Synthetic Contribution 2 reported bilevel run helper that uses the bounded
  decomposition loop, Pyomo binary master, no-good-cut next-master rebuild, and
  fixture-backed subproblem for end-to-end trajectory comparison workflows.
- Executable Contribution 2 reported bilevel comparison example with checked
  CSV output.
- STYLE case-study 2 heat-profile extraction, utility/equipment cost fixtures,
  gas-turbine/HRSG/boiler/VHP candidate derivation, hot-oil and flash-steam
  recovery scaffolds, and successive steam-property update boundaries.

Public entry points:

- `BilevelCandidateAssignment`
- `style_case_study_2_contribution2_best_configuration_catalog()`
- `style_case_study_2_contribution2_physical_profile_catalog()`
- `run_static_style_scenario(...)`
- `scipy_milp_static_style_solver(...)`
- `BilevelIntegerAssignment`
- `BilevelSolutionPool`
- `BilevelSubproblemResult`
- `BilevelDecompositionRun`
- `add_bilevel_no_good_cuts(...)`
- `bilevel_no_good_cut_expression(...)`
- `build_bilevel_master_with_no_good_cuts(...)`
- `build_static_style_binary_selection_master(...)`
- `compatible_bilevel_candidate_assignments(...)`
- `compatible_bilevel_integer_assignments(...)`
- `bilevel_candidate_pool_rows(...)`
- `bilevel_candidate_pool_comparison_rows(...)`
- `bilevel_candidate_selection_delta_rows(...)`
- `bilevel_candidate_selection_delta_summary_rows(...)`
- `bilevel_candidate_source_filter_detail_rows(...)`
- `bilevel_candidate_source_filter_summary_rows(...)`
- `bilevel_candidate_source_filter_variable_rows(...)`
- `bilevel_candidate_audit_bundle_rows(...)`
- `bilevel_skipped_candidate_delta_summary_rows(...)`
- `bilevel_incumbents_from_computational_results(...)`
- `bilevel_decomposition_run_rows(...)`
- `contribution2_bilevel_benchmark_trajectory_rows(...)`
- `contribution2_bilevel_trajectory_comparison_rows(...)`
- `format_bilevel_decomposition_run_rows(...)`
- `format_contribution2_bilevel_benchmark_trajectory_rows(...)`
- `format_contribution2_bilevel_trajectory_comparison_rows(...)`
- `contribution2_reported_bilevel_decomposition_run(...)`
- `contribution2_synthetic_bilevel_decomposition_run(...)`
- `format_bilevel_candidate_pool_rows(...)`
- `format_bilevel_candidate_pool_comparison_rows(...)`
- `format_bilevel_candidate_selection_delta_rows(...)`
- `format_bilevel_candidate_selection_delta_summary_rows(...)`
- `format_bilevel_candidate_source_filter_detail_rows(...)`
- `format_bilevel_candidate_source_filter_summary_rows(...)`
- `format_bilevel_candidate_source_filter_variable_rows(...)`
- `format_bilevel_candidate_audit_bundle_rows(...)`
- `format_bilevel_skipped_candidate_delta_summary_rows(...)`
- `fix_style_master_integer_assignment(...)`
- `run_bilevel_decomposition(...)`
- `run_bilevel_decomposition_iteration(...)`
- `run_static_style_binary_selection_candidate_decomposition(...)`
- `run_static_style_binary_selection_decomposition(...)`
- `run_static_style_fixed_assignment_decomposition(...)`
- `style_binary_selection_candidate_from_scenario(...)`
- `style_binary_selection_candidate_records_from_scenarios(...)`
- `style_binary_selection_candidate_solver(...)`
- `style_binary_selection_candidates_from_scenarios(...)`
- `style_binary_selection_master_assignment_from_model(...)`
- `style_candidate_pool_rows(...)`
- `style_candidate_pool_comparison_rows(...)`
- `style_candidate_selection_delta_rows(...)`
- `style_candidate_selection_delta_summary_rows(...)`
- `style_candidate_source_filter_detail_rows(...)`
- `style_candidate_source_filter_summary_rows(...)`
- `style_candidate_source_filter_variable_rows(...)`
- `style_candidate_audit_bundle_rows(...)`
- `style_skipped_candidate_delta_summary_rows(...)`
- `format_style_candidate_pool_rows(...)`
- `format_style_candidate_pool_comparison_rows(...)`
- `format_style_candidate_selection_delta_rows(...)`
- `format_style_candidate_selection_delta_summary_rows(...)`
- `format_style_candidate_source_filter_detail_rows(...)`
- `format_style_candidate_source_filter_summary_rows(...)`
- `format_style_candidate_source_filter_variable_rows(...)`
- `format_style_candidate_audit_bundle_rows(...)`
- `format_style_skipped_candidate_delta_summary_rows(...)`
- `format_style_fuel_consumption_family_rows(...)`
- `format_style_fuel_consumption_equipment_rows(...)`
- `format_style_fuel_consumption_capacity_rows(...)`
- `format_style_fuel_consumption_diagnosis_rows(...)`
- `format_style_fuel_calibration_target_rows(...)`
- `format_style_fuel_consumption_residual_ranking_rows(...)`
- `FuelConsumptionAccountingFactor`
- `OperatingCostAccountingAdjustment`
- `format_style_operating_cost_component_rows(...)`
- `format_style_operating_cost_target_rows(...)`
- `static_style_fuel_capacity_context_by_equipment(...)`
- `static_style_fuel_consumption_by_equipment(...)`
- `static_style_fuel_consumption_by_family(...)`
- `style_fuel_consumption_capacity_rows(...)`
- `style_fuel_consumption_diagnosis_rows(...)`
- `style_fuel_calibration_target_rows(...)`
- `style_fuel_consumption_factor_map_from_calibration_target_rows(...)`
- `style_fuel_consumption_equipment_rows(...)`
- `style_operating_cost_adjustment_map_from_target_rows(...)`
- `style_operating_cost_component_rows(...)`
- `style_operating_cost_target_rows(...)`
- `style_fuel_consumption_family_rows(...)`
- `style_fuel_consumption_residual_ranking_rows(...)`
- `style_fixed_assignment_subproblem_result(...)`
- `style_master_binary_variables(...)`
- `style_master_integer_assignment_from_model(...)`
- `openutility-style-table2-9`

Checked reports:

- `examples/table_2_9_reported_equipment.csv`
- `examples/table_2_9_physical_profile.csv`
- `examples/table_2_9_physical_profile_fuel_capacity.csv`
- `examples/table_2_9_physical_profile_fuel_diagnosis.csv`
- `examples/table_2_9_physical_profile_fuel_equipment.csv`
- `examples/table_2_9_physical_profile_fuel_families.csv`
- `examples/table_2_9_physical_profile_fuel_ranking.csv`
- `examples/table_2_9_physical_profile_fuel_and_operating_targeted_summary.csv`
- `examples/table_2_9_physical_profile_fuel_targeted_summary.csv`
- `examples/table_2_9_physical_profile_fuel_targeted_operating_components.csv`
- `examples/table_2_9_physical_profile_fuel_targeted_operating_targets.csv`
- `examples/table_2_9_physical_profile_fuel_targets.csv`
- `examples/steam_property_comparisons.csv`
- `examples/model_statistics.csv`
- `examples/computational_results.csv`
- `examples/computational_bilevel_trajectory.csv`
- `examples/contribution2_bilevel_reported_comparison.py`
- `examples/contribution2_bilevel_reported_comparison.csv`
- `examples/contribution2_candidate_decomposition_skipped_candidate.py`
- `examples/contribution2_candidate_decomposition_skipped_candidate.csv`
- `examples/contribution2_candidate_decomposition_pool.csv`
- `examples/contribution2_candidate_decomposition_source_summary.csv`
- `examples/contribution2_candidate_decomposition_source_detail.csv`
- `examples/contribution2_candidate_decomposition_source_variables.csv`
- `examples/contribution2_candidate_decomposition_pool_comparison.csv`
- `examples/contribution2_candidate_decomposition_selection_delta.csv`
- `examples/contribution2_candidate_decomposition_selection_delta_summary.csv`
- `examples/contribution2_candidate_decomposition_skip_delta_summary.csv`
- `examples/contribution2_candidate_decomposition_audit_bundle.csv`
- `examples/contribution2_candidate_decomposition_cost_comparison.csv`
- `examples/contribution2_candidate_decomposition_skipped_candidates.csv`
- `examples/contribution2_physical_profile_decomposition_smoke.py`
- `examples/contribution2_physical_profile_decomposition_smoke.csv`
- `examples/contribution2_physical_profile_decomposition_trajectories.csv`
- `examples/contribution2_physical_profile_decomposition_cost_comparison.csv`
- `examples/computational_best_methods.csv`
- `examples/computational_method_summary.csv`

Known physical-profile residuals:

- `utility-system-stand-alone`: fuel consumption, operating cost, and total cost
  retain explicit physical-profile deltas.
- `utility-system-microgrid`: fuel consumption retains an explicit physical
  delta.
- `hot-oil-fsr-stand-alone`: fuel consumption retains an explicit physical
  delta.
- `hot-oil-fsr-microgrid`: fuel consumption retains an explicit physical delta.

Verification at this checkpoint:

- `python -m pytest`
- `python -m ruff check .`
