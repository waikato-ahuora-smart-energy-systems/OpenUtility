from __future__ import annotations

from dataclasses import dataclass

import pytest
import pyomo.environ as pyo

from case_study.jimenez_romero_utility_system_optimization.benchmarks import (
    CONTRIBUTION2_COMPUTATIONAL_RESULTS,
    Contribution2ComputationalResult,
)
from case_study.jimenez_romero_utility_system_optimization.contribution2_computational_performance import (
    contribution2_reported_bilevel_decomposition_run,
    contribution2_synthetic_bilevel_decomposition_run,
)
from case_study.jimenez_romero_utility_system_optimization.style_model_builders import (
    style_case_study_2_contribution2_physical_profile_catalog,
)
from OpenUtility.style import (
    BilevelDecompositionRun,
    BilevelIncumbent,
    BilevelIntegerAssignment,
    BilevelSolutionPool,
    BilevelSkippedCandidate,
    BilevelSubproblemResult,
    BoilerCandidate,
    GasTurbineCandidate,
    HotOilConfig,
    HrsgCandidate,
    StaticStyleScenario,
    StaticStyleSolverStatus,
    SteamLevelCandidate,
    StyleModelData,
    VhpSteamCandidate,
    VhpSteamSourceCandidate,
    add_bilevel_no_good_cuts,
    bilevel_decomposition_run_rows,
    bilevel_incumbents_from_computational_results,
    bilevel_no_good_cut_expression,
    build_bilevel_master_with_no_good_cuts,
    build_static_style_binary_selection_master,
    build_static_style_model,
    compatible_bilevel_candidate_assignments,
    compatible_bilevel_integer_assignments,
    fix_style_master_integer_assignment,
    run_bilevel_decomposition,
    run_bilevel_decomposition_iteration,
    run_static_style_binary_selection_candidate_decomposition,
    run_static_style_fixed_assignment_decomposition,
    scipy_milp_static_style_solver,
    style_binary_selection_candidate_from_scenario,
    style_binary_selection_candidate_records_from_scenarios,
    style_binary_selection_candidate_solver,
    style_binary_selection_candidates_from_scenarios,
    style_binary_selection_master_assignment_from_model,
    style_fixed_assignment_subproblem_result,
    style_master_binary_variables,
    style_master_integer_assignment_from_model,
    run_static_style_binary_selection_decomposition,
)


def test_bilevel_integer_assignment_creates_no_good_cut_terms() -> None:
    assignment = BilevelIntegerAssignment.from_mapping(
        {
            "select_boiler": 1,
            "select_hrsg": 0,
            "select_vhp_turbine": 1,
        },
    )

    cut = assignment.exclusion_cut()

    assert assignment.selected_variables == ("select_boiler", "select_vhp_turbine")
    assert assignment.unselected_variables == ("select_hrsg",)
    assert cut.selected_variables == ("select_boiler", "select_vhp_turbine")
    assert cut.unselected_variables == ("select_hrsg",)
    assert cut.left_hand_side_value(assignment) == 0
    assert cut.excludes(assignment) is True

    different_assignment = BilevelIntegerAssignment.from_mapping(
        {
            "select_boiler": 1,
            "select_hrsg": 1,
            "select_vhp_turbine": 1,
        },
    )

    assert cut.left_hand_side_value(different_assignment) == 1
    assert cut.is_satisfied_by(different_assignment) is True
    assert cut.excludes(different_assignment) is False
    assert assignment.hamming_distance(different_assignment) == 1


def test_bilevel_solution_pool_tracks_best_unique_incumbent() -> None:
    first = BilevelIncumbent(
        label="iteration-1",
        objective_value=64.86,
        assignment=BilevelIntegerAssignment.from_mapping({"select_boiler": 1}),
        best_bound=64.00,
        elapsed_seconds=120.0,
    )
    second = BilevelIncumbent(
        label="iteration-2",
        objective_value=53.891,
        assignment=BilevelIntegerAssignment.from_mapping({"select_boiler": 0}),
        best_bound=52.659,
        elapsed_seconds=2613.3,
    )

    pool = BilevelSolutionPool((first,)).with_incumbent(second)

    assert pool.best_incumbent() == second
    assert pool.best_objective_value == pytest.approx(53.891)
    assert second.optimality_gap == pytest.approx(1.232)
    assert len(pool.exclusion_cuts()) == 2

    with pytest.raises(ValueError, match="duplicate bilevel incumbent assignment"):
        pool.with_incumbent(first)


def test_bilevel_no_good_cut_expression_uses_pyomo_binary_variables() -> None:
    model = pyo.ConcreteModel()
    model.master_choice = pyo.Var(
        ("select_boiler", "select_hrsg"),
        domain=pyo.Binary,
    )
    assignment = BilevelIntegerAssignment.from_mapping(
        {
            "select_boiler": 1,
            "select_hrsg": 0,
        },
    )

    expression = bilevel_no_good_cut_expression(
        assignment.exclusion_cut(),
        model.master_choice,
    )

    model.master_choice["select_boiler"].value = 1
    model.master_choice["select_hrsg"].value = 0
    assert pyo.value(expression) == pytest.approx(0.0)

    model.master_choice["select_boiler"].value = 0
    model.master_choice["select_hrsg"].value = 0
    assert pyo.value(expression) == pytest.approx(1.0)


