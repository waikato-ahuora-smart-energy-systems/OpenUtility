from __future__ import annotations

import pytest

import OpenUtility.style.case_studies as case_studies
from OpenUtility.benchmarks import (
    STYLE_CASE_STUDY_2_STREAMS,
    get_contribution2_case_study2_best_configuration,
)
from OpenUtility.style import (
    StaticStyleScenario,
    StaticStyleScenarioCatalog,
    SteamLevelCandidate,
    StyleModelData,
    VhpSteamCandidate,
    CoolPropSteamPropertyProvider,
    apply_steam_property_update,
    build_static_style_model,
    compare_static_style_result_to_best_configuration,
    run_static_style_scenario,
    scipy_milp_static_style_solver,
    static_style_fuel_consumption_by_equipment,
    style_case_study_2_best_configuration_physical_profile_model_data,
    style_case_study_2_best_configuration_property_spec,
    style_case_study_2_best_configuration_reported_flow_model_data,
    style_case_study_2_best_configuration_reported_equipment_model_data,
    style_case_study_2_best_configuration_boiler_candidate,
    style_case_study_2_best_configuration_gas_turbine_candidate,
    style_case_study_2_best_configuration_flash_steam_recovery_config,
    style_case_study_2_best_configuration_hot_oil_config,
    style_case_study_2_best_configuration_hot_oil_thermal_efficiency_for_reported_operating_cost,
    style_case_study_2_best_configuration_hrsg_candidate,
    style_case_study_2_best_configuration_hrsg_supplementary_firing_efficiency_for_reported_fuel_consumption,
    style_case_study_2_best_configuration_inter_main_letdown_candidates,
    style_case_study_2_best_configuration_with_gas_turbine_hrsg,
    style_case_study_2_best_configuration_with_inter_main_letdowns,
    style_case_study_2_best_configuration_with_boiler,
    style_case_study_2_best_configuration_vhp_turbine_candidate,
    style_case_study_2_best_configuration_with_vhp_turbine,
    style_case_study_2_boiler_candidate,
    style_case_study_2_boiler_gas_turbine_hrsg_scenario_data,
    style_case_study_2_capital_recovery_factor,
    style_case_study_2_complete_static_scenario_catalog,
    style_case_study_2_contribution2_best_configuration_catalog,
    style_case_study_2_contribution2_physical_profile_catalog,
    style_case_study_2_base_model_data,
    style_case_study_2_cooling_water_config,
    style_case_study_2_equipment_cost_input,
    style_case_study_2_fuel_cost,
    style_case_study_2_gas_turbine_candidate,
    style_case_study_2_gas_turbine_exhaust_flow,
    style_case_study_2_gas_turbine_hrsg_scenario_data,
    style_case_study_2_gas_turbine_scenario_data,
    style_case_study_2_heat_interval_profile,
    style_case_study_2_hrsg_candidate,
    style_case_study_2_hrsg_equipment_cost_input,
    style_case_study_2_scenario_catalog,
    style_case_study_2_static_scenario,
    style_case_study_2_vhp_enthalpies,
    style_case_study_2_vhp_back_pressure_turbine_candidate,
    style_case_study_2_vhp_letdown_candidate,
    style_case_study_2_vhp_turbine_equipment_cost_input,
    style_case_study_2_with_vhp_back_pressure_turbine,
    style_case_study_2_with_vhp_letdown,
    style_case_study_2_water_cost,
)


def test_style_case_study_2_heat_interval_profile_uses_extracted_streams() -> None:
    profile = style_case_study_2_heat_interval_profile()
    expected_source_heat = sum(
        stream.heat_capacity_flow
        * abs(stream.supply_temperature - stream.target_temperature)
        for stream in STYLE_CASE_STUDY_2_STREAMS
        if stream.stream_type == "hot"
    )
    expected_sink_heat = sum(
        stream.heat_capacity_flow
        * abs(stream.supply_temperature - stream.target_temperature)
        for stream in STYLE_CASE_STUDY_2_STREAMS
        if stream.stream_type == "cold"
    )

    assert profile.intervals[0].upper == pytest.approx(292.5)
    assert profile.intervals[-1].lower == pytest.approx(75.0)
    assert sum(profile.source_heat.values()) == pytest.approx(expected_source_heat)
    assert sum(profile.sink_heat.values()) == pytest.approx(expected_sink_heat)


def test_style_case_study_2_heat_interval_profile_can_use_openpinch_streams() -> None:
    openpinch_profile = style_case_study_2_heat_interval_profile(
        use_openpinch_streams=True,
    )
    fixture_profile = style_case_study_2_heat_interval_profile(
        use_openpinch_streams=False,
    )

    assert openpinch_profile.intervals == fixture_profile.intervals
    assert openpinch_profile.source_heat == pytest.approx(fixture_profile.source_heat)
    assert openpinch_profile.sink_heat == pytest.approx(fixture_profile.sink_heat)


def test_style_case_study_2_heat_interval_profile_falls_back_without_openpinch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_missing_openpinch(_streams: object) -> tuple[object, ...]:
        raise ImportError("OpenPinch missing")

    monkeypatch.setattr(
        case_studies,
        "openpinch_streams_from_thesis_streams",
        raise_missing_openpinch,
    )

    profile = style_case_study_2_heat_interval_profile(use_openpinch_streams=True)
    fixture_profile = style_case_study_2_heat_interval_profile(
        use_openpinch_streams=False,
    )

    assert profile.intervals == fixture_profile.intervals
    assert profile.source_heat == pytest.approx(fixture_profile.source_heat)
    assert profile.sink_heat == pytest.approx(fixture_profile.sink_heat)


def test_style_case_study_2_base_model_data_uses_site_and_resource_fixtures() -> None:
    data = style_case_study_2_base_model_data(
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        feedwater_enthalpy=0.5,
    )
    source_heat = sum(level.source_heat_available for level in data.steam_levels)
    sink_heat = sum(level.sink_heat_demand for level in data.steam_levels)

    assert data.steam_mains == ("MP",)
    assert len(data.steam_levels) == len(style_case_study_2_heat_interval_profile().intervals)
    assert source_heat > sink_heat
    assert data.power_demand == pytest.approx(40.0)
    assert data.grid_export_limit == pytest.approx(10.0)
    assert data.grid_import_limit is None
    assert data.operating_hours == pytest.approx(8600.0)
    assert data.cost_scale == pytest.approx(1e-6)
    assert data.electricity_cost is not None
    assert data.electricity_cost.import_unit_cost == pytest.approx(88.65)
    assert data.electricity_cost.export_unit_price == pytest.approx(79.79)
    assert data.cooling_water is not None
    assert data.cooling_water.unit_cost == pytest.approx(1.230)
    assert data.water_cost is not None
    assert data.water_cost.unit_cost == pytest.approx(0.301)
    assert all(
        level.generation_enthalpy_delta == pytest.approx(2.0)
        for level in data.steam_levels
    )
    assert all(level.use_enthalpy_delta == pytest.approx(1.0) for level in data.steam_levels)
    assert all(level.feedwater_enthalpy == pytest.approx(0.5) for level in data.steam_levels)


def test_style_case_study_2_capital_recovery_factor_uses_site_finance() -> None:
    assert style_case_study_2_capital_recovery_factor() == pytest.approx(
        0.09367877905196814,
    )


def test_style_case_study_2_resource_helpers_create_model_cost_inputs() -> None:
    fuel_cost = style_case_study_2_fuel_cost(
        "natural-gas",
        equipment_type="boiler",
        equipment_name="boiler-packaged",
    )
    cooling_water = style_case_study_2_cooling_water_config(process_cooling_load=12.5)
    water = style_case_study_2_water_cost()

    assert fuel_cost.name == "boiler-packaged-natural-gas"
    assert fuel_cost.equipment_type == "boiler"
    assert fuel_cost.equipment_name == "boiler-packaged"
    assert fuel_cost.unit_cost == pytest.approx(24.30)
    assert cooling_water.unit_cost == pytest.approx(1.230)
    assert cooling_water.process_cooling_load == pytest.approx(12.5)
    assert water.unit_cost == pytest.approx(0.301)


def test_style_case_study_2_equipment_cost_input_selects_piecewise_coefficients() -> None:
    packaged_boiler = style_case_study_2_equipment_cost_input(
        equipment_type="boiler",
        subtype="packaged",
        equipment_name="boiler-packaged",
        design_size=100.0,
    )
    large_industrial_gt = style_case_study_2_equipment_cost_input(
        equipment_type="gas-turbine",
        subtype="industrial",
        equipment_name="gt-industrial",
        design_size=40.0,
    )
    steam_turbine = style_case_study_2_equipment_cost_input(
        equipment_type="steam-turbine",
        subtype="all",
        equipment_name="vhp-st",
        design_size=20.0,
        model_equipment_type="vhp_turbine",
    )

    assert packaged_boiler.name == "boiler-packaged-capital"
    assert packaged_boiler.equipment_type == "boiler"
    assert packaged_boiler.annualization_factor == pytest.approx(
        style_case_study_2_capital_recovery_factor(),
    )
    assert packaged_boiler.installation_factor == pytest.approx(4.0)
    assert packaged_boiler.variable_capital_cost == pytest.approx(46432.32)
    assert packaged_boiler.fixed_capital_cost == pytest.approx(318715.66)

    assert large_industrial_gt.equipment_type == "gas_turbine"
    assert large_industrial_gt.variable_capital_cost == pytest.approx(204104.04)
    assert large_industrial_gt.fixed_capital_cost == pytest.approx(4439144.00)
    assert steam_turbine.equipment_type == "vhp_turbine"
    assert steam_turbine.variable_capital_cost == pytest.approx(345101.63)


def test_style_case_study_2_equipment_cost_input_requires_unambiguous_mapping() -> None:
    with pytest.raises(ValueError, match="model_equipment_type is required"):
        style_case_study_2_equipment_cost_input(
            equipment_type="steam-turbine",
            subtype="all",
            equipment_name="st",
            design_size=20.0,
        )

    with pytest.raises(ValueError, match="No case-study 2 equipment cost coefficient"):
        style_case_study_2_equipment_cost_input(
            equipment_type="gas-turbine",
            subtype="industrial",
            equipment_name="gt-industrial",
            design_size=200.0,
        )


def test_style_case_study_2_gas_turbine_candidate_uses_p1b_coefficients() -> None:
    candidate = style_case_study_2_gas_turbine_candidate(
        name="gt-industrial",
        turbine_type="industrial",
        fuel="natural-gas",
        max_power_generation=40.0,
        minimum_load_fraction=0.5,
        ambient_temperature=15.0,
    )
    ambient_ratio = (1.02 - 1.33e-3 * 15.0) / (1.1 - 6.66e-3 * 15.0)
    expected_max_fuel_power = (2.5948 * 40.0 + 30.093) * ambient_ratio
    expected_max_fuel_flow = expected_max_fuel_power / 13.08

    assert candidate.name == "gt-industrial"
    assert candidate.fuel_lhv == pytest.approx(13.08)
    assert candidate.max_fuel_flow == pytest.approx(expected_max_fuel_flow)
    assert candidate.min_fuel_flow == pytest.approx(expected_max_fuel_flow * 0.5)
    assert candidate.minimum_load_fraction == pytest.approx(0.5)
    assert candidate.power_slope == pytest.approx(13.08 / (2.5948 * ambient_ratio))
    assert candidate.power_intercept == pytest.approx(30.093 / 2.5948)
    assert (
        candidate.power_slope * candidate.max_fuel_flow
        - candidate.power_intercept
    ) == pytest.approx(40.0)


def test_style_case_study_2_gas_turbine_candidate_requires_energy_fuel() -> None:
    with pytest.raises(ValueError, match="does not define a lower heating value"):
        style_case_study_2_gas_turbine_candidate(
            name="gt-hot-oil",
            turbine_type="industrial",
            fuel="hot-oil",
            max_power_generation=40.0,
        )


def test_style_case_study_2_static_scenario_wraps_base_data_and_benchmark() -> None:
    scenario = style_case_study_2_static_scenario(
        scenario="proposed-without-hot-oil",
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        feedwater_enthalpy=0.5,
    )

    assert scenario.case_study == "case-study-2"
    assert scenario.scenario == "proposed-without-hot-oil"
    assert scenario.benchmark is not None
    assert scenario.benchmark.total_annualized_cost == pytest.approx(64.77)
    assert scenario.data.power_demand == pytest.approx(40.0)
    assert scenario.data.steam_levels[0].feedwater_enthalpy == pytest.approx(0.5)


