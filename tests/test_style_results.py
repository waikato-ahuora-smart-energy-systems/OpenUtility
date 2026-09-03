from __future__ import annotations

from dataclasses import replace

import pytest

from OpenUtility.utility_system import (
    EquipmentCost,
    FuelCost,
    FuelConsumptionAccountingFactor,
    GasTurbineCandidate,
    HotOilConfig,
    OperatingCostAccountingAdjustment,
    UtilitySystemResult,
    SteamLevelCandidate,
    UtilitySystemModelData,
    VhpBackPressureTurbineCandidate,
    VhpSteamCandidate,
    build_utility_system_model,
    compare_utility_system_result_to_best_configuration,
    compare_utility_system_result_to_benchmark,
    extract_utility_system_result,
    utility_system_operating_cost_components,
    utility_system_fuel_capacity_context_by_equipment,
    utility_system_fuel_consumption_by_equipment,
    utility_system_fuel_consumption_by_family,
)
from minimal_utility_system import (
    minimal_best_configuration_benchmark,
    minimal_utility_benchmark,
)


def test_extract_utility_system_result_summarizes_solved_pyomo_values() -> None:
    data = _result_extraction_data()
    model = build_utility_system_model(data)
    _fix_result_solution(model)

    result = extract_utility_system_result(
        model,
        case_study="example-site",
        scenario="gas-turbine-with-steam-turbine",
    )

    assert result.case_study == "example-site"
    assert result.scenario == "gas-turbine-with-steam-turbine"
    assert result.utility_steam_flow == pytest.approx(239.86)
    assert result.fuel_consumption == pytest.approx(249.03)
    assert result.power_generation == pytest.approx(46.67)
    assert result.steam_turbine_power == pytest.approx(20.88)
    assert result.gas_turbine_power == pytest.approx(25.79)
    assert result.fuel_cost == pytest.approx(51.04)
    assert result.hot_oil_operating_cost == pytest.approx(0.0)
    assert result.operating_cost == pytest.approx(51.04)
    assert result.maintenance_cost == pytest.approx(1.75)
    assert result.capital_cost == pytest.approx(11.98)
    assert result.total_annualized_cost == pytest.approx(64.77)


def test_extract_utility_system_result_excludes_hot_oil_from_fuel_consumption() -> None:
    data = replace(
        _result_extraction_data(),
        hot_oil=HotOilConfig(fuel_unit_cost=0.5, thermal_efficiency=0.8),
    )
    model = build_utility_system_model(data)
    _fix_result_solution(model)
    model.hot_oil_fuel_consumption.fix(10.0)

    result = extract_utility_system_result(
        model,
        case_study="example-site",
        scenario="with-hot-oil",
    )

    assert result.fuel_consumption == pytest.approx(249.03)
    assert result.fuel_cost == pytest.approx(51.04)
    assert result.hot_oil_operating_cost == pytest.approx(5.0)
    assert result.operating_cost == pytest.approx(56.04)


def test_extract_utility_system_result_applies_fuel_accounting_factors() -> None:
    data = replace(
        _result_extraction_data(),
        fuel_consumption_factors=(
            FuelConsumptionAccountingFactor(
                equipment_type="gas_turbine",
                equipment_name="gt",
                factor=0.95,
            ),
        ),
    )
    model = build_utility_system_model(data)
    _fix_result_solution(model)

    result = extract_utility_system_result(
        model,
        case_study="example-site",
        scenario="reported-fuel-basis",
    )
    rows = utility_system_fuel_consumption_by_equipment(model)

    assert result.fuel_consumption == pytest.approx(249.03 * 0.95)
    assert result.power_generation == pytest.approx(46.67)
    assert rows[0].fuel_multiplier == pytest.approx(0.95)
    assert rows[0].fuel_consumption == pytest.approx(249.03 * 0.95)


def test_extract_utility_system_result_applies_utility_steam_flow_adjustment() -> None:
    data = replace(
        _result_extraction_data(),
        utility_steam_flow_adjustment=1.5,
    )
    model = build_utility_system_model(data)
    _fix_result_solution(model)

    result = extract_utility_system_result(
        model,
        case_study="example-site",
        scenario="utility-steam-targeted",
    )

    assert result.utility_steam_flow == pytest.approx(241.36)
    assert result.fuel_consumption == pytest.approx(249.03)


