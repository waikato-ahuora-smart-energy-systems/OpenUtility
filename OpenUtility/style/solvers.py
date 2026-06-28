"""Pyomo solver adapters for static STYLE scenario runs."""

from __future__ import annotations

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.repn import generate_standard_repn

from .runner import StaticStyleSolve, StaticStyleSolverStatus


def pyomo_static_style_solver(
    solver_name: str,
    *,
    tee: bool = False,
    options: Mapping[str, object] | None = None,
) -> StaticStyleSolve:
    """Return a runner-compatible callback using a Pyomo `SolverFactory` solver."""

    solver_options = None if options is None else dict(options)

    def solve(model: pyo.ConcreteModel) -> StaticStyleSolverStatus:
        return solve_static_style_model_with_pyomo(
            model,
            solver_name,
            tee=tee,
            options=solver_options,
        )

    return solve


def scipy_milp_static_style_solver(
    *,
    options: Mapping[str, object] | None = None,
) -> StaticStyleSolve:
    """Return a runner-compatible callback using SciPy's HiGHS MILP solver."""

    solver_options = None if options is None else dict(options)

    def solve(model: pyo.ConcreteModel) -> StaticStyleSolverStatus:
        return solve_static_style_model_with_scipy_milp(
            model,
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
    results = solver.solve(model, tee=tee)
    return _solver_status_from_results(results)


def solve_static_style_model_with_scipy_milp(
    model: pyo.ConcreteModel,
    *,
    options: Mapping[str, object] | None = None,
) -> StaticStyleSolverStatus:
    """Solve a linear Pyomo MILP using SciPy's bundled HiGHS interface."""

    scipy_inputs = _scipy_milp_inputs(model)
    result = _run_scipy_milp(scipy_inputs, options=options)
    if result.x is not None:
        _write_scipy_solution(scipy_inputs.variables, result.x)
    return _scipy_milp_status(result)


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


def _scipy_milp_inputs(model: pyo.ConcreteModel):
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint
    from scipy.sparse import coo_array

    variables = tuple(model.component_data_objects(pyo.Var, descend_into=True))
    variable_index = {id(variable): index for index, variable in enumerate(variables)}
    objective = _single_active_objective(model)
    objective_repn = generate_standard_repn(objective.expr)
    if not objective_repn.is_linear():
        raise ValueError("objective must be linear for SciPy MILP solving")

    c = np.zeros(len(variables), dtype=float)
    objective_sign = 1.0 if objective.sense == pyo.minimize else -1.0
    _add_linear_terms(c, objective_repn, variable_index, multiplier=objective_sign)

    lower_bounds = []
    upper_bounds = []
    integrality = []
    for variable in variables:
        lower, upper = _variable_bounds(variable)
        lower_bounds.append(lower)
        upper_bounds.append(upper)
        integrality.append(1 if variable.is_binary() or variable.is_integer() else 0)

    rows: list[int] = []
    columns: list[int] = []
    values: list[float] = []
    constraint_lower_bounds: list[float] = []
    constraint_upper_bounds: list[float] = []
    for row, constraint in enumerate(
        model.component_data_objects(pyo.Constraint, active=True, descend_into=True),
    ):
        repn = generate_standard_repn(constraint.body)
        if not repn.is_linear():
            raise ValueError("constraints must be linear for SciPy MILP solving")
        for variable, coefficient in zip(
            repn.linear_vars,
            repn.linear_coefs,
            strict=True,
        ):
            rows.append(row)
            columns.append(variable_index[id(variable)])
            values.append(float(pyo.value(coefficient)))
        constant = float(pyo.value(repn.constant))
        constraint_lower_bounds.append(_bound_value(constraint.lower, -np.inf) - constant)
        constraint_upper_bounds.append(_bound_value(constraint.upper, np.inf) - constant)

    linear_constraints = ()
    if constraint_lower_bounds:
        matrix = coo_array(
            (values, (rows, columns)),
            shape=(len(constraint_lower_bounds), len(variables)),
        ).tocsc()
        linear_constraints = (
            LinearConstraint(
                matrix,
                np.array(constraint_lower_bounds, dtype=float),
                np.array(constraint_upper_bounds, dtype=float),
            ),
        )
    return _ScipyMilpInputs(
        variables=variables,
        c=c,
        integrality=np.array(integrality, dtype=int),
        bounds=Bounds(
            np.array(lower_bounds, dtype=float),
            np.array(upper_bounds, dtype=float),
        ),
        constraints=linear_constraints,
    )


def _run_scipy_milp(inputs, *, options: Mapping[str, object] | None):
    from scipy.optimize import milp

    return milp(
        c=inputs.c,
        integrality=inputs.integrality,
        bounds=inputs.bounds,
        constraints=inputs.constraints,
        options=None if options is None else dict(options),
    )


def _write_scipy_solution(variables: tuple[pyo.Var, ...], solution) -> None:
    for variable, value in zip(variables, solution, strict=True):
        variable.set_value(_clean_solution_value(variable, float(value)))


def _scipy_milp_status(result) -> StaticStyleSolverStatus:
    if result.success:
        return StaticStyleSolverStatus(
            status="ok",
            termination_condition="optimal",
            message=_text_or_none(result.message),
        )
    termination = {
        1: "limit",
        2: "infeasible",
        3: "unbounded",
    }.get(result.status, "error")
    return StaticStyleSolverStatus(
        status="warning",
        termination_condition=termination,
        message=_text_or_none(result.message),
    )


def _single_active_objective(model: pyo.ConcreteModel):
    objectives = tuple(
        model.component_data_objects(pyo.Objective, active=True, descend_into=True),
    )
    if len(objectives) != 1:
        raise ValueError("SciPy MILP solving requires exactly one active objective")
    return objectives[0]


def _add_linear_terms(
    c,
    repn,
    variable_index: Mapping[int, int],
    *,
    multiplier: float,
) -> None:
    for variable, coefficient in zip(repn.linear_vars, repn.linear_coefs, strict=True):
        c[variable_index[id(variable)]] += multiplier * float(pyo.value(coefficient))


def _variable_bounds(variable) -> tuple[float, float]:
    import numpy as np

    if variable.fixed:
        value = float(pyo.value(variable))
        return value, value
    lower = _bound_value(variable.lb, -np.inf)
    upper = _bound_value(variable.ub, np.inf)
    if variable.is_binary():
        lower = max(0.0, lower)
        upper = min(1.0, upper)
    return lower, upper


def _clean_solution_value(variable, value: float, *, tolerance: float = 1e-9) -> float:
    if variable.is_binary() or variable.is_integer():
        value = round(value)
    lower = None if variable.lb is None else float(pyo.value(variable.lb))
    upper = None if variable.ub is None else float(pyo.value(variable.ub))
    if lower is not None and value < lower and lower - value <= tolerance:
        return lower
    if upper is not None and value > upper and value - upper <= tolerance:
        return upper
    return value


def _bound_value(bound, default: float) -> float:
    if bound is None:
        return default
    return float(pyo.value(bound))


class _ScipyMilpInputs:
    def __init__(
        self,
        *,
        variables: tuple[pyo.Var, ...],
        c,
        integrality,
        bounds,
        constraints,
    ) -> None:
        self.variables = variables
        self.c = c
        self.integrality = integrality
        self.bounds = bounds
        self.constraints = constraints


def _text_or_default(value: object | None, default: str) -> str:
    text = _text_or_none(value)
    return default if text is None else text


def _text_or_none(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return None if not text else text


def _require_text(value: str, label: str) -> None:
    if not value.strip():
        raise ValueError(f"{label} must not be blank")