def test_style_case_study_2_gas_turbine_scenario_data_adds_candidate_and_costs() -> None:
    data = style_case_study_2_gas_turbine_scenario_data(
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        fuel="natural-gas",
        max_power_generation=40.0,
        minimum_load_fraction=0.5,
    )

    assert len(data.gas_turbines) == 1
    assert data.gas_turbines[0].name == "gt-industrial"
    assert data.gas_turbines[0].max_fuel_flow > 0.0
    assert len(data.fuel_costs) == 1
    assert data.fuel_costs[0].equipment_type == "gas_turbine"
    assert data.fuel_costs[0].equipment_name == "gt-industrial"
    assert data.fuel_costs[0].unit_cost == pytest.approx(24.30)
    assert len(data.equipment_costs) == 1
    assert data.equipment_costs[0].equipment_type == "gas_turbine"
    assert data.equipment_costs[0].equipment_name == "gt-industrial"
    assert data.equipment_costs[0].variable_capital_cost == pytest.approx(204104.04)


def test_style_case_study_2_hrsg_candidate_uses_gas_turbine_exhaust_envelope() -> None:
    gas_turbine = style_case_study_2_gas_turbine_candidate(
        name="gt-industrial",
        turbine_type="industrial",
        fuel="natural-gas",
        max_power_generation=40.0,
    )
    hrsg = style_case_study_2_hrsg_candidate(
        name="hrsg-gt-industrial",
        gas_turbine=gas_turbine,
        vhp_header="VHP_100",
        steam_generation_efficiency=0.8,
    )
    full_load_power = (
        gas_turbine.power_slope * gas_turbine.max_fuel_flow
        - gas_turbine.power_intercept
    )
    expected_exhaust_heat = (
        gas_turbine.fuel_lhv * gas_turbine.max_fuel_flow - full_load_power
    )

    assert hrsg.name == "hrsg-gt-industrial"
    assert hrsg.gas_turbine == "gt-industrial"
    assert hrsg.vhp_header == "VHP_100"
    assert hrsg.steam_generation_efficiency == pytest.approx(0.8)
    assert hrsg.max_heat_input == pytest.approx(expected_exhaust_heat)
    assert hrsg.supplementary_fuel_lhv == pytest.approx(0.0)


def test_style_case_study_2_hrsg_cost_converts_exhaust_flow_to_heat_basis() -> None:
    gas_turbine = style_case_study_2_gas_turbine_candidate(
        name="gt-industrial",
        turbine_type="industrial",
        fuel="natural-gas",
        max_power_generation=40.0,
    )
    hrsg = style_case_study_2_hrsg_candidate(
        name="hrsg-gt-industrial",
        gas_turbine=gas_turbine,
        vhp_header="VHP_100",
        steam_generation_efficiency=0.8,
    )
    exhaust_flow = style_case_study_2_gas_turbine_exhaust_flow(
        gas_turbine=gas_turbine,
        turbine_type="industrial",
    )
    cost = style_case_study_2_hrsg_equipment_cost_input(
        hrsg=hrsg,
        gas_turbine=gas_turbine,
        turbine_type="industrial",
    )
    expected_air_flow = 0.0028 * 40000.0 + 18.444
    expected_fuel_flow = gas_turbine.max_fuel_flow * 1000.0 / 3600.0
    expected_exhaust_flow = (expected_air_flow + expected_fuel_flow) * 3.6

    assert exhaust_flow == pytest.approx(expected_exhaust_flow)
    assert cost.name == "hrsg-gt-industrial-capital"
    assert cost.equipment_type == "hrsg"
    assert cost.equipment_name == "hrsg-gt-industrial"
    assert cost.variable_capital_cost == pytest.approx(
        22895.56 * exhaust_flow / hrsg.max_heat_input,
    )
    assert cost.fixed_capital_cost == pytest.approx(135.33)


def test_style_case_study_2_boiler_candidate_maps_efficiency_to_fuel_coefficient() -> None:
    boiler = style_case_study_2_boiler_candidate(
        name="boiler-packaged",
        vhp_header="VHP_100",
        max_steam_generation=200.0,
        thermal_efficiency=0.85,
        minimum_load_fraction=0.25,
    )

    assert boiler.name == "boiler-packaged"
    assert boiler.vhp_header == "VHP_100"
    assert boiler.size_fuel_coefficient == pytest.approx(0.0)
    assert boiler.load_fuel_coefficient == pytest.approx(1.0 / 0.85)
    assert boiler.min_capacity == pytest.approx(0.0)
    assert boiler.max_capacity == pytest.approx(200.0)
    assert boiler.minimum_load_fraction == pytest.approx(0.25)


def test_style_case_study_2_vhp_enthalpies_use_site_pressure_and_feedwater_temperature() -> None:
    steam_enthalpy, feedwater_enthalpy = style_case_study_2_vhp_enthalpies(
        steam_temperature=570.0,
    )

    assert steam_enthalpy == pytest.approx(0.9866, abs=1e-4)
    assert feedwater_enthalpy == pytest.approx(0.1419, abs=1e-4)
    assert steam_enthalpy - feedwater_enthalpy == pytest.approx(0.8447, abs=1e-4)


def test_style_case_study_2_best_configuration_property_spec_uses_reported_conditions() -> None:
    spec = style_case_study_2_best_configuration_property_spec(
        "utility-system-microgrid",
    )

    assert [target.steam_level for target in spec.levels] == ["HP", "MP", "LP"]
    assert [target.pressure for target in spec.levels] == pytest.approx(
        [37.8, 12.3, 2.7],
    )
    assert [target.main_temperature for target in spec.levels] == pytest.approx(
        [441.3, 285.1, 150.0],
    )
    assert spec.vhp_headers[0].vhp_header == "VHP_100"
    assert spec.vhp_headers[0].pressure == pytest.approx(100.0)
    assert spec.vhp_headers[0].temperature == pytest.approx(570.0)


def test_style_case_study_2_best_configuration_property_spec_updates_model_data() -> None:
    data = StyleModelData(
        steam_mains=("HP", "MP", "LP"),
        steam_levels=(
            SteamLevelCandidate(
                name="HP",
                steam_main="HP",
                temperature=441.3,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=1.0,
                use_enthalpy_delta=1.0,
            ),
            SteamLevelCandidate(
                name="MP",
                steam_main="MP",
                temperature=285.1,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=1.0,
                use_enthalpy_delta=1.0,
            ),
            SteamLevelCandidate(
                name="LP",
                steam_main="LP",
                temperature=150.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=1.0,
                use_enthalpy_delta=1.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_100",
                steam_enthalpy=1.0,
                feedwater_enthalpy=0.0,
                steam_flow_upper_bound=300.0,
            ),
        ),
        power_demand=40.0,
    )
    update = apply_steam_property_update(
        data,
        style_case_study_2_best_configuration_property_spec(
            "utility-system-microgrid",
        ),
        CoolPropSteamPropertyProvider(),
    )

    assert update.data.vhp_headers[0].steam_enthalpy == pytest.approx(
        0.9866,
        abs=1e-4,
    )
    assert update.data.steam_levels[0].main_steam_enthalpy == pytest.approx(
        0.9206,
        abs=1e-4,
    )
    assert update.data.steam_levels[1].main_steam_enthalpy == pytest.approx(
        0.8369,
        abs=1e-4,
    )


def test_style_case_study_2_best_configuration_property_spec_accepts_level_name_mapping() -> None:
    spec = style_case_study_2_best_configuration_property_spec(
        "hot-oil-fsr-microgrid",
        steam_level_names={"MP": "MP_295p5", "LP": "LP_150"},
        vhp_header_name="VHP_100bar",
    )

    assert [target.steam_level for target in spec.levels] == ["MP_295p5", "LP_150"]
    assert [target.pressure for target in spec.levels] == pytest.approx([20.0, 2.7])
    assert spec.vhp_headers[0].vhp_header == "VHP_100bar"


def test_style_case_study_2_best_configuration_reported_flow_model_data_is_buildable() -> None:
    data = style_case_study_2_best_configuration_reported_flow_model_data(
        "utility-system-microgrid",
    )
    model = build_static_style_model(data)

    assert data.steam_mains == ("HP", "MP", "LP")
    assert [level.name for level in data.steam_levels] == ["HP", "MP", "LP"]
    assert [level.source_heat_available for level in data.steam_levels] == (
        pytest.approx([0.0, 42.4, 153.7])
    )
    assert [level.sink_heat_demand for level in data.steam_levels] == pytest.approx(
        [104.2, 155.6, 103.9],
    )
    assert data.vhp_headers[0].name == "VHP_100"
    assert data.vhp_headers[0].steam_enthalpy == pytest.approx(0.9866, abs=1e-4)
    assert data.vhp_headers[0].steam_flow_upper_bound == pytest.approx(217.78)
    assert data.grid_export_limit == pytest.approx(10.0)
    assert list(model.STEAM_MAINS.data()) == ["HP", "MP", "LP"]


def test_style_case_study_2_best_configuration_physical_profile_model_data_uses_extracted_heat_loads() -> None:
    baseline = style_case_study_2_base_model_data(
        steam_main="MP",
        generation_enthalpy_delta=1.0,
        use_enthalpy_delta=1.0,
    )
    data = style_case_study_2_best_configuration_physical_profile_model_data(
        "utility-system-microgrid",
        steam_main="MP",
        target_steam_level=baseline.steam_levels[0].name,
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
    )
    model = build_static_style_model(data)
    reported = get_contribution2_case_study2_best_configuration(
        "utility-system-microgrid",
    )

    assert data.steam_mains == ("MP",)
    assert len(data.steam_levels) == len(baseline.steam_levels)
    assert [level.source_heat_available for level in data.steam_levels] == (
        pytest.approx([level.source_heat_available for level in baseline.steam_levels])
    )
    assert [level.sink_heat_demand for level in data.steam_levels] == pytest.approx(
        [level.sink_heat_demand for level in baseline.steam_levels],
    )
    assert sum(level.sink_heat_demand for level in data.steam_levels) != pytest.approx(
        sum(reported.process_steam_use),
    )
    assert data.steam_levels[0].main_steam_enthalpy == pytest.approx(0.8369, abs=1e-4)
    assert data.vhp_headers[0].steam_enthalpy == pytest.approx(0.9866, abs=1e-4)
    assert [boiler.name for boiler in data.boilers] == ["reported-boiler"]
    assert [hrsg.name for hrsg in data.hrsgs] == ["reported-hrsg"]
    assert [turbine.name for turbine in data.vhp_turbines] == ["reported-vhp-st"]
    assert list(model.STEAM_LEVELS.data()) == [
        level.name for level in data.steam_levels
    ]


def test_style_case_study_2_best_configuration_physical_profile_model_data_defaults_to_reported_mains() -> None:
    baseline = style_case_study_2_base_model_data(
        steam_main="HP",
        generation_enthalpy_delta=1.0,
        use_enthalpy_delta=1.0,
    )
    data = style_case_study_2_best_configuration_physical_profile_model_data(
        "utility-system-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
    )
    model = build_static_style_model(data)
    first_by_main = {
        steam_main: next(
            level for level in data.steam_levels if level.steam_main == steam_main
        )
        for steam_main in data.steam_mains
    }
    source_heat_by_main = {
        steam_main: sum(
            level.source_heat_available
            for level in data.steam_levels
            if level.steam_main == steam_main
        )
        for steam_main in data.steam_mains
    }
    sink_heat_by_main = {
        steam_main: sum(
            level.sink_heat_demand
            for level in data.steam_levels
            if level.steam_main == steam_main
        )
        for steam_main in data.steam_mains
    }

    assert data.steam_mains == ("HP", "MP", "LP")
    assert len(data.steam_levels) == 45 * 3
    assert [level.name for level in data.steam_levels[:3]] == [
        "HP_272p5",
        "HP_267p5",
        "HP_257p5",
    ]
    assert first_by_main["HP"].main_steam_enthalpy == pytest.approx(
        0.9206,
        abs=1e-4,
    )
    assert first_by_main["MP"].main_steam_enthalpy == pytest.approx(
        0.8369,
        abs=1e-4,
    )
    assert first_by_main["LP"].main_steam_enthalpy == pytest.approx(
        0.7677,
        abs=1e-4,
    )
    assert source_heat_by_main == pytest.approx(
        {
            "HP": sum(level.source_heat_available for level in baseline.steam_levels),
            "MP": 0.0,
            "LP": 0.0,
        }
    )
    assert sink_heat_by_main == pytest.approx(
        {
            "HP": sum(level.sink_heat_demand for level in baseline.steam_levels),
            "MP": 0.0,
            "LP": 0.0,
        }
    )
    assert len(model.one_level_per_main) == 3


def test_style_case_study_2_best_configuration_physical_profile_model_data_uses_enthalpy_basis_for_target_level() -> None:
    data = style_case_study_2_best_configuration_physical_profile_model_data(
        "utility-system-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
    )
    target_level = next(
        level
        for level in data.steam_levels
        if level.name == data.vhp_turbines[0].steam_level
    )

    assert target_level.generation_enthalpy_delta == pytest.approx(
        target_level.generated_steam_enthalpy
    )
    assert target_level.use_enthalpy_delta == pytest.approx(
        target_level.steam_enthalpy_for_use
    )


