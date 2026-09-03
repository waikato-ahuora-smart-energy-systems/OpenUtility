from __future__ import annotations

import json

import pytest
import pyomo.environ as pyo

from OpenUtility.utility_system import (
    BilevelDecompositionIteration,
    BilevelDecompositionRun,
    BilevelIncumbent,
    BilevelCandidateAssignment,
    BilevelIntegerAssignment,
    BilevelSolutionPool,
    BilevelSkippedCandidate,
    BilevelSubproblemResult,
    UtilitySystemScenario,
    UtilitySystemResult,
    SteamLevelCandidate,
    UtilitySystemModelData,
    best_configuration_comparison_rows,
    best_configuration_summary_row,
    bilevel_candidate_audit_bundle_rows,
    bilevel_decomposition_run_rows,
    bilevel_candidate_pool_rows,
    bilevel_candidate_pool_comparison_rows,
    bilevel_candidate_selection_delta_rows,
    bilevel_candidate_selection_delta_summary_rows,
    bilevel_candidate_source_filter_detail_rows,
    bilevel_candidate_source_filter_summary_rows,
    bilevel_candidate_source_filter_variable_rows,
    bilevel_skipped_candidate_rows,
    bilevel_skipped_candidate_delta_summary_rows,
    compare_utility_system_result_to_best_configuration,
    format_comparison_rows,
    format_bilevel_candidate_audit_bundle_rows,
    format_bilevel_decomposition_run_rows,
    format_bilevel_candidate_pool_rows,
    format_bilevel_candidate_pool_comparison_rows,
    format_bilevel_candidate_selection_delta_rows,
    format_bilevel_candidate_selection_delta_summary_rows,
    format_bilevel_candidate_source_filter_detail_rows,
    format_bilevel_candidate_source_filter_summary_rows,
    format_bilevel_candidate_source_filter_variable_rows,
    format_bilevel_skipped_candidate_rows,
    format_bilevel_skipped_candidate_delta_summary_rows,
    format_utility_system_operating_cost_component_rows,
    format_utility_system_operating_cost_target_rows,
    format_utility_system_decomposition_objective_comparison_rows,
    format_utility_system_decomposition_skipped_candidate_rows,
    format_utility_system_decomposition_trajectory_rows,
    format_utility_system_fuel_calibration_target_rows,
    format_utility_system_fuel_consumption_diagnosis_rows,
    format_utility_system_fuel_consumption_capacity_rows,
    format_utility_system_fuel_consumption_equipment_rows,
    format_utility_system_fuel_consumption_family_rows,
    format_utility_system_fuel_consumption_residual_ranking_rows,
    format_utility_system_candidate_audit_bundle_rows,
    format_summary_rows,
    utility_system_operating_cost_adjustment_map_from_target_rows,
    utility_system_operating_cost_component_rows,
    utility_system_operating_cost_target_rows,
    utility_system_decomposition_objective_comparison_rows,
    utility_system_decomposition_skipped_candidate_rows,
    utility_system_decomposition_trajectory_rows,
    utility_system_fuel_calibration_target_rows,
    utility_system_fuel_consumption_factor_map_from_calibration_target_rows,
    utility_system_fuel_consumption_diagnosis_rows,
    utility_system_fuel_consumption_capacity_rows,
    utility_system_fuel_consumption_equipment_rows,
    utility_system_fuel_consumption_family_rows,
    utility_system_fuel_consumption_residual_ranking_rows,
    utility_system_candidate_audit_bundle_rows,
    utility_system_candidate_pool_rows,
    utility_system_candidate_pool_comparison_rows,
    utility_system_candidate_selection_delta_rows,
    utility_system_candidate_selection_delta_summary_rows,
    utility_system_candidate_source_filter_detail_rows,
    utility_system_candidate_source_filter_summary_rows,
    utility_system_candidate_source_filter_variable_rows,
    format_utility_system_candidate_pool_rows,
    format_utility_system_candidate_pool_comparison_rows,
    format_utility_system_candidate_selection_delta_rows,
    format_utility_system_candidate_selection_delta_summary_rows,
    format_utility_system_candidate_source_filter_detail_rows,
    format_utility_system_candidate_source_filter_summary_rows,
    format_utility_system_candidate_source_filter_variable_rows,
    utility_system_skipped_candidate_delta_summary_rows,
    format_utility_system_skipped_candidate_delta_summary_rows,
)
from minimal_utility_system import minimal_best_configuration_benchmark


def test_best_configuration_comparison_rows_flattens_deviations() -> None:
    benchmark = minimal_best_configuration_benchmark()
    result = UtilitySystemResult(
        case_study="example-site",
        scenario="microgrid",
        utility_steam_flow=217.78,
        fuel_consumption=245.04,
        power_generation=46.67,
        steam_turbine_power=20.88,
        gas_turbine_power=25.79,
        operating_cost=50.49,
        maintenance_cost=3.59,
        capital_cost=10.78,
        total_annualized_cost=64.86,
        fuel_cost=51.78,
    )
    comparison = compare_utility_system_result_to_best_configuration(
        result,
        benchmark,
    )

    rows = best_configuration_comparison_rows(
        catalog="reported-equipment",
        comparison=comparison,
    )

    assert rows[0]["catalog"] == "reported-equipment"
    assert rows[0]["case_study"] == "example-site"
    assert rows[0]["scenario"] == "microgrid"
    assert rows[0]["field"] == "utility_steam_flow"
    assert rows[0]["actual"] == pytest.approx(217.78)
    assert rows[0]["benchmark"] == pytest.approx(217.78)
    assert rows[0]["within_tolerance"] is True


def test_format_comparison_rows_supports_csv_and_json() -> None:
    rows = (
        {
            "catalog": "reported-equipment",
            "case_study": "example-site",
            "scenario": "microgrid",
            "field": "fuel_consumption",
            "actual": 245.04,
            "benchmark": 245.04,
            "absolute_deviation": 0.0,
            "within_tolerance": True,
        },
    )

    csv_output = format_comparison_rows(rows, output_format="csv")
    json_output = format_comparison_rows(rows, output_format="json")

    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,field,actual,benchmark,"
        "absolute_deviation,within_tolerance"
    )
    assert "fuel_consumption" in csv_output
    assert json.loads(json_output)[0]["field"] == "fuel_consumption"


def test_format_comparison_rows_rejects_unknown_format() -> None:
    with pytest.raises(ValueError, match="unsupported comparison output format"):
        format_comparison_rows((), output_format="yaml")


def test_best_configuration_summary_row_reports_failing_fields() -> None:
    benchmark = minimal_best_configuration_benchmark()
    result = UtilitySystemResult(
        case_study="example-site-physical-profile",
        scenario="microgrid",
        utility_steam_flow=217.78,
        fuel_consumption=248.5740702880787,
        power_generation=46.67,
        steam_turbine_power=20.88,
        gas_turbine_power=25.79,
        operating_cost=50.49,
        maintenance_cost=3.59,
        capital_cost=10.78,
        total_annualized_cost=64.86,
        fuel_cost=51.78,
    )
    comparison = compare_utility_system_result_to_best_configuration(
        result,
        benchmark,
        absolute_tolerance=1e-2,
    )

    row = best_configuration_summary_row(
        catalog="physical-profile",
        comparison=comparison,
    )
    csv_output = format_summary_rows((row,), output_format="csv")

    assert row["within_tolerance"] is False
    assert row["max_absolute_deviation"] == pytest.approx(3.534070288078709)
    assert row["failing_fields"] == "fuel_consumption"
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,within_tolerance,"
        "max_absolute_deviation,failing_fields"
    )


def test_format_summary_rows_supports_json_and_rejects_unknown_format() -> None:
    rows = (
        {
            "catalog": "physical-profile",
            "case_study": "example",
            "scenario": "scenario",
            "within_tolerance": True,
            "max_absolute_deviation": 0.0,
            "failing_fields": "",
        },
    )

    assert json.loads(format_summary_rows(rows, output_format="json"))[0][
        "within_tolerance"
    ]
    with pytest.raises(ValueError, match="unsupported summary output format"):
        format_summary_rows(rows, output_format="yaml")


def test_utility_system_fuel_consumption_family_rows_explain_total_residual() -> None:
    model = pyo.ConcreteModel()
    model.BOILERS = pyo.Set(initialize=("boiler",))
    model.boiler_fuel_consumption = pyo.Var(model.BOILERS, initialize=10.0)
    model.boiler_fuel_consumption["boiler"].fix(10.0)
    model.GAS_TURBINES = pyo.Set(initialize=("gt",))
    model.gas_turbine_fuel_flow = pyo.Var(model.GAS_TURBINES, initialize=20.0)
    model.gas_turbine_fuel_flow["gt"].fix(20.0)
    model.gas_turbine_fuel_lhv = pyo.Param(model.GAS_TURBINES, initialize={"gt": 2.0})
    model.HRSGS = pyo.Set(initialize=("hrsg",))
    model.hrsg_supplementary_fuel_flow = pyo.Var(model.HRSGS, initialize=3.0)
    model.hrsg_supplementary_fuel_flow["hrsg"].fix(3.0)
    model.hrsg_supplementary_fuel_lhv = pyo.Param(
        model.HRSGS,
        initialize={"hrsg": 5.0},
    )
    model.VHP_SOURCES = pyo.Set(initialize=("vhp",))
    model.vhp_source_fuel_consumption = pyo.Var(model.VHP_SOURCES, initialize=7.0)
    model.vhp_source_fuel_consumption["vhp"].fix(7.0)
    model.hot_oil_fuel_consumption = pyo.Var(initialize=9.0)
    model.hot_oil_fuel_consumption.fix(9.0)
    scenario = UtilitySystemScenario(
        case_study="case",
        scenario="microgrid",
        data=UtilitySystemModelData(
            steam_mains=("MP",),
            steam_levels=(
                SteamLevelCandidate(
                    name="MP_100",
                    steam_main="MP",
                    temperature=100.0,
                    source_heat_available=0.0,
                    sink_heat_demand=0.0,
                    generation_enthalpy_delta=1.0,
                    use_enthalpy_delta=1.0,
                ),
            ),
            power_demand=0.0,
        ),
    )
    benchmark = minimal_best_configuration_benchmark()

    rows = utility_system_fuel_consumption_family_rows(
        catalog="physical-profile",
        scenario=scenario,
        model=model,
        benchmark=benchmark,
    )
    csv_output = format_utility_system_fuel_consumption_family_rows(
        rows,
        output_format="csv",
    )

    assert rows == (
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "microgrid",
            "equipment_family": "boiler",
            "included_in_table_fuel_consumption": True,
            "fuel_consumption": 10.0,
            "benchmark_fuel_consumption": 245.04,
            "table_fuel_consumption": 72.0,
            "fuel_consumption_residual": pytest.approx(-173.04),
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "microgrid",
            "equipment_family": "gas_turbine",
            "included_in_table_fuel_consumption": True,
            "fuel_consumption": 40.0,
            "benchmark_fuel_consumption": 245.04,
            "table_fuel_consumption": 72.0,
            "fuel_consumption_residual": pytest.approx(-173.04),
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "microgrid",
            "equipment_family": "hrsg_supplementary",
            "included_in_table_fuel_consumption": True,
            "fuel_consumption": 15.0,
            "benchmark_fuel_consumption": 245.04,
            "table_fuel_consumption": 72.0,
            "fuel_consumption_residual": pytest.approx(-173.04),
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "microgrid",
            "equipment_family": "vhp_source",
            "included_in_table_fuel_consumption": True,
            "fuel_consumption": 7.0,
            "benchmark_fuel_consumption": 245.04,
            "table_fuel_consumption": 72.0,
            "fuel_consumption_residual": pytest.approx(-173.04),
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "microgrid",
            "equipment_family": "hot_oil",
            "included_in_table_fuel_consumption": False,
            "fuel_consumption": 9.0,
            "benchmark_fuel_consumption": 245.04,
            "table_fuel_consumption": 72.0,
            "fuel_consumption_residual": pytest.approx(-173.04),
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "microgrid",
            "equipment_family": "table_total",
            "included_in_table_fuel_consumption": True,
            "fuel_consumption": 72.0,
            "benchmark_fuel_consumption": 245.04,
            "table_fuel_consumption": 72.0,
            "fuel_consumption_residual": pytest.approx(-173.04),
        },
    )
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,equipment_family,"
        "included_in_table_fuel_consumption,fuel_consumption,"
        "benchmark_fuel_consumption,table_fuel_consumption,"
        "fuel_consumption_residual"
    )