def test_add_bilevel_no_good_cuts_creates_indexed_pyomo_constraints() -> None:
    model = pyo.ConcreteModel()
    model.master_choice = pyo.Var(
        ("select_boiler", "select_hrsg"),
        domain=pyo.Binary,
    )
    cuts = (
        BilevelIntegerAssignment.from_mapping(
            {
                "select_boiler": 1,
                "select_hrsg": 0,
            },
        ).exclusion_cut(),
    )

    constraints = add_bilevel_no_good_cuts(model, cuts, model.master_choice)

    assert constraints is model.bilevel_no_good_cuts
    assert tuple(constraints.keys()) == (0,)
    assert constraints[0].lower == pytest.approx(1.0)

    model.master_choice["select_boiler"].value = 1
    model.master_choice["select_hrsg"].value = 0
    assert pyo.value(constraints[0].body) == pytest.approx(0.0)

    model.master_choice["select_boiler"].value = 1
    model.master_choice["select_hrsg"].value = 1
    assert pyo.value(constraints[0].body) == pytest.approx(1.0)


def test_add_bilevel_no_good_cuts_reports_missing_pyomo_variables() -> None:
    model = pyo.ConcreteModel()
    model.master_choice = pyo.Var(("select_boiler",), domain=pyo.Binary)
    cut = BilevelIntegerAssignment.from_mapping(
        {
            "select_boiler": 1,
            "select_hrsg": 0,
        },
    ).exclusion_cut()

    with pytest.raises(KeyError, match="missing Pyomo binary variables"):
        add_bilevel_no_good_cuts(model, (cut,), model.master_choice)


def test_build_bilevel_master_with_no_good_cuts_rebuilds_cut_master() -> None:
    incumbent = BilevelIncumbent(
        label="iteration-1",
        objective_value=10.0,
        assignment=BilevelIntegerAssignment.from_mapping(
            {
                "select_boiler": 1,
                "select_hrsg": 0,
            },
        ),
    )

    model = build_bilevel_master_with_no_good_cuts(
        _synthetic_master_model,
        BilevelSolutionPool((incumbent,)),
        binary_variables=_synthetic_master_binary_variables,
    )

    assert tuple(model.bilevel_no_good_cuts.keys()) == (0,)
    model.master_choice["select_boiler"].value = 1
    model.master_choice["select_hrsg"].value = 0
    assert pyo.value(model.bilevel_no_good_cuts[0].body) == pytest.approx(0.0)

    model.master_choice["select_boiler"].value = 0
    model.master_choice["select_hrsg"].value = 0
    assert pyo.value(model.bilevel_no_good_cuts[0].body) == pytest.approx(1.0)


def test_run_bilevel_decomposition_iteration_records_next_master_cut() -> None:
    def solve_master(model: pyo.ConcreteModel) -> str:
        model.master_choice["select_boiler"].value = 1
        model.master_choice["select_hrsg"].value = 0
        return "master-optimal"

    def solve_subproblem(
        assignment: BilevelIntegerAssignment,
    ) -> BilevelSubproblemResult:
        assert assignment.as_dict() == {
            "select_boiler": 1,
            "select_hrsg": 0,
        }
        return BilevelSubproblemResult(
            objective_value=42.0,
            best_bound=40.0,
            elapsed_seconds=3.5,
            status="slave-optimal",
        )

    iteration = run_bilevel_decomposition_iteration(
        _synthetic_master_model,
        solve_master=solve_master,
        solve_subproblem=solve_subproblem,
        binary_variables=_synthetic_master_binary_variables,
        assignment_from_model=_synthetic_master_assignment,
    )

    assert iteration.master_status == "master-optimal"
    assert iteration.subproblem.status == "slave-optimal"
    assert iteration.incumbent.label == "iteration-1"
    assert iteration.incumbent.objective_value == pytest.approx(42.0)
    assert iteration.incumbent.best_bound == pytest.approx(40.0)
    assert iteration.solution_pool.best_incumbent() == iteration.incumbent
    assert tuple(iteration.next_master_model.bilevel_no_good_cuts.keys()) == (0,)


def test_run_bilevel_decomposition_iteration_applies_existing_pool_cuts() -> None:
    first = BilevelIncumbent(
        label="iteration-1",
        objective_value=42.0,
        assignment=BilevelIntegerAssignment.from_mapping(
            {
                "select_boiler": 1,
                "select_hrsg": 0,
            },
        ),
    )

    def solve_master(model: pyo.ConcreteModel) -> None:
        assert tuple(model.bilevel_no_good_cuts.keys()) == (0,)
        model.master_choice["select_boiler"].value = 0
        model.master_choice["select_hrsg"].value = 1
        assert pyo.value(model.bilevel_no_good_cuts[0].body) == pytest.approx(2.0)

    iteration = run_bilevel_decomposition_iteration(
        _synthetic_master_model,
        solve_master=solve_master,
        solve_subproblem=lambda _: BilevelSubproblemResult(objective_value=41.0),
        solution_pool=BilevelSolutionPool((first,)),
        iteration_index=2,
        binary_variables=_synthetic_master_binary_variables,
        assignment_from_model=_synthetic_master_assignment,
    )

    assert iteration.incumbent.label == "iteration-2"
    assert len(iteration.solution_pool.incumbents) == 2
    assert iteration.solution_pool.best_objective_value == pytest.approx(41.0)
    assert tuple(iteration.next_master_model.bilevel_no_good_cuts.keys()) == (0, 1)