def test_style_case_study_2_best_configuration_physical_profile_model_data_solves_with_scipy_milp() -> None:
    data = style_case_study_2_best_configuration_physical_profile_model_data(
        "utility-system-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
    )
    scenario = StaticStyleScenario(
        case_study="case-study-2",
        scenario="utility-system-microgrid-physical-profile",
        data=data,
    )

    run = run_static_style_scenario(
        scenario,
        solve=scipy_milp_static_style_solver(options={"time_limit": 20.0}),
    )

    assert run.solver.status == "ok"
    assert run.solver.termination_condition == "optimal"
    assert run.result.utility_steam_flow == pytest.approx(206.39857548)
    assert run.result.power_generation == pytest.approx(45.57878802)
    assert run.result.total_annualized_cost == pytest.approx(57.29517192)


def test_style_case_study_2_best_configuration_physical_profile_model_data_reports_table_2_9_deltas() -> None:
    data = style_case_study_2_best_configuration_physical_profile_model_data(
        "utility-system-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="case-study-2",
            scenario="utility-system-microgrid-physical-profile",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(options={"time_limit": 20.0}),
    )
    comparison = compare_static_style_result_to_best_configuration(
        run.result,
        get_contribution2_case_study2_best_configuration("utility-system-microgrid"),
        absolute_tolerance=1e-2,
    )

    assert comparison.within_tolerance is False
    assert comparison.deviation_for("utility_steam_flow").absolute_deviation == (
        pytest.approx(11.38142452)
    )
    assert comparison.deviation_for("fuel_consumption").absolute_deviation == (
        pytest.approx(8.48362827)
    )
    assert comparison.deviation_for("gas_turbine_power").within_tolerance is True
    assert comparison.deviation_for("total_annualized_cost").absolute_deviation == (
        pytest.approx(7.56482808)
    )


def test_style_case_study_2_best_configuration_physical_profile_model_data_can_fix_reported_loads() -> None:
    data = style_case_study_2_best_configuration_physical_profile_model_data(
        "utility-system-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        fix_reported_loads=True,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="case-study-2",
            scenario="utility-system-microgrid-physical-profile",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(options={"time_limit": 20.0}),
    )
    comparison = compare_static_style_result_to_best_configuration(
        run.result,
        get_contribution2_case_study2_best_configuration("utility-system-microgrid"),
        absolute_tolerance=1e-2,
    )

    assert data.boilers[0].min_capacity == pytest.approx(
        data.boilers[0].max_capacity
    )
    assert data.boilers[0].must_select is True
    assert data.gas_turbines[0].must_select is True
    assert data.hrsgs[0].must_select is True
    assert data.vhp_turbines[0].min_capacity == pytest.approx(
        data.vhp_turbines[0].max_capacity
    )
    assert data.vhp_turbines[0].must_select is True
    assert comparison.deviation_for("utility_steam_flow").within_tolerance is True
    assert comparison.deviation_for("power_generation").within_tolerance is True
    assert comparison.deviation_for("fuel_consumption").absolute_deviation == (
        pytest.approx(3.53407029)
    )
    assert comparison.deviation_for("total_annualized_cost").absolute_deviation == (
        pytest.approx(3.33384458)
    )


def test_style_case_study_2_best_configuration_physical_profile_model_data_can_apply_reported_maintenance_and_capital() -> None:
    data = style_case_study_2_best_configuration_physical_profile_model_data(
        "utility-system-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        fix_reported_loads=True,
        reported_fixed_maintenance_cost=3.59,
        reported_capital_cost=10.78,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="case-study-2",
            scenario="utility-system-microgrid-physical-profile",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(options={"time_limit": 20.0}),
    )
    comparison = compare_static_style_result_to_best_configuration(
        run.result,
        get_contribution2_case_study2_best_configuration("utility-system-microgrid"),
        absolute_tolerance=1e-2,
    )

    assert comparison.deviation_for("maintenance_cost").within_tolerance is True
    assert comparison.deviation_for("capital_cost").within_tolerance is True
    assert comparison.deviation_for("fuel_consumption").absolute_deviation == (
        pytest.approx(3.53407029)
    )
    assert comparison.deviation_for("total_annualized_cost").absolute_deviation == (
        pytest.approx(0.05320962)
    )


def test_style_case_study_2_best_configuration_physical_profile_model_data_can_match_reported_fuel_cost_basis() -> None:
    data = style_case_study_2_best_configuration_physical_profile_model_data(
        "utility-system-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        fix_reported_loads=True,
        reported_fixed_maintenance_cost=3.59,
        reported_capital_cost=10.78,
        match_reported_fuel_cost=True,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="case-study-2",
            scenario="utility-system-microgrid-physical-profile",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(options={"time_limit": 20.0}),
    )
    comparison = compare_static_style_result_to_best_configuration(
        run.result,
        get_contribution2_case_study2_best_configuration("utility-system-microgrid"),
        absolute_tolerance=1e-2,
    )

    assert comparison.deviation_for("fuel_cost").within_tolerance is True
    assert comparison.deviation_for("fuel_consumption").absolute_deviation == (
        pytest.approx(3.53407029)
    )
    assert comparison.deviation_for("operating_cost").absolute_deviation == (
        pytest.approx(0.1138, abs=1e-4)
    )
    assert comparison.deviation_for("total_annualized_cost").absolute_deviation == (
        pytest.approx(0.1138, abs=1e-4)
    )


def test_style_case_study_2_best_configuration_physical_profile_model_data_can_apply_residual_auxiliary_cost() -> None:
    data = style_case_study_2_best_configuration_physical_profile_model_data(
        "utility-system-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        fix_reported_loads=True,
        reported_fixed_maintenance_cost=3.59,
        reported_capital_cost=10.78,
        match_reported_fuel_cost=True,
        reported_auxiliary_operating_cost=0.113799586,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="case-study-2",
            scenario="utility-system-microgrid-physical-profile",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(options={"time_limit": 20.0}),
    )
    comparison = compare_static_style_result_to_best_configuration(
        run.result,
        get_contribution2_case_study2_best_configuration("utility-system-microgrid"),
        absolute_tolerance=1e-2,
    )

    assert comparison.deviation_for("fuel_consumption").absolute_deviation == (
        pytest.approx(3.53407029)
    )
    assert comparison.deviation_for("fuel_cost").within_tolerance is True
    assert comparison.deviation_for("operating_cost").within_tolerance is True
    assert comparison.deviation_for("total_annualized_cost").within_tolerance is True


def test_style_case_study_2_best_configuration_physical_profile_model_data_can_allow_unpaid_export_for_stand_alone_fixed_loads() -> None:
    data = style_case_study_2_best_configuration_physical_profile_model_data(
        "utility-system-stand-alone",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        fix_reported_loads=True,
        allow_unpaid_power_export=True,
        reported_fixed_maintenance_cost=3.53,
        reported_capital_cost=10.38,
        match_reported_fuel_cost=True,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="case-study-2",
            scenario="utility-system-stand-alone-physical-profile",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(options={"time_limit": 20.0}),
    )
    comparison = compare_static_style_result_to_best_configuration(
        run.result,
        get_contribution2_case_study2_best_configuration("utility-system-stand-alone"),
        absolute_tolerance=1e-2,
    )

    assert data.grid_export_limit == pytest.approx(1.67)
    assert comparison.deviation_for("utility_steam_flow").within_tolerance is True
    assert comparison.deviation_for("power_generation").within_tolerance is True
    assert comparison.deviation_for("fuel_cost").within_tolerance is True
    assert comparison.deviation_for("maintenance_cost").within_tolerance is True
    assert comparison.deviation_for("capital_cost").within_tolerance is True
    assert comparison.deviation_for("fuel_consumption").absolute_deviation == (
        pytest.approx(2.76735909)
    )
    assert comparison.deviation_for("operating_cost").absolute_deviation == (
        pytest.approx(0.94311439)
    )


def test_style_case_study_2_best_configuration_physical_profile_model_data_can_include_hot_oil_and_fsr() -> None:
    data = style_case_study_2_best_configuration_physical_profile_model_data(
        "hot-oil-fsr-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        hot_oil_fuel="natural-gas",
        hot_oil_thermal_efficiency=0.85,
        include_flash_steam_recovery=True,
    )
    model = build_static_style_model(data)
    mp_level_names = {
        level.name for level in data.steam_levels if level.steam_main == "MP"
    }
    lp_level_names = {
        level.name for level in data.steam_levels if level.steam_main == "LP"
    }

    assert data.steam_mains == ("MP", "LP")
    assert data.hot_oil is not None
    assert data.hot_oil.high_temperature_heat_demand == pytest.approx(51.86)
    assert data.flash_steam_recovery is not None
    assert [route.name for route in data.flash_steam_recovery.routes] == [
        "MP-to-LP-FSR",
    ]
    assert data.flash_steam_recovery.routes[0].source_level in mp_level_names
    assert data.flash_steam_recovery.routes[0].target_level in lp_level_names
    assert list(model.FLASH_ROUTES.data()) == ["MP-to-LP-FSR"]


def test_style_case_study_2_best_configuration_physical_profile_model_data_can_calibrate_hot_oil_fsr_costs() -> None:
    benchmark = get_contribution2_case_study2_best_configuration(
        "hot-oil-fsr-microgrid",
    )
    auxiliary_cost = (
        benchmark.operating_cost
        - benchmark.fuel_cost
        - (benchmark.hot_oil_operating_cost or 0.0)
        - (benchmark.power_revenue or 0.0)
    )
    data = style_case_study_2_best_configuration_physical_profile_model_data(
        "hot-oil-fsr-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        target_steam_level="MP_75",
        fix_reported_loads=True,
        hot_oil_fuel="natural-gas",
        match_reported_hot_oil_operating_cost=True,
        include_flash_steam_recovery=True,
        match_reported_fuel_cost=True,
        reported_power_revenue=benchmark.power_revenue,
        reported_fixed_maintenance_cost=benchmark.maintenance_cost,
        reported_capital_cost=benchmark.capital_cost,
        reported_auxiliary_operating_cost=auxiliary_cost,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="case-study-2",
            scenario="hot-oil-fsr-microgrid-physical-profile",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(options={"time_limit": 20.0}),
    )
    comparison = compare_static_style_result_to_best_configuration(
        run.result,
        benchmark,
        absolute_tolerance=1e-2,
    )

    assert comparison.deviation_for("utility_steam_flow").within_tolerance is True
    assert comparison.deviation_for("power_generation").within_tolerance is True
    assert comparison.deviation_for("fuel_cost").within_tolerance is True
    assert comparison.deviation_for("hot_oil_operating_cost").within_tolerance is True
    assert comparison.deviation_for("operating_cost").within_tolerance is True
    assert comparison.deviation_for("maintenance_cost").within_tolerance is True
    assert comparison.deviation_for("capital_cost").within_tolerance is True
    assert comparison.deviation_for("total_annualized_cost").within_tolerance is True
    assert comparison.deviation_for("fuel_consumption").absolute_deviation == (
        pytest.approx(4.54048231)
    )


def test_style_case_study_2_best_configuration_physical_profile_model_data_can_calibrate_hot_oil_fsr_stand_alone_costs() -> None:
    benchmark = get_contribution2_case_study2_best_configuration(
        "hot-oil-fsr-stand-alone",
    )
    auxiliary_cost = (
        benchmark.operating_cost
        - benchmark.fuel_cost
        - (benchmark.hot_oil_operating_cost or 0.0)
        - (benchmark.power_revenue or 0.0)
    )
    data = style_case_study_2_best_configuration_physical_profile_model_data(
        "hot-oil-fsr-stand-alone",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        target_steam_level="MP_75",
        fix_reported_loads=True,
        allow_unpaid_power_export=True,
        include_auxiliary_vhp_source=True,
        hot_oil_fuel="natural-gas",
        match_reported_hot_oil_operating_cost=True,
        include_flash_steam_recovery=True,
        match_reported_fuel_cost=True,
        reported_fixed_maintenance_cost=benchmark.maintenance_cost,
        reported_capital_cost=benchmark.capital_cost,
        reported_auxiliary_operating_cost=auxiliary_cost,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="case-study-2",
            scenario="hot-oil-fsr-stand-alone-physical-profile",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(options={"time_limit": 20.0}),
    )
    comparison = compare_static_style_result_to_best_configuration(
        run.result,
        benchmark,
        absolute_tolerance=1.1e-2,
    )

    assert data.vhp_sources[0].max_capacity == pytest.approx(47.652)
    assert data.vhp_sources[0].must_select is True
    assert comparison.deviation_for("utility_steam_flow").within_tolerance is True
    assert comparison.deviation_for("power_generation").within_tolerance is True
    assert comparison.deviation_for("fuel_cost").within_tolerance is True
    assert comparison.deviation_for("hot_oil_operating_cost").within_tolerance is True
    assert comparison.deviation_for("operating_cost").within_tolerance is True
    assert comparison.deviation_for("maintenance_cost").within_tolerance is True
    assert comparison.deviation_for("capital_cost").within_tolerance is True
    assert comparison.deviation_for("total_annualized_cost").within_tolerance is True