def test_utility_system_fuel_consumption_equipment_rows_trace_family_totals() -> None:
    model = pyo.ConcreteModel()
    model.BOILERS = pyo.Set(initialize=("boiler",))
    model.boiler_fuel_consumption = pyo.Var(model.BOILERS, initialize=10.0)
    model.boiler_fuel_consumption["boiler"].fix(10.0)
    model.GAS_TURBINES = pyo.Set(initialize=("gt",))
    model.gas_turbine_fuel_flow = pyo.Var(model.GAS_TURBINES, initialize=20.0)
    model.gas_turbine_fuel_flow["gt"].fix(20.0)
    model.gas_turbine_fuel_lhv = pyo.Param(model.GAS_TURBINES, initialize={"gt": 2.0})
    model.HRSGS = pyo.Set(initialize=("hrsg",))
    model.hrsg_supplementary_fuel_flow = pyo.Var(model.HRSGS, initialize=3.0)
    model.hrsg_supplementary_fuel_flow["hrsg"].fix(3.0)
    model.hrsg_supplementary_fuel_lhv = pyo.Param(
        model.HRSGS,
        initialize={"hrsg": 5.0},
    )
    model.VHP_SOURCES = pyo.Set(initialize=("vhp",))
    model.vhp_source_fuel_consumption = pyo.Var(model.VHP_SOURCES, initialize=7.0)
    model.vhp_source_fuel_consumption["vhp"].fix(7.0)
    model.hot_oil_fuel_consumption = pyo.Var(initialize=9.0)
    model.hot_oil_fuel_consumption.fix(9.0)
    scenario = UtilitySystemScenario(
        case_study="case",
        scenario="microgrid",
        data=UtilitySystemModelData(
            steam_mains=("MP",),
            steam_levels=(
                SteamLevelCandidate(
                    name="MP_100",
                    steam_main="MP",
                    temperature=100.0,
                    source_heat_available=0.0,
                    sink_heat_demand=0.0,
                    generation_enthalpy_delta=1.0,
                    use_enthalpy_delta=1.0,
                ),
            ),
            power_demand=0.0,
        ),
    )
    benchmark = minimal_best_configuration_benchmark()

    rows = utility_system_fuel_consumption_equipment_rows(
        catalog="physical-profile",
        scenario=scenario,
        model=model,
        benchmark=benchmark,
    )
    csv_output = format_utility_system_fuel_consumption_equipment_rows(
        rows,
        output_format="csv",
    )

    assert rows[1] == {
        "catalog": "physical-profile",
        "case_study": "case",
        "scenario": "microgrid",
        "equipment_family": "gas_turbine",
        "equipment_name": "gt",
        "fuel_variable": "gas_turbine_fuel_flow[gt]",
        "fuel_multiplier": 2.0,
        "included_in_table_fuel_consumption": True,
        "fuel_consumption": 40.0,
        "family_fuel_consumption": 40.0,
        "share_of_family": 1.0,
        "benchmark_fuel_consumption": 245.04,
        "table_fuel_consumption": 72.0,
        "fuel_consumption_residual": pytest.approx(-173.04),
    }
    assert rows[-1]["equipment_family"] == "hot_oil"
    assert rows[-1]["included_in_table_fuel_consumption"] is False
    assert rows[-1]["family_fuel_consumption"] == pytest.approx(9.0)
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,equipment_family,equipment_name,"
        "fuel_variable,fuel_multiplier,included_in_table_fuel_consumption,"
        "fuel_consumption,family_fuel_consumption,share_of_family,"
        "benchmark_fuel_consumption,table_fuel_consumption,"
        "fuel_consumption_residual"
    )


def test_utility_system_fuel_consumption_capacity_rows_report_utilization_context() -> (
    None
):
    model = pyo.ConcreteModel()
    model.GAS_TURBINES = pyo.Set(initialize=("gt",))
    model.gas_turbine_fuel_flow = pyo.Var(model.GAS_TURBINES, initialize=20.0)
    model.gas_turbine_fuel_flow["gt"].fix(20.0)
    model.gas_turbine_fuel_lhv = pyo.Param(model.GAS_TURBINES, initialize={"gt": 2.0})
    model.gas_turbine_max_fuel_flow = pyo.Param(
        model.GAS_TURBINES,
        initialize={"gt": 25.0},
    )
    model.gas_turbine_selected = pyo.Var(model.GAS_TURBINES, initialize=1.0)
    model.gas_turbine_selected["gt"].fix(1.0)
    scenario = UtilitySystemScenario(
        case_study="case",
        scenario="microgrid",
        data=UtilitySystemModelData(
            steam_mains=("MP",),
            steam_levels=(
                SteamLevelCandidate(
                    name="MP_100",
                    steam_main="MP",
                    temperature=100.0,
                    source_heat_available=0.0,
                    sink_heat_demand=0.0,
                    generation_enthalpy_delta=1.0,
                    use_enthalpy_delta=1.0,
                ),
            ),
            power_demand=0.0,
        ),
    )
    benchmark = minimal_best_configuration_benchmark()

    rows = utility_system_fuel_consumption_capacity_rows(
        catalog="physical-profile",
        scenario=scenario,
        model=model,
        benchmark=benchmark,
    )
    csv_output = format_utility_system_fuel_consumption_capacity_rows(
        rows,
        output_format="csv",
    )

    assert rows == (
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "microgrid",
            "equipment_family": "gas_turbine",
            "equipment_name": "gt",
            "fuel_variable": "gas_turbine_fuel_flow[gt]",
            "fuel_consumption": 40.0,
            "selection_variable": "gas_turbine_selected[gt]",
            "selected": True,
            "capacity_basis": "fuel_consumption",
            "actual_capacity_basis_value": 40.0,
            "capacity_value": 50.0,
            "capacity_utilization": 0.8,
            "benchmark_fuel_consumption": 245.04,
            "table_fuel_consumption": 40.0,
            "fuel_consumption_residual": pytest.approx(-205.04),
        },
    )
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,equipment_family,equipment_name,"
        "fuel_variable,fuel_consumption,selection_variable,selected,"
        "capacity_basis,actual_capacity_basis_value,capacity_value,"
        "capacity_utilization,benchmark_fuel_consumption,"
        "table_fuel_consumption,fuel_consumption_residual"
    )


def test_utility_system_fuel_consumption_diagnosis_rows_classify_residual_drivers() -> (
    None
):
    capacity_rows = (
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "capacity-bound",
            "equipment_family": "gas_turbine",
            "equipment_name": "gt",
            "fuel_variable": "gas_turbine_fuel_flow[gt]",
            "fuel_consumption": 40.0,
            "selection_variable": "gas_turbine_selected[gt]",
            "selected": True,
            "capacity_basis": "fuel_consumption",
            "actual_capacity_basis_value": 40.0,
            "capacity_value": 40.0,
            "capacity_utilization": 1.0,
            "benchmark_fuel_consumption": 38.0,
            "table_fuel_consumption": 40.0,
            "fuel_consumption_residual": 2.0,
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "hot-oil-context",
            "equipment_family": "gas_turbine",
            "equipment_name": "gt",
            "fuel_variable": "gas_turbine_fuel_flow[gt]",
            "fuel_consumption": 10.0,
            "selection_variable": "gas_turbine_selected[gt]",
            "selected": True,
            "capacity_basis": "fuel_consumption",
            "actual_capacity_basis_value": 10.0,
            "capacity_value": 20.0,
            "capacity_utilization": 0.5,
            "benchmark_fuel_consumption": 8.0,
            "table_fuel_consumption": 10.0,
            "fuel_consumption_residual": 2.0,
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "hot-oil-context",
            "equipment_family": "hot_oil",
            "equipment_name": "hot_oil_furnace",
            "fuel_variable": "hot_oil_fuel_consumption",
            "fuel_consumption": 6.0,
            "selection_variable": "hot_oil_furnace_selected",
            "selected": True,
            "capacity_basis": "heat_load",
            "actual_capacity_basis_value": 30.0,
            "capacity_value": None,
            "capacity_utilization": None,
            "benchmark_fuel_consumption": 8.0,
            "table_fuel_consumption": 10.0,
            "fuel_consumption_residual": 2.0,
        },
    )

    rows = utility_system_fuel_consumption_diagnosis_rows(capacity_rows)
    csv_output = format_utility_system_fuel_consumption_diagnosis_rows(
        rows,
        output_format="csv",
    )

    assert rows[0]["scenario"] == "capacity-bound"
    assert rows[0]["residual_driver"] == "capped_fuel_capacity"
    assert rows[0]["largest_included_equipment_family"] == "gas_turbine"
    assert rows[0]["largest_included_capacity_utilization"] == pytest.approx(1.0)
    assert rows[1]["scenario"] == "hot-oil-context"
    assert rows[1]["residual_driver"] == "hot_oil_heat_load_context"
    assert rows[1]["hot_oil_heat_load"] == pytest.approx(30.0)
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,residual_rank,residual_driver,"
        "largest_included_equipment_family,largest_included_equipment_name,"
        "largest_included_fuel_consumption,"
        "largest_included_capacity_utilization,hot_oil_heat_load,"
        "auxiliary_vhp_fuel_consumption,benchmark_fuel_consumption,"
        "table_fuel_consumption,fuel_consumption_residual,"
        "absolute_fuel_consumption_residual"
    )


