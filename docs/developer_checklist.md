# Developer Checklist

Use this checklist to reproduce the current OpenUtility package state from a
clean checkout.

## Install

Create or activate a Python environment with Python 3.14.2 or newer, then install
the package in editable mode with release dependencies:

```bash
python -m pip install -e ".[dev,docs,notebook,release]"
```

The default Table 2-9 workflow uses the Pyomo/HiGHS SolverFactory path with the
required `highspy` package and Pyomo `appsi_highs` solver. The package uses
Pyomo solver adapters directly; `appsi_highs` is the supported default.

## Verify

Run the release gate:

```bash
python tools/release_check.py
```

For offline local triage only, skip the network-dependent audit and fresh wheel
install smoke test:

```bash
python tools/release_check.py --skip-audit --skip-smoke-install
```

The gate runs Ruff linting and format checks, mypy, pytest with coverage,
case-study notebook execution through the test suite, Sphinx docs with warnings
as errors, package build, wheel inspection, Twine checks, dependency audit, and
fresh wheel-install smoke tests.

## Recreate Reports

Generate the calibrated reported-equipment Table 2-9 report:

```bash
openutility-style-table2-9 --catalog reported-equipment --format csv
```

Generate the calibrated physical-profile Table 2-9 report:

```bash
openutility-style-table2-9 --catalog physical-profile --format csv
```

Generate the physical-profile summary view:

```bash
openutility-style-table2-9 --catalog physical-profile --view summary --format csv
```

Generate the physical-profile fuel-family residual report:

```bash
openutility-style-table2-9 --catalog physical-profile --view fuel-families --format csv
```

Generate the physical-profile fuel-residual ranking report:

```bash
openutility-style-table2-9 --catalog physical-profile --view fuel-ranking --format csv
```

Generate the physical-profile equipment-level fuel trace:

```bash
openutility-style-table2-9 --catalog physical-profile --view fuel-equipment --format csv
```

Generate the physical-profile fuel-capacity context report:

```bash
openutility-style-table2-9 --catalog physical-profile --view fuel-capacity --format csv
```

Generate the physical-profile fuel residual diagnosis report:

```bash
openutility-style-table2-9 --catalog physical-profile --view fuel-diagnosis --format csv
```

Generate the physical-profile fuel calibration target report:

```bash
openutility-style-table2-9 --catalog physical-profile --view fuel-targets --format csv
```

Generate the physical-profile summary after applying computed fuel targets:

```bash
openutility-style-table2-9 --catalog physical-profile --apply-fuel-targets --view summary --format csv
```

Generate the physical-profile summary after applying computed fuel and
operating-cost targets:

```bash
openutility-style-table2-9 --catalog physical-profile --apply-fuel-targets --apply-operating-targets --view summary --format csv
```

Generate the physical-profile operating-cost component report after applying
computed fuel targets:

```bash
openutility-style-table2-9 --catalog physical-profile --apply-fuel-targets --view operating-components --format csv
```

Generate the physical-profile operating-cost target report after applying
computed fuel targets:

```bash
openutility-style-table2-9 --catalog physical-profile --apply-fuel-targets --view operating-targets --format csv
```

Generate the candidate-driven decomposition cost comparison:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-summary --format csv
```

Generate the compatible candidate-pool inventory:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-pool --format csv
```

Generate the candidate source-filtering summary:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-source-summary --format csv
```

Generate the detailed candidate source-filtering report:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-source-detail --format csv
```

Generate variable-level source incompatibility diagnostics:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-source-variables --format csv
```

Generate the candidate-pool Hamming-distance comparison:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-pool-comparison --format csv
```

Generate the candidate binary-selection delta report:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-selection-delta --format csv
```

Generate the grouped candidate-selection delta summary:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-selection-summary --format csv
```

Generate the skipped-candidate delta summary:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-skip-delta-summary --format csv
```

Generate the consolidated candidate audit bundle:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-audit-bundle --format csv
```

Generate the skipped-candidate audit view:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-skips --format csv
```

The checked example files are:

- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/table_2_9_reported_equipment.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/table_2_9_physical_profile.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/table_2_9_physical_profile_fuel_capacity.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/table_2_9_physical_profile_fuel_diagnosis.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/table_2_9_physical_profile_fuel_equipment.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/table_2_9_physical_profile_fuel_families.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/table_2_9_physical_profile_fuel_ranking.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/table_2_9_physical_profile_fuel_and_operating_targeted_summary.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/table_2_9_physical_profile_fuel_targeted_summary.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/table_2_9_physical_profile_fuel_targeted_operating_components.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/table_2_9_physical_profile_fuel_targeted_operating_targets.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/table_2_9_physical_profile_fuel_targets.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_computational_performance/outputs/contribution2_bilevel_reported_comparison.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/contribution2_candidate_decomposition_skipped_candidate.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/contribution2_candidate_decomposition_pool.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/contribution2_candidate_decomposition_source_summary.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/contribution2_candidate_decomposition_source_detail.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/contribution2_candidate_decomposition_source_variables.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/contribution2_candidate_decomposition_pool_comparison.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/contribution2_candidate_decomposition_selection_delta.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/contribution2_candidate_decomposition_selection_delta_summary.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/contribution2_candidate_decomposition_skip_delta_summary.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/contribution2_candidate_decomposition_audit_bundle.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/contribution2_candidate_decomposition_cost_comparison.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/contribution2_candidate_decomposition_skipped_candidates.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/contribution2_physical_profile_decomposition_smoke.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/contribution2_physical_profile_decomposition_trajectories.csv`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/outputs/contribution2_physical_profile_decomposition_cost_comparison.csv`

`tests/test_cli.py` verifies that the checked example files match the generated
CSV reports.
