"""Contribution 2 bilevel benchmark replay helpers."""

from __future__ import annotations

import pyomo.environ as pyo

from case_study.jimenez_romero_utility_system_optimization.benchmarks import (
    get_contribution2_computational_result,
)
from OpenUtility.style.bilevel import (
    BilevelDecompositionRun,
    BilevelIntegerAssignment,
    BilevelSubproblemResult,
    run_bilevel_decomposition,
)


def contribution2_reported_bilevel_decomposition_run(
    *,
    test_number: int,
    scenario: int,
) -> BilevelDecompositionRun:
    """Represent one captured Contribution 2 bilevel result as a run."""

    return contribution2_synthetic_bilevel_decomposition_run(
        test_number=test_number,
        scenario=scenario,
    )


def contribution2_synthetic_bilevel_decomposition_run(
    *,
    test_number: int,
    scenario: int,
) -> BilevelDecompositionRun:
    """Generate a loop-backed synthetic run for one reported bilevel result."""

    result = get_contribution2_computational_result(
        test_number,
        scenario,
        "bilevel",
    )
    reported_assignment = _contribution2_reported_bilevel_assignment(
        test_number=test_number,
        scenario=scenario,
    )

    def build_master() -> pyo.ConcreteModel:
        return _contribution2_synthetic_bilevel_master_model(reported_assignment)

    def solve_master(model: pyo.ConcreteModel) -> str:
        _fix_contribution2_synthetic_master_assignment(
            model,
            reported_assignment,
        )
        return "synthetic-master-optimal"

    def solve_subproblem(
        assignment: BilevelIntegerAssignment,
    ) -> BilevelSubproblemResult:
        if assignment != reported_assignment:
            raise ValueError(
                "synthetic Contribution 2 master assignment does not match "
                "the reported fixture",
            )
        return BilevelSubproblemResult(
            objective_value=result.best_solution_found,
            best_bound=result.best_possible,
            elapsed_seconds=result.computational_time_seconds,
            status="reported",
            hit_time_limit=result.hit_time_limit,
            source_method=result.method,
        )

    generated_run = run_bilevel_decomposition(
        build_master,
        solve_master=solve_master,
        solve_subproblem=solve_subproblem,
        max_iterations=1,
        binary_variables=lambda model: model.master_choice,
        assignment_from_model=_contribution2_synthetic_bilevel_assignment_from_model,
    )
    return BilevelDecompositionRun(
        iterations=generated_run.iterations,
        solution_pool=generated_run.solution_pool,
        stop_reason="reported",
    )


def _contribution2_reported_bilevel_assignment(
    *,
    test_number: int,
    scenario: int,
) -> BilevelIntegerAssignment:
    return BilevelIntegerAssignment.from_mapping(
        {
            "reported_bilevel_solution": 1,
            f"test_{test_number}": 1,
            f"scenario_{scenario}": 1,
        },
    )


def _contribution2_synthetic_bilevel_master_model(
    assignment: BilevelIntegerAssignment,
) -> pyo.ConcreteModel:
    model = pyo.ConcreteModel(name="synthetic Contribution 2 bilevel master")
    model.master_choice = pyo.Var(
        tuple(assignment.as_dict()),
        domain=pyo.Binary,
    )
    return model


def _fix_contribution2_synthetic_master_assignment(
    model: pyo.ConcreteModel,
    assignment: BilevelIntegerAssignment,
) -> None:
    values = assignment.as_dict()
    for variable_name in model.master_choice:
        model.master_choice[variable_name].value = values[variable_name]


def _contribution2_synthetic_bilevel_assignment_from_model(
    model: pyo.ConcreteModel,
) -> BilevelIntegerAssignment:
    return BilevelIntegerAssignment.from_mapping(
        {
            variable_name: int(pyo.value(model.master_choice[variable_name]) >= 0.5)
            for variable_name in model.master_choice
        },
    )


__all__ = (
    "contribution2_reported_bilevel_decomposition_run",
    "contribution2_synthetic_bilevel_decomposition_run",
)
