from __future__ import annotations

import pytest

from OpenPinch.classes.stream import Stream
from OpenPinch.classes.stream_collection import StreamCollection
from OpenPinch.classes.zone import Zone
from case_study.jimenez_romero_utility_system_optimization.benchmarks import (
    CONTRIBUTION2_CASE_STUDY_2_BEST_CONFIGURATIONS,
    CONTRIBUTION2_COMPUTATIONAL_RESULTS,
    CONTRIBUTION2_MODEL_STATISTICS,
    CONTRIBUTION2_STEAM_PROPERTY_COMPARISONS,
    STYLE_CASE_STUDY_1_HOT_OIL_RESULTS,
    STYLE_GAS_TURBINE_AMBIENT_CORRECTION,
    STYLE_GAS_TURBINE_FULL_LOAD_COEFFICIENTS,
    STYLE_GAS_TURBINE_PART_LOAD_COEFFICIENTS,
    STYLE_CASE_STUDY_2_EQUIPMENT_COSTS,
    STYLE_CASE_STUDY_2_RESOURCES,
    STYLE_CASE_STUDY_2_SITE_CONFIG,
    STYLE_CASE_STUDY_2_RESULTS,
    STYLE_CASE_STUDY_2_STREAMS,
    STYLE_CASE_STUDY_2_TOTAL_SITE_ZONE,
    get_contribution2_case_study2_best_configuration,
    get_contribution2_computational_result,
    get_contribution2_model_statistic,
    get_contribution2_steam_property_comparison,
    get_style_hot_oil_result,
    get_style_result,
    get_style_steam_target,
)
from OpenUtility.thermal import build_temperature_intervals, heat_content_by_interval


def test_case_study_1_steam_system_targets_are_captured() -> None:
    literature = get_style_steam_target("case-study-1", "varbanov-2005")
    authors = get_style_steam_target("case-study-1", "authors")

    assert literature.utility_steam_temperature == pytest.approx(503.0)
    assert literature.boiler_flowrate == pytest.approx(93.324)
    assert literature.letdown_flowrate == pytest.approx(16.645)
    assert literature.power_generation == pytest.approx(4.762)
    assert literature.power_generation_per_boiler_flow == pytest.approx(0.051)

    assert authors.utility_steam_temperature == pytest.approx(471.0)
    assert authors.boiler_flowrate == pytest.approx(107.140)
    assert authors.letdown_flowrate == pytest.approx(0.036)
    assert authors.power_generation == pytest.approx(8.364)
    assert authors.power_generation_per_boiler_flow == pytest.approx(0.078)
    assert (
        authors.power_generation_per_boiler_flow
        > literature.power_generation_per_boiler_flow
    )


def test_case_study_1_hot_oil_design_economics_are_captured() -> None:
    with_additional_main = get_style_hot_oil_result(
        "case-study-1",
        "hot-oil-and-additional-steam-main",
    )
    hot_oil_only = get_style_hot_oil_result("case-study-1", "hot-oil")
    best = min(
        STYLE_CASE_STUDY_1_HOT_OIL_RESULTS,
        key=lambda item: item.total_annualized_cost,
    )

    assert with_additional_main.mp_pressure == pytest.approx(15.2)
    assert with_additional_main.lp_pressure == pytest.approx(2.7)
    assert with_additional_main.boiler_flowrate == pytest.approx(87.22)
    assert with_additional_main.power_generation == pytest.approx(9.35)
    assert with_additional_main.total_operating_cost == pytest.approx(6.64)
    assert with_additional_main.total_capital_cost == pytest.approx(4.83)
    assert with_additional_main.total_annualized_cost == pytest.approx(11.47)

    assert hot_oil_only.boiler_flowrate == pytest.approx(75.90)
    assert hot_oil_only.hot_oil_fuel_cost == pytest.approx(1.22)
    assert hot_oil_only.total_annualized_cost == pytest.approx(11.67)
    assert best.scenario == "hot-oil-and-additional-steam-main"


def test_case_study_2_conventional_and_proposed_results_are_captured() -> None:
    conventional = get_style_result("case-study-2", "conventional")
    proposed = get_style_result("case-study-2", "proposed-without-hot-oil")

    assert conventional.total_annualized_cost == pytest.approx(75.86)
    assert proposed.total_annualized_cost == pytest.approx(64.77)
    assert proposed.fuel_consumption == pytest.approx(249.03)
    assert proposed.power_generation == pytest.approx(46.67)


