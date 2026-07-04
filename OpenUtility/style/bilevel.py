"""Solver-independent helpers for STYLE bilevel decomposition bookkeeping."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from math import isfinite
from typing import Any, Protocol

import pyomo.environ as pyo

from .data import StyleModelData
from .pyomo_model import build_static_style_model
from .results import extract_static_style_result
from .runner import (
    StaticStyleScenario,
    StaticStyleSolve,
    StaticStyleSolverStatus,
    run_static_style_scenario,
)


STYLE_MASTER_BINARY_COMPONENT_NAMES: tuple[str, ...] = (
    "level_selected",
    "hot_oil_selected",
    "hot_oil_furnace_selected",
    "vhp_selected",
    "vhp_source_selected",
    "boiler_selected",
    "vhp_turbine_selected",
    "steam_main_turbine_selected",
    "gas_turbine_selected",
    "hrsg_selected",
    "hrsg_supplementary_firing_selected",
)


class _ComputationalResultRecord(Protocol):
    @property
    def test_number(self) -> int: ...

    @property
    def scenario(self) -> int: ...

    @property
    def method(self) -> str: ...

    @property
    def best_solution_found(self) -> float: ...

    @property
    def best_possible(self) -> float | None: ...

    @property
    def computational_time_seconds(self) -> float: ...

    @property
    def hit_time_limit(self) -> bool: ...


@dataclass(frozen=True)
class BilevelIntegerAssignment:
    """Binary master-problem decision vector for one candidate configuration."""

    values: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        normalized = tuple(sorted(self.values, key=lambda item: item[0]))
        _validate_binary_assignment(normalized)
        object.__setattr__(self, "values", normalized)

    @classmethod
    def from_mapping(cls, values: Mapping[str, int]) -> BilevelIntegerAssignment:
        """Create an assignment from a variable-to-binary-value mapping."""

        return cls(tuple(values.items()))

    @property
    def selected_variables(self) -> tuple[str, ...]:
        """Return variable names fixed to one."""

        return tuple(variable for variable, value in self.values if value == 1)

    @property
    def unselected_variables(self) -> tuple[str, ...]:
        """Return variable names fixed to zero."""

        return tuple(variable for variable, value in self.values if value == 0)

    def as_dict(self) -> dict[str, int]:
        """Return a dictionary copy of the assignment."""

        return dict(self.values)

    def exclusion_cut(self) -> BilevelIntegerCut:
        """Return no-good-cut terms that exclude this exact assignment."""

        return BilevelIntegerCut(
            selected_variables=self.selected_variables,
            unselected_variables=self.unselected_variables,
        )

    def hamming_distance(self, other: BilevelIntegerAssignment) -> int:
        """Return the number of binary values that differ from another assignment."""

        values = self.as_dict()
        other_values = other.as_dict()
        if values.keys() != other_values.keys():
            raise ValueError("bilevel assignments must contain the same variables")
        return sum(
            1 for variable, value in values.items() if value != other_values[variable]
        )


@dataclass(frozen=True)
class BilevelCandidateAssignment:
    """A candidate binary assignment with optional source provenance."""

    assignment: BilevelIntegerAssignment
    source_label: str | None = None

    def __post_init__(self) -> None:
        if self.source_label is not None and not self.source_label.strip():
            raise ValueError("candidate source label must not be blank")


@dataclass(frozen=True)
class BilevelIntegerCut:
    """No-good-cut terms for excluding a previous binary assignment."""

    selected_variables: tuple[str, ...]
    unselected_variables: tuple[str, ...]
    minimum_hamming_distance: int = 1

    def __post_init__(self) -> None:
        selected = tuple(sorted(self.selected_variables))
        unselected = tuple(sorted(self.unselected_variables))
        if not selected and not unselected:
            raise ValueError("bilevel integer cut must contain at least one variable")
        overlap = set(selected).intersection(unselected)
        if overlap:
            raise ValueError("bilevel integer cut variables cannot overlap")
        if self.minimum_hamming_distance < 1:
            raise ValueError("minimum hamming distance must be at least 1")
        object.__setattr__(self, "selected_variables", selected)
        object.__setattr__(self, "unselected_variables", unselected)

    @property
    def variable_names(self) -> tuple[str, ...]:
        """Return all variables referenced by the cut."""

        return self.selected_variables + self.unselected_variables

    def left_hand_side_value(self, assignment: BilevelIntegerAssignment) -> int:
        """Evaluate cut distance terms for a complete binary assignment."""

        values = assignment.as_dict()
        missing = tuple(
            variable for variable in self.variable_names if variable not in values
        )
        if missing:
            raise ValueError(f"assignment is missing cut variables: {missing!r}")
        selected_distance = sum(
            1 for variable in self.selected_variables if values[variable] == 0
        )
        unselected_distance = sum(
            1 for variable in self.unselected_variables if values[variable] == 1
        )
        return selected_distance + unselected_distance

    def is_satisfied_by(self, assignment: BilevelIntegerAssignment) -> bool:
        """Return whether the assignment satisfies the no-good cut."""

        return self.left_hand_side_value(assignment) >= self.minimum_hamming_distance

    def excludes(self, assignment: BilevelIntegerAssignment) -> bool:
        """Return whether the cut rejects this assignment."""

        return not self.is_satisfied_by(assignment)


@dataclass(frozen=True)
class BilevelIncumbent:
    """One incumbent solution found by a bilevel decomposition workflow."""

    label: str
    objective_value: float
    assignment: BilevelIntegerAssignment
    best_bound: float | None = None
    elapsed_seconds: float | None = None
    hit_time_limit: bool = False
    source_method: str | None = None

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("bilevel incumbent label is required")
        if not isfinite(self.objective_value):
            raise ValueError("bilevel incumbent objective value must be finite")
        if self.best_bound is not None and not isfinite(self.best_bound):
            raise ValueError("bilevel incumbent best bound must be finite")
        if self.elapsed_seconds is not None and self.elapsed_seconds < 0.0:
            raise ValueError("bilevel incumbent elapsed seconds must be non-negative")

    @property
    def optimality_gap(self) -> float | None:
        """Return incumbent-minus-bound gap for minimization problems."""

        if self.best_bound is None:
            return None
        return self.objective_value - self.best_bound

    def exclusion_cut(self) -> BilevelIntegerCut:
        """Return a no-good cut for this incumbent's assignment."""

        return self.assignment.exclusion_cut()


