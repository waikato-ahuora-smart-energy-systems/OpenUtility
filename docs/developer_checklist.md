# Developer Checklist

Use this checklist to reproduce the current OpenUtility package state from a
clean checkout.

## Install

Create or activate a Python environment with Python 3.11 or newer, then install
the package in editable mode with development dependencies:

```bash
python -m pip install -e ".[dev]"
```

The default Table 2-9 workflow uses the SciPy/HiGHS MILP adapter and does not
require an external MILP executable. Pyomo solver adapters remain available for
environments with GLPK, CBC, or another configured solver.

## Verify

Run the full test suite:

```bash
python -m pytest
```

Run lint checks:

```bash
python -m ruff check .
```

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
- `examples/contribution2_bilevel_reported_comparison.csv`
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
- `examples/contribution2_physical_profile_decomposition_smoke.csv`
- `examples/contribution2_physical_profile_decomposition_trajectories.csv`
- `examples/contribution2_physical_profile_decomposition_cost_comparison.csv`

`tests/test_cli.py` verifies that the checked example files match the generated
CSV reports.
