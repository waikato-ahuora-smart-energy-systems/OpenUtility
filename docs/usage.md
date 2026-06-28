# Usage

OpenUtility currently exposes the Contribution 2 case-study 2 Table 2-9
replication through both a command-line report and Python scenario catalogs.

## Command Line

Run the calibrated reported-equipment catalog:

```bash
openutility-style-table2-9 --catalog reported-equipment --format csv
```

Run the calibrated physical-profile catalog:

```bash
openutility-style-table2-9 --catalog physical-profile --format csv
```

Use JSON output when another tool will consume the report:

```bash
openutility-style-table2-9 --catalog physical-profile --format json
```

Use the summary view for one row per scenario:

```bash
openutility-style-table2-9 --catalog physical-profile --view summary --format csv
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

Generate the Contribution 2 steam-property comparison report:

```bash
openutility-style-table2-9 --report steam-properties --format csv
```

Recompute the IAPWS-side steam-property values with the configured property
provider:

```bash
openutility-style-table2-9 --report steam-properties --computed --format csv
```

Generate Contribution 2 model statistics:

```bash
openutility-style-table2-9 --report model-statistics --format csv
```

Generate Contribution 2 computational results:

```bash
openutility-style-table2-9 --report computational-results --format csv
```

Generate the best reported solution method for each computational test/scenario:

```bash
openutility-style-table2-9 --report computational-results --view best-method --format csv
```

Generate method-level computational summaries:

```bash
openutility-style-table2-9 --report computational-results --view method-summary --format csv
```

Generate the captured Contribution 2 bilevel benchmark trajectory:

```bash
openutility-style-table2-9 --report computational-results --view bilevel-trajectory --format csv
```

Generate all calibrated physical-profile decomposition trajectories:

```bash
openutility-style-table2-9 --report style-decomposition --catalog physical-profile --format csv
```

Trajectory rows include `skipped_candidate_count`, which is non-zero for
candidate-driven runs that cut failed fixed-assignment subproblems. Candidate
trajectory rows also include `candidate_source` when candidates were created
from scenario records. Candidate source labels in the candidate-driven CLI
views are qualified with `calibrated:` or `uncalibrated:` when both source
catalogs are combined.

Compare those decomposition objectives with Table 2-9 total costs:

```bash
openutility-style-table2-9 --report style-decomposition --catalog physical-profile --view summary --format csv
```

Generate the candidate-driven decomposition trajectory with a skipped failed
candidate:

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

Compare compatible candidates with the accepted incumbent assignment using
Hamming distance over the binary master variables:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-pool-comparison --format csv
```

List the accepted-versus-candidate binary selection deltas:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-selection-delta --format csv
```

Summarize those deltas by binary component family:

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

Compare the candidate-driven decomposition objective with the Table 2-9 total
cost for the target scenario:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-summary --format csv
```

Audit candidate-driven assignments that were skipped after failed subproblem
evaluation. Rows include the candidate source scenario when candidates were
created from scenario records:

```bash
openutility-style-table2-9 --report style-decomposition --view candidate-skips --format csv
```

Use `--uncalibrated` to run the same catalog without benchmark-calibration
controls:

```bash
openutility-style-table2-9 --catalog physical-profile --uncalibrated --format csv
```

The CLI uses the SciPy/HiGHS MILP adapter bundled through SciPy. Use
`--solver-time-limit` to change the per-scenario solver limit.

Checked CSV examples are stored in:

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
- `examples/computational_best_methods.csv`
- `examples/computational_method_summary.csv`
- `examples/computational_bilevel_trajectory.csv`
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

Run the synthetic reported bilevel comparison example workflow:

```bash
python examples/contribution2_bilevel_reported_comparison.py
```

Run the physical-profile decomposition smoke workflow:

```bash
python examples/contribution2_physical_profile_decomposition_smoke.py
```

Run the candidate-driven decomposition example that cuts one failed candidate:

```bash
python examples/contribution2_candidate_decomposition_skipped_candidate.py
```

## Python API

Run the calibrated reported-equipment catalog:

```python
from OpenUtility.benchmarks import get_contribution2_case_study2_best_configuration
from OpenUtility.style import (
    compare_static_style_result_to_best_configuration,
    run_static_style_scenario,
    scipy_milp_static_style_solver,
    style_case_study_2_contribution2_best_configuration_catalog,
)

catalog = style_case_study_2_contribution2_best_configuration_catalog()
solve = scipy_milp_static_style_solver(options={"time_limit": 20.0})

for scenario in catalog:
    run = run_static_style_scenario(scenario, solve=solve)
    benchmark = get_contribution2_case_study2_best_configuration(scenario.scenario)
    comparison = compare_static_style_result_to_best_configuration(
        run.result,
        benchmark,
        absolute_tolerance=scenario.absolute_tolerance,
    )
    print(scenario.scenario, comparison.within_tolerance)
```

Use `style_case_study_2_contribution2_physical_profile_catalog()` for the
physical-profile catalog. Pass `calibrated=False` to inspect uncalibrated
physical-profile behavior.

Create solver-independent bilevel incumbent records from captured Contribution
2 computational rows:

```python
from OpenUtility.benchmarks import Contribution2ComputationalResult
from OpenUtility.style import (
    BilevelIntegerAssignment,
    BilevelSolutionPool,
    bilevel_incumbents_from_computational_results,
)


def assignment_from_result(
    result: Contribution2ComputationalResult,
) -> BilevelIntegerAssignment:
    values = {
        f"test_{test_number}": int(test_number == result.test_number)
        for test_number in range(1, 13)
    }
    values.update(
        {
            f"scenario_{scenario}": int(scenario == result.scenario)
            for scenario in (1, 2)
        },
    )
    return BilevelIntegerAssignment.from_mapping(values)


pool = BilevelSolutionPool(
    bilevel_incumbents_from_computational_results(
        assignment_factory=assignment_from_result,
    ),
)
print(pool.best_incumbent().label)
```