@dataclass(frozen=True)
class BilevelSolutionPool:
    """Collection of unique bilevel incumbents for a minimization workflow."""

    incumbents: tuple[BilevelIncumbent, ...] = ()

    def __post_init__(self) -> None:
        _validate_unique_incumbent_assignments(self.incumbents)

    @property
    def best_objective_value(self) -> float:
        """Return the objective value of the best incumbent."""

        return self.best_incumbent().objective_value

    def best_incumbent(self) -> BilevelIncumbent:
        """Return the incumbent with the smallest objective value."""

        if not self.incumbents:
            raise ValueError("bilevel solution pool is empty")
        return min(self.incumbents, key=lambda incumbent: incumbent.objective_value)

    def with_incumbent(self, incumbent: BilevelIncumbent) -> BilevelSolutionPool:
        """Return a new pool containing one additional incumbent."""

        return BilevelSolutionPool(self.incumbents + (incumbent,))

    def exclusion_cuts(self) -> tuple[BilevelIntegerCut, ...]:
        """Return no-good cuts for all incumbent assignments in the pool."""

        return tuple(incumbent.exclusion_cut() for incumbent in self.incumbents)


@dataclass(frozen=True)
class BilevelSubproblemResult:
    """Slave/subproblem result for a fixed master binary assignment."""

    objective_value: float
    best_bound: float | None = None
    elapsed_seconds: float | None = None
    status: str = "unknown"
    hit_time_limit: bool = False
    source_method: str = "bilevel"

    def __post_init__(self) -> None:
        if not isfinite(self.objective_value):
            raise ValueError("bilevel subproblem objective value must be finite")
        if self.best_bound is not None and not isfinite(self.best_bound):
            raise ValueError("bilevel subproblem best bound must be finite")
        if self.elapsed_seconds is not None and self.elapsed_seconds < 0.0:
            raise ValueError("bilevel subproblem elapsed seconds must be non-negative")
        if not self.status.strip():
            raise ValueError("bilevel subproblem status must not be blank")
        if not self.source_method.strip():
            raise ValueError("bilevel subproblem source method must not be blank")


@dataclass(frozen=True)
class BilevelSkippedCandidate:
    """A candidate assignment rejected after failed subproblem evaluation."""

    candidate_label: str
    assignment: BilevelIntegerAssignment
    reason: str
    source_label: str | None = None

    def __post_init__(self) -> None:
        if not self.candidate_label.strip():
            raise ValueError("skipped candidate label must not be blank")
        if not self.reason.strip():
            raise ValueError("skipped candidate reason must not be blank")
        if self.source_label is not None and not self.source_label.strip():
            raise ValueError("skipped candidate source label must not be blank")