def test_utility_system_fuel_calibration_target_rows_compute_adjustment_to_benchmark() -> (
    None
):
    capacity_rows = (
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "capacity-bound",
            "equipment_family": "gas_turbine",
            "equipment_name": "gt",
            "fuel_variable": "gas_turbine_fuel_flow[gt]",
            "fuel_consumption": 40.0,
            "selection_variable": "gas_turbine_selected[gt]",
            "selected": True,
            "capacity_basis": "fuel_consumption",
            "actual_capacity_basis_value": 40.0,
            "capacity_value": 40.0,
            "capacity_utilization": 1.0,
            "benchmark_fuel_consumption": 38.0,
            "table_fuel_consumption": 40.0,
            "fuel_consumption_residual": 2.0,
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "capacity-bound",
            "equipment_family": "hrsg_supplementary",
            "equipment_name": "hrsg",
            "fuel_variable": "hrsg_supplementary_fuel_flow[hrsg]",
            "fuel_consumption": 12.0,
            "selection_variable": "hrsg_supplementary_firing_selected[hrsg]",
            "selected": True,
            "capacity_basis": "fuel_consumption",
            "actual_capacity_basis_value": 12.0,
            "capacity_value": 12.0,
            "capacity_utilization": 1.0,
            "benchmark_fuel_consumption": 38.0,
            "table_fuel_consumption": 40.0,
            "fuel_consumption_residual": 2.0,
        },
    )

    rows = utility_system_fuel_calibration_target_rows(capacity_rows)
    csv_output = format_utility_system_fuel_calibration_target_rows(
        rows,
        output_format="csv",
    )

    assert rows == (
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "capacity-bound",
            "residual_rank": 1,
            "calibration_action": "reduce_largest_capped_equipment_fuel",
            "target_equipment_family": "gas_turbine",
            "target_equipment_name": "gt",
            "capacity_basis": "fuel_consumption",
            "capacity_utilization": 1.0,
            "current_equipment_fuel_consumption": 40.0,
            "required_equipment_fuel_consumption": 38.0,
            "fuel_consumption_adjustment": -2.0,
            "fuel_consumption_adjustment_factor": 0.95,
            "benchmark_fuel_consumption": 38.0,
            "table_fuel_consumption": 40.0,
            "target_table_fuel_consumption": 38.0,
            "fuel_consumption_residual": 2.0,
        },
    )
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,residual_rank,calibration_action,"
        "target_equipment_family,target_equipment_name,capacity_basis,"
        "capacity_utilization,current_equipment_fuel_consumption,"
        "required_equipment_fuel_consumption,fuel_consumption_adjustment,"
        "fuel_consumption_adjustment_factor,benchmark_fuel_consumption,"
        "table_fuel_consumption,target_table_fuel_consumption,"
        "fuel_consumption_residual"
    )


def test_utility_system_fuel_calibration_target_rows_increase_capped_equipment_fuel() -> (
    None
):
    rows = utility_system_fuel_calibration_target_rows(
        (
            {
                "catalog": "physical-profile",
                "case_study": "case",
                "scenario": "under-fired",
                "equipment_family": "gas_turbine",
                "equipment_name": "gt",
                "fuel_variable": "gas_turbine_fuel_flow[gt]",
                "fuel_consumption": 36.0,
                "selection_variable": "gas_turbine_selected[gt]",
                "selected": True,
                "capacity_basis": "fuel_consumption",
                "actual_capacity_basis_value": 36.0,
                "capacity_value": 36.0,
                "capacity_utilization": 1.0,
                "benchmark_fuel_consumption": 38.0,
                "table_fuel_consumption": 36.0,
                "fuel_consumption_residual": -2.0,
            },
        ),
    )

    assert rows[0]["calibration_action"] == "increase_largest_capped_equipment_fuel"
    assert rows[0]["required_equipment_fuel_consumption"] == pytest.approx(38.0)
    assert rows[0]["fuel_consumption_adjustment"] == pytest.approx(2.0)
    assert rows[0]["fuel_consumption_adjustment_factor"] == pytest.approx(38.0 / 36.0)


def test_utility_system_fuel_consumption_factor_map_from_calibration_target_rows() -> (
    None
):
    target_rows = (
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "scenario-a",
            "residual_rank": 1,
            "calibration_action": "reduce_largest_capped_equipment_fuel",
            "target_equipment_family": "boiler",
            "target_equipment_name": "boiler-1",
            "capacity_basis": "steam_generation",
            "capacity_utilization": 1.0,
            "current_equipment_fuel_consumption": 40.0,
            "required_equipment_fuel_consumption": 38.0,
            "fuel_consumption_adjustment": -2.0,
            "fuel_consumption_adjustment_factor": 0.95,
            "benchmark_fuel_consumption": 38.0,
            "table_fuel_consumption": 40.0,
            "target_table_fuel_consumption": 38.0,
            "fuel_consumption_residual": 2.0,
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "scenario-b",
            "residual_rank": 2,
            "calibration_action": "no_capped_capacity_target",
            "target_equipment_family": "gas_turbine",
            "target_equipment_name": "gt-1",
            "capacity_basis": "fuel_consumption",
            "capacity_utilization": 0.5,
            "current_equipment_fuel_consumption": 20.0,
            "required_equipment_fuel_consumption": 20.0,
            "fuel_consumption_adjustment": 0.0,
            "fuel_consumption_adjustment_factor": None,
            "benchmark_fuel_consumption": 20.0,
            "table_fuel_consumption": 20.0,
            "target_table_fuel_consumption": 20.0,
            "fuel_consumption_residual": 0.0,
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "scenario-c",
            "residual_rank": 3,
            "calibration_action": "increase_largest_capped_equipment_fuel",
            "target_equipment_family": "gas_turbine",
            "target_equipment_name": "gt-1",
            "capacity_basis": "fuel_consumption",
            "capacity_utilization": 1.0,
            "current_equipment_fuel_consumption": 36.0,
            "required_equipment_fuel_consumption": 38.0,
            "fuel_consumption_adjustment": 2.0,
            "fuel_consumption_adjustment_factor": 38.0 / 36.0,
            "benchmark_fuel_consumption": 38.0,
            "table_fuel_consumption": 36.0,
            "target_table_fuel_consumption": 38.0,
            "fuel_consumption_residual": -2.0,
        },
    )

    factors = utility_system_fuel_consumption_factor_map_from_calibration_target_rows(
        target_rows,
    )

    assert set(factors) == {"scenario-a", "scenario-c"}
    assert factors["scenario-a"] == {("boiler", "boiler-1"): 0.95}
    assert factors["scenario-c"][("gas_turbine", "gt-1")] == pytest.approx(
        38.0 / 36.0,
    )


def test_utility_system_operating_cost_component_rows_compare_auxiliary_bucket() -> (
    None
):
    model = pyo.ConcreteModel()
    model.STEAM_LEVELS = pyo.Set(initialize=("MP",))
    model.operating_cost_per_heat = pyo.Param(model.STEAM_LEVELS, initialize=0.0)
    model.source_heat_to_steam = pyo.Var(model.STEAM_LEVELS, initialize=0.0)
    model.source_heat_to_steam["MP"].fix(0.0)
    model.total_fuel_operating_cost = pyo.Var(initialize=50.6)
    model.total_fuel_operating_cost.fix(50.6)
    model.hot_oil_operating_cost = pyo.Var(initialize=0.0)
    model.hot_oil_operating_cost.fix(0.0)
    model.electricity_operating_cost = pyo.Var(initialize=0.0)
    model.electricity_operating_cost.fix(0.0)
    model.cooling_water_operating_cost = pyo.Var(initialize=3.173114394)
    model.cooling_water_operating_cost.fix(3.173114394)
    model.water_operating_cost = pyo.Var(initialize=0.0)
    model.water_operating_cost.fix(0.0)
    scenario = UtilitySystemScenario(
        case_study="case",
        scenario="stand-alone",
        data=UtilitySystemModelData(
            steam_mains=("MP",),
            steam_levels=(
                SteamLevelCandidate(
                    name="MP_100",
                    steam_main="MP",
                    temperature=100.0,
                    source_heat_available=0.0,
                    sink_heat_demand=0.0,
                    generation_enthalpy_delta=1.0,
                    use_enthalpy_delta=1.0,
                ),
            ),
            power_demand=0.0,
        ),
    )

    rows = utility_system_operating_cost_component_rows(
        catalog="physical-profile",
        scenario=scenario,
        model=model,
        benchmark=minimal_best_configuration_benchmark(),
    )
    csv_output = format_utility_system_operating_cost_component_rows(
        rows,
        output_format="csv",
    )

    assert rows[3] == {
        "catalog": "physical-profile",
        "case_study": "case",
        "scenario": "stand-alone",
        "operating_cost_component": "auxiliary_or_unallocated",
        "actual_operating_cost": pytest.approx(3.173114394),
        "benchmark_operating_cost": pytest.approx(-1.29),
        "operating_cost_residual": pytest.approx(4.463114394),
    }
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,operating_cost_component,"
        "actual_operating_cost,benchmark_operating_cost,operating_cost_residual"
    )