def test_extract_utility_system_result_applies_operating_cost_adjustments() -> None:
    data = replace(
        _result_extraction_data(),
        operating_cost_adjustments=(
            OperatingCostAccountingAdjustment(
                component="auxiliary_or_unallocated",
                amount=-0.5,
            ),
        ),
    )
    model = build_utility_system_model(data)
    _fix_result_solution(model)

    result = extract_utility_system_result(
        model,
        case_study="example-site",
        scenario="operating-targeted",
    )
    rows = utility_system_operating_cost_components(model)

    assert result.operating_cost == pytest.approx(50.54)
    assert result.total_annualized_cost == pytest.approx(64.27)
    assert rows[3].component == "auxiliary_or_unallocated"
    assert rows[3].operating_cost == pytest.approx(-0.5)
    assert rows[4].component == "total"
    assert rows[4].operating_cost == pytest.approx(50.54)


def test_utility_system_operating_cost_components_report_auxiliary_bucket() -> None:
    data = _result_extraction_data()
    model = build_utility_system_model(data)
    _fix_result_solution(model)

    rows = utility_system_operating_cost_components(model)

    assert rows[0].component == "fuel"
    assert rows[0].operating_cost == pytest.approx(51.04)
    assert rows[1].component == "hot_oil"
    assert rows[1].operating_cost == pytest.approx(0.0)
    assert rows[2].component == "electricity"
    assert rows[2].operating_cost == pytest.approx(0.0)
    assert rows[3].component == "auxiliary_or_unallocated"
    assert rows[3].operating_cost == pytest.approx(0.0)
    assert rows[4].component == "total"
    assert rows[4].operating_cost == pytest.approx(51.04)


def test_utility_system_fuel_consumption_by_family_reports_table_scope() -> None:
    data = replace(
        _result_extraction_data(),
        hot_oil=HotOilConfig(fuel_unit_cost=0.5, thermal_efficiency=0.8),
    )
    model = build_utility_system_model(data)
    _fix_result_solution(model)
    model.hot_oil_fuel_consumption.fix(10.0)

    rows = utility_system_fuel_consumption_by_family(model)

    assert rows[0].equipment_family == "boiler"
    assert rows[0].fuel_consumption == pytest.approx(0.0)
    assert rows[0].included_in_table_fuel_consumption is True
    assert rows[1].equipment_family == "gas_turbine"
    assert rows[1].fuel_consumption == pytest.approx(249.03)
    assert rows[4].equipment_family == "hot_oil"
    assert rows[4].fuel_consumption == pytest.approx(10.0)
    assert rows[4].included_in_table_fuel_consumption is False
    assert rows[5].equipment_family == "table_total"
    assert rows[5].fuel_consumption == pytest.approx(249.03)


def test_utility_system_fuel_consumption_by_equipment_reports_source_variables() -> (
    None
):
    data = replace(
        _result_extraction_data(),
        hot_oil=HotOilConfig(fuel_unit_cost=0.5, thermal_efficiency=0.8),
    )
    model = build_utility_system_model(data)
    _fix_result_solution(model)
    model.hot_oil_fuel_consumption.fix(10.0)

    rows = utility_system_fuel_consumption_by_equipment(model)

    assert rows[0].equipment_family == "gas_turbine"
    assert rows[0].equipment_name == "gt"
    assert rows[0].fuel_variable == "gas_turbine_fuel_flow[gt]"
    assert rows[0].fuel_multiplier == pytest.approx(1.0)
    assert rows[0].fuel_consumption == pytest.approx(249.03)
    assert rows[0].included_in_table_fuel_consumption is True
    assert rows[1].equipment_family == "hot_oil"
    assert rows[1].equipment_name == "hot_oil_furnace"
    assert rows[1].fuel_variable == "hot_oil_fuel_consumption"
    assert rows[1].fuel_multiplier == pytest.approx(1.0)
    assert rows[1].fuel_consumption == pytest.approx(10.0)
    assert rows[1].included_in_table_fuel_consumption is False