@dataclass(frozen=True)
class BilevelDecompositionIteration:
    """Result of one deterministic bilevel decomposition iteration."""

    iteration_index: int
    master_model: pyo.Block
    master_status: Any
    assignment: BilevelIntegerAssignment
    subproblem: BilevelSubproblemResult
    incumbent: BilevelIncumbent
    solution_pool: BilevelSolutionPool
    next_master_model: pyo.Block
    candidate_source_label: str | None = None

    def __post_init__(self) -> None:
        if self.iteration_index < 1:
            raise ValueError("bilevel iteration index must be at least 1")
        if (
            self.candidate_source_label is not None
            and not self.candidate_source_label.strip()
        ):
            raise ValueError("candidate source label must not be blank")


@dataclass(frozen=True)
class BilevelDecompositionRun:
    """Result of a bounded bilevel decomposition run."""

    iterations: tuple[BilevelDecompositionIteration, ...]
    solution_pool: BilevelSolutionPool
    stop_reason: str
    skipped_candidate_count: int = 0
    skipped_candidates: tuple[BilevelSkippedCandidate, ...] = ()

    def __post_init__(self) -> None:
        if not self.stop_reason.strip():
            raise ValueError("bilevel decomposition stop reason must not be blank")
        if self.skipped_candidate_count < 0:
            raise ValueError("skipped candidate count must be non-negative")
        if self.skipped_candidates and self.skipped_candidate_count == 0:
            object.__setattr__(
                self,
                "skipped_candidate_count",
                len(self.skipped_candidates),
            )
        if self.skipped_candidates and self.skipped_candidate_count != len(
            self.skipped_candidates
        ):
            raise ValueError(
                "skipped candidate count must match skipped candidate diagnostics",
            )

    @property
    def converged(self) -> bool:
        """Return whether the run stopped on a convergence criterion."""

        return self.stop_reason == "optimality-gap"

    def best_incumbent(self) -> BilevelIncumbent:
        """Return the best incumbent in the final solution pool."""

        return self.solution_pool.best_incumbent()


def bilevel_incumbents_from_computational_results(
    results: Iterable[_ComputationalResultRecord],
    *,
    assignment_factory: Callable[
        [_ComputationalResultRecord],
        BilevelIntegerAssignment,
    ],
    method: str = "bilevel",
) -> tuple[BilevelIncumbent, ...]:
    """Convert captured computational-result rows into bilevel incumbents."""

    return tuple(
        BilevelIncumbent(
            label=f"test-{result.test_number}-scenario-{result.scenario}",
            objective_value=result.best_solution_found,
            assignment=assignment_factory(result),
            best_bound=result.best_possible,
            elapsed_seconds=result.computational_time_seconds,
            hit_time_limit=result.hit_time_limit,
            source_method=result.method,
        )
        for result in results
        if result.method == method
    )


def bilevel_no_good_cut_expression(
    cut: BilevelIntegerCut,
    binary_variables: Any,
) -> Any:
    """Return a Pyomo expression for the left-hand side of a no-good cut."""

    selected_terms = (
        1 - _lookup_pyomo_binary_variable(binary_variables, variable)
        for variable in cut.selected_variables
    )
    unselected_terms = (
        _lookup_pyomo_binary_variable(binary_variables, variable)
        for variable in cut.unselected_variables
    )
    return sum(selected_terms) + sum(unselected_terms)


def add_bilevel_no_good_cuts(
    model: pyo.Block,
    cuts: Iterable[BilevelIntegerCut],
    binary_variables: Any,
    *,
    component_name: str = "bilevel_no_good_cuts",
) -> pyo.Constraint:
    """Attach no-good-cut constraints to a Pyomo model or block."""

    cut_tuple = tuple(cuts)
    if not cut_tuple:
        raise ValueError("at least one bilevel no-good cut is required")
    if model.component(component_name) is not None:
        raise ValueError(f"Pyomo component {component_name!r} already exists")
    missing_variables = _missing_pyomo_binary_variables(cut_tuple, binary_variables)
    if missing_variables:
        raise KeyError(f"missing Pyomo binary variables: {missing_variables!r}")

    def no_good_cut_rule(_model: pyo.Block, cut_index: int) -> Any:
        cut = cut_tuple[cut_index]
        return (
            bilevel_no_good_cut_expression(cut, binary_variables)
            >= cut.minimum_hamming_distance
        )

    constraints = pyo.Constraint(range(len(cut_tuple)), rule=no_good_cut_rule)
    model.add_component(component_name, constraints)
    return constraints


def build_bilevel_master_with_no_good_cuts(
    build_master: Callable[[], pyo.Block],
    solution_pool: BilevelSolutionPool,
    *,
    binary_variables: Any = None,
    component_name: str = "bilevel_no_good_cuts",
) -> pyo.Block:
    """Build a master model and attach no-good cuts from a solution pool."""

    model = build_master()
    cuts = solution_pool.exclusion_cuts()
    if not cuts:
        return model
    add_bilevel_no_good_cuts(
        model,
        cuts,
        _resolve_binary_variables(model, binary_variables),
        component_name=component_name,
    )
    return model