def test_case_study_2_site_configuration_is_captured() -> None:
    config = STYLE_CASE_STUDY_2_SITE_CONFIG

    assert config.case_study == "case-study-2"
    assert config.power_demand == pytest.approx(40.0)
    assert config.max_power_export == pytest.approx(10.0)
    assert config.operating_hours == pytest.approx(8600.0)
    assert config.interest_rate_percent == pytest.approx(8.0)
    assert config.plant_life_years == pytest.approx(25.0)
    assert config.capital_installation_factor == pytest.approx(4.0)
    assert config.cooling_water_temperature_rise == pytest.approx(10.0)
    assert config.boiler_feedwater_temperature == pytest.approx(120.0)
    assert config.vhp_pressure == pytest.approx(100.0)


def test_case_study_2_stream_table_is_captured() -> None:
    streams = STYLE_CASE_STUDY_2_STREAMS

    assert isinstance(streams, StreamCollection)
    assert len(streams) == 36
    assert all(isinstance(stream, Stream) for stream in streams)
    assert streams.get_stream_names()[0] == "A-1"
    assert streams["A-1"].type == "Hot"
    assert streams.get_stream_names()[-1] == "E-9"
    assert streams["E-9"].type == "Hot"
    assert sum(
        stream.heat_flow.value for stream in streams if stream.type == "Hot"
    ) == (pytest.approx(330.0))
    assert sum(
        stream.heat_flow.value for stream in streams if stream.type == "Cold"
    ) == (pytest.approx(220.0))

    stream_a1 = streams["A-1"]
    assert stream_a1.t_max_star.value == pytest.approx(292.5)
    assert stream_a1.t_min_star.value == pytest.approx(272.5)
    assert stream_a1.CP.value == pytest.approx(1.5)
    assert stream_a1.heat_flow.value == pytest.approx(30.0)

    stream_c1 = streams["C-1"]
    assert stream_c1.t_min_star.value == pytest.approx(176.5)
    assert stream_c1.t_max_star.value == pytest.approx(181.5)
    assert stream_c1.CP.value == pytest.approx(2.0)
    assert stream_c1.heat_flow.value == pytest.approx(10.0)


def test_case_study_2_streams_are_organized_in_openpinch_zone() -> None:
    zone = STYLE_CASE_STUDY_2_TOTAL_SITE_ZONE

    assert isinstance(zone, Zone)
    assert zone.name == "case-study-2"
    assert set(zone.subzones) == {"A", "B", "C", "D", "E"}
    assert len(zone.process_streams) == 36
    assert zone.subzones["A"].process_streams.get_stream_names() == [
        "A-1",
        "A-2",
        "A-3",
        "A-4",
    ]
    assert zone.subzones["E"].process_streams.get_stream_names() == [
        "E-8",
        "E-9",
        "E-1",
        "E-2",
        "E-3",
        "E-4",
        "E-5",
        "E-6",
        "E-7",
    ]


def test_case_study_2_streams_feed_existing_thermal_profile_builder() -> None:
    intervals = build_temperature_intervals(STYLE_CASE_STUDY_2_STREAMS)
    profile = heat_content_by_interval(STYLE_CASE_STUDY_2_STREAMS, intervals)
    expected_source_heat = sum(
        stream.heat_flow.value
        for stream in STYLE_CASE_STUDY_2_STREAMS
        if stream.type == "Hot"
    )
    expected_sink_heat = sum(
        stream.heat_flow.value
        for stream in STYLE_CASE_STUDY_2_STREAMS
        if stream.type == "Cold"
    )

    assert intervals[0].upper == pytest.approx(292.5)
    assert intervals[-1].lower == pytest.approx(75.0)
    assert sum(profile.source_heat.values()) == pytest.approx(expected_source_heat)
    assert sum(profile.sink_heat.values()) == pytest.approx(expected_sink_heat)


def test_case_study_2_resource_table_is_captured() -> None:
    resources = {resource.name: resource for resource in STYLE_CASE_STUDY_2_RESOURCES}

    assert len(resources) == 9
    assert resources["natural-gas"].lower_heating_value == pytest.approx(13.08)
    assert resources["natural-gas"].unit_cost == pytest.approx(24.30)
    assert resources["natural-gas"].cost_unit == "eur_per_mwh"
    assert resources["electricity-import"].unit_cost == pytest.approx(88.65)
    assert resources["electricity-export"].unit_cost == pytest.approx(79.79)
    assert resources["treated-water"].lower_heating_value is None
    assert resources["treated-water"].unit_cost == pytest.approx(0.301)
    assert resources["treated-water"].cost_unit == "eur_per_tonne"