def test_style_case_study_2_best_configuration_physical_profile_model_data_requires_fixed_loads_to_match_fuel_cost_basis() -> None:
    with pytest.raises(ValueError, match="requires fixed reported loads"):
        style_case_study_2_best_configuration_physical_profile_model_data(
            "utility-system-microgrid",
            turbine_type="industrial",
            gas_turbine_fuel="natural-gas",
            boiler_type="packaged",
            boiler_fuel="natural-gas",
            boiler_thermal_efficiency=0.85,
            steam_generation_efficiency=0.8,
            hrsg_supplementary_fuel="natural-gas",
            match_reported_fuel_cost=True,
        )


def test_style_case_study_2_best_configuration_reported_flow_model_data_accepts_level_names() -> None:
    data = style_case_study_2_best_configuration_reported_flow_model_data(
        "hot-oil-fsr-microgrid",
        steam_level_names={"MP": "MP_295p5", "LP": "LP_150"},
        vhp_header_name="VHP_100bar",
    )

    assert data.steam_mains == ("MP", "LP")
    assert [level.name for level in data.steam_levels] == ["MP_295p5", "LP_150"]
    assert data.vhp_headers[0].name == "VHP_100bar"
    assert [level.main_steam_enthalpy for level in data.steam_levels] == (
        pytest.approx([0.8371, 0.7677], abs=1e-4)
    )


def test_style_case_study_2_best_configuration_reported_flow_model_data_can_use_enthalpy_basis() -> None:
    data = style_case_study_2_best_configuration_reported_flow_model_data(
        "hot-oil-fsr-microgrid",
        generation_enthalpy_delta=None,
        use_enthalpy_delta=None,
    )

    assert [level.generation_enthalpy_delta for level in data.steam_levels] == (
        pytest.approx([level.main_steam_enthalpy for level in data.steam_levels])
    )
    assert [level.use_enthalpy_delta for level in data.steam_levels] == (
        pytest.approx([level.main_steam_enthalpy for level in data.steam_levels])
    )
    assert [level.sink_heat_demand for level in data.steam_levels] == pytest.approx(
        [
            181.21 * data.steam_levels[0].main_steam_enthalpy,
            74.87 * data.steam_levels[1].main_steam_enthalpy,
        ],
    )


def test_style_case_study_2_best_configuration_vhp_turbine_candidate_uses_reported_power() -> None:
    turbine = style_case_study_2_best_configuration_vhp_turbine_candidate(
        "utility-system-microgrid",
        name="vhp-st",
        vhp_header="VHP_100",
        steam_level="HP",
    )

    assert turbine.name == "vhp-st"
    assert turbine.vhp_header == "VHP_100"
    assert turbine.steam_level == "HP"
    assert turbine.power_slope == pytest.approx(20.88 / 217.78)
    assert turbine.power_intercept == pytest.approx(0.0)
    assert turbine.max_capacity == pytest.approx(217.78)


def test_style_case_study_2_best_configuration_boiler_candidate_uses_reported_flow() -> None:
    boiler = style_case_study_2_best_configuration_boiler_candidate(
        "utility-system-microgrid",
        name="reported-boiler",
        vhp_header="VHP_100",
        thermal_efficiency=0.85,
    )

    assert boiler.name == "reported-boiler"
    assert boiler.vhp_header == "VHP_100"
    assert boiler.max_capacity == pytest.approx(115.45)
    assert boiler.load_fuel_coefficient == pytest.approx(1.0 / 0.85)


def test_style_case_study_2_best_configuration_boiler_requires_reported_boiler_flow() -> None:
    with pytest.raises(ValueError, match="does not report a boiler flowrate"):
        style_case_study_2_best_configuration_boiler_candidate(
            "hot-oil-fsr-microgrid",
            name="reported-boiler",
            vhp_header="VHP_100",
            thermal_efficiency=0.85,
        )


def test_style_case_study_2_best_configuration_with_boiler_wires_reported_flow_data() -> None:
    data = style_case_study_2_best_configuration_reported_flow_model_data(
        "utility-system-microgrid",
    )

    connected = style_case_study_2_best_configuration_with_boiler(
        data,
        "utility-system-microgrid",
        name="reported-boiler",
        boiler_type="packaged",
        fuel="natural-gas",
        thermal_efficiency=0.85,
    )
    model = build_static_style_model(connected)

    assert connected.boilers[0].max_capacity == pytest.approx(115.45)
    assert connected.fuel_costs[-1].equipment_type == "boiler"
    assert connected.fuel_costs[-1].equipment_name == "reported-boiler"
    assert connected.equipment_costs[-1].equipment_type == "boiler"
    assert connected.equipment_costs[-1].equipment_name == "reported-boiler"
    assert list(model.BOILERS.data()) == ["reported-boiler"]


def test_style_case_study_2_best_configuration_gas_turbine_candidate_uses_reported_power() -> None:
    turbine = style_case_study_2_best_configuration_gas_turbine_candidate(
        "utility-system-microgrid",
        name="reported-gt",
        turbine_type="industrial",
        fuel="natural-gas",
    )

    assert turbine.name == "reported-gt"
    assert turbine.max_fuel_flow > 0.0
    assert (
        turbine.power_slope * turbine.max_fuel_flow - turbine.power_intercept
    ) == pytest.approx(25.79)


def test_style_case_study_2_best_configuration_hrsg_candidate_uses_reported_flow() -> None:
    steam_enthalpy, feedwater_enthalpy = style_case_study_2_vhp_enthalpies(
        steam_temperature=570.0,
    )
    turbine = style_case_study_2_best_configuration_gas_turbine_candidate(
        "utility-system-microgrid",
        name="reported-gt",
        turbine_type="industrial",
        fuel="natural-gas",
    )

    hrsg = style_case_study_2_best_configuration_hrsg_candidate(
        "utility-system-microgrid",
        name="reported-hrsg",
        gas_turbine=turbine,
        vhp_header="VHP_100",
        vhp_steam_enthalpy=steam_enthalpy,
        vhp_feedwater_enthalpy=feedwater_enthalpy,
        steam_generation_efficiency=0.8,
    )

    expected_heat_input = 102.33 * (steam_enthalpy - feedwater_enthalpy) / 0.8
    assert hrsg.name == "reported-hrsg"
    assert hrsg.gas_turbine == "reported-gt"
    assert hrsg.max_heat_input == pytest.approx(expected_heat_input)


def test_style_case_study_2_best_configuration_hrsg_candidate_sizes_supplementary_firing() -> None:
    steam_enthalpy, feedwater_enthalpy = style_case_study_2_vhp_enthalpies(
        steam_temperature=570.0,
    )
    turbine = style_case_study_2_best_configuration_gas_turbine_candidate(
        "utility-system-microgrid",
        name="reported-gt",
        turbine_type="industrial",
        fuel="natural-gas",
    )
    exhaust_only = style_case_study_2_hrsg_candidate(
        name="exhaust-only",
        gas_turbine=turbine,
        vhp_header="VHP_100",
        steam_generation_efficiency=0.8,
    )

    hrsg = style_case_study_2_best_configuration_hrsg_candidate(
        "utility-system-microgrid",
        name="reported-hrsg",
        gas_turbine=turbine,
        vhp_header="VHP_100",
        vhp_steam_enthalpy=steam_enthalpy,
        vhp_feedwater_enthalpy=feedwater_enthalpy,
        steam_generation_efficiency=0.8,
        supplementary_fuel="natural-gas",
    )

    supplementary_heat = hrsg.max_heat_input - exhaust_only.max_heat_input
    assert supplementary_heat > 0.0
    assert hrsg.supplementary_fuel_lhv > 0.0
    assert hrsg.max_supplementary_fuel_flow == pytest.approx(
        supplementary_heat / hrsg.supplementary_fuel_lhv,
    )


def test_style_case_study_2_best_configuration_hrsg_supplementary_efficiency_matches_reported_fuel() -> None:
    efficiency = (
        style_case_study_2_best_configuration_hrsg_supplementary_firing_efficiency_for_reported_fuel_consumption(
            "hot-oil-fsr-microgrid",
            turbine_type="industrial",
            gas_turbine_fuel="natural-gas",
            steam_generation_efficiency=0.8,
        )
    )

    assert efficiency == pytest.approx(1.0849, abs=1e-4)


def test_style_case_study_2_best_configuration_with_gas_turbine_hrsg_wires_reported_flow_data() -> None:
    data = style_case_study_2_best_configuration_reported_flow_model_data(
        "utility-system-microgrid",
    )

    connected = style_case_study_2_best_configuration_with_gas_turbine_hrsg(
        data,
        "utility-system-microgrid",
        gas_turbine_name="reported-gt",
        turbine_type="industrial",
        fuel="natural-gas",
        hrsg_name="reported-hrsg",
        steam_generation_efficiency=0.8,
    )
    model = build_static_style_model(connected)

    assert connected.gas_turbines[0].name == "reported-gt"
    assert connected.hrsgs[0].name == "reported-hrsg"
    assert connected.fuel_costs[-1].equipment_type == "gas_turbine"
    assert {cost.equipment_type for cost in connected.equipment_costs[-2:]} == {
        "gas_turbine",
        "hrsg",
    }
    assert list(model.GAS_TURBINES.data()) == ["reported-gt"]
    assert list(model.HRSGS.data()) == ["reported-hrsg"]


def test_style_case_study_2_best_configuration_with_vhp_turbine_wires_reported_flow_data() -> None:
    data = style_case_study_2_best_configuration_reported_flow_model_data(
        "utility-system-microgrid",
    )

    connected = style_case_study_2_best_configuration_with_vhp_turbine(
        data,
        "utility-system-microgrid",
        name="vhp-st",
        steam_level="HP",
    )
    model = build_static_style_model(connected)

    assert connected.vhp_turbines[0].max_capacity == pytest.approx(217.78)
    assert connected.vhp_turbines[0].power_slope == pytest.approx(20.88 / 217.78)
    assert connected.equipment_costs[-1].equipment_type == "vhp_turbine"
    assert connected.equipment_costs[-1].equipment_name == "vhp-st"
    assert list(model.VHP_TURBINES.data()) == ["vhp-st"]


def test_style_case_study_2_best_configuration_reported_equipment_model_data_combines_helpers() -> None:
    data = style_case_study_2_best_configuration_reported_equipment_model_data(
        "utility-system-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
    )
    model = build_static_style_model(data)

    assert data.steam_mains == ("HP", "MP", "LP")
    assert [boiler.name for boiler in data.boilers] == ["reported-boiler"]
    assert [turbine.name for turbine in data.gas_turbines] == ["reported-gt"]
    assert [hrsg.name for hrsg in data.hrsgs] == ["reported-hrsg"]
    assert [turbine.name for turbine in data.vhp_turbines] == ["reported-vhp-st"]
    assert list(model.BOILERS.data()) == ["reported-boiler"]
    assert list(model.GAS_TURBINES.data()) == ["reported-gt"]
    assert list(model.HRSGS.data()) == ["reported-hrsg"]
    assert list(model.VHP_TURBINES.data()) == ["reported-vhp-st"]


def test_style_case_study_2_best_configuration_reported_equipment_model_data_skips_absent_boiler() -> None:
    data = style_case_study_2_best_configuration_reported_equipment_model_data(
        "hot-oil-fsr-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        steam_generation_efficiency=0.8,
    )

    assert data.boilers == ()
    assert [turbine.name for turbine in data.gas_turbines] == ["reported-gt"]
    assert [hrsg.name for hrsg in data.hrsgs] == ["reported-hrsg"]


def test_style_case_study_2_best_configuration_reported_equipment_model_data_solves_enthalpy_basis() -> None:
    data = style_case_study_2_best_configuration_reported_equipment_model_data(
        "utility-system-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
    )

    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="contribution-2-case-study-2",
            scenario="utility-system-microgrid",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(),
    )

    assert run.solver.termination_condition == "optimal"
    assert run.result.utility_steam_flow > 0.0
    assert run.result.power_generation >= data.power_demand


def test_style_case_study_2_best_configuration_reported_equipment_model_data_reports_calibration_gap() -> None:
    data = style_case_study_2_best_configuration_reported_equipment_model_data(
        "utility-system-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="contribution-2-case-study-2",
            scenario="utility-system-microgrid",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(),
    )

    comparison = compare_static_style_result_to_best_configuration(
        run.result,
        get_contribution2_case_study2_best_configuration("utility-system-microgrid"),
        absolute_tolerance=1e-2,
    )

    assert comparison.within_tolerance is False
    assert comparison.deviation_for("gas_turbine_power").within_tolerance is True
    assert comparison.deviation_for("utility_steam_flow").absolute_deviation == (
        pytest.approx(10.6715, abs=1e-4)
    )
    assert comparison.deviation_for("total_annualized_cost").absolute_deviation == (
        pytest.approx(10.5993, abs=1e-4)
    )