def run_bilevel_decomposition_iteration(
    build_master: Callable[[], pyo.Block],
    *,
    solve_master: Callable[[pyo.Block], Any],
    solve_subproblem: Callable[[BilevelIntegerAssignment], BilevelSubproblemResult],
    solution_pool: BilevelSolutionPool | None = None,
    iteration_index: int = 1,
    binary_variables: Any = None,
    assignment_from_model: Callable[
        [pyo.Block],
        BilevelIntegerAssignment,
    ]
    | None = None,
    component_name: str = "bilevel_no_good_cuts",
) -> BilevelDecompositionIteration:
    """Run one master/slave bilevel decomposition iteration."""

    if iteration_index < 1:
        raise ValueError("bilevel iteration index must be at least 1")
    starting_pool = BilevelSolutionPool() if solution_pool is None else solution_pool
    master_model = build_bilevel_master_with_no_good_cuts(
        build_master,
        starting_pool,
        binary_variables=binary_variables,
        component_name=component_name,
    )
    master_status = solve_master(master_model)
    read_assignment = (
        style_master_integer_assignment_from_model
        if assignment_from_model is None
        else assignment_from_model
    )
    assignment = read_assignment(master_model)
    subproblem = solve_subproblem(assignment)
    if not isinstance(subproblem, BilevelSubproblemResult):
        raise TypeError("solve_subproblem must return BilevelSubproblemResult")
    incumbent = BilevelIncumbent(
        label=f"iteration-{iteration_index}",
        objective_value=subproblem.objective_value,
        assignment=assignment,
        best_bound=subproblem.best_bound,
        elapsed_seconds=subproblem.elapsed_seconds,
        hit_time_limit=subproblem.hit_time_limit,
        source_method=subproblem.source_method,
    )
    updated_pool = starting_pool.with_incumbent(incumbent)
    next_master_model = build_bilevel_master_with_no_good_cuts(
        build_master,
        updated_pool,
        binary_variables=binary_variables,
        component_name=component_name,
    )
    return BilevelDecompositionIteration(
        iteration_index=iteration_index,
        master_model=master_model,
        master_status=master_status,
        assignment=assignment,
        subproblem=subproblem,
        incumbent=incumbent,
        solution_pool=updated_pool,
        next_master_model=next_master_model,
    )


def run_bilevel_decomposition(
    build_master: Callable[[], pyo.Block],
    *,
    solve_master: Callable[[pyo.Block], Any],
    solve_subproblem: Callable[[BilevelIntegerAssignment], BilevelSubproblemResult],
    max_iterations: int,
    solution_pool: BilevelSolutionPool | None = None,
    absolute_gap_tolerance: float | None = None,
    binary_variables: Any = None,
    assignment_from_model: Callable[
        [pyo.Block],
        BilevelIntegerAssignment,
    ]
    | None = None,
    component_name: str = "bilevel_no_good_cuts",
) -> BilevelDecompositionRun:
    """Run a bounded sequence of bilevel decomposition iterations."""

    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")
    if absolute_gap_tolerance is not None and absolute_gap_tolerance < 0.0:
        raise ValueError("absolute_gap_tolerance must be non-negative")

    pool = BilevelSolutionPool() if solution_pool is None else solution_pool
    iterations: list[BilevelDecompositionIteration] = []
    stop_reason = "max-iterations"
    for iteration_index in range(1, max_iterations + 1):
        try:
            iteration = run_bilevel_decomposition_iteration(
                build_master,
                solve_master=solve_master,
                solve_subproblem=solve_subproblem,
                solution_pool=pool,
                iteration_index=iteration_index,
                binary_variables=binary_variables,
                assignment_from_model=assignment_from_model,
                component_name=component_name,
            )
        except ValueError as exc:
            if "duplicate bilevel incumbent assignment" not in str(exc):
                raise
            stop_reason = "duplicate-incumbent"
            break
        iterations.append(iteration)
        pool = iteration.solution_pool
        if _incumbent_satisfies_gap(
            iteration.incumbent,
            absolute_gap_tolerance,
        ):
            stop_reason = "optimality-gap"
            break
    return BilevelDecompositionRun(
        iterations=tuple(iterations),
        solution_pool=pool,
        stop_reason=stop_reason,
    )


def style_master_binary_variables(
    model: pyo.Block,
    *,
    component_names: Iterable[str] = STYLE_MASTER_BINARY_COMPONENT_NAMES,
) -> dict[str, Any]:
    """Return canonical STYLE master binary variable names and Pyomo variables."""

    variables: dict[str, Any] = {}
    for component_name in component_names:
        component = model.component(component_name)
        if component is None or component.ctype is not pyo.Var:
            continue
        variables.update(
            _style_binary_variables_from_component(component_name, component)
        )
    return variables


