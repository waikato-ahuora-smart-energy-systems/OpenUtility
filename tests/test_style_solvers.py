from __future__ import annotations

from types import SimpleNamespace

import pyomo.environ as pyo
import pytest

from OpenUtility.style import (
    StaticStyleScenario,
    SteamLevelCandidate,
    StyleModelData,
    pyomo_static_style_solver,
    run_static_style_scenario,
    solve_static_style_model_with_pyomo,
)


def test_solve_static_style_model_with_pyomo_reports_solver_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_solvers = []

    def solver_factory(name: str):
        solver = _FakeAvailableSolver(name)
        created_solvers.append(solver)
        return solver

    monkeypatch.setattr(
        "OpenUtility.style.solvers.pyo.SolverFactory",
        solver_factory,
    )
    model = pyo.ConcreteModel()

    status = solve_static_style_model_with_pyomo(
        model,
        "fake-milp",
        tee=True,
        options={"mipgap": 0.01},
    )

    solver = created_solvers[0]
    assert solver.name == "fake-milp"
    assert solver.options == {"mipgap": 0.01}
    assert solver.solved_model is model
    assert solver.tee is True
    assert solver.load_solutions is False
    assert status.status == "ok"
    assert status.termination_condition == "optimal"
    assert status.message == "fixed test solve"


def test_pyomo_static_style_solver_returns_runner_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_solvers = []

    def solver_factory(name: str):
        solver = _FakeAvailableSolver(name)
        created_solvers.append(solver)
        return solver

    monkeypatch.setattr(
        "OpenUtility.style.solvers.pyo.SolverFactory",
        solver_factory,
    )
    model = pyo.ConcreteModel()
    solve = pyomo_static_style_solver("fake-milp", options={"threads": 2})

    status = solve(model)

    assert created_solvers[0].options == {"threads": 2}
    assert status.status == "ok"


def test_solve_static_style_model_with_pyomo_requires_available_solver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def solver_factory(name: str):
        return _FakeUnavailableSolver(name)

    monkeypatch.setattr(
        "OpenUtility.style.solvers.pyo.SolverFactory",
        solver_factory,
    )

    with pytest.raises(RuntimeError, match="Pyomo solver 'missing' is not available"):
        solve_static_style_model_with_pyomo(pyo.ConcreteModel(), "missing")


def test_solve_static_style_model_with_pyomo_sets_pyomo_values() -> None:
    model = pyo.ConcreteModel()
    model.use_unit = pyo.Var(domain=pyo.Binary)
    model.load_flow = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0.0, 10.0))
    model.minimum_supply = pyo.Constraint(
        expr=model.use_unit + model.load_flow >= 1.5,
    )
    model.objective = pyo.Objective(expr=0.1 * model.use_unit + model.load_flow)

    status = solve_static_style_model_with_pyomo(model, "appsi_highs")

    assert status.status == "ok"
    assert status.termination_condition == "optimal"
    assert pyo.value(model.use_unit) == pytest.approx(1.0)
    assert pyo.value(model.load_flow) == pytest.approx(0.5)


def test_pyomo_static_style_solver_solves_scalar_model() -> None:
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals)
    model.minimum = pyo.Constraint(expr=model.x >= 2.0)
    model.objective = pyo.Objective(expr=model.x)
    solve = pyomo_static_style_solver("appsi_highs", options={"time_limit": 10.0})

    status = solve(model)

    assert status.status == "ok"
    assert pyo.value(model.x) == pytest.approx(2.0)


def test_pyomo_highs_solver_solves_static_style_runner_smoke() -> None:
    scenario = StaticStyleScenario(
        case_study="solver-smoke",
        scenario="balanced-one-level",
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

    run = run_static_style_scenario(
        scenario,
        solve=pyomo_static_style_solver("appsi_highs"),
    )

    assert run.solver.status == "ok"
    assert run.solver.termination_condition == "optimal"
    assert pyo.value(run.model.level_selected["MP_100"]) == pytest.approx(1.0)
    assert pyo.value(run.model.source_heat_to_steam["MP_100"]) == pytest.approx(5.0)
    assert pyo.value(run.model.process_steam_to_sink["MP_100"]) == pytest.approx(5.0)
    assert run.result.total_annualized_cost == pytest.approx(0.0)


def test_pyomo_highs_solver_allows_selected_header_heat_to_cascade_to_lower_sink() -> None:
    scenario = StaticStyleScenario(
        case_study="solver-smoke",
        scenario="selected-header-cascades-sink-heat",
        data=StyleModelData(
            steam_mains=("MP",),
            steam_levels=(
                SteamLevelCandidate(
                    name="MP_200",
                    steam_main="MP",
                    temperature=200.0,
                    source_heat_available=5.0,
                    sink_heat_demand=0.0,
                    generation_enthalpy_delta=1.0,
                    use_enthalpy_delta=1.0,
                    source_heat_upper_bound=5.0,
                    sink_heat_upper_bound=5.0,
                    annualized_level_cost=0.0,
                ),
                SteamLevelCandidate(
                    name="MP_100",
                    steam_main="MP",
                    temperature=100.0,
                    source_heat_available=0.0,
                    sink_heat_demand=5.0,
                    generation_enthalpy_delta=1.0,
                    use_enthalpy_delta=1.0,
                    source_heat_upper_bound=5.0,
                    sink_heat_upper_bound=5.0,
                    annualized_level_cost=1.0,
                ),
            ),
            power_demand=0.0,
            grid_import_limit=0.0,
            grid_export_limit=0.0,
        ),
    )

    run = run_static_style_scenario(
        scenario,
        solve=pyomo_static_style_solver("appsi_highs"),
    )

    assert run.solver.status == "ok"
    assert pyo.value(run.model.level_selected["MP_200"]) == pytest.approx(1.0)
    assert pyo.value(run.model.level_selected["MP_100"]) == pytest.approx(0.0)
    assert pyo.value(run.model.sink_heat_from_steam["MP_200"]) == pytest.approx(5.0)
    assert pyo.value(run.model.sink_residual_heat["MP_200"]) == pytest.approx(5.0)
    assert pyo.value(run.model.sink_residual_heat["MP_100"]) == pytest.approx(0.0)


class _FakeAvailableSolver:
    def __init__(self, name: str) -> None:
        self.name = name
        self.options = {}
        self.solved_model = None
        self.tee = None
        self.load_solutions = None

    def available(self, exception_flag: bool = False) -> bool:
        assert exception_flag is False
        return True

    def solve(self, model, tee: bool = False, load_solutions: bool = True):
        self.solved_model = model
        self.tee = tee
        self.load_solutions = load_solutions
        return SimpleNamespace(
            solver=SimpleNamespace(
                status="ok",
                termination_condition="optimal",
                message="fixed test solve",
            ),
            solution=(),
        )


class _FakeUnavailableSolver:
    def __init__(self, name: str) -> None:
        self.name = name
        self.options = {}

    def available(self, exception_flag: bool = False) -> bool:
        assert exception_flag is False
        return False

    def solve(self, model, tee: bool = False):
        raise AssertionError("unavailable solver must not be called")