def test_case_study_2_equipment_cost_table_is_captured() -> None:
    equipment_costs = {
        (cost.equipment_type, cost.subtype, cost.range_lower, cost.range_upper): cost
        for cost in STYLE_CASE_STUDY_2_EQUIPMENT_COSTS
    }

    assert len(equipment_costs) == 11
    packaged_boiler = equipment_costs[("boiler", "packaged", 50.0, 350.0)]
    assert packaged_boiler.variable_cost == pytest.approx(46432.32)
    assert packaged_boiler.fixed_cost == pytest.approx(318715.66)
    assert packaged_boiler.size_unit == "t_per_h"

    industrial_gt = equipment_costs[("gas-turbine", "industrial", 34.1, 125.0)]
    assert industrial_gt.variable_cost == pytest.approx(204104.04)
    assert industrial_gt.fixed_cost == pytest.approx(4439144.00)

    small_hrsg = equipment_costs[("hrsg", "all", None, 85.0)]
    assert small_hrsg.variable_cost == pytest.approx(2894.08)
    assert small_hrsg.fixed_cost == pytest.approx(266.54)


def test_style_gas_turbine_full_load_coefficients_are_captured() -> None:
    coefficients = {
        coefficient.turbine_type: coefficient
        for coefficient in STYLE_GAS_TURBINE_FULL_LOAD_COEFFICIENTS
    }

    assert coefficients["industrial"].full_load_a == pytest.approx(2.5948)
    assert coefficients["industrial"].full_load_b == pytest.approx(30093.0)
    assert coefficients["industrial"].air_flow_c == pytest.approx(0.0028)
    assert coefficients["industrial"].air_flow_d == pytest.approx(18.444)
    assert coefficients["aeroderivative"].full_load_a == pytest.approx(2.1816)
    assert coefficients["aeroderivative"].full_load_b == pytest.approx(10002.0)
    assert coefficients["aeroderivative"].air_flow_c == pytest.approx(0.0029)
    assert coefficients["aeroderivative"].air_flow_d == pytest.approx(5.538)


def test_style_gas_turbine_correction_and_part_load_coefficients_are_captured() -> None:
    part_load = {
        coefficient.fuel: coefficient
        for coefficient in STYLE_GAS_TURBINE_PART_LOAD_COEFFICIENTS
    }

    assert STYLE_GAS_TURBINE_AMBIENT_CORRECTION.temperature_power_e == pytest.approx(
        1.02,
    )
    assert STYLE_GAS_TURBINE_AMBIENT_CORRECTION.temperature_power_f == pytest.approx(
        1.33e-3,
    )
    assert STYLE_GAS_TURBINE_AMBIENT_CORRECTION.temperature_efficiency_g == (
        pytest.approx(1.1)
    )
    assert STYLE_GAS_TURBINE_AMBIENT_CORRECTION.temperature_efficiency_h == (
        pytest.approx(6.66e-3)
    )
    assert part_load["natural-gas"].part_load_a == pytest.approx(0.152)
    assert part_load["natural-gas"].part_load_b == pytest.approx(-0.00142)
    assert part_load["distillate-oil"].part_load_a == pytest.approx(0.144)
    assert part_load["distillate-oil"].part_load_b == pytest.approx(-0.00153)


def test_case_study_2_best_static_style_configuration_is_hot_oil_and_fsr() -> None:
    best = min(
        STYLE_CASE_STUDY_2_RESULTS,
        key=lambda item: item.total_annualized_cost,
    )

    assert best.scenario == "hot-oil-and-fsr"
    assert best.total_annualized_cost == pytest.approx(54.72)
    assert best.fuel_consumption == pytest.approx(201.13)


def test_contribution2_model_statistics_table_is_captured() -> None:
    test_6 = get_contribution2_model_statistic(6)
    test_9 = get_contribution2_model_statistic(9)

    assert len(CONTRIBUTION2_MODEL_STATISTICS) == 12
    assert test_6.reference == "Sun et al. (2015)"
    assert test_6.steam_mains == 3
    assert test_6.power_demand == pytest.approx(40.0)
    assert test_6.integrates_hot_oil_and_fsr is True
    assert test_6.variable_count == 9550
    assert test_6.binary_count == 709
    assert test_6.equation_count == 6879

    assert test_9.reference == "Oluleye (2015)"
    assert test_9.variable_count == 16048
    assert test_9.binary_count == 957
    assert test_9.equation_count == 10713