def test_utility_system_operating_cost_target_rows_compute_auxiliary_adjustment() -> (
    None
):
    rows = (
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "scenario-a",
            "operating_cost_component": "fuel",
            "actual_operating_cost": 48.0,
            "benchmark_operating_cost": 48.0,
            "operating_cost_residual": 0.0,
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "scenario-a",
            "operating_cost_component": "auxiliary_or_unallocated",
            "actual_operating_cost": 5.0,
            "benchmark_operating_cost": 2.0,
            "operating_cost_residual": 3.0,
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "scenario-a",
            "operating_cost_component": "total",
            "actual_operating_cost": 53.0,
            "benchmark_operating_cost": 50.0,
            "operating_cost_residual": 3.0,
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "scenario-b",
            "operating_cost_component": "electricity",
            "actual_operating_cost": -4.5,
            "benchmark_operating_cost": -3.5,
            "operating_cost_residual": -1.0,
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "scenario-b",
            "operating_cost_component": "auxiliary_or_unallocated",
            "actual_operating_cost": 3.0,
            "benchmark_operating_cost": 2.0,
            "operating_cost_residual": 1.0,
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "scenario-b",
            "operating_cost_component": "total",
            "actual_operating_cost": 49.0,
            "benchmark_operating_cost": 49.0,
            "operating_cost_residual": 0.0,
        },
    )

    target_rows = utility_system_operating_cost_target_rows(rows)
    csv_output = format_utility_system_operating_cost_target_rows(
        target_rows,
        output_format="csv",
    )

    assert target_rows == (
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "scenario-a",
            "residual_rank": 1,
            "target_operating_cost_component": "auxiliary_or_unallocated",
            "current_component_operating_cost": 5.0,
            "required_component_operating_cost": 2.0,
            "operating_cost_adjustment": -3.0,
            "operating_cost_adjustment_factor": 0.4,
            "benchmark_operating_cost": 50.0,
            "actual_operating_cost": 53.0,
            "target_operating_cost": 50.0,
            "operating_cost_residual": 3.0,
        },
    )
    assert utility_system_operating_cost_adjustment_map_from_target_rows(
        target_rows
    ) == {
        "scenario-a": {"auxiliary_or_unallocated": -3.0},
    }
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,residual_rank,target_operating_cost_component,"
        "current_component_operating_cost,required_component_operating_cost,"
        "operating_cost_adjustment,operating_cost_adjustment_factor,"
        "benchmark_operating_cost,actual_operating_cost,target_operating_cost,"
        "operating_cost_residual"
    )


def test_utility_system_fuel_consumption_residual_ranking_rows_rank_largest_residuals() -> (
    None
):
    fuel_rows = (
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "scenario-a",
            "equipment_family": "gas_turbine",
            "included_in_table_fuel_consumption": True,
            "fuel_consumption": 30.0,
            "benchmark_fuel_consumption": 100.0,
            "table_fuel_consumption": 110.0,
            "fuel_consumption_residual": 10.0,
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "scenario-a",
            "equipment_family": "hrsg_supplementary",
            "included_in_table_fuel_consumption": True,
            "fuel_consumption": 80.0,
            "benchmark_fuel_consumption": 100.0,
            "table_fuel_consumption": 110.0,
            "fuel_consumption_residual": 10.0,
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "scenario-a",
            "equipment_family": "table_total",
            "included_in_table_fuel_consumption": True,
            "fuel_consumption": 110.0,
            "benchmark_fuel_consumption": 100.0,
            "table_fuel_consumption": 110.0,
            "fuel_consumption_residual": 10.0,
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "scenario-b",
            "equipment_family": "gas_turbine",
            "included_in_table_fuel_consumption": True,
            "fuel_consumption": 70.0,
            "benchmark_fuel_consumption": 50.0,
            "table_fuel_consumption": 70.0,
            "fuel_consumption_residual": 20.0,
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "scenario-b",
            "equipment_family": "table_total",
            "included_in_table_fuel_consumption": True,
            "fuel_consumption": 70.0,
            "benchmark_fuel_consumption": 50.0,
            "table_fuel_consumption": 70.0,
            "fuel_consumption_residual": 20.0,
        },
    )

    rows = utility_system_fuel_consumption_residual_ranking_rows(fuel_rows)
    csv_output = format_utility_system_fuel_consumption_residual_ranking_rows(
        rows,
        output_format="csv",
    )
    json_output = format_utility_system_fuel_consumption_residual_ranking_rows(
        rows,
        output_format="json",
    )

    assert rows == (
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "scenario-b",
            "residual_rank": 1,
            "largest_fuel_family": "gas_turbine",
            "largest_family_fuel_consumption": 70.0,
            "largest_family_share_of_table": 1.0,
            "benchmark_fuel_consumption": 50.0,
            "table_fuel_consumption": 70.0,
            "fuel_consumption_residual": 20.0,
            "absolute_fuel_consumption_residual": 20.0,
            "residual_percent_of_benchmark": 40.0,
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "scenario-a",
            "residual_rank": 2,
            "largest_fuel_family": "hrsg_supplementary",
            "largest_family_fuel_consumption": 80.0,
            "largest_family_share_of_table": pytest.approx(80.0 / 110.0),
            "benchmark_fuel_consumption": 100.0,
            "table_fuel_consumption": 110.0,
            "fuel_consumption_residual": 10.0,
            "absolute_fuel_consumption_residual": 10.0,
            "residual_percent_of_benchmark": 10.0,
        },
    )
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,residual_rank,largest_fuel_family,"
        "largest_family_fuel_consumption,largest_family_share_of_table,"
        "benchmark_fuel_consumption,table_fuel_consumption,"
        "fuel_consumption_residual,absolute_fuel_consumption_residual,"
        "residual_percent_of_benchmark"
    )
    assert json.loads(json_output)[0]["scenario"] == "scenario-b"


def test_utility_system_fuel_consumption_residual_ranking_rows_allows_zero_denominators() -> (
    None
):
    fuel_rows = (
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "zero-benchmark",
            "equipment_family": "gas_turbine",
            "included_in_table_fuel_consumption": True,
            "fuel_consumption": 0.0,
            "benchmark_fuel_consumption": 0.0,
            "table_fuel_consumption": 0.0,
            "fuel_consumption_residual": 0.0,
        },
        {
            "catalog": "physical-profile",
            "case_study": "case",
            "scenario": "zero-benchmark",
            "equipment_family": "table_total",
            "included_in_table_fuel_consumption": True,
            "fuel_consumption": 0.0,
            "benchmark_fuel_consumption": 0.0,
            "table_fuel_consumption": 0.0,
            "fuel_consumption_residual": 0.0,
        },
    )

    rows = utility_system_fuel_consumption_residual_ranking_rows(fuel_rows)

    assert rows[0]["largest_family_share_of_table"] is None
    assert rows[0]["residual_percent_of_benchmark"] is None


def test_bilevel_decomposition_run_rows_are_reportable() -> None:
    assignment = BilevelIntegerAssignment.from_mapping(
        {
            "boiler_selected[boiler_1]": 1,
            "hrsg_selected[hrsg_1]": 0,
        },
    )
    incumbent = BilevelIncumbent(
        label="iteration-1",
        objective_value=42.0,
        assignment=assignment,
        best_bound=40.0,
        elapsed_seconds=3.5,
    )
    run = BilevelDecompositionRun(
        iterations=(
            BilevelDecompositionIteration(
                iteration_index=1,
                master_model=pyo.ConcreteModel(),
                master_status="master-optimal",
                assignment=assignment,
                subproblem=BilevelSubproblemResult(
                    objective_value=42.0,
                    best_bound=40.0,
                    elapsed_seconds=3.5,
                    status="slave-optimal",
                ),
                incumbent=incumbent,
                solution_pool=BilevelSolutionPool((incumbent,)),
                next_master_model=pyo.ConcreteModel(),
                candidate_source_label="source-scenario",
            ),
        ),
        solution_pool=BilevelSolutionPool((incumbent,)),
        stop_reason="max-iterations",
    )

    rows = bilevel_decomposition_run_rows(run)
    csv_output = format_bilevel_decomposition_run_rows(
        rows,
        output_format="csv",
    )
    json_output = format_bilevel_decomposition_run_rows(
        rows,
        output_format="json",
    )

    assert rows == (
        {
            "iteration_index": 1,
            "candidate_source": "source-scenario",
            "objective_value": 42.0,
            "best_bound": 40.0,
            "optimality_gap": pytest.approx(2.0),
            "elapsed_seconds": 3.5,
            "hit_time_limit": False,
            "selected_binary_count": 1,
            "unselected_binary_count": 1,
            "subproblem_status": "slave-optimal",
            "stop_reason": "max-iterations",
            "skipped_candidate_count": 0,
        },
    )
    assert csv_output.splitlines()[0] == (
        "iteration_index,candidate_source,objective_value,best_bound,optimality_gap,"
        "elapsed_seconds,hit_time_limit,selected_binary_count,"
        "unselected_binary_count,subproblem_status,stop_reason,"
        "skipped_candidate_count"
    )
    assert json.loads(json_output)[0]["subproblem_status"] == "slave-optimal"


def test_bilevel_skipped_candidate_rows_are_reportable() -> None:
    skipped = BilevelSkippedCandidate(
        candidate_label="candidate-2",
        source_label="source-scenario",
        assignment=BilevelIntegerAssignment.from_mapping(
            {
                "boiler_selected[boiler_1]": 1,
                "hrsg_selected[hrsg_1]": 0,
            },
        ),
        reason="infeasible fixed-assignment subproblem",
    )
    run = BilevelDecompositionRun(
        iterations=(),
        solution_pool=BilevelSolutionPool(),
        stop_reason="candidate-exhausted",
        skipped_candidates=(skipped,),
    )

    rows = bilevel_skipped_candidate_rows(run)
    csv_output = format_bilevel_skipped_candidate_rows(rows, output_format="csv")
    json_output = format_bilevel_skipped_candidate_rows(rows, output_format="json")

    assert rows == (
        {
            "skip_index": 1,
            "candidate_label": "candidate-2",
            "candidate_source": "source-scenario",
            "selected_binary_count": 1,
            "unselected_binary_count": 1,
            "selected_variables": "boiler_selected[boiler_1]",
            "reason": "infeasible fixed-assignment subproblem",
        },
    )
    assert csv_output.splitlines()[0] == (
        "skip_index,candidate_label,candidate_source,selected_binary_count,"
        "unselected_binary_count,selected_variables,reason"
    )
    assert json.loads(json_output)[0]["candidate_label"] == "candidate-2"


def test_bilevel_candidate_pool_rows_are_reportable() -> None:
    candidate = BilevelCandidateAssignment(
        source_label="source-scenario",
        assignment=BilevelIntegerAssignment.from_mapping(
            {
                "boiler_selected[boiler_1]": 1,
                "hrsg_selected[hrsg_1]": 0,
            },
        ),
    )

    rows = bilevel_candidate_pool_rows((candidate,))
    csv_output = format_bilevel_candidate_pool_rows(rows, output_format="csv")
    json_output = format_bilevel_candidate_pool_rows(rows, output_format="json")

    assert rows == (
        {
            "candidate_index": 1,
            "candidate_source": "source-scenario",
            "selected_binary_count": 1,
            "unselected_binary_count": 1,
            "selected_variables": "boiler_selected[boiler_1]",
        },
    )
    assert csv_output.splitlines()[0] == (
        "candidate_index,candidate_source,selected_binary_count,"
        "unselected_binary_count,selected_variables"
    )
    assert json.loads(json_output)[0]["candidate_source"] == "source-scenario"