def test_run_bilevel_decomposition_stops_at_gap_tolerance() -> None:
    choices = (
        {"select_boiler": 1, "select_hrsg": 0},
        {"select_boiler": 0, "select_hrsg": 1},
    )
    objectives = {
        (1, 0): BilevelSubproblemResult(objective_value=42.0, best_bound=40.0),
        (0, 1): BilevelSubproblemResult(objective_value=41.0, best_bound=40.95),
    }
    solve_count = 0

    def solve_master(model: pyo.ConcreteModel) -> None:
        nonlocal solve_count
        assert _cut_count(model) == solve_count
        choice = choices[solve_count]
        for variable, value in choice.items():
            model.master_choice[variable].value = value
        solve_count += 1

    def solve_subproblem(
        assignment: BilevelIntegerAssignment,
    ) -> BilevelSubproblemResult:
        values = assignment.as_dict()
        return objectives[(values["select_boiler"], values["select_hrsg"])]

    run = run_bilevel_decomposition(
        _synthetic_master_model,
        solve_master=solve_master,
        solve_subproblem=solve_subproblem,
        max_iterations=3,
        absolute_gap_tolerance=0.1,
        binary_variables=_synthetic_master_binary_variables,
        assignment_from_model=_synthetic_master_assignment,
    )

    assert run.stop_reason == "optimality-gap"
    assert run.converged is True
    assert len(run.iterations) == 2
    assert run.best_incumbent().objective_value == pytest.approx(41.0)
    assert solve_count == 2


def test_run_bilevel_decomposition_stops_at_max_iterations() -> None:
    choices = (
        {"select_boiler": 1, "select_hrsg": 0},
        {"select_boiler": 0, "select_hrsg": 1},
    )
    solve_count = 0

    def solve_master(model: pyo.ConcreteModel) -> None:
        nonlocal solve_count
        choice = choices[solve_count]
        for variable, value in choice.items():
            model.master_choice[variable].value = value
        solve_count += 1

    run = run_bilevel_decomposition(
        _synthetic_master_model,
        solve_master=solve_master,
        solve_subproblem=lambda assignment: BilevelSubproblemResult(
            objective_value=100.0 - len(assignment.selected_variables),
        ),
        max_iterations=2,
        binary_variables=_synthetic_master_binary_variables,
        assignment_from_model=_synthetic_master_assignment,
    )

    assert run.stop_reason == "max-iterations"
    assert run.converged is False
    assert len(run.iterations) == 2
    assert len(run.solution_pool.incumbents) == 2


def test_run_bilevel_decomposition_stops_on_duplicate_incumbent() -> None:
    def solve_master(model: pyo.ConcreteModel) -> None:
        model.master_choice["select_boiler"].value = 1
        model.master_choice["select_hrsg"].value = 0

    run = run_bilevel_decomposition(
        _synthetic_master_model,
        solve_master=solve_master,
        solve_subproblem=lambda _: BilevelSubproblemResult(objective_value=42.0),
        max_iterations=2,
        binary_variables=_synthetic_master_binary_variables,
        assignment_from_model=_synthetic_master_assignment,
    )

    assert run.stop_reason == "duplicate-incumbent"
    assert run.converged is False
    assert len(run.iterations) == 1
    assert len(run.solution_pool.incumbents) == 1


def test_contribution2_reported_bilevel_decomposition_run_matches_fixture() -> None:
    run = contribution2_reported_bilevel_decomposition_run(
        test_number=6,
        scenario=2,
    )
    iteration = run.iterations[0]

    assert run.stop_reason == "reported"
    assert run.converged is False
    assert len(run.iterations) == 1
    assert iteration.incumbent.label == "iteration-1"
    assert iteration.incumbent.objective_value == pytest.approx(53.891)
    assert iteration.incumbent.best_bound == pytest.approx(52.659)
    assert iteration.incumbent.elapsed_seconds == pytest.approx(2613.3)
    assert iteration.subproblem.status == "reported"
    assert iteration.assignment.as_dict() == {
        "reported_bilevel_solution": 1,
        "test_6": 1,
        "scenario_2": 1,
    }


def test_contribution2_synthetic_bilevel_decomposition_run_uses_loop() -> None:
    run = contribution2_synthetic_bilevel_decomposition_run(
        test_number=6,
        scenario=2,
    )
    iteration = run.iterations[0]

    assert run.stop_reason == "reported"
    assert iteration.master_status == "synthetic-master-optimal"
    assert iteration.subproblem.source_method == "bilevel"
    assert iteration.assignment.as_dict() == {
        "reported_bilevel_solution": 1,
        "test_6": 1,
        "scenario_2": 1,
    }
    assert tuple(iteration.next_master_model.bilevel_no_good_cuts.keys()) == (0,)

    for variable_name, value in iteration.assignment.as_dict().items():
        iteration.next_master_model.master_choice[variable_name].value = value
    assert pyo.value(iteration.next_master_model.bilevel_no_good_cuts[0].body) == (
        pytest.approx(0.0)
    )