def test_style_case_study_2_best_configuration_reported_equipment_model_data_can_fix_reported_loads() -> None:
    data = style_case_study_2_best_configuration_reported_equipment_model_data(
        "utility-system-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        fix_reported_loads=True,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="contribution-2-case-study-2",
            scenario="utility-system-microgrid",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(),
    )
    comparison = compare_static_style_result_to_best_configuration(
        run.result,
        get_contribution2_case_study2_best_configuration("utility-system-microgrid"),
        absolute_tolerance=1e-2,
    )

    assert data.boilers[0].min_capacity == pytest.approx(
        data.boilers[0].max_capacity,
    )
    assert data.boilers[0].must_select is True
    assert data.gas_turbines[0].must_select is True
    assert data.hrsgs[0].must_select is True
    assert data.vhp_turbines[0].min_capacity == pytest.approx(
        data.vhp_turbines[0].max_capacity,
    )
    assert data.vhp_turbines[0].must_select is True
    assert comparison.deviation_for("utility_steam_flow").within_tolerance is True
    assert comparison.deviation_for("power_generation").within_tolerance is True
    assert comparison.deviation_for("fuel_consumption").absolute_deviation == (
        pytest.approx(3.5341, abs=1e-4)
    )


def test_style_case_study_2_best_configuration_reported_equipment_model_data_can_allow_unpaid_export() -> None:
    data = style_case_study_2_best_configuration_reported_equipment_model_data(
        "utility-system-stand-alone",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        fix_reported_loads=True,
        allow_unpaid_power_export=True,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="contribution-2-case-study-2",
            scenario="utility-system-stand-alone",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(),
    )

    assert data.grid_export_limit == pytest.approx(1.67)
    assert run.result.power_generation == pytest.approx(41.67)


def test_style_case_study_2_best_configuration_reported_equipment_model_data_can_apply_reported_maintenance() -> None:
    data = style_case_study_2_best_configuration_reported_equipment_model_data(
        "utility-system-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        fix_reported_loads=True,
        reported_fixed_maintenance_cost=3.59,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="contribution-2-case-study-2",
            scenario="utility-system-microgrid",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(),
    )

    assert run.result.maintenance_cost == pytest.approx(3.59)
    assert run.result.total_annualized_cost == pytest.approx(61.9430, abs=1e-4)


def test_style_case_study_2_best_configuration_reported_equipment_model_data_can_match_reported_power_revenue() -> None:
    data = style_case_study_2_best_configuration_reported_equipment_model_data(
        "utility-system-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        fix_reported_loads=True,
        reported_power_revenue=-3.50,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="contribution-2-case-study-2",
            scenario="utility-system-microgrid",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(),
    )

    assert data.electricity_cost is not None
    assert data.electricity_cost.export_unit_price == pytest.approx(61.0160, abs=1e-4)
    assert run.result.operating_cost == pytest.approx(48.4470, abs=1e-4)


def test_style_case_study_2_best_configuration_reported_equipment_model_data_can_apply_auxiliary_operating_cost() -> None:
    data = style_case_study_2_best_configuration_reported_equipment_model_data(
        "utility-system-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        fix_reported_loads=True,
        reported_power_revenue=-3.50,
        reported_auxiliary_operating_cost=2.0429907911972833,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="contribution-2-case-study-2",
            scenario="utility-system-microgrid",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(),
    )

    assert run.result.operating_cost == pytest.approx(50.49, abs=1e-4)


def test_style_case_study_2_best_configuration_reported_equipment_model_data_can_match_reported_capital() -> None:
    data = style_case_study_2_best_configuration_reported_equipment_model_data(
        "utility-system-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        fix_reported_loads=True,
        reported_capital_cost=10.78,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="contribution-2-case-study-2",
            scenario="utility-system-microgrid",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(),
    )

    assert run.result.capital_cost == pytest.approx(10.78, abs=1e-4)


def test_style_case_study_2_best_configuration_reported_equipment_model_data_matches_reported_economics() -> None:
    data = style_case_study_2_best_configuration_reported_equipment_model_data(
        "utility-system-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_thermal_efficiency=0.85,
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        fix_reported_loads=True,
        reported_fixed_maintenance_cost=3.59,
        reported_power_revenue=-3.50,
        reported_auxiliary_operating_cost=2.0429907911972833,
        reported_capital_cost=10.78,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="contribution-2-case-study-2",
            scenario="utility-system-microgrid",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(),
    )
    comparison = compare_static_style_result_to_best_configuration(
        run.result,
        get_contribution2_case_study2_best_configuration("utility-system-microgrid"),
        absolute_tolerance=1e-2,
    )

    assert comparison.deviation_for("utility_steam_flow").within_tolerance is True
    assert comparison.deviation_for("power_generation").within_tolerance is True
    assert comparison.deviation_for("operating_cost").within_tolerance is True
    assert comparison.deviation_for("maintenance_cost").within_tolerance is True
    assert comparison.deviation_for("capital_cost").within_tolerance is True
    assert comparison.deviation_for("total_annualized_cost").within_tolerance is True
    assert comparison.deviation_for("fuel_consumption").absolute_deviation == (
        pytest.approx(3.5341, abs=1e-4)
    )


def test_style_case_study_2_best_configuration_hot_oil_config_uses_reported_load() -> None:
    config = style_case_study_2_best_configuration_hot_oil_config(
        "hot-oil-fsr-microgrid",
        fuel="natural-gas",
        thermal_efficiency=0.85,
    )

    assert config.fuel_unit_cost == pytest.approx(24.30)
    assert config.thermal_efficiency == pytest.approx(0.85)
    assert config.high_temperature_heat_demand == pytest.approx(51.86)


def test_style_case_study_2_best_configuration_hot_oil_efficiency_matches_reported_cost() -> None:
    efficiency = (
        style_case_study_2_best_configuration_hot_oil_thermal_efficiency_for_reported_operating_cost(
            "hot-oil-fsr-microgrid",
            fuel="natural-gas",
        )
    )

    assert efficiency == pytest.approx(0.7848, abs=1e-4)


def test_style_case_study_2_best_configuration_hot_oil_config_requires_reported_load() -> None:
    with pytest.raises(ValueError, match="does not report a hot-oil system load"):
        style_case_study_2_best_configuration_hot_oil_config(
            "utility-system-microgrid",
            fuel="natural-gas",
            thermal_efficiency=0.85,
        )


def test_style_case_study_2_best_configuration_reported_equipment_model_data_can_include_hot_oil() -> None:
    data = style_case_study_2_best_configuration_reported_equipment_model_data(
        "hot-oil-fsr-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        hot_oil_fuel="natural-gas",
        hot_oil_thermal_efficiency=0.85,
    )
    model = build_static_style_model(data)

    assert data.hot_oil is not None
    assert data.hot_oil.high_temperature_heat_demand == pytest.approx(51.86)
    assert model.hot_oil_high_temperature_heat_demand.value == pytest.approx(51.86)


def test_style_case_study_2_best_configuration_flash_steam_recovery_config_uses_reported_flash() -> None:
    data = style_case_study_2_best_configuration_reported_flow_model_data(
        "hot-oil-fsr-microgrid",
    )

    config = style_case_study_2_best_configuration_flash_steam_recovery_config(
        data,
        "hot-oil-fsr-microgrid",
    )

    assert [level.steam_level for level in config.levels] == ["MP", "LP"]
    assert [route.name for route in config.routes] == ["MP-to-LP-FSR"]
    assert config.routes[0].source_level == "MP"
    assert config.routes[0].target_level == "LP"
    assert config.routes[0].max_flow == pytest.approx(177.7383, abs=1e-4)
    assert config.condensate_return_fraction == pytest.approx(0.9808, abs=1e-4)


def test_style_case_study_2_best_configuration_flash_steam_recovery_config_accepts_level_names() -> None:
    data = style_case_study_2_best_configuration_reported_flow_model_data(
        "hot-oil-fsr-microgrid",
        steam_level_names={"MP": "MP_295p5", "LP": "LP_150"},
    )

    config = style_case_study_2_best_configuration_flash_steam_recovery_config(
        data,
        "hot-oil-fsr-microgrid",
    )

    assert [level.steam_level for level in config.levels] == ["MP_295p5", "LP_150"]
    assert config.routes[0].source_level == "MP_295p5"
    assert config.routes[0].target_level == "LP_150"


def test_style_case_study_2_best_configuration_reported_equipment_model_data_can_include_fsr() -> None:
    data = style_case_study_2_best_configuration_reported_equipment_model_data(
        "hot-oil-fsr-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        include_flash_steam_recovery=True,
    )
    model = build_static_style_model(data)

    assert data.flash_steam_recovery is not None
    assert [route.name for route in data.flash_steam_recovery.routes] == [
        "MP-to-LP-FSR",
    ]
    assert list(model.FLASH_ROUTES.data()) == ["MP-to-LP-FSR"]


def test_style_case_study_2_best_configuration_reported_equipment_model_data_fixed_loads_force_reported_units_with_hot_oil_and_fsr() -> None:
    data = style_case_study_2_best_configuration_reported_equipment_model_data(
        "hot-oil-fsr-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        hot_oil_fuel="natural-gas",
        hot_oil_thermal_efficiency=0.85,
        include_flash_steam_recovery=True,
        fix_reported_loads=True,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="contribution-2-case-study-2",
            scenario="hot-oil-fsr-microgrid",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(),
    )

    assert run.result.utility_steam_flow == pytest.approx(136.67)
    assert run.result.power_generation == pytest.approx(46.67)


def test_style_case_study_2_best_configuration_reported_equipment_model_data_can_match_hot_oil_fsr_fuel_consumption() -> None:
    data = style_case_study_2_best_configuration_reported_equipment_model_data(
        "hot-oil-fsr-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        hot_oil_fuel="natural-gas",
        hot_oil_thermal_efficiency=0.85,
        include_flash_steam_recovery=True,
        fix_reported_loads=True,
        match_reported_fuel_consumption=True,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="contribution-2-case-study-2",
            scenario="hot-oil-fsr-microgrid",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(),
    )
    comparison = compare_static_style_result_to_best_configuration(
        run.result,
        get_contribution2_case_study2_best_configuration("hot-oil-fsr-microgrid"),
        absolute_tolerance=1e-2,
    )

    assert comparison.deviation_for("utility_steam_flow").within_tolerance is True
    assert comparison.deviation_for("power_generation").within_tolerance is True
    assert comparison.deviation_for("fuel_consumption").within_tolerance is True


def test_style_case_study_2_best_configuration_reported_equipment_model_data_can_match_hot_oil_operating_cost() -> None:
    data = style_case_study_2_best_configuration_reported_equipment_model_data(
        "hot-oil-fsr-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        hot_oil_fuel="natural-gas",
        hot_oil_thermal_efficiency=0.85,
        match_reported_hot_oil_operating_cost=True,
        include_flash_steam_recovery=True,
        fix_reported_loads=True,
        match_reported_fuel_consumption=True,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="contribution-2-case-study-2",
            scenario="hot-oil-fsr-microgrid",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(),
    )
    comparison = compare_static_style_result_to_best_configuration(
        run.result,
        get_contribution2_case_study2_best_configuration("hot-oil-fsr-microgrid"),
        absolute_tolerance=1e-2,
    )

    assert comparison.deviation_for("hot_oil_operating_cost").within_tolerance is True
    assert comparison.deviation_for("fuel_consumption").within_tolerance is True


def test_style_case_study_2_best_configuration_reported_equipment_model_data_can_match_hot_oil_fsr_microgrid_economics() -> None:
    data = style_case_study_2_best_configuration_reported_equipment_model_data(
        "hot-oil-fsr-microgrid",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        hot_oil_fuel="natural-gas",
        include_flash_steam_recovery=True,
        fix_reported_loads=True,
        match_reported_economics=True,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="contribution-2-case-study-2",
            scenario="hot-oil-fsr-microgrid",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(),
    )
    comparison = compare_static_style_result_to_best_configuration(
        run.result,
        get_contribution2_case_study2_best_configuration("hot-oil-fsr-microgrid"),
        absolute_tolerance=1e-2,
    )

    assert comparison.within_tolerance is True


def test_style_case_study_2_best_configuration_reported_equipment_model_data_auxiliary_source_solves_hot_oil_fsr_stand_alone() -> None:
    data = style_case_study_2_best_configuration_reported_equipment_model_data(
        "hot-oil-fsr-stand-alone",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        hot_oil_fuel="natural-gas",
        hot_oil_thermal_efficiency=0.85,
        include_flash_steam_recovery=True,
        include_auxiliary_vhp_source=True,
        fix_reported_loads=True,
        allow_unpaid_power_export=True,
        match_reported_fuel_consumption=True,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="contribution-2-case-study-2",
            scenario="hot-oil-fsr-stand-alone",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(),
    )

    assert data.vhp_sources[0].max_capacity == pytest.approx(47.652)
    assert data.vhp_sources[0].must_select is True
    assert run.solver.termination_condition == "optimal"
    assert run.result.utility_steam_flow == pytest.approx(137.09, abs=1e-4)
    assert run.result.fuel_consumption == pytest.approx(121.96, abs=1e-4)
    assert run.result.power_generation == pytest.approx(41.67, abs=1e-4)