def test_bilevel_candidate_pool_comparison_rows_are_reportable() -> None:
    accepted = BilevelIntegerAssignment.from_mapping(
        {
            "select_boiler": 1,
            "select_hrsg": 0,
        },
    )
    candidates = (
        BilevelCandidateAssignment(
            source_label="accepted-source",
            assignment=accepted,
        ),
        BilevelCandidateAssignment(
            source_label="near-source",
            assignment=BilevelIntegerAssignment.from_mapping(
                {
                    "select_boiler": 1,
                    "select_hrsg": 1,
                },
            ),
        ),
    )

    rows = bilevel_candidate_pool_comparison_rows(
        candidates,
        accepted_assignment=accepted,
    )
    csv_output = format_bilevel_candidate_pool_comparison_rows(
        rows,
        output_format="csv",
    )
    json_output = format_bilevel_candidate_pool_comparison_rows(
        rows,
        output_format="json",
    )

    assert rows == (
        {
            "candidate_index": 1,
            "candidate_source": "accepted-source",
            "hamming_distance_to_accepted": 0,
            "matches_accepted": True,
            "selected_binary_count": 1,
            "unselected_binary_count": 1,
        },
        {
            "candidate_index": 2,
            "candidate_source": "near-source",
            "hamming_distance_to_accepted": 1,
            "matches_accepted": False,
            "selected_binary_count": 2,
            "unselected_binary_count": 0,
        },
    )
    assert csv_output.splitlines()[0] == (
        "candidate_index,candidate_source,hamming_distance_to_accepted,"
        "matches_accepted,selected_binary_count,unselected_binary_count"
    )
    assert json.loads(json_output)[1]["hamming_distance_to_accepted"] == 1


def test_bilevel_candidate_source_filter_summary_rows_are_reportable() -> None:
    candidates = (
        BilevelCandidateAssignment(
            source_label="source-a",
            assignment=BilevelIntegerAssignment.from_mapping(
                {
                    "select_boiler": 1,
                    "select_hrsg": 0,
                },
            ),
        ),
        BilevelCandidateAssignment(
            source_label="source-b",
            assignment=BilevelIntegerAssignment.from_mapping(
                {
                    "select_boiler": 1,
                },
            ),
        ),
        BilevelCandidateAssignment(
            source_label="source-c",
            assignment=BilevelIntegerAssignment.from_mapping(
                {
                    "select_boiler": 1,
                    "select_hrsg": 1,
                    "select_turbine": 1,
                },
            ),
        ),
    )

    rows = bilevel_candidate_source_filter_summary_rows(
        candidates,
        variable_names=("select_boiler", "select_hrsg"),
    )
    csv_output = format_bilevel_candidate_source_filter_summary_rows(
        rows,
        output_format="csv",
    )
    json_output = format_bilevel_candidate_source_filter_summary_rows(
        rows,
        output_format="json",
    )

    assert rows == (
        {
            "source_record_count": 3,
            "compatible_candidate_count": 1,
            "incompatible_candidate_count": 2,
            "target_variable_count": 2,
            "candidate_sources": "source-a;source-b;source-c",
            "compatible_candidate_sources": "source-a",
            "incompatible_candidate_sources": "source-b;source-c",
        },
    )
    assert csv_output.splitlines()[0] == (
        "source_record_count,compatible_candidate_count,"
        "incompatible_candidate_count,target_variable_count,candidate_sources,"
        "compatible_candidate_sources,incompatible_candidate_sources"
    )
    assert json.loads(json_output)[0]["incompatible_candidate_count"] == 2


def test_bilevel_candidate_source_filter_detail_rows_are_reportable() -> None:
    candidates = (
        BilevelCandidateAssignment(
            source_label="calibrated:case:scenario-a",
            assignment=BilevelIntegerAssignment.from_mapping(
                {
                    "select_boiler": 1,
                    "select_hrsg": 0,
                },
            ),
        ),
        BilevelCandidateAssignment(
            source_label="uncalibrated:case:scenario-b",
            assignment=BilevelIntegerAssignment.from_mapping(
                {
                    "select_boiler": 1,
                    "select_turbine": 1,
                },
            ),
        ),
    )

    rows = bilevel_candidate_source_filter_detail_rows(
        candidates,
        variable_names=("select_boiler", "select_hrsg"),
    )
    csv_output = format_bilevel_candidate_source_filter_detail_rows(
        rows,
        output_format="csv",
    )
    json_output = format_bilevel_candidate_source_filter_detail_rows(
        rows,
        output_format="json",
    )

    assert rows == (
        {
            "candidate_index": 1,
            "source_catalog": "calibrated",
            "candidate_source": "case:scenario-a",
            "target_variable_count": 2,
            "candidate_variable_count": 2,
            "selected_binary_count": 1,
            "unselected_binary_count": 1,
            "compatible_with_target": True,
            "missing_target_variable_count": 0,
            "extra_candidate_variable_count": 0,
        },
        {
            "candidate_index": 2,
            "source_catalog": "uncalibrated",
            "candidate_source": "case:scenario-b",
            "target_variable_count": 2,
            "candidate_variable_count": 2,
            "selected_binary_count": 2,
            "unselected_binary_count": 0,
            "compatible_with_target": False,
            "missing_target_variable_count": 1,
            "extra_candidate_variable_count": 1,
        },
    )
    assert csv_output.splitlines()[0] == (
        "candidate_index,source_catalog,candidate_source,target_variable_count,"
        "candidate_variable_count,selected_binary_count,unselected_binary_count,"
        "compatible_with_target,missing_target_variable_count,"
        "extra_candidate_variable_count"
    )
    assert json.loads(json_output)[1]["source_catalog"] == "uncalibrated"


def test_bilevel_candidate_source_filter_variable_rows_are_reportable() -> None:
    candidates = (
        BilevelCandidateAssignment(
            source_label="calibrated:case:scenario-a",
            assignment=BilevelIntegerAssignment.from_mapping(
                {
                    "select_boiler": 1,
                    "select_hrsg": 0,
                },
            ),
        ),
        BilevelCandidateAssignment(
            source_label="uncalibrated:case:scenario-b",
            assignment=BilevelIntegerAssignment.from_mapping(
                {
                    "select_boiler": 1,
                    "select_turbine": 1,
                },
            ),
        ),
    )

    rows = bilevel_candidate_source_filter_variable_rows(
        candidates,
        variable_names=("select_boiler", "select_hrsg"),
    )
    csv_output = format_bilevel_candidate_source_filter_variable_rows(
        rows,
        output_format="csv",
    )
    json_output = format_bilevel_candidate_source_filter_variable_rows(
        rows,
        output_format="json",
    )

    assert rows == (
        {
            "candidate_index": 2,
            "source_catalog": "uncalibrated",
            "candidate_source": "case:scenario-b",
            "difference_type": "missing-target",
            "variable_name": "select_hrsg",
        },
        {
            "candidate_index": 2,
            "source_catalog": "uncalibrated",
            "candidate_source": "case:scenario-b",
            "difference_type": "extra-candidate",
            "variable_name": "select_turbine",
        },
    )
    assert csv_output.splitlines()[0] == (
        "candidate_index,source_catalog,candidate_source,difference_type,variable_name"
    )
    assert json.loads(json_output)[1]["difference_type"] == "extra-candidate"


def test_bilevel_candidate_selection_delta_rows_are_reportable() -> None:
    accepted = BilevelIntegerAssignment.from_mapping(
        {
            "select_boiler": 1,
            "select_hrsg": 0,
            "select_turbine": 1,
        },
    )
    candidate = BilevelCandidateAssignment(
        source_label="near-source",
        assignment=BilevelIntegerAssignment.from_mapping(
            {
                "select_boiler": 1,
                "select_hrsg": 1,
                "select_turbine": 0,
            },
        ),
    )

    rows = bilevel_candidate_selection_delta_rows(
        (candidate,),
        accepted_assignment=accepted,
    )
    csv_output = format_bilevel_candidate_selection_delta_rows(
        rows,
        output_format="csv",
    )
    json_output = format_bilevel_candidate_selection_delta_rows(
        rows,
        output_format="json",
    )

    assert rows == (
        {
            "candidate_index": 1,
            "candidate_source": "near-source",
            "variable_name": "select_hrsg",
            "accepted_value": 0,
            "candidate_value": 1,
            "delta_type": "candidate-only",
        },
        {
            "candidate_index": 1,
            "candidate_source": "near-source",
            "variable_name": "select_turbine",
            "accepted_value": 1,
            "candidate_value": 0,
            "delta_type": "accepted-only",
        },
    )
    assert csv_output.splitlines()[0] == (
        "candidate_index,candidate_source,variable_name,accepted_value,"
        "candidate_value,delta_type"
    )
    assert json.loads(json_output)[0]["delta_type"] == "candidate-only"


def test_bilevel_candidate_selection_delta_summary_rows_are_reportable() -> None:
    accepted = BilevelIntegerAssignment.from_mapping(
        {
            "hrsg_selected[reported-hrsg]": 1,
            "level_selected[MP_75]": 1,
            "level_selected[MP_151p5]": 0,
        },
    )
    candidate = BilevelCandidateAssignment(
        source_label="near-source",
        assignment=BilevelIntegerAssignment.from_mapping(
            {
                "hrsg_selected[reported-hrsg]": 0,
                "level_selected[MP_75]": 0,
                "level_selected[MP_151p5]": 1,
            },
        ),
    )

    rows = bilevel_candidate_selection_delta_summary_rows(
        (candidate,),
        accepted_assignment=accepted,
    )
    csv_output = format_bilevel_candidate_selection_delta_summary_rows(
        rows,
        output_format="csv",
    )
    json_output = format_bilevel_candidate_selection_delta_summary_rows(
        rows,
        output_format="json",
    )

    assert rows == (
        {
            "candidate_index": 1,
            "candidate_source": "near-source",
            "component_name": "hrsg_selected",
            "accepted_only_count": 1,
            "candidate_only_count": 0,
            "total_delta_count": 1,
        },
        {
            "candidate_index": 1,
            "candidate_source": "near-source",
            "component_name": "level_selected",
            "accepted_only_count": 1,
            "candidate_only_count": 1,
            "total_delta_count": 2,
        },
    )
    assert csv_output.splitlines()[0] == (
        "candidate_index,candidate_source,component_name,accepted_only_count,"
        "candidate_only_count,total_delta_count"
    )
    assert json.loads(json_output)[1]["component_name"] == "level_selected"