def test_style_master_binary_variables_extracts_canonical_selection_lookup() -> None:
    model = build_static_style_model(_style_master_data())

    variables = style_master_binary_variables(model)

    assert variables["level_selected[MP_185]"] is model.level_selected["MP_185"]
    assert variables["vhp_selected[VHP_90]"] is model.vhp_selected["VHP_90"]
    assert (
        variables["vhp_source_selected[source_1]"]
        is model.vhp_source_selected["source_1"]
    )
    assert variables["boiler_selected[boiler_1]"] is model.boiler_selected["boiler_1"]
    assert (
        variables["gas_turbine_selected[gt_1]"]
        is model.gas_turbine_selected["gt_1"]
    )
    assert variables["hrsg_selected[hrsg_1]"] is model.hrsg_selected["hrsg_1"]
    assert (
        variables["hrsg_supplementary_firing_selected[hrsg_1]"]
        is model.hrsg_supplementary_firing_selected["hrsg_1"]
    )
    assert variables["hot_oil_furnace_selected"] is model.hot_oil_furnace_selected
    assert "boiler_size[boiler_1]" not in variables


def test_style_master_assignment_reads_current_pyomo_binary_values() -> None:
    model = build_static_style_model(_style_master_data())
    variables = style_master_binary_variables(model)
    for variable in variables.values():
        variable.value = 0.0
    model.level_selected["MP_185"].value = 1.0
    model.boiler_selected["boiler_1"].value = 1.0
    model.hrsg_supplementary_firing_selected["hrsg_1"].value = 1.0

    assignment = style_master_integer_assignment_from_model(model)

    values = assignment.as_dict()
    assert values["level_selected[MP_185]"] == 1
    assert values["boiler_selected[boiler_1]"] == 1
    assert values["gas_turbine_selected[gt_1]"] == 0
    assert values["hrsg_supplementary_firing_selected[hrsg_1]"] == 1

    constraints = add_bilevel_no_good_cuts(
        model,
        (assignment.exclusion_cut(),),
        variables,
    )
    assert pyo.value(constraints[0].body) == pytest.approx(0.0)


def test_fix_style_master_integer_assignment_fixes_pyomo_binary_values() -> None:
    model = build_static_style_model(_style_master_data())
    variables = style_master_binary_variables(model)
    values = {name: 0 for name in variables}
    values["level_selected[MP_185]"] = 1
    values["boiler_selected[boiler_1]"] = 1
    values["hot_oil_furnace_selected"] = 1
    assignment = BilevelIntegerAssignment.from_mapping(values)

    fixed_names = fix_style_master_integer_assignment(model, assignment)

    assert fixed_names == tuple(variables)
    for name, variable in variables.items():
        assert variable.fixed is True
        assert pyo.value(variable) == pytest.approx(values[name])
    assert style_master_integer_assignment_from_model(model) == assignment


def test_fix_style_master_integer_assignment_requires_exact_binary_names() -> None:
    model = build_static_style_model(_style_master_data())
    variables = style_master_binary_variables(model)
    missing_assignment = BilevelIntegerAssignment.from_mapping(
        {
            name: 0
            for name in variables
            if name != "level_selected[MP_185]"
        },
    )
    extra_assignment = BilevelIntegerAssignment.from_mapping(
        dict.fromkeys((*variables, "unknown_binary"), 0),
    )

    with pytest.raises(KeyError, match="missing STYLE master binary values"):
        fix_style_master_integer_assignment(model, missing_assignment)
    with pytest.raises(KeyError, match="unknown STYLE master binary values"):
        fix_style_master_integer_assignment(model, extra_assignment)


def test_style_fixed_assignment_subproblem_result_solves_static_style_model() -> None:
    scenario = _static_style_subproblem_smoke_scenario()
    assignment = _static_style_assignment(
        scenario,
        selected_variables=("level_selected[MP_100]",),
    )

    subproblem = style_fixed_assignment_subproblem_result(
        scenario,
        assignment,
        solve=scipy_milp_static_style_solver(),
    )

    assert subproblem.objective_value == pytest.approx(0.0)
    assert subproblem.best_bound is None
    assert subproblem.status == "optimal"
    assert subproblem.source_method == "static-style-fixed-assignment"


def test_style_fixed_assignment_subproblem_result_rejects_failed_solve() -> None:
    scenario = _static_style_subproblem_smoke_scenario()
    assignment = _static_style_assignment(scenario)

    def solve(_model: pyo.ConcreteModel) -> StaticStyleSolverStatus:
        return StaticStyleSolverStatus(
            status="warning",
            termination_condition="infeasible",
            message="test infeasible subproblem",
        )

    with pytest.raises(RuntimeError, match="fixed-assignment subproblem"):
        style_fixed_assignment_subproblem_result(scenario, assignment, solve=solve)


def test_run_static_style_fixed_assignment_decomposition_uses_style_master() -> None:
    scenario = _static_style_subproblem_smoke_scenario()

    run = run_static_style_fixed_assignment_decomposition(
        scenario,
        solve_master=scipy_milp_static_style_solver(),
        solve_subproblem=scipy_milp_static_style_solver(),
        max_iterations=1,
    )
    iteration = run.iterations[0]

    assert run.stop_reason == "max-iterations"
    assert len(run.iterations) == 1
    assert iteration.master_status.termination_condition == "optimal"
    assert iteration.assignment.as_dict()["level_selected[MP_100]"] == 1
    assert iteration.subproblem.objective_value == pytest.approx(0.0)
    assert iteration.subproblem.status == "optimal"
    assert run.best_incumbent().objective_value == pytest.approx(0.0)
    assert tuple(iteration.next_master_model.bilevel_no_good_cuts.keys()) == (0,)


