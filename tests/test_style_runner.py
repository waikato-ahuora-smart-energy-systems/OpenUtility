from __future__ import annotations

import pytest

from case_study.jimenez_romero_utility_system_optimization.benchmarks import get_style_result
from OpenUtility.style import (
    EquipmentCost,
    FuelCost,
    GasTurbineCandidate,
    StaticStyleScenario,
    StaticStyleSolverStatus,
    SteamLevelCandidate,
    StyleModelData,
    VhpBackPressureTurbineCandidate,
    VhpSteamCandidate,
    run_static_style_scenario,
)


def test_run_static_style_scenario_builds_solves_extracts_and_compares() -> None:
    scenario = StaticStyleScenario(
        case_study="case-study-2",
        scenario="proposed-without-hot-oil",
        data=_result_extraction_data(),
        benchmark=get_style_result("case-study-2", "proposed-without-hot-oil"),
    )
    solved_models = []

    def solve(model):
        solved_models.append(model)
        _fix_result_solution(model)
        return StaticStyleSolverStatus(
            status="ok",
            termination_condition="optimal",
            message="fixed test solution",
        )

    run = run_static_style_scenario(scenario, solve=solve)

    assert solved_models == [run.model]
    assert run.scenario == scenario
    assert run.solver.status == "ok"
    assert run.solver.termination_condition == "optimal"
    assert run.solver.message == "fixed test solution"
    assert run.result.total_annualized_cost == pytest.approx(64.77)
    assert run.comparison is not None
    assert run.comparison.within_tolerance is True


def test_run_static_style_scenario_allows_no_benchmark() -> None:
    scenario = StaticStyleScenario(
        case_study="case-study-2",
        scenario="scratch",
        data=_result_extraction_data(),
    )

    def solve(model):
        _fix_result_solution(model)
        return None

    run = run_static_style_scenario(scenario, solve=solve)

    assert run.result.scenario == "scratch"
    assert run.solver.status == "unknown"
    assert run.comparison is None


def test_run_static_style_scenario_stops_before_extracting_failed_solve() -> None:
    scenario = StaticStyleScenario(
        case_study="case-study-2",
        scenario="scratch",
        data=_result_extraction_data(),
    )

    def solve(model):
        return StaticStyleSolverStatus(
            status="warning",
            termination_condition="infeasible",
            message="test infeasible model",
        )

    with pytest.raises(RuntimeError, match="Static STYLE solve did not produce"):
        run_static_style_scenario(scenario, solve=solve)


def _result_extraction_data() -> StyleModelData:
    return StyleModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_3",
                steam_main="MP",
                temperature=134.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=1.0,
                use_enthalpy_delta=1.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_90",
                steam_enthalpy=1.0,
                feedwater_enthalpy=0.0,
                steam_flow_upper_bound=300.0,
            ),
        ),
        vhp_turbines=(
            VhpBackPressureTurbineCandidate(
                name="st",
                vhp_header="VHP_90",
                steam_level="MP_3",
                power_slope=1.0,
                power_intercept=0.0,
                min_capacity=0.0,
                max_capacity=300.0,
                minimum_load_fraction=0.0,
            ),
        ),
        gas_turbines=(
            GasTurbineCandidate(
                name="gt",
                fuel_lhv=1.0,
                power_slope=1.0,
                power_intercept=0.0,
                min_fuel_flow=0.0,
                max_fuel_flow=300.0,
                minimum_load_fraction=0.0,
            ),
        ),
        equipment_costs=(
            EquipmentCost(
                name="st-capital",
                equipment_type="vhp_turbine",
                equipment_name="st",
                annualization_factor=1.0,
                installation_factor=1.0,
                variable_capital_cost=0.0,
                fixed_capital_cost=11.98,
                variable_maintenance_cost=0.0,
                fixed_maintenance_cost=1.75,
            ),
        ),
        fuel_costs=(
            FuelCost(
                name="gt-fuel",
                equipment_type="gas_turbine",
                equipment_name="gt",
                unit_cost=51.04 / 249.03,
            ),
        ),
        power_demand=0.0,
    )


def _fix_result_solution(model) -> None:
    model.level_selected["MP_3"].fix(1.0)
    model.vhp_selected["VHP_90"].fix(1.0)
    model.source_heat_to_steam["MP_3"].fix(0.0)
    model.utility_steam_from_vhp["VHP_90", "MP_3"].fix(239.86)
    model.utility_steam_to_header["MP_3"].fix(239.86)
    model.source_steam_generated["MP_3"].fix(0.0)
    model.feedwater_to_header["MP_3"].fix(0.0)
    model.process_steam_to_sink["MP_3"].fix(239.86)
    model.header_steam_export["MP_3"].fix(0.0)
    model.deaerator_steam_from_header["MP_3"].fix(0.0)
    model.vhp_turbine_selected["st"].fix(1.0)
    model.vhp_turbine_steam_flow["st"].fix(239.86)
    model.vhp_turbine_power_generation["st"].fix(20.88)
    model.gas_turbine_selected["gt"].fix(1.0)
    model.gas_turbine_fuel_flow["gt"].fix(249.03)
    model.gas_turbine_power_generation["gt"].fix(25.79)
    model.onsite_power_generation.fix(46.67)
    model.grid_power_import.fix(0.0)
    model.grid_power_export.fix(0.0)
    model.hot_oil_fuel_consumption.fix(0.0)