def test_bilevel_skipped_candidate_delta_summary_rows_are_reportable() -> None:
    accepted = BilevelIntegerAssignment.from_mapping(
        {
            "hrsg_selected[reported-hrsg]": 1,
            "level_selected[MP_75]": 1,
            "level_selected[MP_151p5]": 0,
        },
    )
    skipped = BilevelSkippedCandidate(
        candidate_label="candidate-2",
        source_label="near-source",
        assignment=BilevelIntegerAssignment.from_mapping(
            {
                "hrsg_selected[reported-hrsg]": 0,
                "level_selected[MP_75]": 0,
                "level_selected[MP_151p5]": 1,
            },
        ),
        reason="infeasible fixed-assignment subproblem",
    )
    run = BilevelDecompositionRun(
        iterations=(),
        solution_pool=BilevelSolutionPool(),
        stop_reason="candidate-exhausted",
        skipped_candidates=(skipped,),
    )

    rows = bilevel_skipped_candidate_delta_summary_rows(
        run,
        accepted_assignment=accepted,
    )
    csv_output = format_bilevel_skipped_candidate_delta_summary_rows(
        rows,
        output_format="csv",
    )
    json_output = format_bilevel_skipped_candidate_delta_summary_rows(
        rows,
        output_format="json",
    )

    assert rows == (
        {
            "skip_index": 1,
            "candidate_label": "candidate-2",
            "candidate_source": "near-source",
            "component_name": "hrsg_selected",
            "accepted_only_count": 1,
            "candidate_only_count": 0,
            "total_delta_count": 1,
            "reason": "infeasible fixed-assignment subproblem",
        },
        {
            "skip_index": 1,
            "candidate_label": "candidate-2",
            "candidate_source": "near-source",
            "component_name": "level_selected",
            "accepted_only_count": 1,
            "candidate_only_count": 1,
            "total_delta_count": 2,
            "reason": "infeasible fixed-assignment subproblem",
        },
    )
    assert csv_output.splitlines()[0] == (
        "skip_index,candidate_label,candidate_source,component_name,"
        "accepted_only_count,candidate_only_count,total_delta_count,reason"
    )
    assert json.loads(json_output)[0]["candidate_label"] == "candidate-2"


def test_bilevel_candidate_audit_bundle_rows_are_reportable() -> None:
    accepted = BilevelIntegerAssignment.from_mapping(
        {
            "hrsg_selected[reported-hrsg]": 1,
            "level_selected[MP_75]": 1,
            "level_selected[MP_151p5]": 0,
        },
    )
    candidate = BilevelCandidateAssignment(
        source_label="near-source",
        assignment=BilevelIntegerAssignment.from_mapping(
            {
                "hrsg_selected[reported-hrsg]": 0,
                "level_selected[MP_75]": 0,
                "level_selected[MP_151p5]": 1,
            },
        ),
    )
    skipped = BilevelSkippedCandidate(
        candidate_label="candidate-2",
        source_label="near-source",
        assignment=candidate.assignment,
        reason="infeasible fixed-assignment subproblem",
    )
    incumbent = BilevelIncumbent(
        label="iteration-1",
        objective_value=42.0,
        assignment=accepted,
        best_bound=40.0,
    )
    run = BilevelDecompositionRun(
        iterations=(),
        solution_pool=BilevelSolutionPool((incumbent,)),
        stop_reason="candidate-exhausted",
        skipped_candidates=(skipped,),
    )
    candidates = (
        BilevelCandidateAssignment(
            source_label="accepted-source",
            assignment=accepted,
        ),
        candidate,
    )

    rows = bilevel_candidate_audit_bundle_rows(
        candidates,
        run=run,
        accepted_assignment=accepted,
    )
    csv_output = format_bilevel_candidate_audit_bundle_rows(
        rows,
        output_format="csv",
    )
    json_output = format_bilevel_candidate_audit_bundle_rows(
        rows,
        output_format="json",
    )

    assert rows == (
        {
            "audit_section": "accepted-incumbent",
            "candidate_index": "",
            "skip_index": "",
            "candidate_label": "iteration-1",
            "candidate_source": "",
            "component_name": "",
            "objective_value": 42.0,
            "best_bound": 40.0,
            "optimality_gap": 2.0,
            "selected_binary_count": 2,
            "unselected_binary_count": 1,
            "hamming_distance_to_accepted": 0,
            "matches_accepted": True,
            "accepted_only_count": "",
            "candidate_only_count": "",
            "total_delta_count": "",
            "selected_variables": (
                "hrsg_selected[reported-hrsg];level_selected[MP_75]"
            ),
            "reason": "candidate-exhausted",
        },
        {
            "audit_section": "candidate-pool",
            "candidate_index": 1,
            "skip_index": "",
            "candidate_label": "",
            "candidate_source": "accepted-source",
            "component_name": "",
            "objective_value": "",
            "best_bound": "",
            "optimality_gap": "",
            "selected_binary_count": 2,
            "unselected_binary_count": 1,
            "hamming_distance_to_accepted": 0,
            "matches_accepted": True,
            "accepted_only_count": "",
            "candidate_only_count": "",
            "total_delta_count": "",
            "selected_variables": (
                "hrsg_selected[reported-hrsg];level_selected[MP_75]"
            ),
            "reason": "",
        },
        {
            "audit_section": "candidate-pool",
            "candidate_index": 2,
            "skip_index": "",
            "candidate_label": "",
            "candidate_source": "near-source",
            "component_name": "",
            "objective_value": "",
            "best_bound": "",
            "optimality_gap": "",
            "selected_binary_count": 1,
            "unselected_binary_count": 2,
            "hamming_distance_to_accepted": 3,
            "matches_accepted": False,
            "accepted_only_count": "",
            "candidate_only_count": "",
            "total_delta_count": "",
            "selected_variables": "level_selected[MP_151p5]",
            "reason": "",
        },
        {
            "audit_section": "candidate-delta-summary",
            "candidate_index": 2,
            "skip_index": "",
            "candidate_label": "",
            "candidate_source": "near-source",
            "component_name": "hrsg_selected",
            "objective_value": "",
            "best_bound": "",
            "optimality_gap": "",
            "selected_binary_count": "",
            "unselected_binary_count": "",
            "hamming_distance_to_accepted": "",
            "matches_accepted": "",
            "accepted_only_count": 1,
            "candidate_only_count": 0,
            "total_delta_count": 1,
            "selected_variables": "",
            "reason": "",
        },
        {
            "audit_section": "candidate-delta-summary",
            "candidate_index": 2,
            "skip_index": "",
            "candidate_label": "",
            "candidate_source": "near-source",
            "component_name": "level_selected",
            "objective_value": "",
            "best_bound": "",
            "optimality_gap": "",
            "selected_binary_count": "",
            "unselected_binary_count": "",
            "hamming_distance_to_accepted": "",
            "matches_accepted": "",
            "accepted_only_count": 1,
            "candidate_only_count": 1,
            "total_delta_count": 2,
            "selected_variables": "",
            "reason": "",
        },
        {
            "audit_section": "skipped-candidate",
            "candidate_index": "",
            "skip_index": 1,
            "candidate_label": "candidate-2",
            "candidate_source": "near-source",
            "component_name": "",
            "objective_value": "",
            "best_bound": "",
            "optimality_gap": "",
            "selected_binary_count": 1,
            "unselected_binary_count": 2,
            "hamming_distance_to_accepted": "",
            "matches_accepted": "",
            "accepted_only_count": "",
            "candidate_only_count": "",
            "total_delta_count": "",
            "selected_variables": "level_selected[MP_151p5]",
            "reason": "infeasible fixed-assignment subproblem",
        },
        {
            "audit_section": "skipped-candidate-delta-summary",
            "candidate_index": "",
            "skip_index": 1,
            "candidate_label": "candidate-2",
            "candidate_source": "near-source",
            "component_name": "hrsg_selected",
            "objective_value": "",
            "best_bound": "",
            "optimality_gap": "",
            "selected_binary_count": "",
            "unselected_binary_count": "",
            "hamming_distance_to_accepted": "",
            "matches_accepted": "",
            "accepted_only_count": 1,
            "candidate_only_count": 0,
            "total_delta_count": 1,
            "selected_variables": "",
            "reason": "infeasible fixed-assignment subproblem",
        },
        {
            "audit_section": "skipped-candidate-delta-summary",
            "candidate_index": "",
            "skip_index": 1,
            "candidate_label": "candidate-2",
            "candidate_source": "near-source",
            "component_name": "level_selected",
            "objective_value": "",
            "best_bound": "",
            "optimality_gap": "",
            "selected_binary_count": "",
            "unselected_binary_count": "",
            "hamming_distance_to_accepted": "",
            "matches_accepted": "",
            "accepted_only_count": 1,
            "candidate_only_count": 1,
            "total_delta_count": 2,
            "selected_variables": "",
            "reason": "infeasible fixed-assignment subproblem",
        },
    )
    assert csv_output.splitlines()[0] == (
        "audit_section,candidate_index,skip_index,candidate_label,"
        "candidate_source,component_name,objective_value,best_bound,"
        "optimality_gap,selected_binary_count,unselected_binary_count,"
        "hamming_distance_to_accepted,matches_accepted,accepted_only_count,"
        "candidate_only_count,total_delta_count,selected_variables,reason"
    )
    assert json.loads(json_output)[0]["audit_section"] == "accepted-incumbent"


def test_utility_system_decomposition_trajectory_rows_include_scenario_metadata() -> (
    None
):
    assignment = BilevelIntegerAssignment.from_mapping({"select_level": 1})
    incumbent = BilevelIncumbent(
        label="iteration-1",
        objective_value=12.5,
        assignment=assignment,
    )
    run = BilevelDecompositionRun(
        iterations=(
            BilevelDecompositionIteration(
                iteration_index=1,
                master_model=pyo.ConcreteModel(),
                master_status="master-optimal",
                assignment=assignment,
                subproblem=BilevelSubproblemResult(
                    objective_value=12.5,
                    status="optimal",
                ),
                incumbent=incumbent,
                solution_pool=BilevelSolutionPool((incumbent,)),
                next_master_model=pyo.ConcreteModel(),
            ),
        ),
        solution_pool=BilevelSolutionPool((incumbent,)),
        stop_reason="max-iterations",
    )
    scenario = UtilitySystemScenario(
        case_study="case",
        scenario="scenario",
        data=UtilitySystemModelData(
            steam_mains=("MP",),
            steam_levels=(
                SteamLevelCandidate(
                    name="MP_100",
                    steam_main="MP",
                    temperature=100.0,
                    source_heat_available=0.0,
                    sink_heat_demand=0.0,
                    generation_enthalpy_delta=1.0,
                    use_enthalpy_delta=1.0,
                ),
            ),
            power_demand=0.0,
        ),
    )

    rows = utility_system_decomposition_trajectory_rows(
        catalog="physical-profile",
        scenario=scenario,
        run=run,
    )
    csv_output = format_utility_system_decomposition_trajectory_rows(
        rows,
        output_format="csv",
    )

    assert rows[0]["catalog"] == "physical-profile"
    assert rows[0]["case_study"] == "case"
    assert rows[0]["scenario"] == "scenario"
    assert rows[0]["candidate_source"] == ""
    assert rows[0]["objective_value"] == pytest.approx(12.5)
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,iteration_index,candidate_source,"
        "objective_value,best_bound,optimality_gap,elapsed_seconds,"
        "hit_time_limit,selected_binary_count,unselected_binary_count,"
        "subproblem_status,stop_reason,skipped_candidate_count"
    )