def style_master_integer_assignment_from_model(
    model: pyo.Block,
    *,
    threshold: float = 0.5,
    component_names: Iterable[str] = STYLE_MASTER_BINARY_COMPONENT_NAMES,
) -> BilevelIntegerAssignment:
    """Read current STYLE master binary values into a bilevel assignment."""

    if not 0.0 <= threshold <= 1.0:
        raise ValueError("binary assignment threshold must be between 0 and 1")
    variables = style_master_binary_variables(
        model,
        component_names=component_names,
    )
    if not variables:
        raise ValueError("STYLE model contains no master binary variables")
    values: dict[str, int] = {}
    for name, variable in variables.items():
        value = pyo.value(variable, exception=False)
        if value is None:
            raise ValueError(f"master binary variable {name!r} has no value")
        values[name] = int(value >= threshold)
    return BilevelIntegerAssignment.from_mapping(values)


def fix_style_master_integer_assignment(
    model: pyo.Block,
    assignment: BilevelIntegerAssignment,
    *,
    component_names: Iterable[str] = STYLE_MASTER_BINARY_COMPONENT_NAMES,
) -> tuple[str, ...]:
    """Fix STYLE master binary variables to a complete bilevel assignment."""

    variables = style_master_binary_variables(
        model,
        component_names=component_names,
    )
    values = assignment.as_dict()
    missing_values = tuple(name for name in variables if name not in values)
    if missing_values:
        raise KeyError(
            f"missing STYLE master binary values in assignment: {missing_values!r}",
        )
    unknown_values = tuple(name for name in values if name not in variables)
    if unknown_values:
        raise KeyError(
            f"unknown STYLE master binary values in assignment: {unknown_values!r}",
        )
    for name, variable in variables.items():
        variable.fix(values[name])
    return tuple(variables)


def style_fixed_assignment_subproblem_result(
    scenario: StaticStyleScenario,
    assignment: BilevelIntegerAssignment,
    *,
    solve: StaticStyleSolve,
) -> BilevelSubproblemResult:
    """Solve a static STYLE model with master binaries fixed by assignment."""

    model = build_static_style_model(scenario.data)
    fix_style_master_integer_assignment(model, assignment)
    solver_status = _normalize_static_style_solver_status(solve(model))
    _raise_if_failed_static_style_subproblem(solver_status)
    result = extract_static_style_result(
        model,
        case_study=scenario.case_study,
        scenario=scenario.scenario,
    )
    return BilevelSubproblemResult(
        objective_value=result.total_annualized_cost,
        status=_static_style_subproblem_status_label(solver_status),
        source_method="static-style-fixed-assignment",
    )


def run_static_style_fixed_assignment_decomposition(
    scenario: StaticStyleScenario,
    *,
    solve_master: StaticStyleSolve,
    solve_subproblem: StaticStyleSolve,
    max_iterations: int,
    absolute_gap_tolerance: float | None = None,
) -> BilevelDecompositionRun:
    """Run the generic bilevel loop with STYLE master and fixed subproblem."""

    return run_bilevel_decomposition(
        lambda: build_static_style_model(scenario.data),
        solve_master=solve_master,
        solve_subproblem=lambda assignment: style_fixed_assignment_subproblem_result(
            scenario,
            assignment,
            solve=solve_subproblem,
        ),
        max_iterations=max_iterations,
        absolute_gap_tolerance=absolute_gap_tolerance,
        binary_variables=style_master_binary_variables,
        assignment_from_model=style_master_integer_assignment_from_model,
    )


def build_static_style_binary_selection_master(
    data: StyleModelData,
) -> pyo.ConcreteModel:
    """Build a binary-only STYLE master from canonical selection variables."""

    full_model = build_static_style_model(data)
    variable_names = tuple(style_master_binary_variables(full_model))
    if not variable_names:
        raise ValueError("STYLE data produced no master binary variables")
    model = pyo.ConcreteModel(name="static STYLE binary selection master")
    model.master_choice = pyo.Var(variable_names, domain=pyo.Binary)
    model.selection_count_objective = pyo.Objective(
        expr=sum(model.master_choice[name] for name in variable_names),
    )
    return model


def style_binary_selection_master_assignment_from_model(
    model: pyo.Block,
    *,
    threshold: float = 0.5,
) -> BilevelIntegerAssignment:
    """Read a binary-selection master solution into an assignment."""

    if not 0.0 <= threshold <= 1.0:
        raise ValueError("binary assignment threshold must be between 0 and 1")
    if model.component("master_choice") is None:
        raise ValueError("binary-selection master contains no master_choice variable")
    values: dict[str, int] = {}
    for name in model.master_choice:
        value = pyo.value(model.master_choice[name], exception=False)
        if value is None:
            raise ValueError(f"master binary variable {name!r} has no value")
        values[name] = int(value >= threshold)
    return BilevelIntegerAssignment.from_mapping(values)