def test_build_static_style_binary_selection_master_uses_style_binary_names() -> None:
    data = _style_master_data()
    full_model = build_static_style_model(data)

    master = build_static_style_binary_selection_master(data)

    assert tuple(master.master_choice) == tuple(style_master_binary_variables(full_model))
    assert all(master.master_choice[name].is_binary() for name in master.master_choice)
    assert len(tuple(master.component_data_objects(pyo.Var))) == len(
        style_master_binary_variables(full_model),
    )


def test_static_style_binary_selection_decomposition_evaluates_fixed_subproblem() -> None:
    scenario = _static_style_subproblem_smoke_scenario()
    assignment = _static_style_assignment(
        scenario,
        selected_variables=("level_selected[MP_100]",),
    )

    def solve_master(model: pyo.ConcreteModel) -> str:
        for name, value in assignment.as_dict().items():
            model.master_choice[name].value = value
        return "binary-selection-master"

    run = run_static_style_binary_selection_decomposition(
        scenario,
        solve_master=solve_master,
        solve_subproblem=scipy_milp_static_style_solver(),
        max_iterations=1,
    )
    iteration = run.iterations[0]

    assert iteration.master_status == "binary-selection-master"
    assert style_binary_selection_master_assignment_from_model(
        iteration.master_model,
    ) == assignment
    assert iteration.subproblem.objective_value == pytest.approx(0.0)
    assert tuple(iteration.next_master_model.bilevel_no_good_cuts.keys()) == (0,)


def test_style_binary_selection_candidate_solver_skips_excluded_assignments() -> None:
    data = _style_master_data()
    variable_names = tuple(
        build_static_style_binary_selection_master(data).master_choice,
    )
    first_values = dict.fromkeys(variable_names, 0)
    first_values["level_selected[MP_185]"] = 1
    second_values = dict.fromkeys(variable_names, 0)
    second_values["boiler_selected[boiler_1]"] = 1
    first = BilevelIntegerAssignment.from_mapping(first_values)
    second = BilevelIntegerAssignment.from_mapping(second_values)
    solve_master = style_binary_selection_candidate_solver((first, second))

    master = build_static_style_binary_selection_master(data)
    first_status = solve_master(master)

    assert first_status == "candidate-1"
    assert style_binary_selection_master_assignment_from_model(master) == first

    cut_master = build_bilevel_master_with_no_good_cuts(
        lambda: build_static_style_binary_selection_master(data),
        BilevelSolutionPool(
            (
                BilevelIncumbent(
                    label="first",
                    objective_value=1.0,
                    assignment=first,
                ),
            ),
        ),
        binary_variables=lambda model: model.master_choice,
    )
    second_status = solve_master(cut_master)

    assert second_status == "candidate-2"
    assert style_binary_selection_master_assignment_from_model(cut_master) == second


def test_style_binary_selection_candidate_from_scenario_solves_and_extracts_assignment() -> None:
    scenario = next(iter(style_case_study_2_contribution2_physical_profile_catalog()))

    assignment = style_binary_selection_candidate_from_scenario(
        scenario,
        solve=scipy_milp_static_style_solver(),
    )

    assert len(assignment.selected_variables) == 7
    assert len(assignment.unselected_variables) == 270
    assert assignment.as_dict()["level_selected[HP_272p5]"] == 1
    assert assignment.as_dict()["boiler_selected[reported-boiler]"] == 1


def test_style_binary_selection_candidates_from_scenarios_are_unique_and_ordered() -> None:
    scenarios = tuple(
        style_case_study_2_contribution2_physical_profile_catalog(),
    ) + tuple(
        style_case_study_2_contribution2_physical_profile_catalog(calibrated=False),
    )

    candidates = style_binary_selection_candidates_from_scenarios(
        scenarios,
        solve=scipy_milp_static_style_solver(),
    )

    assert len(candidates) == 4
    assert [len(candidate.values) for candidate in candidates] == [277, 187, 186, 186]
    assert [len(candidate.selected_variables) for candidate in candidates] == [
        7,
        46,
        45,
        24,
    ]


def test_style_binary_selection_candidate_records_preserve_source_labels() -> None:
    scenarios = tuple(
        style_case_study_2_contribution2_physical_profile_catalog(),
    ) + tuple(
        style_case_study_2_contribution2_physical_profile_catalog(calibrated=False),
    )

    records = style_binary_selection_candidate_records_from_scenarios(
        scenarios,
        solve=scipy_milp_static_style_solver(),
    )

    assert len(records) == 4
    assert records[0].source_label == (
        "contribution-2-case-study-2-physical-profile:"
        "utility-system-stand-alone"
    )
    assert [len(record.assignment.selected_variables) for record in records] == [
        7,
        46,
        45,
        24,
    ]