def test_utility_system_fuel_capacity_context_by_equipment_reports_utilization() -> (
    None
):
    data = _result_extraction_data()
    model = build_utility_system_model(data)
    _fix_result_solution(model)

    rows = utility_system_fuel_capacity_context_by_equipment(model)

    assert rows[0].equipment_family == "gas_turbine"
    assert rows[0].equipment_name == "gt"
    assert rows[0].selection_variable == "gas_turbine_selected[gt]"
    assert rows[0].selected is True
    assert rows[0].capacity_basis == "fuel_consumption"
    assert rows[0].actual_capacity_basis_value == pytest.approx(249.03)
    assert rows[0].capacity_value == pytest.approx(300.0)
    assert rows[0].capacity_utilization == pytest.approx(249.03 / 300.0)


def test_compare_utility_system_result_to_benchmark_reports_field_deviations() -> None:
    data = _result_extraction_data()
    model = build_utility_system_model(data)
    _fix_result_solution(model)
    result = extract_utility_system_result(
        model,
        case_study="example-site",
        scenario="gas-turbine-with-steam-turbine",
    )

    comparison = compare_utility_system_result_to_benchmark(
        result,
        minimal_utility_benchmark(),
    )

    assert comparison.within_tolerance is True
    assert comparison.max_absolute_deviation == pytest.approx(0.0)
    assert comparison.deviation_for("total_annualized_cost").actual == pytest.approx(
        64.77,
    )
    assert comparison.deviation_for("total_annualized_cost").benchmark == (
        pytest.approx(64.77)
    )


def test_compare_utility_system_result_to_benchmark_detects_mismatch() -> None:
    data = _result_extraction_data()
    model = build_utility_system_model(data)
    _fix_result_solution(model)
    model.gas_turbine_power_generation["gt"].fix(25.00)
    model.onsite_power_generation.fix(45.88)
    result = extract_utility_system_result(
        model,
        case_study="example-site",
        scenario="gas-turbine-with-steam-turbine",
    )

    comparison = compare_utility_system_result_to_benchmark(
        result,
        minimal_utility_benchmark(),
        absolute_tolerance=0.1,
    )

    assert comparison.within_tolerance is False
    assert comparison.deviation_for("power_generation").absolute_deviation == (
        pytest.approx(0.79)
    )


def test_compare_utility_system_result_to_best_configuration_reports_split_power() -> (
    None
):
    benchmark = minimal_best_configuration_benchmark()
    result = UtilitySystemResult(
        case_study="example-site",
        scenario="gas-turbine-with-steam-turbine",
        utility_steam_flow=217.78,
        fuel_consumption=245.04,
        power_generation=46.67,
        steam_turbine_power=20.88,
        gas_turbine_power=25.79,
        operating_cost=50.49,
        maintenance_cost=3.59,
        capital_cost=10.78,
        total_annualized_cost=64.86,
    )

    comparison = compare_utility_system_result_to_best_configuration(
        result,
        benchmark,
    )

    assert comparison.within_tolerance is True
    assert comparison.max_absolute_deviation == pytest.approx(0.0)
    assert comparison.deviation_for("steam_turbine_power").actual == pytest.approx(
        20.88,
    )
    assert comparison.deviation_for("gas_turbine_power").benchmark == pytest.approx(
        25.79,
    )


def test_compare_utility_system_result_to_best_configuration_reports_detailed_operating_costs_when_available() -> (
    None
):
    benchmark = minimal_best_configuration_benchmark("heat-recovery-microgrid")
    result = UtilitySystemResult(
        case_study="example-site",
        scenario="heat-recovery-microgrid",
        utility_steam_flow=136.67,
        fuel_consumption=175.03,
        power_generation=46.67,
        steam_turbine_power=11.41,
        gas_turbine_power=35.26,
        operating_cost=41.66,
        maintenance_cost=2.63,
        capital_cost=9.60,
        total_annualized_cost=53.89,
        fuel_cost=29.10,
        hot_oil_operating_cost=13.81,
    )

    comparison = compare_utility_system_result_to_best_configuration(
        result,
        benchmark,
    )

    assert comparison.within_tolerance is True
    assert comparison.deviation_for("fuel_cost").benchmark == pytest.approx(29.10)
    assert comparison.deviation_for("hot_oil_operating_cost").actual == pytest.approx(
        13.81,
    )


def _result_extraction_data() -> UtilitySystemModelData:
    return UtilitySystemModelData(
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
