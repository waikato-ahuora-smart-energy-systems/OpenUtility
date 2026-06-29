"""Scenario-level orchestration for static STYLE model runs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeAlias

import pyomo.environ as pyo

from case_study.jimenez_romero_utility_system_optimization.benchmarks import StyleBenchmarkResult

from .data import StyleModelData
from .pyomo_model import build_static_style_model
from .results import (
    StaticStyleBenchmarkComparison,
    StaticStyleResult,
    compare_static_style_result_to_benchmark,
    extract_static_style_result,
)


@dataclass(frozen=True)
class StaticStyleScenario:
    """Inputs and optional benchmark for one static STYLE run."""

    case_study: str
    scenario: str
    data: StyleModelData
    benchmark: StyleBenchmarkResult | None = None
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
            raise ValueError("benchmark identifies a different STYLE scenario")


@dataclass(frozen=True)
class StaticStyleSolverStatus:
    """Solver status summary reported by a static STYLE solve callback."""

    status: str = "unknown"
    termination_condition: str | None = None
    message: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.status, "status")


@dataclass(frozen=True)
class StaticStyleRunResult:
    """Built model, solve status, extracted result, and optional benchmark check."""

    scenario: StaticStyleScenario
    model: pyo.ConcreteModel
    solver: StaticStyleSolverStatus
    result: StaticStyleResult
    comparison: StaticStyleBenchmarkComparison | None


StaticStyleSolve: TypeAlias = Callable[
    [pyo.ConcreteModel],
    StaticStyleSolverStatus | None,
]


def run_static_style_scenario(
    scenario: StaticStyleScenario,
    *,
    solve: StaticStyleSolve,
) -> StaticStyleRunResult:
    """Build, solve, extract, and optionally benchmark one static STYLE scenario."""

    model = build_static_style_model(scenario.data)
    solver_status = _normalize_solver_status(solve(model))
    _raise_if_failed_solve(solver_status)
    result = extract_static_style_result(
        model,
        case_study=scenario.case_study,
        scenario=scenario.scenario,
    )
    comparison = None
    if scenario.benchmark is not None:
        comparison = compare_static_style_result_to_benchmark(
            result,
            scenario.benchmark,
            absolute_tolerance=scenario.absolute_tolerance,
        )
    return StaticStyleRunResult(
        scenario=scenario,
        model=model,
        solver=solver_status,
        result=result,
        comparison=comparison,
    )


def _normalize_solver_status(
    status: StaticStyleSolverStatus | None,
) -> StaticStyleSolverStatus:
    if status is None:
        return StaticStyleSolverStatus()
    if not isinstance(status, StaticStyleSolverStatus):
        raise TypeError("solve must return StaticStyleSolverStatus or None")
    return status


def _raise_if_failed_solve(status: StaticStyleSolverStatus) -> None:
    termination = (
        None
        if status.termination_condition is None
        else status.termination_condition.strip().lower()
    )
    if termination not in {"error", "infeasible", "limit", "unbounded"}:
        return
    message = f"Static STYLE solve did not produce an extractable solution: {status}"
    raise RuntimeError(message)


def _require_text(value: str, label: str) -> None:
    if not value.strip():
        raise ValueError(f"{label} must not be blank")


def _require_non_negative(value: float, label: str) -> None:
    if value < 0.0:
        raise ValueError(f"{label} must be non-negative")