def test_style_binary_selection_candidate_records_accept_source_label_factory() -> None:
    scenarios = tuple(
        style_case_study_2_contribution2_physical_profile_catalog(),
    )

    records = style_binary_selection_candidate_records_from_scenarios(
        scenarios[:1],
        solve=scipy_milp_static_style_solver(),
        source_label_factory=lambda scenario: f"calibrated:{scenario.scenario}",
    )

    assert len(records) == 1
    assert records[0].source_label == "calibrated:utility-system-stand-alone"


def test_compatible_bilevel_integer_assignments_filters_to_target_variables() -> None:
    calibrated_catalog = style_case_study_2_contribution2_physical_profile_catalog()
    uncalibrated_catalog = style_case_study_2_contribution2_physical_profile_catalog(
        calibrated=False,
    )
    scenarios = tuple(calibrated_catalog) + tuple(uncalibrated_catalog)
    candidates = style_binary_selection_candidates_from_scenarios(
        scenarios,
        solve=scipy_milp_static_style_solver(),
    )
    target = calibrated_catalog.get(
        "contribution-2-case-study-2-physical-profile",
        "hot-oil-fsr-microgrid",
    )
    target_variables = tuple(
        build_static_style_binary_selection_master(target.data).master_choice,
    )

    compatible = compatible_bilevel_integer_assignments(
        candidates,
        variable_names=target_variables,
    )

    assert len(compatible) == 2
    assert [len(candidate.selected_variables) for candidate in compatible] == [45, 24]
    assert all(
        set(candidate.as_dict()) == set(target_variables)
        for candidate in compatible
    )


def test_compatible_bilevel_candidate_assignments_keeps_source_labels() -> None:
    calibrated_catalog = style_case_study_2_contribution2_physical_profile_catalog()
    uncalibrated_catalog = style_case_study_2_contribution2_physical_profile_catalog(
        calibrated=False,
    )
    target = calibrated_catalog.get(
        "contribution-2-case-study-2-physical-profile",
        "hot-oil-fsr-microgrid",
    )
    records = style_binary_selection_candidate_records_from_scenarios(
        tuple(calibrated_catalog) + tuple(uncalibrated_catalog),
        solve=scipy_milp_static_style_solver(),
    )

    compatible = compatible_bilevel_candidate_assignments(
        records,
        variable_names=build_static_style_binary_selection_master(
            target.data,
        ).master_choice,
    )

    assert [len(record.assignment.selected_variables) for record in compatible] == [
        45,
        24,
    ]
    assert [record.source_label for record in compatible] == [
        "contribution-2-case-study-2-physical-profile:hot-oil-fsr-microgrid",
        "contribution-2-case-study-2-physical-profile:hot-oil-fsr-stand-alone",
    ]


def test_solved_candidate_pool_drives_binary_selection_master_after_cut() -> None:
    calibrated_catalog = style_case_study_2_contribution2_physical_profile_catalog()
    uncalibrated_catalog = style_case_study_2_contribution2_physical_profile_catalog(
        calibrated=False,
    )
    target = calibrated_catalog.get(
        "contribution-2-case-study-2-physical-profile",
        "hot-oil-fsr-microgrid",
    )
    target_variables = tuple(
        build_static_style_binary_selection_master(target.data).master_choice,
    )
    candidates = compatible_bilevel_integer_assignments(
        style_binary_selection_candidates_from_scenarios(
            tuple(calibrated_catalog) + tuple(uncalibrated_catalog),
            solve=scipy_milp_static_style_solver(),
        ),
        variable_names=target_variables,
    )
    solve_master = style_binary_selection_candidate_solver(candidates)

    master = build_static_style_binary_selection_master(target.data)
    first_status = solve_master(master)

    assert first_status == "candidate-1"
    assert style_binary_selection_master_assignment_from_model(master) == candidates[0]

    cut_master = build_bilevel_master_with_no_good_cuts(
        lambda: build_static_style_binary_selection_master(target.data),
        BilevelSolutionPool(
            (
                BilevelIncumbent(
                    label="first-solved-candidate",
                    objective_value=1.0,
                    assignment=candidates[0],
                ),
            ),
        ),
        binary_variables=lambda model: model.master_choice,
    )
    second_status = solve_master(cut_master)

    assert second_status == "candidate-2"
    assert style_binary_selection_master_assignment_from_model(cut_master) == (
        candidates[1]
    )


def test_static_style_binary_selection_candidate_decomposition_skips_failed_candidate() -> None:
    calibrated_catalog = style_case_study_2_contribution2_physical_profile_catalog()
    uncalibrated_catalog = style_case_study_2_contribution2_physical_profile_catalog(
        calibrated=False,
    )
    target = calibrated_catalog.get(
        "contribution-2-case-study-2-physical-profile",
        "hot-oil-fsr-microgrid",
    )
    candidates = compatible_bilevel_integer_assignments(
        style_binary_selection_candidates_from_scenarios(
            tuple(calibrated_catalog) + tuple(uncalibrated_catalog),
            solve=scipy_milp_static_style_solver(),
        ),
        variable_names=build_static_style_binary_selection_master(
            target.data,
        ).master_choice,
    )

    run = run_static_style_binary_selection_candidate_decomposition(
        target,
        candidates=candidates,
        solve_subproblem=scipy_milp_static_style_solver(),
        max_iterations=2,
    )

    assert run.stop_reason == "candidate-exhausted"
    assert run.skipped_candidate_count == 1
    assert len(run.skipped_candidates) == 1
    assert run.skipped_candidates[0].candidate_label == "candidate-2"
    assert run.skipped_candidates[0].assignment == candidates[1]
    assert "fixed-assignment subproblem" in run.skipped_candidates[0].reason
    assert len(run.iterations) == 1
    assert run.iterations[0].master_status == "candidate-1"
    assert run.iterations[0].subproblem.objective_value == pytest.approx(53.89)
    assert run.iterations[0].assignment == candidates[0]
    assert run.solution_pool.best_objective_value == pytest.approx(53.89)