def style_binary_selection_candidate_solver(
    candidates: Iterable[BilevelIntegerAssignment],
) -> Callable[[pyo.Block], str]:
    """Return a master callback that applies the first cut-feasible candidate."""

    candidate_tuple = tuple(candidates)
    if not candidate_tuple:
        raise ValueError("at least one binary-selection candidate is required")

    def solve_master(model: pyo.Block) -> str:
        for index, assignment in enumerate(candidate_tuple, start=1):
            _fix_binary_selection_master_choice(model, assignment)
            if _binary_selection_master_cuts_are_satisfied(model):
                return f"candidate-{index}"
        raise RuntimeError(
            "No binary-selection candidate satisfies the current master cuts",
        )

    return solve_master


def style_binary_selection_candidate_from_scenario(
    scenario: StaticStyleScenario,
    *,
    solve: StaticStyleSolve,
) -> BilevelIntegerAssignment:
    """Solve a static STYLE scenario and extract its binary master assignment."""

    run = run_static_style_scenario(scenario, solve=solve)
    return style_master_integer_assignment_from_model(run.model)


def style_binary_selection_candidates_from_scenarios(
    scenarios: Iterable[StaticStyleScenario],
    *,
    solve: StaticStyleSolve,
) -> tuple[BilevelIntegerAssignment, ...]:
    """Return unique solved binary-selection candidates in scenario order."""

    return tuple(
        record.assignment
        for record in style_binary_selection_candidate_records_from_scenarios(
            scenarios,
            solve=solve,
        )
    )


def style_binary_selection_candidate_records_from_scenarios(
    scenarios: Iterable[StaticStyleScenario],
    *,
    solve: StaticStyleSolve,
    source_label_factory: Callable[[StaticStyleScenario], str] | None = None,
) -> tuple[BilevelCandidateAssignment, ...]:
    """Return unique solved binary-selection candidates with source labels."""

    records: list[BilevelCandidateAssignment] = []
    seen: set[BilevelIntegerAssignment] = set()
    for scenario in scenarios:
        candidate = style_binary_selection_candidate_from_scenario(
            scenario,
            solve=solve,
        )
        if candidate in seen:
            continue
        records.append(
            BilevelCandidateAssignment(
                assignment=candidate,
                source_label=(
                    _style_scenario_source_label(scenario)
                    if source_label_factory is None
                    else source_label_factory(scenario)
                ),
            ),
        )
        seen.add(candidate)
    return tuple(records)


def compatible_bilevel_integer_assignments(
    assignments: Iterable[BilevelIntegerAssignment],
    *,
    variable_names: Iterable[str],
) -> tuple[BilevelIntegerAssignment, ...]:
    """Return assignments whose variable set exactly matches target names."""

    target_variables = set(variable_names)
    if not target_variables:
        raise ValueError("at least one target variable name is required")
    return tuple(
        assignment
        for assignment in assignments
        if set(assignment.as_dict()) == target_variables
    )


def compatible_bilevel_candidate_assignments(
    assignments: Iterable[BilevelCandidateAssignment],
    *,
    variable_names: Iterable[str],
) -> tuple[BilevelCandidateAssignment, ...]:
    """Return candidate records whose assignment variables match target names."""

    target_variables = set(variable_names)
    if not target_variables:
        raise ValueError("at least one target variable name is required")
    return tuple(
        candidate
        for candidate in assignments
        if set(candidate.assignment.as_dict()) == target_variables
    )


def run_static_style_binary_selection_decomposition(
    scenario: StaticStyleScenario,
    *,
    solve_master: Callable[[pyo.Block], Any],
    solve_subproblem: StaticStyleSolve,
    max_iterations: int,
    absolute_gap_tolerance: float | None = None,
) -> BilevelDecompositionRun:
    """Run a separated binary STYLE master with fixed STYLE subproblems."""

    return run_bilevel_decomposition(
        lambda: build_static_style_binary_selection_master(scenario.data),
        solve_master=solve_master,
        solve_subproblem=lambda assignment: style_fixed_assignment_subproblem_result(
            scenario,
            assignment,
            solve=solve_subproblem,
        ),
        max_iterations=max_iterations,
        absolute_gap_tolerance=absolute_gap_tolerance,
        binary_variables=lambda model: model.master_choice,
        assignment_from_model=style_binary_selection_master_assignment_from_model,
    )