Attach no-good cuts to Pyomo binary master variables:

```python
import pyomo.environ as pyo

from OpenUtility.style import add_bilevel_no_good_cuts

model = pyo.ConcreteModel()
model.master_choice = pyo.Var(("boiler", "hrsg"), domain=pyo.Binary)
cuts = tuple(incumbent.exclusion_cut() for incumbent in pool.incumbents)
add_bilevel_no_good_cuts(model, cuts, model.master_choice)
```

Run one deterministic bilevel decomposition iteration with caller-provided
master and subproblem callbacks:

```python
from OpenUtility.style import (
    BilevelSubproblemResult,
    run_bilevel_decomposition,
)


def solve_subproblem(assignment):
    return BilevelSubproblemResult(objective_value=53.891, best_bound=52.659)


run = run_bilevel_decomposition(
    build_master,
    solve_master=solve_master,
    solve_subproblem=solve_subproblem,
    max_iterations=10,
    absolute_gap_tolerance=0.01,
)
print(run.stop_reason, run.best_incumbent().objective_value)
```

Format a bilevel run trajectory:

```python
from OpenUtility.style import (
    bilevel_decomposition_run_rows,
    contribution2_bilevel_benchmark_trajectory_rows,
    contribution2_bilevel_trajectory_comparison_rows,
    contribution2_synthetic_bilevel_decomposition_run,
    format_bilevel_decomposition_run_rows,
)

rows = bilevel_decomposition_run_rows(run)
print(format_bilevel_decomposition_run_rows(rows, output_format="csv"))
reported_run = contribution2_synthetic_bilevel_decomposition_run(
    test_number=6,
    scenario=2,
)
reported_rows = bilevel_decomposition_run_rows(reported_run)
benchmark_rows = contribution2_bilevel_benchmark_trajectory_rows()
comparison_rows = contribution2_bilevel_trajectory_comparison_rows(
    test_number=6,
    scenario=2,
    actual_rows=reported_rows,
    benchmark_rows=benchmark_rows,
)
```

Extract a STYLE model's current master binary assignment:

```python
from OpenUtility.style import (
    build_static_style_model,
    build_static_style_binary_selection_master,
    compatible_bilevel_integer_assignments,
    fix_style_master_integer_assignment,
    scipy_milp_static_style_solver,
    style_case_study_2_contribution2_physical_profile_catalog,
    style_fixed_assignment_subproblem_result,
    style_master_binary_variables,
    style_master_integer_assignment_from_model,
    run_static_style_fixed_assignment_decomposition,
    run_static_style_binary_selection_decomposition,
    run_static_style_binary_selection_candidate_decomposition,
    style_binary_selection_candidate_from_scenario,
    style_binary_selection_candidate_solver,
    style_binary_selection_candidates_from_scenarios,
    style_binary_selection_master_assignment_from_model,
)

catalog = style_case_study_2_contribution2_physical_profile_catalog()
scenario = next(iter(catalog))
model = build_static_style_model(scenario.data)
master_variables = style_master_binary_variables(model)
# Solve or fix the binary variables before reading the assignment.
assignment = style_master_integer_assignment_from_model(model)
# Build a separate model and fix its binaries before evaluating a subproblem.
subproblem_model = build_static_style_model(scenario.data)
fix_style_master_integer_assignment(subproblem_model, assignment)
subproblem = style_fixed_assignment_subproblem_result(
    scenario,
    assignment,
    solve=scipy_milp_static_style_solver(),
)
decomposition_run = run_static_style_fixed_assignment_decomposition(
    scenario,
    solve_master=scipy_milp_static_style_solver(),
    solve_subproblem=scipy_milp_static_style_solver(),
    max_iterations=1,
)
binary_master = build_static_style_binary_selection_master(scenario.data)
for name, value in assignment.as_dict().items():
    binary_master.master_choice[name].value = value
binary_assignment = style_binary_selection_master_assignment_from_model(binary_master)

binary_master_run = run_static_style_binary_selection_decomposition(
    scenario,
    solve_master=style_binary_selection_candidate_solver((binary_assignment,)),
    solve_subproblem=scipy_milp_static_style_solver(),
    max_iterations=1,
)
solved_candidate = style_binary_selection_candidate_from_scenario(
    scenario,
    solve=scipy_milp_static_style_solver(),
)
candidate_pool = style_binary_selection_candidates_from_scenarios(
    catalog,
    solve=scipy_milp_static_style_solver(),
)
compatible_candidates = compatible_bilevel_integer_assignments(
    candidate_pool,
    variable_names=style_master_binary_variables(subproblem_model),
)
candidate_run = run_static_style_binary_selection_candidate_decomposition(
    scenario,
    candidates=compatible_candidates,
    solve_subproblem=scipy_milp_static_style_solver(),
    max_iterations=1,
)
```

## Interpreting Residuals

The reported-equipment catalog is calibrated to reproduce all compared Table
2-9 rows, with only the published hot-oil/FSR stand-alone total-cost rounding
tolerance.

The calibrated physical-profile catalog keeps the extracted P1.D heat interval
profile active. It matches the reported utility steam, power, fuel cost,
maintenance, capital, and calibrated hot-oil/economic rows where controls are
defined, while preserving the physical fuel-consumption deltas. The current
residuals are summarized in `docs/replication_plan.md`.