def test_candidate_decomposition_skipped_diagnostic_reports_candidate_source() -> None:
    calibrated_catalog = style_case_study_2_contribution2_physical_profile_catalog()
    uncalibrated_catalog = style_case_study_2_contribution2_physical_profile_catalog(
        calibrated=False,
    )
    target = calibrated_catalog.get(
        "contribution-2-case-study-2-physical-profile",
        "hot-oil-fsr-microgrid",
    )
    candidates = compatible_bilevel_candidate_assignments(
        style_binary_selection_candidate_records_from_scenarios(
            tuple(calibrated_catalog) + tuple(uncalibrated_catalog),
            solve=scipy_milp_static_style_solver(),
        ),
        variable_names=build_static_style_binary_selection_master(
            target.data,
        ).master_choice,
    )

    run = run_static_style_binary_selection_candidate_decomposition(
        target,
        candidates=candidates,
        solve_subproblem=scipy_milp_static_style_solver(),
        max_iterations=2,
    )

    assert run.skipped_candidates[0].candidate_label == "candidate-2"
    assert run.skipped_candidates[0].source_label == candidates[1].source_label
    assert run.skipped_candidates[0].source_label == (
        "contribution-2-case-study-2-physical-profile:hot-oil-fsr-stand-alone"
    )
    rows = bilevel_decomposition_run_rows(run)
    assert rows[0]["candidate_source"] == candidates[0].source_label
    assert rows[0]["candidate_source"] == (
        "contribution-2-case-study-2-physical-profile:hot-oil-fsr-microgrid"
    )


def test_bilevel_decomposition_run_counts_skipped_candidate_diagnostics() -> None:
    skipped = BilevelSkippedCandidate(
        candidate_label="candidate-1",
        assignment=BilevelIntegerAssignment.from_mapping({"select_boiler": 1}),
        reason="infeasible fixed-assignment subproblem",
    )

    run = BilevelDecompositionRun(
        iterations=(),
        solution_pool=BilevelSolutionPool(),
        stop_reason="candidate-exhausted",
        skipped_candidates=(skipped,),
    )

    assert run.skipped_candidate_count == 1
    assert run.skipped_candidates == (skipped,)


def test_static_style_binary_selection_decomposition_advances_after_no_good_cut() -> None:
    scenario = StaticStyleScenario(
        case_study="subproblem-smoke",
        scenario="equipment-alternatives",
        data=_style_master_data(),
    )
    first = _static_style_assignment(
        scenario,
        selected_variables=("level_selected[MP_185]", "vhp_selected[VHP_90]"),
    )
    second = _static_style_assignment(
        scenario,
        selected_variables=(
            "level_selected[MP_185]",
            "vhp_selected[VHP_90]",
            "boiler_selected[boiler_1]",
        ),
    )

    run = run_static_style_binary_selection_decomposition(
        scenario,
        solve_master=style_binary_selection_candidate_solver((first, second)),
        solve_subproblem=scipy_milp_static_style_solver(),
        max_iterations=2,
    )

    assert run.stop_reason == "max-iterations"
    assert [iteration.master_status for iteration in run.iterations] == [
        "candidate-1",
        "candidate-2",
    ]
    assert [iteration.assignment for iteration in run.iterations] == [first, second]
    assert [iteration.subproblem.objective_value for iteration in run.iterations] == [
        pytest.approx(0.0),
        pytest.approx(0.0),
    ]
    assert len(run.solution_pool.incumbents) == 2


def test_static_style_fixed_assignment_decomposition_runs_physical_profile_catalog_case() -> None:
    scenario = next(iter(style_case_study_2_contribution2_physical_profile_catalog()))

    run = run_static_style_fixed_assignment_decomposition(
        scenario,
        solve_master=scipy_milp_static_style_solver(),
        solve_subproblem=scipy_milp_static_style_solver(),
        max_iterations=1,
    )
    rows = bilevel_decomposition_run_rows(run)

    assert scenario.scenario == "utility-system-stand-alone"
    assert rows == (
            {
                "iteration_index": 1,
                "candidate_source": "",
                "objective_value": pytest.approx(67.6834),
                "best_bound": None,
                "optimality_gap": None,
            "elapsed_seconds": None,
            "hit_time_limit": False,
            "selected_binary_count": 7,
            "unselected_binary_count": 270,
            "subproblem_status": "optimal",
            "stop_reason": "max-iterations",
            "skipped_candidate_count": 0,
        },
    )


def test_style_master_assignment_requires_solved_binary_values() -> None:
    model = build_static_style_model(_style_master_data())

    with pytest.raises(ValueError, match="has no value"):
        style_master_integer_assignment_from_model(model)