def test_utility_system_decomposition_skipped_candidate_rows_include_scenario_metadata() -> (
    None
):
    skipped = BilevelSkippedCandidate(
        candidate_label="candidate-2",
        source_label="source-scenario",
        assignment=BilevelIntegerAssignment.from_mapping({"select_level": 1}),
        reason="infeasible fixed-assignment subproblem",
    )
    run = BilevelDecompositionRun(
        iterations=(),
        solution_pool=BilevelSolutionPool(),
        stop_reason="candidate-exhausted",
        skipped_candidates=(skipped,),
    )
    scenario = UtilitySystemScenario(
        case_study="case",
        scenario="scenario",
        data=UtilitySystemModelData(
            steam_mains=("MP",),
            steam_levels=(
                SteamLevelCandidate(
                    name="MP_100",
                    steam_main="MP",
                    temperature=100.0,
                    source_heat_available=0.0,
                    sink_heat_demand=0.0,
                    generation_enthalpy_delta=1.0,
                    use_enthalpy_delta=1.0,
                ),
            ),
            power_demand=0.0,
        ),
    )

    rows = utility_system_decomposition_skipped_candidate_rows(
        catalog="physical-profile-candidates",
        scenario=scenario,
        run=run,
    )
    csv_output = format_utility_system_decomposition_skipped_candidate_rows(
        rows,
        output_format="csv",
    )

    assert rows[0]["catalog"] == "physical-profile-candidates"
    assert rows[0]["case_study"] == "case"
    assert rows[0]["scenario"] == "scenario"
    assert rows[0]["candidate_label"] == "candidate-2"
    assert rows[0]["candidate_source"] == "source-scenario"
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,skip_index,candidate_label,"
        "candidate_source,selected_binary_count,unselected_binary_count,"
        "selected_variables,reason"
    )


def test_utility_system_candidate_pool_rows_include_scenario_metadata() -> None:
    candidate = BilevelCandidateAssignment(
        source_label="source-scenario",
        assignment=BilevelIntegerAssignment.from_mapping({"select_level": 1}),
    )
    scenario = UtilitySystemScenario(
        case_study="case",
        scenario="scenario",
        data=UtilitySystemModelData(
            steam_mains=("MP",),
            steam_levels=(
                SteamLevelCandidate(
                    name="MP_100",
                    steam_main="MP",
                    temperature=100.0,
                    source_heat_available=0.0,
                    sink_heat_demand=0.0,
                    generation_enthalpy_delta=1.0,
                    use_enthalpy_delta=1.0,
                ),
            ),
            power_demand=0.0,
        ),
    )

    rows = utility_system_candidate_pool_rows(
        catalog="physical-profile-candidates",
        scenario=scenario,
        candidates=(candidate,),
    )
    csv_output = format_utility_system_candidate_pool_rows(rows, output_format="csv")

    assert rows[0]["catalog"] == "physical-profile-candidates"
    assert rows[0]["case_study"] == "case"
    assert rows[0]["scenario"] == "scenario"
    assert rows[0]["candidate_source"] == "source-scenario"
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,candidate_index,candidate_source,"
        "selected_binary_count,unselected_binary_count,selected_variables"
    )


def test_utility_system_candidate_pool_comparison_rows_include_scenario_metadata() -> (
    None
):
    accepted = BilevelIntegerAssignment.from_mapping({"select_level": 1})
    candidate = BilevelCandidateAssignment(
        source_label="source-scenario",
        assignment=accepted,
    )
    scenario = UtilitySystemScenario(
        case_study="case",
        scenario="scenario",
        data=UtilitySystemModelData(
            steam_mains=("MP",),
            steam_levels=(
                SteamLevelCandidate(
                    name="MP_100",
                    steam_main="MP",
                    temperature=100.0,
                    source_heat_available=0.0,
                    sink_heat_demand=0.0,
                    generation_enthalpy_delta=1.0,
                    use_enthalpy_delta=1.0,
                ),
            ),
            power_demand=0.0,
        ),
    )

    rows = utility_system_candidate_pool_comparison_rows(
        catalog="physical-profile-candidates",
        scenario=scenario,
        candidates=(candidate,),
        accepted_assignment=accepted,
    )
    csv_output = format_utility_system_candidate_pool_comparison_rows(
        rows,
        output_format="csv",
    )

    assert rows[0]["catalog"] == "physical-profile-candidates"
    assert rows[0]["case_study"] == "case"
    assert rows[0]["scenario"] == "scenario"
    assert rows[0]["hamming_distance_to_accepted"] == 0
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,candidate_index,candidate_source,"
        "hamming_distance_to_accepted,matches_accepted,selected_binary_count,"
        "unselected_binary_count"
    )


def test_utility_system_candidate_source_filter_summary_rows_include_scenario_metadata() -> (
    None
):
    candidates = (
        BilevelCandidateAssignment(
            source_label="source-a",
            assignment=BilevelIntegerAssignment.from_mapping(
                {
                    "select_level": 1,
                    "select_hrsg": 0,
                },
            ),
        ),
        BilevelCandidateAssignment(
            source_label="source-b",
            assignment=BilevelIntegerAssignment.from_mapping({"select_level": 1}),
        ),
    )
    scenario = UtilitySystemScenario(
        case_study="case",
        scenario="scenario",
        data=UtilitySystemModelData(
            steam_mains=("MP",),
            steam_levels=(
                SteamLevelCandidate(
                    name="MP_100",
                    steam_main="MP",
                    temperature=100.0,
                    source_heat_available=0.0,
                    sink_heat_demand=0.0,
                    generation_enthalpy_delta=1.0,
                    use_enthalpy_delta=1.0,
                ),
            ),
            power_demand=0.0,
        ),
    )

    rows = utility_system_candidate_source_filter_summary_rows(
        catalog="physical-profile-candidates",
        scenario=scenario,
        candidates=candidates,
        variable_names=("select_level", "select_hrsg"),
    )
    csv_output = format_utility_system_candidate_source_filter_summary_rows(
        rows,
        output_format="csv",
    )

    assert rows == (
        {
            "catalog": "physical-profile-candidates",
            "case_study": "case",
            "scenario": "scenario",
            "source_record_count": 2,
            "compatible_candidate_count": 1,
            "incompatible_candidate_count": 1,
            "target_variable_count": 2,
            "candidate_sources": "source-a;source-b",
            "compatible_candidate_sources": "source-a",
            "incompatible_candidate_sources": "source-b",
        },
    )
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,source_record_count,"
        "compatible_candidate_count,incompatible_candidate_count,"
        "target_variable_count,candidate_sources,compatible_candidate_sources,"
        "incompatible_candidate_sources"
    )


def test_utility_system_candidate_source_filter_detail_rows_include_scenario_metadata() -> (
    None
):
    candidates = (
        BilevelCandidateAssignment(
            source_label="calibrated:case:source",
            assignment=BilevelIntegerAssignment.from_mapping(
                {
                    "select_level": 1,
                    "select_hrsg": 0,
                },
            ),
        ),
    )
    scenario = UtilitySystemScenario(
        case_study="case",
        scenario="scenario",
        data=UtilitySystemModelData(
            steam_mains=("MP",),
            steam_levels=(
                SteamLevelCandidate(
                    name="MP_100",
                    steam_main="MP",
                    temperature=100.0,
                    source_heat_available=0.0,
                    sink_heat_demand=0.0,
                    generation_enthalpy_delta=1.0,
                    use_enthalpy_delta=1.0,
                ),
            ),
            power_demand=0.0,
        ),
    )

    rows = utility_system_candidate_source_filter_detail_rows(
        catalog="physical-profile-candidates",
        scenario=scenario,
        candidates=candidates,
        variable_names=("select_level", "select_hrsg"),
    )
    csv_output = format_utility_system_candidate_source_filter_detail_rows(
        rows,
        output_format="csv",
    )

    assert rows == (
        {
            "catalog": "physical-profile-candidates",
            "case_study": "case",
            "scenario": "scenario",
            "candidate_index": 1,
            "source_catalog": "calibrated",
            "candidate_source": "case:source",
            "target_variable_count": 2,
            "candidate_variable_count": 2,
            "selected_binary_count": 1,
            "unselected_binary_count": 1,
            "compatible_with_target": True,
            "missing_target_variable_count": 0,
            "extra_candidate_variable_count": 0,
        },
    )
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,candidate_index,source_catalog,"
        "candidate_source,target_variable_count,candidate_variable_count,"
        "selected_binary_count,unselected_binary_count,compatible_with_target,"
        "missing_target_variable_count,extra_candidate_variable_count"
    )


def test_utility_system_candidate_source_filter_variable_rows_include_scenario_metadata() -> (
    None
):
    candidates = (
        BilevelCandidateAssignment(
            source_label="calibrated:case:source",
            assignment=BilevelIntegerAssignment.from_mapping(
                {
                    "select_level": 1,
                    "select_turbine": 1,
                },
            ),
        ),
    )
    scenario = UtilitySystemScenario(
        case_study="case",
        scenario="scenario",
        data=UtilitySystemModelData(
            steam_mains=("MP",),
            steam_levels=(
                SteamLevelCandidate(
                    name="MP_100",
                    steam_main="MP",
                    temperature=100.0,
                    source_heat_available=0.0,
                    sink_heat_demand=0.0,
                    generation_enthalpy_delta=1.0,
                    use_enthalpy_delta=1.0,
                ),
            ),
            power_demand=0.0,
        ),
    )

    rows = utility_system_candidate_source_filter_variable_rows(
        catalog="physical-profile-candidates",
        scenario=scenario,
        candidates=candidates,
        variable_names=("select_level", "select_hrsg"),
    )
    csv_output = format_utility_system_candidate_source_filter_variable_rows(
        rows,
        output_format="csv",
    )

    assert rows == (
        {
            "catalog": "physical-profile-candidates",
            "case_study": "case",
            "scenario": "scenario",
            "candidate_index": 1,
            "source_catalog": "calibrated",
            "candidate_source": "case:source",
            "difference_type": "missing-target",
            "variable_name": "select_hrsg",
        },
        {
            "catalog": "physical-profile-candidates",
            "case_study": "case",
            "scenario": "scenario",
            "candidate_index": 1,
            "source_catalog": "calibrated",
            "candidate_source": "case:source",
            "difference_type": "extra-candidate",
            "variable_name": "select_turbine",
        },
    )
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,candidate_index,source_catalog,"
        "candidate_source,difference_type,variable_name"
    )