def test_style_case_study_2_best_configuration_reported_equipment_model_data_can_match_hot_oil_fsr_stand_alone_economics() -> None:
    data = style_case_study_2_best_configuration_reported_equipment_model_data(
        "hot-oil-fsr-stand-alone",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        steam_generation_efficiency=0.8,
        hrsg_supplementary_fuel="natural-gas",
        hot_oil_fuel="natural-gas",
        include_flash_steam_recovery=True,
        include_auxiliary_vhp_source=True,
        fix_reported_loads=True,
        allow_unpaid_power_export=True,
        match_reported_economics=True,
    )
    run = run_static_style_scenario(
        StaticStyleScenario(
            case_study="contribution-2-case-study-2",
            scenario="hot-oil-fsr-stand-alone",
            data=data,
        ),
        solve=scipy_milp_static_style_solver(),
    )
    comparison = compare_static_style_result_to_best_configuration(
        run.result,
        get_contribution2_case_study2_best_configuration("hot-oil-fsr-stand-alone"),
        absolute_tolerance=1.1e-2,
    )

    assert comparison.within_tolerance is True


def test_style_case_study_2_best_configuration_inter_main_letdown_candidates_use_reported_balance() -> None:
    data = style_case_study_2_best_configuration_reported_flow_model_data(
        "utility-system-microgrid",
    )

    letdowns = style_case_study_2_best_configuration_inter_main_letdown_candidates(
        data,
        "utility-system-microgrid",
    )

    assert [letdown.name for letdown in letdowns] == [
        "HP-to-MP-LD",
        "MP-to-LP-LD",
    ]
    assert [letdown.source_level for letdown in letdowns] == ["HP", "MP"]
    assert [letdown.target_level for letdown in letdowns] == ["MP", "LP"]
    assert [letdown.max_flow for letdown in letdowns] == pytest.approx(
        [113.58, 0.38],
    )


def test_style_case_study_2_best_configuration_inter_main_letdown_candidates_accept_level_names() -> None:
    data = style_case_study_2_best_configuration_reported_flow_model_data(
        "hot-oil-fsr-microgrid",
        steam_level_names={"MP": "MP_295p5", "LP": "LP_150"},
    )

    letdowns = style_case_study_2_best_configuration_inter_main_letdown_candidates(
        data,
        "hot-oil-fsr-microgrid",
    )

    assert [letdown.name for letdown in letdowns] == ["MP-to-LP-LD"]
    assert letdowns[0].source_level == "MP_295p5"
    assert letdowns[0].target_level == "LP_150"
    assert letdowns[0].max_flow == pytest.approx(55.86)


def test_style_case_study_2_best_configuration_with_inter_main_letdowns_wires_reported_flow_data() -> None:
    data = style_case_study_2_best_configuration_reported_flow_model_data(
        "utility-system-microgrid",
    )

    connected = style_case_study_2_best_configuration_with_inter_main_letdowns(
        data,
        "utility-system-microgrid",
    )
    model = build_static_style_model(connected)

    assert [letdown.name for letdown in connected.steam_main_letdowns] == [
        "HP-to-MP-LD",
        "MP-to-LP-LD",
    ]
    assert list(model.STEAM_MAIN_LETDOWNS.data()) == [
        "HP-to-MP-LD",
        "MP-to-LP-LD",
    ]


def test_style_case_study_2_gas_turbine_hrsg_scenario_data_is_buildable() -> None:
    data = style_case_study_2_gas_turbine_hrsg_scenario_data(
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        fuel="natural-gas",
        max_power_generation=40.0,
        vhp_header_name="VHP_100",
        vhp_steam_enthalpy=5.0,
        vhp_feedwater_enthalpy=1.0,
        steam_generation_efficiency=0.8,
    )
    model = build_static_style_model(data)

    assert data.vhp_headers[0].name == "VHP_100"
    assert data.vhp_headers[0].steam_flow_upper_bound == pytest.approx(
        data.hrsgs[0].max_heat_input * 0.8 / 4.0,
    )
    assert data.hrsgs[0].name == "hrsg-gt-industrial"
    assert data.hrsgs[0].gas_turbine == "gt-industrial"
    assert len(data.equipment_costs) == 2
    assert data.equipment_costs[1].equipment_type == "hrsg"
    assert data.equipment_costs[1].equipment_name == "hrsg-gt-industrial"
    assert list(model.GAS_TURBINES.data()) == ["gt-industrial"]
    assert list(model.HRSGS.data()) == ["hrsg-gt-industrial"]
    assert list(model.VHP_HEADERS.data()) == ["VHP_100"]


def test_style_case_study_2_boiler_gas_turbine_hrsg_scenario_data_is_buildable() -> None:
    data = style_case_study_2_boiler_gas_turbine_hrsg_scenario_data(
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        max_power_generation=40.0,
        vhp_header_name="VHP_100",
        vhp_steam_enthalpy=5.0,
        vhp_feedwater_enthalpy=1.0,
        steam_generation_efficiency=0.8,
        boiler_name="boiler-packaged",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_max_steam_generation=200.0,
        boiler_thermal_efficiency=0.85,
    )
    model = build_static_style_model(data)

    assert list(model.BOILERS.data()) == ["boiler-packaged"]
    assert list(model.GAS_TURBINES.data()) == ["gt-industrial"]
    assert list(model.HRSGS.data()) == ["hrsg-gt-industrial"]
    assert data.vhp_headers[0].steam_flow_upper_bound > 200.0
    assert {cost.equipment_type for cost in data.fuel_costs} == {
        "boiler",
        "gas_turbine",
    }
    assert {cost.equipment_type for cost in data.equipment_costs} == {
        "boiler",
        "gas_turbine",
        "hrsg",
    }
    boiler_cost = next(
        cost for cost in data.equipment_costs if cost.equipment_type == "boiler"
    )
    assert boiler_cost.variable_capital_cost == pytest.approx(46432.32)


def test_style_case_study_2_vhp_letdown_candidate_uses_vhp_flow_bound() -> None:
    letdown = style_case_study_2_vhp_letdown_candidate(
        name="vhp-to-mp",
        vhp_header="VHP_100",
        steam_level="MP_292p5",
        max_flow=250.0,
    )

    assert letdown.name == "vhp-to-mp"
    assert letdown.vhp_header == "VHP_100"
    assert letdown.steam_level == "MP_292p5"
    assert letdown.max_flow == pytest.approx(250.0)


def test_style_case_study_2_vhp_back_pressure_turbine_candidate_is_explicit() -> None:
    turbine = style_case_study_2_vhp_back_pressure_turbine_candidate(
        name="vhp-to-mp-st",
        vhp_header="VHP_100",
        steam_level="MP_292p5",
        power_slope=20.88 / 239.86,
        power_intercept=0.0,
        max_flow=250.0,
        minimum_load_fraction=0.25,
    )

    assert turbine.name == "vhp-to-mp-st"
    assert turbine.vhp_header == "VHP_100"
    assert turbine.steam_level == "MP_292p5"
    assert turbine.power_slope == pytest.approx(20.88 / 239.86)
    assert turbine.power_intercept == pytest.approx(0.0)
    assert turbine.min_capacity == pytest.approx(0.0)
    assert turbine.max_capacity == pytest.approx(250.0)
    assert turbine.minimum_load_fraction == pytest.approx(0.25)


def test_style_case_study_2_vhp_turbine_equipment_cost_uses_design_power() -> None:
    turbine = style_case_study_2_vhp_back_pressure_turbine_candidate(
        name="vhp-to-mp-st",
        vhp_header="VHP_100",
        steam_level="MP_292p5",
        power_slope=20.88 / 239.86,
        power_intercept=0.0,
        max_flow=239.86,
    )

    cost = style_case_study_2_vhp_turbine_equipment_cost_input(turbine=turbine)

    assert cost.name == "vhp-to-mp-st-capital"
    assert cost.equipment_type == "vhp_turbine"
    assert cost.equipment_name == "vhp-to-mp-st"
    assert cost.variable_capital_cost == pytest.approx(345101.63)
    assert cost.fixed_capital_cost == pytest.approx(44057.43)


def test_style_case_study_2_with_vhp_letdown_wires_generation_to_header() -> None:
    data = style_case_study_2_boiler_gas_turbine_hrsg_scenario_data(
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        max_power_generation=40.0,
        vhp_header_name="VHP_100",
        vhp_steam_enthalpy=5.0,
        vhp_feedwater_enthalpy=1.0,
        steam_generation_efficiency=0.8,
        boiler_name="boiler-packaged",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_max_steam_generation=200.0,
        boiler_thermal_efficiency=0.85,
    )
    target_level = data.steam_levels[0].name
    connected = style_case_study_2_with_vhp_letdown(
        data,
        name="vhp-to-first-mp",
        steam_level=target_level,
    )
    model = build_static_style_model(connected)

    assert connected.vhp_letdowns[0].vhp_header == "VHP_100"
    assert connected.vhp_letdowns[0].steam_level == target_level
    assert connected.vhp_letdowns[0].max_flow == pytest.approx(
        connected.vhp_headers[0].steam_flow_upper_bound,
    )
    assert list(model.VHP_LETDOWNS.data()) == ["vhp-to-first-mp"]


def test_style_case_study_2_with_vhp_back_pressure_turbine_wires_generation_to_header() -> None:
    data = style_case_study_2_boiler_gas_turbine_hrsg_scenario_data(
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        max_power_generation=40.0,
        vhp_header_name="VHP_100",
        vhp_steam_enthalpy=5.0,
        vhp_feedwater_enthalpy=1.0,
        steam_generation_efficiency=0.8,
        boiler_name="boiler-packaged",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_max_steam_generation=200.0,
        boiler_thermal_efficiency=0.85,
    )
    target_level = data.steam_levels[0].name
    connected = style_case_study_2_with_vhp_back_pressure_turbine(
        data,
        name="vhp-to-first-mp-st",
        steam_level=target_level,
        power_slope=20.88 / 239.86,
        power_intercept=0.0,
    )
    model = build_static_style_model(connected)

    assert connected.vhp_turbines[0].vhp_header == "VHP_100"
    assert connected.vhp_turbines[0].steam_level == target_level
    assert connected.vhp_turbines[0].max_capacity == pytest.approx(
        connected.vhp_headers[0].steam_flow_upper_bound,
    )
    assert connected.equipment_costs[-1].equipment_type == "vhp_turbine"
    assert connected.equipment_costs[-1].equipment_name == "vhp-to-first-mp-st"
    assert list(model.VHP_TURBINES.data()) == ["vhp-to-first-mp-st"]


def test_style_case_study_2_complete_static_scenario_catalog_is_buildable() -> None:
    base_data = style_case_study_2_boiler_gas_turbine_hrsg_scenario_data(
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        max_power_generation=40.0,
        vhp_header_name="VHP_100",
        vhp_steam_enthalpy=5.0,
        vhp_feedwater_enthalpy=1.0,
        steam_generation_efficiency=0.8,
        boiler_name="boiler-packaged",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_max_steam_generation=200.0,
        boiler_thermal_efficiency=0.85,
    )
    catalog = style_case_study_2_complete_static_scenario_catalog(
        scenario="proposed-without-hot-oil",
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        max_power_generation=40.0,
        vhp_header_name="VHP_100",
        vhp_steam_enthalpy=5.0,
        vhp_feedwater_enthalpy=1.0,
        steam_generation_efficiency=0.8,
        boiler_name="boiler-packaged",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_max_steam_generation=200.0,
        boiler_thermal_efficiency=0.85,
        target_steam_level=base_data.steam_levels[0].name,
    )
    assembled = catalog.get("case-study-2", "proposed-without-hot-oil")
    model = build_static_style_model(assembled.data)

    assert assembled.benchmark is not None
    assert assembled.benchmark.total_annualized_cost == pytest.approx(64.77)
    assert len(assembled.data.boilers) == 1
    assert len(assembled.data.gas_turbines) == 1
    assert len(assembled.data.hrsgs) == 1
    assert len(assembled.data.vhp_letdowns) == 1
    assert list(model.VHP_LETDOWNS.data()) == ["vhp-to-mp"]


def test_style_case_study_2_complete_static_scenario_catalog_can_include_vhp_turbine() -> None:
    base_data = style_case_study_2_boiler_gas_turbine_hrsg_scenario_data(
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        max_power_generation=40.0,
        vhp_header_name="VHP_100",
        vhp_steam_enthalpy=5.0,
        vhp_feedwater_enthalpy=1.0,
        steam_generation_efficiency=0.8,
        boiler_name="boiler-packaged",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_max_steam_generation=200.0,
        boiler_thermal_efficiency=0.85,
    )
    catalog = style_case_study_2_complete_static_scenario_catalog(
        scenario="proposed-without-hot-oil",
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        max_power_generation=40.0,
        vhp_header_name="VHP_100",
        vhp_steam_enthalpy=5.0,
        vhp_feedwater_enthalpy=1.0,
        steam_generation_efficiency=0.8,
        boiler_name="boiler-packaged",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_max_steam_generation=200.0,
        boiler_thermal_efficiency=0.85,
        target_steam_level=base_data.steam_levels[0].name,
        vhp_turbine_name="vhp-to-mp-st",
        vhp_turbine_power_slope=20.88 / 239.86,
        vhp_turbine_power_intercept=0.0,
    )
    assembled = catalog.get("case-study-2", "proposed-without-hot-oil")
    model = build_static_style_model(assembled.data)

    assert len(assembled.data.vhp_turbines) == 1
    assert assembled.data.vhp_turbines[0].name == "vhp-to-mp-st"
    assert assembled.data.equipment_costs[-1].equipment_type == "vhp_turbine"
    assert list(model.VHP_TURBINES.data()) == ["vhp-to-mp-st"]