def test_bilevel_incumbents_from_contribution2_computational_results() -> None:
    incumbents = bilevel_incumbents_from_computational_results(
        CONTRIBUTION2_COMPUTATIONAL_RESULTS,
        assignment_factory=_benchmark_assignment,
    )
    pool = BilevelSolutionPool(incumbents)
    best = pool.best_incumbent()

    assert len(pool.incumbents) == 24
    assert best.label == "test-12-scenario-2"
    assert best.objective_value == pytest.approx(11.252)
    assert best.best_bound == pytest.approx(9.235)
    assert best.optimality_gap == pytest.approx(2.017)
    assert best.elapsed_seconds == pytest.approx(2621.2)
    assert best.assignment.as_dict()["test_12"] == 1
    assert best.assignment.as_dict()["scenario_2"] == 1
    assert len(pool.exclusion_cuts()) == 24


def test_bilevel_incumbents_accept_generic_computational_result_records() -> None:
    results = (
        _SyntheticComputationalResult(
            test_number=1,
            scenario=1,
            method="bilevel",
            best_solution_found=12.0,
            best_possible=10.0,
            computational_time_seconds=3.5,
            hit_time_limit=False,
        ),
        _SyntheticComputationalResult(
            test_number=1,
            scenario=2,
            method="baron",
            best_solution_found=11.0,
            best_possible=9.0,
            computational_time_seconds=4.0,
            hit_time_limit=True,
        ),
    )

    incumbents = bilevel_incumbents_from_computational_results(
        results,
        assignment_factory=_benchmark_assignment,
    )

    assert len(incumbents) == 1
    assert incumbents[0].label == "test-1-scenario-1"
    assert incumbents[0].objective_value == pytest.approx(12.0)
    assert incumbents[0].best_bound == pytest.approx(10.0)
    assert incumbents[0].elapsed_seconds == pytest.approx(3.5)


@dataclass(frozen=True)
class _SyntheticComputationalResult:
    test_number: int
    scenario: int
    method: str
    best_solution_found: float
    best_possible: float | None
    computational_time_seconds: float
    hit_time_limit: bool


def _benchmark_assignment(
    result: Contribution2ComputationalResult | _SyntheticComputationalResult,
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


def _synthetic_master_model() -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    model.master_choice = pyo.Var(
        ("select_boiler", "select_hrsg"),
        domain=pyo.Binary,
    )
    return model


def _synthetic_master_binary_variables(
    model: pyo.ConcreteModel,
) -> pyo.Var:
    return model.master_choice


def _synthetic_master_assignment(
    model: pyo.ConcreteModel,
) -> BilevelIntegerAssignment:
    return BilevelIntegerAssignment.from_mapping(
        {
            choice: int(pyo.value(model.master_choice[choice]) >= 0.5)
            for choice in model.master_choice
        },
    )


def _cut_count(model: pyo.ConcreteModel) -> int:
    constraints = model.component("bilevel_no_good_cuts")
    if constraints is None:
        return 0
    return len(constraints)


def _static_style_assignment(
    scenario: StaticStyleScenario,
    *,
    selected_variables: tuple[str, ...] = (),
) -> BilevelIntegerAssignment:
    model = build_static_style_model(scenario.data)
    selected = set(selected_variables)
    return BilevelIntegerAssignment.from_mapping(
        {
            name: int(name in selected)
            for name in style_master_binary_variables(model)
        },
    )


def _static_style_subproblem_smoke_scenario() -> StaticStyleScenario:
    return StaticStyleScenario(
        case_study="subproblem-smoke",
        scenario="one-level",
        data=StyleModelData(
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
        ),
    )


def _style_master_data() -> StyleModelData:
    return StyleModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_90",
                steam_enthalpy=5.0,
                feedwater_enthalpy=1.0,
                steam_flow_upper_bound=20.0,
            ),
        ),
        vhp_sources=(
            VhpSteamSourceCandidate(
                name="source_1",
                vhp_header="VHP_90",
                min_capacity=0.0,
                max_capacity=5.0,
                minimum_load_fraction=0.0,
            ),
        ),
        boilers=(
            BoilerCandidate(
                name="boiler_1",
                vhp_header="VHP_90",
                size_fuel_coefficient=0.0,
                load_fuel_coefficient=1.0,
                min_capacity=0.0,
                max_capacity=10.0,
                minimum_load_fraction=0.0,
            ),
        ),
        gas_turbines=(
            GasTurbineCandidate(
                name="gt_1",
                fuel_lhv=10.0,
                power_slope=1.0,
                power_intercept=0.0,
                min_fuel_flow=0.0,
                max_fuel_flow=10.0,
                minimum_load_fraction=0.0,
            ),
        ),
        hrsgs=(
            HrsgCandidate(
                name="hrsg_1",
                gas_turbine="gt_1",
                vhp_header="VHP_90",
                steam_generation_efficiency=0.8,
                max_heat_input=20.0,
                supplementary_fuel_lhv=10.0,
                supplementary_firing_efficiency=0.9,
                max_supplementary_fuel_flow=5.0,
            ),
        ),
        hot_oil=HotOilConfig(
            fuel_unit_cost=1.0,
            thermal_efficiency=0.8,
        ),
        power_demand=0.0,
    )
