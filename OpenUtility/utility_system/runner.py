"""Scenario-level orchestration for static utility-system model runs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeAlias

import pyomo.environ as pyo

from .data import UtilitySystemModelData
from .pyomo_model import build_utility_system_model
from .results import (
    UtilitySystemBenchmarkComparison,
    UtilitySystemResult,
    UtilitySystemBenchmarkRecord,
    compare_utility_system_result_to_benchmark,
    extract_utility_system_result,
)


@dataclass(frozen=True)
class UtilitySystemScenario:
    """Inputs and optional benchmark for one static utility-system run."""

    case_study: str
    scenario: str
    data: UtilitySystemModelData
    benchmark: UtilitySystemBenchmarkRecord | None = None
    absolute_tolerance: float = 1e-6

    def __post_init__(self) -> None:
        _require_text(self.case_study, "case_study")
        _require_text(self.scenario, "scenario")
        _require_non_negative(self.absolute_tolerance, "absolute_tolerance")
        if self.benchmark is None:
            return
        if (
            self.case_study != self.benchmark.case_study
            or self.scenario != self.benchmark.scenario
        ):
            raise ValueError("benchmark identifies a different utility-system scenario")


@dataclass(frozen=True)
class UtilitySystemSolverStatus:
    """Solver status summary reported by a static utility-system solve callback."""

    status: str = "unknown"
    termination_condition: str | None = None
    message: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.status, "status")


@dataclass(frozen=True)
class UtilitySystemRunResult:
    """Built model, solve status, extracted result, and optional benchmark check."""

    scenario: UtilitySystemScenario
    model: pyo.ConcreteModel
    solver: UtilitySystemSolverStatus
    result: UtilitySystemResult
    comparison: UtilitySystemBenchmarkComparison | None


UtilitySystemSolve: TypeAlias = Callable[
    [pyo.ConcreteModel],
    UtilitySystemSolverStatus | None,
]


def run_utility_system_scenario(
    scenario: UtilitySystemScenario,
    *,
    solve: UtilitySystemSolve,
) -> UtilitySystemRunResult:
    """Build, solve, extract, and optionally benchmark one static utility-system scenario."""

    model = build_utility_system_model(scenario.data)
    solver_status = _normalize_solver_status(solve(model))
    _raise_if_failed_solve(solver_status)
    result = extract_utility_system_result(
        model,
        case_study=scenario.case_study,
        scenario=scenario.scenario,
    )
    comparison = None
    if scenario.benchmark is not None:
        comparison = compare_utility_system_result_to_benchmark(
            result,
            scenario.benchmark,
            absolute_tolerance=scenario.absolute_tolerance,
        )
    return UtilitySystemRunResult(
        scenario=scenario,
        model=model,
        solver=solver_status,
        result=result,
        comparison=comparison,
    )


def _normalize_solver_status(
    status: UtilitySystemSolverStatus | None,
) -> UtilitySystemSolverStatus:
    if status is None:
        return UtilitySystemSolverStatus()
    if not isinstance(status, UtilitySystemSolverStatus):
        raise TypeError("solve must return UtilitySystemSolverStatus or None")
    return status


def _raise_if_failed_solve(status: UtilitySystemSolverStatus) -> None:
    termination = (
        None
        if status.termination_condition is None
        else status.termination_condition.strip().lower()
    )
    if termination not in {"error", "infeasible", "limit", "unbounded"}:
        return
    message = (
        f"Static utility-system solve did not produce an extractable solution: {status}"
    )
    raise RuntimeError(message)


def _require_text(value: str, label: str) -> None:
    if not value.strip():
        raise ValueError(f"{label} must not be blank")


def _require_non_negative(value: float, label: str) -> None:
    if value < 0.0:
        raise ValueError(f"{label} must be non-negative")