def test_style_case_study_2_complete_static_scenario_runs_with_scipy_milp() -> None:
    vhp_steam_enthalpy, vhp_feedwater_enthalpy = style_case_study_2_vhp_enthalpies(
        steam_temperature=570.0,
    )
    base_data = style_case_study_2_boiler_gas_turbine_hrsg_scenario_data(
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        max_power_generation=40.0,
        vhp_header_name="VHP_100",
        vhp_steam_enthalpy=vhp_steam_enthalpy,
        vhp_feedwater_enthalpy=vhp_feedwater_enthalpy,
        steam_generation_efficiency=0.8,
        boiler_name="boiler-packaged",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_max_steam_generation=200.0,
        boiler_thermal_efficiency=0.85,
    )
    catalog = style_case_study_2_complete_static_scenario_catalog(
        scenario="proposed-without-hot-oil",
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        max_power_generation=40.0,
        vhp_header_name="VHP_100",
        vhp_steam_enthalpy=vhp_steam_enthalpy,
        vhp_feedwater_enthalpy=vhp_feedwater_enthalpy,
        steam_generation_efficiency=0.8,
        boiler_name="boiler-packaged",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_max_steam_generation=200.0,
        boiler_thermal_efficiency=0.85,
        target_steam_level=base_data.steam_levels[0].name,
        vhp_turbine_name="vhp-to-mp-st",
        vhp_turbine_power_slope=20.88 / 239.86,
        vhp_turbine_power_intercept=0.0,
    )
    scenario = catalog.get("case-study-2", "proposed-without-hot-oil")

    run = run_static_style_scenario(
        scenario,
        solve=scipy_milp_static_style_solver(options={"time_limit": 20.0}),
    )

    assert run.solver.status == "ok"
    assert run.solver.termination_condition == "optimal"
    assert run.comparison is not None
    assert run.result.utility_steam_flow > 0.0
    assert run.result.total_annualized_cost > 0.0


def test_style_case_study_2_complete_static_scenario_can_match_benchmark_power_generation() -> None:
    vhp_steam_enthalpy, vhp_feedwater_enthalpy = style_case_study_2_vhp_enthalpies(
        steam_temperature=570.0,
    )
    base_data = style_case_study_2_boiler_gas_turbine_hrsg_scenario_data(
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        max_power_generation=40.0,
        vhp_header_name="VHP_100",
        vhp_steam_enthalpy=vhp_steam_enthalpy,
        vhp_feedwater_enthalpy=vhp_feedwater_enthalpy,
        steam_generation_efficiency=0.8,
        boiler_name="boiler-packaged",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_max_steam_generation=200.0,
        boiler_thermal_efficiency=0.85,
    )
    catalog = style_case_study_2_complete_static_scenario_catalog(
        scenario="proposed-without-hot-oil",
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        max_power_generation=40.0,
        vhp_header_name="VHP_100",
        vhp_steam_enthalpy=vhp_steam_enthalpy,
        vhp_feedwater_enthalpy=vhp_feedwater_enthalpy,
        steam_generation_efficiency=0.8,
        boiler_name="boiler-packaged",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_max_steam_generation=200.0,
        boiler_thermal_efficiency=0.85,
        target_steam_level=base_data.steam_levels[0].name,
        vhp_turbine_name="vhp-to-mp-st",
        vhp_turbine_power_slope=20.88 / 239.86,
        vhp_turbine_power_intercept=0.0,
        match_benchmark_power_generation=True,
    )
    scenario = catalog.get("case-study-2", "proposed-without-hot-oil")

    run = run_static_style_scenario(
        scenario,
        solve=scipy_milp_static_style_solver(options={"time_limit": 20.0}),
    )

    assert run.comparison is not None
    assert run.comparison.deviation_for("power_generation").within_tolerance is True
    assert run.comparison.deviation_for("fuel_consumption").within_tolerance is False


def test_style_case_study_2_complete_static_scenario_can_match_benchmark_maintenance_cost() -> None:
    vhp_steam_enthalpy, vhp_feedwater_enthalpy = style_case_study_2_vhp_enthalpies(
        steam_temperature=570.0,
    )
    base_data = style_case_study_2_boiler_gas_turbine_hrsg_scenario_data(
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        max_power_generation=40.0,
        vhp_header_name="VHP_100",
        vhp_steam_enthalpy=vhp_steam_enthalpy,
        vhp_feedwater_enthalpy=vhp_feedwater_enthalpy,
        steam_generation_efficiency=0.8,
        boiler_name="boiler-packaged",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_max_steam_generation=200.0,
        boiler_thermal_efficiency=0.85,
    )
    catalog = style_case_study_2_complete_static_scenario_catalog(
        scenario="proposed-without-hot-oil",
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        max_power_generation=40.0,
        vhp_header_name="VHP_100",
        vhp_steam_enthalpy=vhp_steam_enthalpy,
        vhp_feedwater_enthalpy=vhp_feedwater_enthalpy,
        steam_generation_efficiency=0.8,
        boiler_name="boiler-packaged",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_max_steam_generation=200.0,
        boiler_thermal_efficiency=0.85,
        target_steam_level=base_data.steam_levels[0].name,
        vhp_turbine_name="vhp-to-mp-st",
        vhp_turbine_power_slope=20.88 / 239.86,
        vhp_turbine_power_intercept=0.0,
        match_benchmark_maintenance_cost=True,
    )
    scenario = catalog.get("case-study-2", "proposed-without-hot-oil")

    run = run_static_style_scenario(
        scenario,
        solve=scipy_milp_static_style_solver(options={"time_limit": 20.0}),
    )

    assert run.comparison is not None
    assert run.comparison.deviation_for("maintenance_cost").within_tolerance is True
    assert run.comparison.deviation_for("fuel_consumption").within_tolerance is False


def test_style_case_study_2_complete_static_scenario_can_match_benchmark_capital_cost() -> None:
    vhp_steam_enthalpy, vhp_feedwater_enthalpy = style_case_study_2_vhp_enthalpies(
        steam_temperature=570.0,
    )
    base_data = style_case_study_2_boiler_gas_turbine_hrsg_scenario_data(
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        max_power_generation=40.0,
        vhp_header_name="VHP_100",
        vhp_steam_enthalpy=vhp_steam_enthalpy,
        vhp_feedwater_enthalpy=vhp_feedwater_enthalpy,
        steam_generation_efficiency=0.8,
        boiler_name="boiler-packaged",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_max_steam_generation=200.0,
        boiler_thermal_efficiency=0.85,
    )
    catalog = style_case_study_2_complete_static_scenario_catalog(
        scenario="proposed-without-hot-oil",
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        max_power_generation=40.0,
        vhp_header_name="VHP_100",
        vhp_steam_enthalpy=vhp_steam_enthalpy,
        vhp_feedwater_enthalpy=vhp_feedwater_enthalpy,
        steam_generation_efficiency=0.8,
        boiler_name="boiler-packaged",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_max_steam_generation=200.0,
        boiler_thermal_efficiency=0.85,
        target_steam_level=base_data.steam_levels[0].name,
        vhp_turbine_name="vhp-to-mp-st",
        vhp_turbine_power_slope=20.88 / 239.86,
        vhp_turbine_power_intercept=0.0,
        match_benchmark_capital_cost=True,
    )
    scenario = catalog.get("case-study-2", "proposed-without-hot-oil")

    run = run_static_style_scenario(
        scenario,
        solve=scipy_milp_static_style_solver(options={"time_limit": 20.0}),
    )

    assert run.comparison is not None
    assert run.comparison.deviation_for("capital_cost").within_tolerance is True
    assert run.comparison.deviation_for("fuel_consumption").within_tolerance is False


def test_style_case_study_2_complete_static_scenario_can_apply_operating_cost_adjustment() -> None:
    vhp_steam_enthalpy, vhp_feedwater_enthalpy = style_case_study_2_vhp_enthalpies(
        steam_temperature=570.0,
    )
    base_data = style_case_study_2_boiler_gas_turbine_hrsg_scenario_data(
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        max_power_generation=40.0,
        vhp_header_name="VHP_100",
        vhp_steam_enthalpy=vhp_steam_enthalpy,
        vhp_feedwater_enthalpy=vhp_feedwater_enthalpy,
        steam_generation_efficiency=0.8,
        boiler_name="boiler-packaged",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_max_steam_generation=200.0,
        boiler_thermal_efficiency=0.85,
    )
    catalog_kwargs = {
        "scenario": "proposed-without-hot-oil",
        "steam_main": "MP",
        "generation_enthalpy_delta": 2.0,
        "use_enthalpy_delta": 1.0,
        "gas_turbine_name": "gt-industrial",
        "turbine_type": "industrial",
        "gas_turbine_fuel": "natural-gas",
        "max_power_generation": 40.0,
        "vhp_header_name": "VHP_100",
        "vhp_steam_enthalpy": vhp_steam_enthalpy,
        "vhp_feedwater_enthalpy": vhp_feedwater_enthalpy,
        "steam_generation_efficiency": 0.8,
        "boiler_name": "boiler-packaged",
        "boiler_type": "packaged",
        "boiler_fuel": "natural-gas",
        "boiler_max_steam_generation": 200.0,
        "boiler_thermal_efficiency": 0.85,
        "target_steam_level": base_data.steam_levels[0].name,
        "vhp_turbine_name": "vhp-to-mp-st",
        "vhp_turbine_power_slope": 20.88 / 239.86,
        "vhp_turbine_power_intercept": 0.0,
        "match_benchmark_power_generation": True,
        "match_benchmark_maintenance_cost": True,
        "match_benchmark_capital_cost": True,
    }
    baseline_catalog = style_case_study_2_complete_static_scenario_catalog(
        **catalog_kwargs,
    )
    baseline_scenario = baseline_catalog.get("case-study-2", "proposed-without-hot-oil")
    baseline_run = run_static_style_scenario(
        baseline_scenario,
        solve=scipy_milp_static_style_solver(options={"time_limit": 20.0}),
    )
    benchmark = baseline_scenario.benchmark
    assert benchmark is not None
    operating_adjustment = benchmark.operating_cost - baseline_run.result.operating_cost

    targeted_catalog = style_case_study_2_complete_static_scenario_catalog(
        **catalog_kwargs,
        operating_cost_adjustments={
            "auxiliary_or_unallocated": operating_adjustment,
        },
    )
    targeted_scenario = targeted_catalog.get("case-study-2", "proposed-without-hot-oil")
    targeted_run = run_static_style_scenario(
        targeted_scenario,
        solve=scipy_milp_static_style_solver(options={"time_limit": 20.0}),
    )

    assert targeted_run.comparison is not None
    assert (
        targeted_run.comparison.deviation_for("operating_cost").within_tolerance
        is True
    )
    assert (
        targeted_run.comparison.deviation_for("total_annualized_cost").within_tolerance
        is True
    )
    assert (
        targeted_run.comparison.deviation_for("fuel_consumption").within_tolerance
        is False
    )


