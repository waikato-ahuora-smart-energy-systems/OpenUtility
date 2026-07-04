"""Pyomo solver adapters for static STYLE scenario runs."""

from __future__ import annotations

from collections.abc import Mapping

import pyomo.environ as pyo

from .runner import StaticStyleSolve, StaticStyleSolverStatus


def pyomo_static_style_solver(
    solver_name: str,
    *,
    tee: bool = False,
    options: Mapping[str, object] | None = None,
) -> StaticStyleSolve:
    """Return a static STYLE solve callback using a Pyomo `SolverFactory` solver."""

    solver_options = None if options is None else dict(options)

    def solve(model: pyo.ConcreteModel) -> StaticStyleSolverStatus:
        return solve_static_style_model_with_pyomo(
            model,
            solver_name,
            tee=tee,
            options=solver_options,
        )

    return solve


def solve_static_style_model_with_pyomo(
    model: pyo.ConcreteModel,
    solver_name: str,
    *,
    tee: bool = False,
    options: Mapping[str, object] | None = None,
) -> StaticStyleSolverStatus:
    """Solve a static STYLE Pyomo model and normalize solver status metadata."""

    _require_text(solver_name, "solver_name")
    solver = pyo.SolverFactory(solver_name)
    if not solver.available(exception_flag=False):
        raise RuntimeError(f"Pyomo solver {solver_name!r} is not available")
    if options:
        solver.options.update(dict(options))
    results = solver.solve(model, tee=tee, load_solutions=False)
    if _has_solution(results):
        model.solutions.load_from(results)
    return _solver_status_from_results(results)


def _solver_status_from_results(results: object | None) -> StaticStyleSolverStatus:
    if results is None:
        return StaticStyleSolverStatus()
    solver_results = getattr(results, "solver", None)
    return StaticStyleSolverStatus(
        status=_text_or_default(getattr(solver_results, "status", None), "unknown"),
        termination_condition=_text_or_none(
            getattr(solver_results, "termination_condition", None),
        ),
        message=_text_or_none(getattr(solver_results, "message", None)),
    )


def _has_solution(results: object | None) -> bool:
    if results is None:
        return False
    solution = getattr(results, "solution", None)
    return solution is not None and len(solution) > 0


def _text_or_default(value: object | None, default: str) -> str:
    text = _text_or_none(value)
    return default if text is None else text


def _text_or_none(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "<undefined>":
        return None
    return None if not text else text


def _require_text(value: str, label: str) -> None:
    if not value.strip():
        raise ValueError(f"{label} must not be blank")