def run_static_style_binary_selection_candidate_decomposition(
    scenario: StaticStyleScenario,
    *,
    candidates: Iterable[BilevelIntegerAssignment | BilevelCandidateAssignment],
    solve_subproblem: StaticStyleSolve,
    max_iterations: int,
    absolute_gap_tolerance: float | None = None,
) -> BilevelDecompositionRun:
    """Run binary-selection decomposition while cutting failed candidates."""

    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")
    if absolute_gap_tolerance is not None and absolute_gap_tolerance < 0.0:
        raise ValueError("absolute_gap_tolerance must be non-negative")

    candidate_records = _normalize_bilevel_candidate_assignments(candidates)
    solve_master = style_binary_selection_candidate_solver(
        record.assignment for record in candidate_records
    )
    candidate_sources = {
        record.assignment: record.source_label
        for record in candidate_records
        if record.source_label is not None
    }
    failed_cuts: list[BilevelIntegerCut] = []
    skipped_candidates: list[BilevelSkippedCandidate] = []
    solution_pool = BilevelSolutionPool()
    iterations: list[BilevelDecompositionIteration] = []
    stop_reason = "max-iterations"
    while len(iterations) < max_iterations:
        try:
            master_model = _build_static_style_binary_selection_master_with_cuts(
                scenario.data,
                solution_pool=solution_pool,
                failed_cuts=failed_cuts,
            )
            master_status = solve_master(master_model)
        except RuntimeError as exc:
            if "No binary-selection candidate satisfies" not in str(exc):
                raise
            stop_reason = "candidate-exhausted"
            break
        assignment = style_binary_selection_master_assignment_from_model(master_model)
        try:
            subproblem = style_fixed_assignment_subproblem_result(
                scenario,
                assignment,
                solve=solve_subproblem,
            )
        except RuntimeError as exc:
            failed_cuts.append(assignment.exclusion_cut())
            skipped_candidates.append(
                BilevelSkippedCandidate(
                    candidate_label=str(master_status),
                    assignment=assignment,
                    reason=str(exc),
                    source_label=candidate_sources.get(assignment),
                ),
            )
            continue
        iteration_index = len(iterations) + 1
        incumbent = BilevelIncumbent(
            label=f"iteration-{iteration_index}",
            objective_value=subproblem.objective_value,
            assignment=assignment,
            best_bound=subproblem.best_bound,
            elapsed_seconds=subproblem.elapsed_seconds,
            hit_time_limit=subproblem.hit_time_limit,
            source_method=subproblem.source_method,
        )
        solution_pool = solution_pool.with_incumbent(incumbent)
        next_master_model = _build_static_style_binary_selection_master_with_cuts(
            scenario.data,
            solution_pool=solution_pool,
            failed_cuts=failed_cuts,
        )
        iterations.append(
            BilevelDecompositionIteration(
                iteration_index=iteration_index,
                master_model=master_model,
                master_status=master_status,
                assignment=assignment,
                subproblem=subproblem,
                incumbent=incumbent,
                solution_pool=solution_pool,
                next_master_model=next_master_model,
                candidate_source_label=candidate_sources.get(assignment),
            ),
        )
        if _incumbent_satisfies_gap(incumbent, absolute_gap_tolerance):
            stop_reason = "optimality-gap"
            break
    return BilevelDecompositionRun(
        iterations=tuple(iterations),
        solution_pool=solution_pool,
        stop_reason=stop_reason,
        skipped_candidates=tuple(skipped_candidates),
    )


def _build_static_style_binary_selection_master_with_cuts(
    data: StyleModelData,
    *,
    solution_pool: BilevelSolutionPool,
    failed_cuts: Iterable[BilevelIntegerCut],
) -> pyo.ConcreteModel:
    model = build_static_style_binary_selection_master(data)
    cuts = solution_pool.exclusion_cuts() + tuple(failed_cuts)
    if cuts:
        add_bilevel_no_good_cuts(model, cuts, model.master_choice)
    return model


def _normalize_bilevel_candidate_assignments(
    candidates: Iterable[BilevelIntegerAssignment | BilevelCandidateAssignment],
) -> tuple[BilevelCandidateAssignment, ...]:
    records: list[BilevelCandidateAssignment] = []
    for candidate in candidates:
        if isinstance(candidate, BilevelCandidateAssignment):
            records.append(candidate)
        else:
            records.append(BilevelCandidateAssignment(assignment=candidate))
    if not records:
        raise ValueError("at least one binary-selection candidate is required")
    return tuple(records)