def test_style_case_study_2_complete_static_scenario_can_apply_utility_steam_flow_adjustment() -> None:
    vhp_steam_enthalpy, vhp_feedwater_enthalpy = style_case_study_2_vhp_enthalpies(
        steam_temperature=570.0,
    )
    base_data = style_case_study_2_boiler_gas_turbine_hrsg_scenario_data(
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        max_power_generation=40.0,
        vhp_header_name="VHP_100",
        vhp_steam_enthalpy=vhp_steam_enthalpy,
        vhp_feedwater_enthalpy=vhp_feedwater_enthalpy,
        steam_generation_efficiency=0.8,
        boiler_name="boiler-packaged",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_max_steam_generation=200.0,
        boiler_thermal_efficiency=0.85,
    )
    catalog_kwargs = {
        "scenario": "proposed-without-hot-oil",
        "steam_main": "MP",
        "generation_enthalpy_delta": 2.0,
        "use_enthalpy_delta": 1.0,
        "gas_turbine_name": "gt-industrial",
        "turbine_type": "industrial",
        "gas_turbine_fuel": "natural-gas",
        "max_power_generation": 40.0,
        "vhp_header_name": "VHP_100",
        "vhp_steam_enthalpy": vhp_steam_enthalpy,
        "vhp_feedwater_enthalpy": vhp_feedwater_enthalpy,
        "steam_generation_efficiency": 0.8,
        "boiler_name": "boiler-packaged",
        "boiler_type": "packaged",
        "boiler_fuel": "natural-gas",
        "boiler_max_steam_generation": 200.0,
        "boiler_thermal_efficiency": 0.85,
        "target_steam_level": base_data.steam_levels[0].name,
        "vhp_turbine_name": "vhp-to-mp-st",
        "vhp_turbine_power_slope": 20.88 / 239.86,
        "vhp_turbine_power_intercept": 0.0,
        "match_benchmark_power_generation": True,
        "match_benchmark_maintenance_cost": True,
        "match_benchmark_capital_cost": True,
    }
    baseline_catalog = style_case_study_2_complete_static_scenario_catalog(
        **catalog_kwargs,
    )
    baseline_scenario = baseline_catalog.get("case-study-2", "proposed-without-hot-oil")
    baseline_run = run_static_style_scenario(
        baseline_scenario,
        solve=scipy_milp_static_style_solver(options={"time_limit": 20.0}),
    )
    benchmark = baseline_scenario.benchmark
    assert benchmark is not None
    utility_adjustment = (
        benchmark.utility_steam_flow - baseline_run.result.utility_steam_flow
    )

    targeted_catalog = style_case_study_2_complete_static_scenario_catalog(
        **catalog_kwargs,
        utility_steam_flow_adjustment=utility_adjustment,
    )
    targeted_scenario = targeted_catalog.get("case-study-2", "proposed-without-hot-oil")
    targeted_run = run_static_style_scenario(
        targeted_scenario,
        solve=scipy_milp_static_style_solver(options={"time_limit": 20.0}),
    )

    assert targeted_run.comparison is not None
    assert (
        targeted_run.comparison.deviation_for("utility_steam_flow").within_tolerance
        is True
    )
    assert (
        targeted_run.comparison.deviation_for("fuel_consumption").within_tolerance
        is False
    )


def test_style_case_study_2_complete_static_scenario_can_apply_fuel_consumption_factor() -> None:
    vhp_steam_enthalpy, vhp_feedwater_enthalpy = style_case_study_2_vhp_enthalpies(
        steam_temperature=570.0,
    )
    base_data = style_case_study_2_boiler_gas_turbine_hrsg_scenario_data(
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        gas_turbine_fuel="natural-gas",
        max_power_generation=40.0,
        vhp_header_name="VHP_100",
        vhp_steam_enthalpy=vhp_steam_enthalpy,
        vhp_feedwater_enthalpy=vhp_feedwater_enthalpy,
        steam_generation_efficiency=0.8,
        boiler_name="boiler-packaged",
        boiler_type="packaged",
        boiler_fuel="natural-gas",
        boiler_max_steam_generation=200.0,
        boiler_thermal_efficiency=0.85,
    )
    catalog_kwargs = {
        "scenario": "proposed-without-hot-oil",
        "steam_main": "MP",
        "generation_enthalpy_delta": 2.0,
        "use_enthalpy_delta": 1.0,
        "gas_turbine_name": "gt-industrial",
        "turbine_type": "industrial",
        "gas_turbine_fuel": "natural-gas",
        "max_power_generation": 40.0,
        "vhp_header_name": "VHP_100",
        "vhp_steam_enthalpy": vhp_steam_enthalpy,
        "vhp_feedwater_enthalpy": vhp_feedwater_enthalpy,
        "steam_generation_efficiency": 0.8,
        "boiler_name": "boiler-packaged",
        "boiler_type": "packaged",
        "boiler_fuel": "natural-gas",
        "boiler_max_steam_generation": 200.0,
        "boiler_thermal_efficiency": 0.85,
        "target_steam_level": base_data.steam_levels[0].name,
        "vhp_turbine_name": "vhp-to-mp-st",
        "vhp_turbine_power_slope": 20.88 / 239.86,
        "vhp_turbine_power_intercept": 0.0,
        "match_benchmark_power_generation": True,
        "match_benchmark_maintenance_cost": True,
        "match_benchmark_capital_cost": True,
    }
    baseline_catalog = style_case_study_2_complete_static_scenario_catalog(
        **catalog_kwargs,
    )
    baseline_scenario = baseline_catalog.get("case-study-2", "proposed-without-hot-oil")
    baseline_run = run_static_style_scenario(
        baseline_scenario,
        solve=scipy_milp_static_style_solver(options={"time_limit": 20.0}),
    )
    benchmark = baseline_scenario.benchmark
    assert benchmark is not None
    operating_adjustment = benchmark.operating_cost - baseline_run.result.operating_cost
    utility_adjustment = (
        benchmark.utility_steam_flow - baseline_run.result.utility_steam_flow
    )
    fuel_rows = tuple(
        row
        for row in static_style_fuel_consumption_by_equipment(baseline_run.model)
        if row.included_in_table_fuel_consumption and row.fuel_consumption > 0.0
    )
    target_fuel_row = max(fuel_rows, key=lambda row: row.fuel_consumption)
    other_fuel_consumption = (
        baseline_run.result.fuel_consumption - target_fuel_row.fuel_consumption
    )
    target_fuel_factor = (
        benchmark.fuel_consumption - other_fuel_consumption
    ) / target_fuel_row.fuel_consumption

    targeted_catalog = style_case_study_2_complete_static_scenario_catalog(
        **catalog_kwargs,
        utility_steam_flow_adjustment=utility_adjustment,
        operating_cost_adjustments={
            "auxiliary_or_unallocated": operating_adjustment,
        },
        fuel_consumption_factors={
            (
                target_fuel_row.equipment_family,
                target_fuel_row.equipment_name,
            ): target_fuel_factor,
        },
    )
    targeted_scenario = targeted_catalog.get("case-study-2", "proposed-without-hot-oil")
    targeted_run = run_static_style_scenario(
        targeted_scenario,
        solve=scipy_milp_static_style_solver(options={"time_limit": 20.0}),
    )

    assert targeted_run.comparison is not None
    assert targeted_run.comparison.within_tolerance is True


def test_style_case_study_2_contribution2_best_configuration_catalog_solves_calibrated_rows() -> None:
    catalog = style_case_study_2_contribution2_best_configuration_catalog()

    assert catalog.keys() == (
        ("contribution-2-case-study-2", "utility-system-stand-alone"),
        ("contribution-2-case-study-2", "utility-system-microgrid"),
        ("contribution-2-case-study-2", "hot-oil-fsr-stand-alone"),
        ("contribution-2-case-study-2", "hot-oil-fsr-microgrid"),
    )
    for scenario in catalog:
        run = run_static_style_scenario(
            scenario,
            solve=scipy_milp_static_style_solver(),
        )
        comparison = compare_static_style_result_to_best_configuration(
            run.result,
            get_contribution2_case_study2_best_configuration(scenario.scenario),
            absolute_tolerance=scenario.absolute_tolerance,
        )

        assert comparison.within_tolerance is True


def test_style_case_study_2_contribution2_physical_profile_catalog_solves_calibrated_rows() -> None:
    catalog = style_case_study_2_contribution2_physical_profile_catalog()

    assert catalog.keys() == (
        (
            "contribution-2-case-study-2-physical-profile",
            "utility-system-stand-alone",
        ),
        ("contribution-2-case-study-2-physical-profile", "utility-system-microgrid"),
        ("contribution-2-case-study-2-physical-profile", "hot-oil-fsr-stand-alone"),
        ("contribution-2-case-study-2-physical-profile", "hot-oil-fsr-microgrid"),
    )
    for scenario in catalog:
        run = run_static_style_scenario(
            scenario,
            solve=scipy_milp_static_style_solver(),
        )
        comparison = compare_static_style_result_to_best_configuration(
            run.result,
            get_contribution2_case_study2_best_configuration(scenario.scenario),
            absolute_tolerance=scenario.absolute_tolerance,
        )

        assert comparison.deviation_for("utility_steam_flow").within_tolerance is True
        assert comparison.deviation_for("power_generation").within_tolerance is True
        assert comparison.deviation_for("fuel_cost").within_tolerance is True
        assert comparison.deviation_for("maintenance_cost").within_tolerance is True
        assert comparison.deviation_for("capital_cost").within_tolerance is True
        assert comparison.deviation_for("fuel_consumption").within_tolerance is False
        if scenario.scenario == "utility-system-stand-alone":
            assert comparison.deviation_for("operating_cost").absolute_deviation == (
                pytest.approx(0.94311439)
            )
            assert comparison.deviation_for(
                "total_annualized_cost",
            ).absolute_deviation == pytest.approx(0.94311439)
        else:
            assert comparison.deviation_for("operating_cost").within_tolerance is True
            assert (
                comparison.deviation_for("total_annualized_cost").within_tolerance
                is True
            )


def test_style_case_study_2_contribution2_physical_profile_catalog_can_apply_fuel_target_factors() -> None:
    catalog = style_case_study_2_contribution2_physical_profile_catalog(
        fuel_consumption_factors_by_scenario={
            "utility-system-stand-alone": {
                ("boiler", "reported-boiler"): 0.9783733722921836,
            },
            "utility-system-microgrid": {
                ("boiler", "reported-boiler"): 0.9691975330322308,
            },
            "hot-oil-fsr-stand-alone": {
                ("gas_turbine", "reported-gt"): 0.9714646130095664,
            },
            "hot-oil-fsr-microgrid": {
                ("gas_turbine", "reported-gt"): 0.9626542326262802,
            },
        },
    )

    for scenario in catalog:
        run = run_static_style_scenario(
            scenario,
            solve=scipy_milp_static_style_solver(),
        )
        comparison = compare_static_style_result_to_best_configuration(
            run.result,
            get_contribution2_case_study2_best_configuration(scenario.scenario),
            absolute_tolerance=scenario.absolute_tolerance,
        )

        assert comparison.deviation_for("fuel_consumption").within_tolerance is True
        assert comparison.deviation_for("utility_steam_flow").within_tolerance is True
        assert comparison.deviation_for("power_generation").within_tolerance is True
        assert comparison.deviation_for("fuel_cost").within_tolerance is True
        assert comparison.deviation_for("maintenance_cost").within_tolerance is True
        assert comparison.deviation_for("capital_cost").within_tolerance is True


def test_style_case_study_2_contribution2_physical_profile_catalog_can_apply_operating_cost_target_adjustments() -> None:
    catalog = style_case_study_2_contribution2_physical_profile_catalog(
        fuel_consumption_factors_by_scenario={
            "utility-system-stand-alone": {
                ("boiler", "reported-boiler"): 0.9783733722921836,
            },
            "utility-system-microgrid": {
                ("boiler", "reported-boiler"): 0.9691975330322308,
            },
            "hot-oil-fsr-stand-alone": {
                ("gas_turbine", "reported-gt"): 0.9714646130095664,
            },
            "hot-oil-fsr-microgrid": {
                ("gas_turbine", "reported-gt"): 0.9626542326262802,
            },
        },
        operating_cost_adjustments_by_scenario={
            "utility-system-stand-alone": {
                "auxiliary_or_unallocated": -0.9431143940000126,
            },
        },
    )

    for scenario in catalog:
        run = run_static_style_scenario(
            scenario,
            solve=scipy_milp_static_style_solver(),
        )
        comparison = compare_static_style_result_to_best_configuration(
            run.result,
            get_contribution2_case_study2_best_configuration(scenario.scenario),
            absolute_tolerance=scenario.absolute_tolerance,
        )

        assert comparison.deviation_for("fuel_consumption").within_tolerance is True
        assert comparison.deviation_for("operating_cost").within_tolerance is True
        assert (
            comparison.deviation_for("total_annualized_cost").within_tolerance
            is True
        )


def test_style_case_study_2_contribution2_physical_profile_catalog_solves_uncalibrated_rows() -> None:
    catalog = style_case_study_2_contribution2_physical_profile_catalog(
        calibrated=False,
    )

    assert catalog.keys() == (
        (
            "contribution-2-case-study-2-physical-profile",
            "utility-system-stand-alone",
        ),
        ("contribution-2-case-study-2-physical-profile", "utility-system-microgrid"),
        ("contribution-2-case-study-2-physical-profile", "hot-oil-fsr-stand-alone"),
        ("contribution-2-case-study-2-physical-profile", "hot-oil-fsr-microgrid"),
    )
    for scenario in catalog:
        run = run_static_style_scenario(
            scenario,
            solve=scipy_milp_static_style_solver(),
        )

        assert run.solver.termination_condition == "optimal"
        assert run.result.total_annualized_cost > 0.0


def test_style_case_study_2_scenario_catalog_registers_assembled_benchmark() -> None:
    catalog = style_case_study_2_scenario_catalog(
        steam_main="MP",
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        gas_turbine_name="gt-industrial",
        turbine_type="industrial",
        fuel="natural-gas",
        max_power_generation=40.0,
        scenario="proposed-without-hot-oil",
    )
    scenario = catalog.get("case-study-2", "proposed-without-hot-oil")

    assert isinstance(catalog, StaticStyleScenarioCatalog)
    assert catalog.keys() == (("case-study-2", "proposed-without-hot-oil"),)
    assert scenario.benchmark is not None
    assert scenario.data.gas_turbines[0].name == "gt-industrial"