def test_utility_system_candidate_selection_delta_rows_include_scenario_metadata() -> (
    None
):
    accepted = BilevelIntegerAssignment.from_mapping(
        {
            "select_level": 1,
            "select_hrsg": 0,
        },
    )
    candidate = BilevelCandidateAssignment(
        source_label="source-scenario",
        assignment=BilevelIntegerAssignment.from_mapping(
            {
                "select_level": 1,
                "select_hrsg": 1,
            },
        ),
    )
    scenario = UtilitySystemScenario(
        case_study="case",
        scenario="scenario",
        data=UtilitySystemModelData(
            steam_mains=("MP",),
            steam_levels=(
                SteamLevelCandidate(
                    name="MP_100",
                    steam_main="MP",
                    temperature=100.0,
                    source_heat_available=0.0,
                    sink_heat_demand=0.0,
                    generation_enthalpy_delta=1.0,
                    use_enthalpy_delta=1.0,
                ),
            ),
            power_demand=0.0,
        ),
    )

    rows = utility_system_candidate_selection_delta_rows(
        catalog="physical-profile-candidates",
        scenario=scenario,
        candidates=(candidate,),
        accepted_assignment=accepted,
    )
    csv_output = format_utility_system_candidate_selection_delta_rows(
        rows,
        output_format="csv",
    )

    assert rows == (
        {
            "catalog": "physical-profile-candidates",
            "case_study": "case",
            "scenario": "scenario",
            "candidate_index": 1,
            "candidate_source": "source-scenario",
            "variable_name": "select_hrsg",
            "accepted_value": 0,
            "candidate_value": 1,
            "delta_type": "candidate-only",
        },
    )
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,candidate_index,candidate_source,"
        "variable_name,accepted_value,candidate_value,delta_type"
    )


def test_utility_system_candidate_selection_delta_summary_rows_include_scenario_metadata() -> (
    None
):
    accepted = BilevelIntegerAssignment.from_mapping(
        {
            "level_selected[MP_75]": 1,
            "level_selected[MP_151p5]": 0,
        },
    )
    candidate = BilevelCandidateAssignment(
        source_label="source-scenario",
        assignment=BilevelIntegerAssignment.from_mapping(
            {
                "level_selected[MP_75]": 0,
                "level_selected[MP_151p5]": 1,
            },
        ),
    )
    scenario = UtilitySystemScenario(
        case_study="case",
        scenario="scenario",
        data=UtilitySystemModelData(
            steam_mains=("MP",),
            steam_levels=(
                SteamLevelCandidate(
                    name="MP_100",
                    steam_main="MP",
                    temperature=100.0,
                    source_heat_available=0.0,
                    sink_heat_demand=0.0,
                    generation_enthalpy_delta=1.0,
                    use_enthalpy_delta=1.0,
                ),
            ),
            power_demand=0.0,
        ),
    )

    rows = utility_system_candidate_selection_delta_summary_rows(
        catalog="physical-profile-candidates",
        scenario=scenario,
        candidates=(candidate,),
        accepted_assignment=accepted,
    )
    csv_output = format_utility_system_candidate_selection_delta_summary_rows(
        rows,
        output_format="csv",
    )

    assert rows == (
        {
            "catalog": "physical-profile-candidates",
            "case_study": "case",
            "scenario": "scenario",
            "candidate_index": 1,
            "candidate_source": "source-scenario",
            "component_name": "level_selected",
            "accepted_only_count": 1,
            "candidate_only_count": 1,
            "total_delta_count": 2,
        },
    )
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,candidate_index,candidate_source,"
        "component_name,accepted_only_count,candidate_only_count,total_delta_count"
    )


def test_utility_system_skipped_candidate_delta_summary_rows_include_scenario_metadata() -> (
    None
):
    accepted = BilevelIntegerAssignment.from_mapping(
        {
            "level_selected[MP_75]": 1,
            "level_selected[MP_151p5]": 0,
        },
    )
    skipped = BilevelSkippedCandidate(
        candidate_label="candidate-2",
        source_label="source-scenario",
        assignment=BilevelIntegerAssignment.from_mapping(
            {
                "level_selected[MP_75]": 0,
                "level_selected[MP_151p5]": 1,
            },
        ),
        reason="infeasible fixed-assignment subproblem",
    )
    run = BilevelDecompositionRun(
        iterations=(),
        solution_pool=BilevelSolutionPool(),
        stop_reason="candidate-exhausted",
        skipped_candidates=(skipped,),
    )
    scenario = UtilitySystemScenario(
        case_study="case",
        scenario="scenario",
        data=UtilitySystemModelData(
            steam_mains=("MP",),
            steam_levels=(
                SteamLevelCandidate(
                    name="MP_100",
                    steam_main="MP",
                    temperature=100.0,
                    source_heat_available=0.0,
                    sink_heat_demand=0.0,
                    generation_enthalpy_delta=1.0,
                    use_enthalpy_delta=1.0,
                ),
            ),
            power_demand=0.0,
        ),
    )

    rows = utility_system_skipped_candidate_delta_summary_rows(
        catalog="physical-profile-candidates",
        scenario=scenario,
        run=run,
        accepted_assignment=accepted,
    )
    csv_output = format_utility_system_skipped_candidate_delta_summary_rows(
        rows,
        output_format="csv",
    )

    assert rows == (
        {
            "catalog": "physical-profile-candidates",
            "case_study": "case",
            "scenario": "scenario",
            "skip_index": 1,
            "candidate_label": "candidate-2",
            "candidate_source": "source-scenario",
            "component_name": "level_selected",
            "accepted_only_count": 1,
            "candidate_only_count": 1,
            "total_delta_count": 2,
            "reason": "infeasible fixed-assignment subproblem",
        },
    )
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,skip_index,candidate_label,"
        "candidate_source,component_name,accepted_only_count,"
        "candidate_only_count,total_delta_count,reason"
    )


def test_utility_system_candidate_audit_bundle_rows_include_scenario_metadata() -> None:
    accepted = BilevelIntegerAssignment.from_mapping(
        {
            "level_selected[MP_75]": 1,
            "level_selected[MP_151p5]": 0,
        },
    )
    candidate = BilevelCandidateAssignment(
        source_label="source-scenario",
        assignment=BilevelIntegerAssignment.from_mapping(
            {
                "level_selected[MP_75]": 0,
                "level_selected[MP_151p5]": 1,
            },
        ),
    )
    skipped = BilevelSkippedCandidate(
        candidate_label="candidate-2",
        source_label="source-scenario",
        assignment=candidate.assignment,
        reason="infeasible fixed-assignment subproblem",
    )
    incumbent = BilevelIncumbent(
        label="iteration-1",
        objective_value=64.86,
        assignment=accepted,
    )
    run = BilevelDecompositionRun(
        iterations=(),
        solution_pool=BilevelSolutionPool((incumbent,)),
        stop_reason="candidate-exhausted",
        skipped_candidates=(skipped,),
    )
    scenario = UtilitySystemScenario(
        case_study="case",
        scenario="scenario",
        data=UtilitySystemModelData(
            steam_mains=("MP",),
            steam_levels=(
                SteamLevelCandidate(
                    name="MP_100",
                    steam_main="MP",
                    temperature=100.0,
                    source_heat_available=0.0,
                    sink_heat_demand=0.0,
                    generation_enthalpy_delta=1.0,
                    use_enthalpy_delta=1.0,
                ),
            ),
            power_demand=0.0,
        ),
    )

    rows = utility_system_candidate_audit_bundle_rows(
        catalog="physical-profile-candidates",
        scenario=scenario,
        candidates=(candidate,),
        run=run,
        accepted_assignment=accepted,
    )
    csv_output = format_utility_system_candidate_audit_bundle_rows(
        rows,
        output_format="csv",
    )

    assert rows[0]["catalog"] == "physical-profile-candidates"
    assert rows[0]["case_study"] == "case"
    assert rows[0]["scenario"] == "scenario"
    assert rows[0]["audit_section"] == "accepted-incumbent"
    assert rows[-1]["audit_section"] == "skipped-candidate-delta-summary"
    assert rows[-1]["component_name"] == "level_selected"
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,audit_section,candidate_index,"
        "skip_index,candidate_label,candidate_source,component_name,"
        "objective_value,best_bound,optimality_gap,selected_binary_count,"
        "unselected_binary_count,hamming_distance_to_accepted,matches_accepted,"
        "accepted_only_count,candidate_only_count,total_delta_count,"
        "selected_variables,reason"
    )


def test_utility_system_decomposition_objective_comparison_rows_are_reportable() -> (
    None
):
    benchmark = minimal_best_configuration_benchmark()
    assignment = BilevelIntegerAssignment.from_mapping({"select_level": 1})
    incumbent = BilevelIncumbent(
        label="iteration-1",
        objective_value=64.86,
        assignment=assignment,
    )
    run = BilevelDecompositionRun(
        iterations=(
            BilevelDecompositionIteration(
                iteration_index=1,
                master_model=pyo.ConcreteModel(),
                master_status="master-optimal",
                assignment=assignment,
                subproblem=BilevelSubproblemResult(
                    objective_value=64.86,
                    status="optimal",
                ),
                incumbent=incumbent,
                solution_pool=BilevelSolutionPool((incumbent,)),
                next_master_model=pyo.ConcreteModel(),
            ),
        ),
        solution_pool=BilevelSolutionPool((incumbent,)),
        stop_reason="max-iterations",
    )
    scenario = UtilitySystemScenario(
        case_study="case",
        scenario="microgrid",
        data=UtilitySystemModelData(
            steam_mains=("MP",),
            steam_levels=(
                SteamLevelCandidate(
                    name="MP_100",
                    steam_main="MP",
                    temperature=100.0,
                    source_heat_available=0.0,
                    sink_heat_demand=0.0,
                    generation_enthalpy_delta=1.0,
                    use_enthalpy_delta=1.0,
                ),
            ),
            power_demand=0.0,
        ),
    )

    rows = utility_system_decomposition_objective_comparison_rows(
        catalog="physical-profile",
        scenario=scenario,
        run=run,
        benchmark=benchmark,
    )
    csv_output = format_utility_system_decomposition_objective_comparison_rows(
        rows,
        output_format="csv",
    )

    assert rows[0]["objective_value"] == pytest.approx(64.86)
    assert rows[0]["benchmark_total_cost"] == pytest.approx(64.86)
    assert rows[0]["absolute_deviation"] == pytest.approx(0.0)
    assert rows[0]["within_tolerance"] is True
    assert csv_output.splitlines()[0] == (
        "catalog,case_study,scenario,iteration_index,objective_value,"
        "benchmark_total_cost,absolute_deviation,within_tolerance"
    )