def test_contribution2_computational_results_table_is_captured() -> None:
    baron = get_contribution2_computational_result(1, 1, "baron")
    smilp = get_contribution2_computational_result(6, 2, "s-milp")
    bilevel = get_contribution2_computational_result(6, 2, "bilevel")
    baron_limited = get_contribution2_computational_result(6, 2, "baron")
    best_test_12_scenario_2 = min(
        (
            item
            for item in CONTRIBUTION2_COMPUTATIONAL_RESULTS
            if item.test_number == 12 and item.scenario == 2
        ),
        key=lambda item: item.best_solution_found,
    )

    assert len(CONTRIBUTION2_COMPUTATIONAL_RESULTS) == 72
    assert baron.best_solution_found == pytest.approx(30.487)
    assert baron.best_possible == pytest.approx(30.456)
    assert baron.computational_time_seconds == pytest.approx(319.1)
    assert baron.hit_time_limit is False

    assert smilp.best_solution_found == pytest.approx(54.718)
    assert smilp.best_possible is None
    assert smilp.computational_time_seconds == pytest.approx(85.3)

    assert bilevel.best_solution_found == pytest.approx(53.891)
    assert bilevel.best_possible == pytest.approx(52.659)
    assert bilevel.computational_time_seconds == pytest.approx(2613.3)

    assert baron_limited.computational_time_seconds == pytest.approx(20000.0)
    assert baron_limited.hit_time_limit is True
    assert best_test_12_scenario_2.method == "bilevel"
    assert best_test_12_scenario_2.best_solution_found == pytest.approx(11.252)


def test_contribution2_steam_property_comparison_table_is_captured() -> None:
    vhp = get_contribution2_steam_property_comparison(
        "best-obtained-configuration",
        "VHP-ST 1",
    )
    total = get_contribution2_steam_property_comparison(
        "fixed-steam-main-pressures",
        "total",
    )

    assert len(CONTRIBUTION2_STEAM_PROPERTY_COMPARISONS) == 6
    assert vhp.inlet_temperature == pytest.approx(570.0)
    assert vhp.inlet_pressure == pytest.approx(100.0)
    assert vhp.outlet_pressure == pytest.approx(20.0)
    assert vhp.real_isentropic_enthalpy_change == pytest.approx(0.1385)
    assert vhp.model_isentropic_enthalpy_change == pytest.approx(0.1367)
    assert vhp.iapws_power_generation == pytest.approx(10.29)
    assert vhp.model_power_generation == pytest.approx(10.15)

    assert total.iapws_power_generation == pytest.approx(10.61)
    assert total.model_power_generation == pytest.approx(10.51)
    assert total.inlet_temperature is None


def test_contribution2_case_study_2_best_configuration_table_is_captured() -> None:
    utility_microgrid = get_contribution2_case_study2_best_configuration(
        "utility-system-microgrid",
    )
    integrated_microgrid = get_contribution2_case_study2_best_configuration(
        "hot-oil-fsr-microgrid",
    )
    best = min(
        CONTRIBUTION2_CASE_STUDY_2_BEST_CONFIGURATIONS,
        key=lambda item: item.total_cost,
    )

    assert len(CONTRIBUTION2_CASE_STUDY_2_BEST_CONFIGURATIONS) == 4
    assert utility_microgrid.steam_mains == ("HP", "MP", "LP")
    assert utility_microgrid.pressures == pytest.approx((37.8, 12.3, 2.7))
    assert utility_microgrid.process_steam_generation[0] is None
    assert utility_microgrid.process_steam_generation[1:] == pytest.approx(
        (42.4, 153.7),
    )
    assert utility_microgrid.power_revenue == pytest.approx(-3.50)
    assert utility_microgrid.total_cost == pytest.approx(64.86)

    assert integrated_microgrid.steam_mains == ("MP", "LP")
    assert integrated_microgrid.pressures == pytest.approx((20.0, 2.7))
    assert integrated_microgrid.flash_steam[0] is None
    assert integrated_microgrid.flash_steam[1:] == pytest.approx((29.62,))
    assert integrated_microgrid.hot_oil_system_load == pytest.approx(51.86)
    assert integrated_microgrid.steam_turbine_power == pytest.approx(11.41)
    assert integrated_microgrid.gas_turbine_power == pytest.approx(35.26)
    assert integrated_microgrid.total_cost == pytest.approx(53.89)

    assert best.scenario == "hot-oil-fsr-microgrid"