def _fix_binary_selection_master_choice(
    model: pyo.Block,
    assignment: BilevelIntegerAssignment,
) -> None:
    if model.component("master_choice") is None:
        raise ValueError("binary-selection master contains no master_choice variable")
    values = assignment.as_dict()
    missing_values = tuple(name for name in model.master_choice if name not in values)
    if missing_values:
        raise KeyError(
            f"missing binary-selection master values: {missing_values!r}",
        )
    unknown_values = tuple(name for name in values if name not in model.master_choice)
    if unknown_values:
        raise KeyError(
            f"unknown binary-selection master values: {unknown_values!r}",
        )
    for name in model.master_choice:
        model.master_choice[name].value = values[name]


def _binary_selection_master_cuts_are_satisfied(
    model: pyo.Block,
    *,
    tolerance: float = 1e-9,
) -> bool:
    cuts = model.component("bilevel_no_good_cuts")
    if cuts is None:
        return True
    for index in cuts:
        body_value = pyo.value(cuts[index].body)
        lower_value = pyo.value(cuts[index].lower)
        if body_value < lower_value - tolerance:
            return False
    return True


def _style_scenario_source_label(scenario: StaticStyleScenario) -> str:
    return f"{scenario.case_study}:{scenario.scenario}"


def _validate_binary_assignment(values: tuple[tuple[str, int], ...]) -> None:
    if not values:
        raise ValueError("bilevel integer assignment must contain at least one value")
    names = tuple(variable for variable, _ in values)
    if len(set(names)) != len(names):
        raise ValueError("bilevel integer assignment contains duplicate variables")
    for variable, value in values:
        if not variable:
            raise ValueError("bilevel integer assignment variable names are required")
        if value not in (0, 1):
            raise ValueError("bilevel integer assignment values must be binary")


def _validate_unique_incumbent_assignments(
    incumbents: tuple[BilevelIncumbent, ...],
) -> None:
    assignments = set()
    for incumbent in incumbents:
        if incumbent.assignment in assignments:
            raise ValueError(
                f"duplicate bilevel incumbent assignment for {incumbent.label!r}",
            )
        assignments.add(incumbent.assignment)


def _missing_pyomo_binary_variables(
    cuts: tuple[BilevelIntegerCut, ...],
    binary_variables: Any,
) -> tuple[str, ...]:
    missing = []
    for cut in cuts:
        for variable in cut.variable_names:
            try:
                _lookup_pyomo_binary_variable(binary_variables, variable)
            except KeyError:
                missing.append(variable)
    return tuple(dict.fromkeys(missing))


def _lookup_pyomo_binary_variable(binary_variables: Any, variable: str) -> Any:
    try:
        return binary_variables[variable]
    except KeyError, IndexError, TypeError:
        pass
    try:
        return binary_variables[(variable,)]
    except KeyError, IndexError, TypeError:
        raise KeyError(variable) from None


def _resolve_binary_variables(model: pyo.Block, binary_variables: Any) -> Any:
    if binary_variables is None:
        return style_master_binary_variables(model)
    if callable(binary_variables):
        return binary_variables(model)
    return binary_variables


def _incumbent_satisfies_gap(
    incumbent: BilevelIncumbent,
    absolute_gap_tolerance: float | None,
) -> bool:
    if absolute_gap_tolerance is None or incumbent.optimality_gap is None:
        return False
    return incumbent.optimality_gap <= absolute_gap_tolerance


def _normalize_static_style_solver_status(
    status: StaticStyleSolverStatus | None,
) -> StaticStyleSolverStatus:
    if status is None:
        return StaticStyleSolverStatus()
    if not isinstance(status, StaticStyleSolverStatus):
        raise TypeError("solve must return StaticStyleSolverStatus or None")
    return status


def _raise_if_failed_static_style_subproblem(
    status: StaticStyleSolverStatus,
) -> None:
    termination = (
        None
        if status.termination_condition is None
        else status.termination_condition.strip().lower()
    )
    if termination not in {"error", "infeasible", "limit", "unbounded"}:
        return
    raise RuntimeError(
        "Static STYLE fixed-assignment subproblem did not produce an "
        f"extractable solution: {status}",
    )


def _static_style_subproblem_status_label(
    status: StaticStyleSolverStatus,
) -> str:
    if status.termination_condition is not None:
        return status.termination_condition
    return status.status


def _style_binary_variables_from_component(
    component_name: str,
    component: Any,
) -> dict[str, Any]:
    if component.is_indexed():
        return {
            _style_master_variable_name(component_name, index): component[index]
            for index in component
            if component[index].is_binary()
        }
    if component.is_binary():
        return {component_name: component}
    return {}


def _style_master_variable_name(component_name: str, index: Any) -> str:
    if isinstance(index, tuple):
        index_text = ",".join(str(part) for part in index)
    else:
        index_text = str(index)
    return f"{component_name}[{index_text}]"
