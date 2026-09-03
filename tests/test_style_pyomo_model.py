from __future__ import annotations

import pytest
import pyomo.environ as pyomo

from OpenUtility.utility_system import (
    BoilerCandidate,
    CoolingWaterConfig,
    DeaeratorConfig,
    EquipmentCost,
    ElectricityCost,
    FlashSteamRecoveryConfig,
    FlashSteamRecoveryLevel,
    FlashSteamRecoveryRoute,
    FuelCost,
    GasTurbineCandidate,
    HotOilConfig,
    HrsgCandidate,
    SteamMainBackPressureTurbineCandidate,
    SteamMainLetdownStationCandidate,
    SteamLevelCandidate,
    UtilitySystemModelData,
    VhpBackPressureTurbineCandidate,
    VhpLetdownStationCandidate,
    VhpSteamCandidate,
    VhpSteamSourceCandidate,
    WaterCost,
    build_utility_system_model,
)


def test_static_style_model_builds_core_source_cascade_components() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=100.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=1.5,
                source_heat_upper_bound=100.0,
            ),
            SteamLevelCandidate(
                name="MP_95",
                steam_main="MP",
                temperature=95.0,
                source_heat_available=25.0,
                sink_heat_demand=50.0,
                generation_enthalpy_delta=2.5,
                use_enthalpy_delta=1.0,
                source_heat_upper_bound=125.0,
            ),
        ),
        power_demand=25.0,
    )

    model = build_utility_system_model(data)

    assert list(model.STEAM_LEVELS.data()) == ["MP_185", "MP_95"]
    assert list(model.STEAM_MAINS.data()) == ["MP"]
    assert model.level_selected["MP_185"].domain is pyomo.Binary
    assert len(model.source_cascade_balance) == 2
    assert len(model.source_steam_generation) == 2
    assert len(model.sink_cascade_balance) == 2
    assert len(model.sink_steam_use) == 2
    assert len(model.sink_process_steam_mass_balance) == 2
    assert len(model.sink_process_steam_energy_balance) == 2
    assert len(model.steam_main_mass_balance) == 2
    assert len(model.steam_main_energy_balance) == 2
    assert len(model.electricity_balance) == 1
    assert len(model.one_level_per_main) == 1


def test_inter_header_connections_conserve_mass_and_energy() -> None:
    data = UtilitySystemModelData(
        steam_mains=("HP", "MP"),
        steam_levels=(
            SteamLevelCandidate(
                name="HP_12",
                steam_main="HP",
                temperature=188.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=1.0,
                use_enthalpy_delta=1.0,
                generated_steam_enthalpy=340.0,
                main_steam_enthalpy=340.0,
                utility_steam_enthalpy=340.0,
            ),
            SteamLevelCandidate(
                name="MP_3",
                steam_main="MP",
                temperature=134.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=1.0,
                use_enthalpy_delta=1.0,
                generated_steam_enthalpy=185.0,
                main_steam_enthalpy=241.0,
                utility_steam_enthalpy=241.0,
                feedwater_enthalpy=20.0,
            ),
        ),
        steam_main_turbines=(
            SteamMainBackPressureTurbineCandidate(
                name="HP_to_MP_ST",
                source_level="HP_12",
                target_level="MP_3",
                power_slope=10.0,
                power_intercept=0.0,
                min_capacity=0.0,
                max_capacity=10.0,
                minimum_load_fraction=0.0,
            ),
        ),
        steam_main_letdowns=(
            SteamMainLetdownStationCandidate(
                name="HP_to_MP_LD",
                source_level="HP_12",
                target_level="MP_3",
                max_flow=10.0,
            ),
        ),
        power_demand=0.0,
    )
    model = build_utility_system_model(data)

    assert list(model.STEAM_MAIN_TURBINES.data()) == ["HP_to_MP_ST"]
    assert list(model.STEAM_MAIN_LETDOWNS.data()) == ["HP_to_MP_LD"]

    model.level_selected["HP_12"].fix(1.0)
    model.level_selected["MP_3"].fix(1.0)
    model.source_steam_generated["HP_12"].fix(3.0)
    model.utility_steam_to_header["HP_12"].fix(0.0)
    model.feedwater_to_header["HP_12"].fix(0.0)
    model.process_steam_to_sink["HP_12"].fix(0.0)
    model.header_steam_export["HP_12"].fix(0.0)
    model.deaerator_steam_from_header["HP_12"].fix(0.0)
    model.source_steam_generated["MP_3"].fix(1.0)
    model.utility_steam_to_header["MP_3"].fix(0.0)
    model.feedwater_to_header["MP_3"].fix(1.0)
    model.process_steam_to_sink["MP_3"].fix(5.0)
    model.header_steam_export["MP_3"].fix(0.0)
    model.deaerator_steam_from_header["MP_3"].fix(0.0)
    model.steam_main_turbine_selected["HP_to_MP_ST"].fix(1.0)
    model.steam_main_turbine_steam_flow["HP_to_MP_ST"].fix(2.0)
    model.steam_main_turbine_power_generation["HP_to_MP_ST"].fix(20.0)
    model.steam_main_letdown_flow["HP_to_MP_LD"].fix(1.0)

    assert pyomo.value(model.steam_main_turbine_power_equation["HP_to_MP_ST"].body) == (
        pytest.approx(0.0)
    )
    assert pyomo.value(model.steam_main_mass_balance["HP_12"].body) == pytest.approx(
        0.0
    )
    assert pyomo.value(model.steam_main_energy_balance["HP_12"].body) == pytest.approx(
        0.0
    )
    assert pyomo.value(model.steam_main_mass_balance["MP_3"].body) == pytest.approx(0.0)
    assert pyomo.value(model.steam_main_energy_balance["MP_3"].body) == pytest.approx(
        0.0
    )


def test_source_generation_equation_uses_pseudo_enthalpy_delta() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=100.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=1.5,
                source_heat_upper_bound=100.0,
            ),
        ),
        power_demand=25.0,
        source_heat_loss_fraction=0.1,
    )
    model = build_utility_system_model(data)

    model.source_heat_to_steam["MP_185"].fix(100.0)
    model.source_steam_generated["MP_185"].fix(45.0)

    assert pyomo.value(model.source_steam_generation["MP_185"].body) == pytest.approx(
        0.0
    )


def test_sink_cascade_balance_moves_residual_heat_down_temperature_levels() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=2.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=1.0,
                sink_heat_upper_bound=5.0,
            ),
            SteamLevelCandidate(
                name="MP_95",
                steam_main="MP",
                temperature=95.0,
                source_heat_available=0.0,
                sink_heat_demand=3.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=1.0,
                sink_heat_upper_bound=3.0,
            ),
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.sink_heat_from_steam["MP_185"].fix(5.0)
    model.sink_residual_heat["MP_185"].fix(3.0)
    model.sink_heat_from_steam["MP_95"].fix(0.0)
    model.sink_residual_heat["MP_95"].fix(0.0)

    assert pyomo.value(model.sink_cascade_balance["MP_185"].body) == pytest.approx(0.0)
    assert pyomo.value(model.sink_cascade_balance["MP_95"].body) == pytest.approx(0.0)


def test_sink_steam_use_includes_desuperheating_mass_and_energy_balance() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=4.5,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
                steam_enthalpy_for_use=4.0,
                feedwater_enthalpy=1.0,
                sink_heat_upper_bound=4.5,
            ),
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.process_steam_to_sink["MP_185"].fix(1.0)
    model.feedwater_to_desuperheat["MP_185"].fix(0.5)
    model.sink_steam_used["MP_185"].fix(1.5)
    model.sink_heat_from_steam["MP_185"].fix(4.5)

    assert pyomo.value(
        model.sink_process_steam_mass_balance["MP_185"].body
    ) == pytest.approx(0.0)
    assert pyomo.value(
        model.sink_process_steam_energy_balance["MP_185"].body
    ) == pytest.approx(0.0)
    assert pyomo.value(model.sink_steam_use["MP_185"].body) == pytest.approx(0.0)


def test_flash_steam_recovery_contributes_to_sink_heating() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP", "LP"),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
            SteamLevelCandidate(
                name="LP_120",
                steam_main="LP",
                temperature=120.0,
                source_heat_available=0.0,
                sink_heat_demand=6.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
                steam_enthalpy_for_use=4.0,
                sink_heat_upper_bound=6.0,
            ),
        ),
        flash_steam_recovery=FlashSteamRecoveryConfig(
            levels=(
                FlashSteamRecoveryLevel(
                    steam_level="MP_185",
                    saturated_vapor_enthalpy=9.0,
                    saturated_liquid_enthalpy=5.0,
                ),
                FlashSteamRecoveryLevel(
                    steam_level="LP_120",
                    saturated_vapor_enthalpy=2.0,
                    saturated_liquid_enthalpy=1.0,
                ),
            ),
            routes=(
                FlashSteamRecoveryRoute(
                    name="mp_to_lp",
                    source_level="MP_185",
                    target_level="LP_120",
                    max_flow=10.0,
                ),
            ),
            condensate_return_fraction=0.5,
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.process_steam_to_sink["LP_120"].fix(1.0)
    model.feedwater_to_desuperheat["LP_120"].fix(0.0)
    model.flash_steam_to_sink["LP_120"].fix(1.0)
    model.sink_steam_used["LP_120"].fix(2.0)
    model.sink_heat_from_steam["LP_120"].fix(6.0)

    assert pyomo.value(
        model.sink_process_steam_mass_balance["LP_120"].body
    ) == pytest.approx(0.0)
    assert pyomo.value(
        model.sink_process_steam_energy_balance["LP_120"].body
    ) == pytest.approx(0.0)
    assert pyomo.value(model.sink_steam_use["LP_120"].body) == pytest.approx(0.0)


def test_flash_steam_recovery_route_conserves_mass_and_energy() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP", "LP"),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
            SteamLevelCandidate(
                name="LP_120",
                steam_main="LP",
                temperature=120.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
        ),
        flash_steam_recovery=FlashSteamRecoveryConfig(
            levels=(
                FlashSteamRecoveryLevel(
                    steam_level="MP_185",
                    saturated_vapor_enthalpy=9.0,
                    saturated_liquid_enthalpy=5.0,
                ),
                FlashSteamRecoveryLevel(
                    steam_level="LP_120",
                    saturated_vapor_enthalpy=8.0,
                    saturated_liquid_enthalpy=2.0,
                ),
            ),
            routes=(
                FlashSteamRecoveryRoute(
                    name="mp_to_lp",
                    source_level="MP_185",
                    target_level="LP_120",
                    max_flow=10.0,
                ),
            ),
            condensate_return_fraction=0.5,
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.sink_steam_used["MP_185"].fix(4.0)
    model.flash_condensate_inlet["MP_185"].fix(2.0)
    model.flash_steam_recovered["mp_to_lp"].fix(1.0)
    model.flash_liquid_recovered["mp_to_lp"].fix(1.0)
    model.flash_steam_to_sink["LP_120"].fix(1.0)

    assert pyomo.value(
        model.flash_condensate_inlet_balance["MP_185"].body
    ) == pytest.approx(0.0)
    assert pyomo.value(
        model.flash_recovery_route_mass_balance["MP_185"].body
    ) == pytest.approx(0.0)
    assert pyomo.value(
        model.flash_recovery_route_energy_balance["MP_185"].body
    ) == pytest.approx(0.0)
    assert pyomo.value(
        model.flash_steam_to_sink_balance["LP_120"].body
    ) == pytest.approx(0.0)


def test_steam_main_balance_tracks_header_mass_and_energy() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=10.0,
                sink_heat_demand=12.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
                generated_steam_enthalpy=5.0,
                main_steam_enthalpy=3.0,
                utility_steam_enthalpy=3.0,
                feedwater_enthalpy=1.0,
                steam_flow_upper_bound=10.0,
            ),
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.source_steam_generated["MP_185"].fix(1.0)
    model.utility_steam_to_header["MP_185"].fix(2.0)
    model.feedwater_to_header["MP_185"].fix(1.0)
    model.process_steam_to_sink["MP_185"].fix(4.0)
    model.header_steam_export["MP_185"].fix(0.0)

    assert pyomo.value(model.steam_main_mass_balance["MP_185"].body) == pytest.approx(
        0.0
    )
    assert pyomo.value(model.steam_main_energy_balance["MP_185"].body) == pytest.approx(
        0.0
    )


def test_steam_main_balance_includes_deaerator_steam_use() -> None:
    data = UtilitySystemModelData(
        steam_mains=("LP",),
        steam_levels=(
            SteamLevelCandidate(
                name="LP_120",
                steam_main="LP",
                temperature=120.0,
                source_heat_available=10.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
                generated_steam_enthalpy=10.0,
                main_steam_enthalpy=10.0,
                steam_flow_upper_bound=10.0,
            ),
        ),
        deaerator=DeaeratorConfig(
            feedwater_enthalpy=2.0,
            condensate_enthalpy=1.0,
            makeup_water_enthalpy=0.5,
            vent_enthalpy=0.0,
            condensate_return_fraction=0.6,
            vent_fraction=0.1,
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.source_steam_generated["LP_120"].fix(2.0)
    model.utility_steam_to_header["LP_120"].fix(0.0)
    model.feedwater_to_header["LP_120"].fix(0.0)
    model.process_steam_to_sink["LP_120"].fix(1.0)
    model.header_steam_export["LP_120"].fix(0.5)
    model.deaerator_steam_from_header["LP_120"].fix(0.5)

    assert pyomo.value(model.steam_main_mass_balance["LP_120"].body) == pytest.approx(
        0.0
    )
    assert pyomo.value(model.steam_main_energy_balance["LP_120"].body) == pytest.approx(
        0.0
    )


def test_deaerator_feedwater_accounting_tracks_site_water_requirement() -> None:
    data = UtilitySystemModelData(
        steam_mains=("LP",),
        steam_levels=(
            SteamLevelCandidate(
                name="LP_120",
                steam_main="LP",
                temperature=120.0,
                source_heat_available=10.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
                main_steam_enthalpy=16.65,
                steam_flow_upper_bound=10.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_90",
                steam_enthalpy=5.0,
                feedwater_enthalpy=1.0,
                steam_flow_upper_bound=20.0,
            ),
        ),
        boilers=(
            BoilerCandidate(
                name="boiler_1",
                vhp_header="VHP_90",
                size_fuel_coefficient=0.0,
                load_fuel_coefficient=1.0,
                min_capacity=1.0,
                max_capacity=10.0,
                minimum_load_fraction=0.2,
            ),
        ),
        gas_turbines=(
            GasTurbineCandidate(
                name="gt_1",
                fuel_lhv=10.0,
                power_slope=0.4,
                power_intercept=0.5,
                min_fuel_flow=1.0,
                max_fuel_flow=10.0,
                minimum_load_fraction=0.2,
            ),
        ),
        hrsgs=(
            HrsgCandidate(
                name="hrsg_1",
                gas_turbine="gt_1",
                vhp_header="VHP_90",
                steam_generation_efficiency=0.8,
                max_heat_input=50.0,
            ),
        ),
        deaerator=DeaeratorConfig(
            feedwater_enthalpy=2.0,
            condensate_enthalpy=1.0,
            makeup_water_enthalpy=0.5,
            vent_enthalpy=0.0,
            condensate_return_fraction=0.6,
            vent_fraction=0.1,
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.source_steam_generated["LP_120"].fix(2.0)
    model.feedwater_to_desuperheat["LP_120"].fix(0.5)
    model.feedwater_to_header["LP_120"].fix(0.25)
    model.boiler_steam_generation["boiler_1"].fix(3.0)
    model.hrsg_steam_generation["hrsg_1"].fix(1.0)
    model.deaerator_feedwater_requirement.fix(6.75)
    model.deaerator_condensate_return.fix(4.05)
    model.deaerator_steam_from_header["LP_120"].fix(0.5)
    model.deaerator_makeup_water.fix(2.25)

    assert pyomo.value(
        model.deaerator_feedwater_requirement_equation.body
    ) == pytest.approx(0.0)
    assert pyomo.value(
        model.deaerator_condensate_return_equation.body
    ) == pytest.approx(0.0)
    assert pyomo.value(model.deaerator_makeup_water_equation.body) == pytest.approx(0.0)
    assert pyomo.value(model.deaerator_energy_balance.body) == pytest.approx(0.0)


def test_utility_steam_import_requires_selected_header() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
                steam_flow_upper_bound=10.0,
            ),
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.utility_steam_to_header["MP_185"].fix(10.0)
    model.level_selected["MP_185"].fix(1.0)

    assert pyomo.value(
        model.utility_steam_requires_selected_header["MP_185"].body
    ) == pytest.approx(0.0)


def test_boiler_block_supplies_vhp_header_and_calculates_fuel() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
                steam_flow_upper_bound=10.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_90",
                steam_enthalpy=5.0,
                feedwater_enthalpy=1.0,
                steam_flow_upper_bound=20.0,
            ),
        ),
        boilers=(
            BoilerCandidate(
                name="boiler_1",
                vhp_header="VHP_90",
                size_fuel_coefficient=0.25,
                load_fuel_coefficient=1.1,
                blowdown_fraction=0.1,
                blowdown_enthalpy_delta=0.5,
                min_capacity=1.0,
                max_capacity=10.0,
                minimum_load_fraction=0.2,
            ),
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.boiler_size["boiler_1"].fix(3.0)
    model.boiler_steam_generation["boiler_1"].fix(2.0)
    model.boiler_fuel_consumption["boiler_1"].fix(11.9)
    model.utility_steam_from_vhp["VHP_90", "MP_185"].fix(2.0)
    model.utility_steam_to_header["MP_185"].fix(2.0)

    assert pyomo.value(
        model.boiler_fuel_consumption_equation["boiler_1"].body
    ) == pytest.approx(0.0)
    assert pyomo.value(model.vhp_mass_balance["VHP_90"].body) == pytest.approx(0.0)
    assert pyomo.value(
        model.utility_steam_from_vhp_aggregation["MP_185"].body
    ) == pytest.approx(0.0)


def test_vhp_source_block_supplies_vhp_header_and_calculates_fuel() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
                steam_flow_upper_bound=10.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_90",
                steam_enthalpy=5.0,
                feedwater_enthalpy=1.0,
                steam_flow_upper_bound=20.0,
            ),
        ),
        vhp_sources=(
            VhpSteamSourceCandidate(
                name="source_1",
                vhp_header="VHP_90",
                min_capacity=1.0,
                max_capacity=10.0,
                minimum_load_fraction=0.2,
                fuel_consumption_per_steam=0.5,
                must_select=True,
            ),
        ),
        fuel_costs=(
            FuelCost(
                name="source_fuel",
                equipment_type="vhp_source",
                equipment_name="source_1",
                unit_cost=4.0,
            ),
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.vhp_selected["VHP_90"].fix(1.0)
    model.vhp_source_selected["source_1"].fix(1.0)
    model.vhp_source_steam_generation["source_1"].fix(4.0)
    model.vhp_source_fuel_consumption["source_1"].fix(2.0)
    model.utility_steam_from_vhp["VHP_90", "MP_185"].fix(4.0)
    model.utility_steam_to_header["MP_185"].fix(4.0)

    assert list(model.VHP_SOURCES.data()) == ["source_1"]
    assert pyomo.value(
        model.vhp_source_fuel_consumption_equation["source_1"].body
    ) == pytest.approx(0.0)
    assert pyomo.value(
        model.vhp_source_generation_upper_bound["source_1"].body
    ) == pytest.approx(-6.0)
    assert pyomo.value(
        model.vhp_source_minimum_load_fraction["source_1"].body
    ) == pytest.approx(-2.0)
    assert pyomo.value(model.vhp_source_must_select_constraint["source_1"].body) == (
        pytest.approx(1.0)
    )
    assert pyomo.value(model.vhp_mass_balance["VHP_90"].body) == pytest.approx(0.0)
    assert pyomo.value(model.fuel_operating_cost["source_fuel"]) == pytest.approx(
        8.0,
    )


def test_boiler_load_and_size_require_selected_unit() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_90",
                steam_enthalpy=5.0,
                feedwater_enthalpy=1.0,
                steam_flow_upper_bound=20.0,
            ),
        ),
        boilers=(
            BoilerCandidate(
                name="boiler_1",
                vhp_header="VHP_90",
                size_fuel_coefficient=0.0,
                load_fuel_coefficient=1.0,
                min_capacity=1.0,
                max_capacity=10.0,
                minimum_load_fraction=0.2,
            ),
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.boiler_selected["boiler_1"].fix(1.0)
    model.boiler_size["boiler_1"].fix(10.0)
    model.boiler_steam_generation["boiler_1"].fix(2.0)

    assert pyomo.value(model.boiler_size_upper_bound["boiler_1"].body) == pytest.approx(
        0.0
    )
    assert pyomo.value(
        model.boiler_minimum_load_fraction["boiler_1"].body
    ) == pytest.approx(0.0)


def test_equipment_costs_add_capital_and_maintenance_to_objective() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_90",
                steam_enthalpy=5.0,
                feedwater_enthalpy=1.0,
                steam_flow_upper_bound=20.0,
            ),
        ),
        boilers=(
            BoilerCandidate(
                name="boiler_1",
                vhp_header="VHP_90",
                size_fuel_coefficient=0.0,
                load_fuel_coefficient=1.0,
                min_capacity=1.0,
                max_capacity=10.0,
                minimum_load_fraction=0.2,
            ),
        ),
        equipment_costs=(
            EquipmentCost(
                name="boiler_cost",
                equipment_type="boiler",
                equipment_name="boiler_1",
                annualization_factor=0.2,
                installation_factor=1.5,
                variable_capital_cost=10.0,
                fixed_capital_cost=100.0,
                variable_maintenance_cost=1.0,
                fixed_maintenance_cost=5.0,
            ),
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.level_selected["MP_185"].fix(0.0)
    model.source_heat_to_steam["MP_185"].fix(0.0)
    model.boiler_selected["boiler_1"].fix(1.0)
    model.boiler_size["boiler_1"].fix(4.0)

    assert pyomo.value(
        model.equipment_annualized_capital_cost["boiler_cost"]
    ) == pytest.approx(42.0)
    assert pyomo.value(model.total_annualized_capital_cost) == pytest.approx(42.0)
    assert pyomo.value(
        model.equipment_maintenance_cost["boiler_cost"]
    ) == pytest.approx(9.0)
    assert pyomo.value(model.total_equipment_maintenance_cost) == pytest.approx(9.0)
    assert pyomo.value(model.total_annualized_cost) == pytest.approx(51.0)


def test_equipment_costs_cover_turbines_gas_turbines_and_hrsgs() -> None:
    data = UtilitySystemModelData(
        steam_mains=("LP",),
        steam_levels=(
            SteamLevelCandidate(
                name="LP_120",
                steam_main="LP",
                temperature=120.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_90",
                steam_enthalpy=5.0,
                feedwater_enthalpy=1.0,
                steam_flow_upper_bound=20.0,
            ),
        ),
        vhp_turbines=(
            VhpBackPressureTurbineCandidate(
                name="st_1",
                vhp_header="VHP_90",
                steam_level="LP_120",
                power_slope=0.2,
                power_intercept=0.0,
                min_capacity=0.0,
                max_capacity=10.0,
                minimum_load_fraction=0.0,
            ),
        ),
        gas_turbines=(
            GasTurbineCandidate(
                name="gt_1",
                fuel_lhv=10.0,
                power_slope=0.3,
                power_intercept=0.0,
                min_fuel_flow=0.0,
                max_fuel_flow=10.0,
                minimum_load_fraction=0.0,
            ),
        ),
        hrsgs=(
            HrsgCandidate(
                name="hrsg_1",
                gas_turbine="gt_1",
                vhp_header="VHP_90",
                steam_generation_efficiency=0.8,
                max_heat_input=20.0,
            ),
        ),
        equipment_costs=(
            EquipmentCost(
                name="steam_turbine_cost",
                equipment_type="vhp_turbine",
                equipment_name="st_1",
                annualization_factor=0.1,
                installation_factor=2.0,
                variable_capital_cost=10.0,
                fixed_capital_cost=100.0,
                variable_maintenance_cost=1.0,
                fixed_maintenance_cost=5.0,
            ),
            EquipmentCost(
                name="gas_turbine_cost",
                equipment_type="gas_turbine",
                equipment_name="gt_1",
                annualization_factor=0.2,
                installation_factor=3.0,
                variable_capital_cost=20.0,
                fixed_capital_cost=200.0,
                variable_maintenance_cost=2.0,
                fixed_maintenance_cost=10.0,
            ),
            EquipmentCost(
                name="hrsg_cost",
                equipment_type="hrsg",
                equipment_name="hrsg_1",
                annualization_factor=0.3,
                installation_factor=4.0,
                variable_capital_cost=30.0,
                fixed_capital_cost=300.0,
                variable_maintenance_cost=3.0,
                fixed_maintenance_cost=15.0,
            ),
        ),
        power_demand=0.0,
    )
    model = build_utility_system_model(data)

    model.level_selected["LP_120"].fix(0.0)
    model.source_heat_to_steam["LP_120"].fix(0.0)
    model.vhp_turbine_selected["st_1"].fix(1.0)
    model.vhp_turbine_power_generation["st_1"].fix(5.0)
    model.gas_turbine_selected["gt_1"].fix(1.0)
    model.gas_turbine_power_generation["gt_1"].fix(6.0)
    model.hrsg_selected["hrsg_1"].fix(1.0)
    model.hrsg_heat_input["hrsg_1"].fix(7.0)

    assert pyomo.value(
        model.equipment_annualized_capital_cost["steam_turbine_cost"]
    ) == pytest.approx(30.0)
    assert pyomo.value(
        model.equipment_annualized_capital_cost["gas_turbine_cost"]
    ) == pytest.approx(192.0)
    assert pyomo.value(
        model.equipment_annualized_capital_cost["hrsg_cost"]
    ) == pytest.approx(612.0)
    assert pyomo.value(model.total_annualized_capital_cost) == pytest.approx(834.0)
    assert pyomo.value(model.total_equipment_maintenance_cost) == pytest.approx(68.0)
    assert pyomo.value(model.total_annualized_cost) == pytest.approx(902.0)


def test_fuel_electricity_and_water_costs_contribute_to_objective() -> None:
    data = UtilitySystemModelData(
        steam_mains=("LP",),
        steam_levels=(
            SteamLevelCandidate(
                name="LP_120",
                steam_main="LP",
                temperature=120.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_90",
                steam_enthalpy=5.0,
                feedwater_enthalpy=1.0,
                steam_flow_upper_bound=20.0,
            ),
        ),
        boilers=(
            BoilerCandidate(
                name="boiler_1",
                vhp_header="VHP_90",
                size_fuel_coefficient=0.0,
                load_fuel_coefficient=1.0,
                min_capacity=1.0,
                max_capacity=10.0,
                minimum_load_fraction=0.2,
            ),
        ),
        deaerator=DeaeratorConfig(
            feedwater_enthalpy=2.0,
            condensate_enthalpy=1.0,
            makeup_water_enthalpy=0.5,
            vent_enthalpy=0.0,
            condensate_return_fraction=0.6,
        ),
        fuel_costs=(
            FuelCost(
                name="boiler_fuel",
                equipment_type="boiler",
                equipment_name="boiler_1",
                unit_cost=5.0,
            ),
        ),
        electricity_cost=ElectricityCost(
            import_unit_cost=4.0,
            export_unit_price=1.0,
        ),
        water_cost=WaterCost(unit_cost=2.0),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.level_selected["LP_120"].fix(0.0)
    model.source_heat_to_steam["LP_120"].fix(0.0)
    model.boiler_fuel_consumption["boiler_1"].fix(10.0)
    model.grid_power_import.fix(3.0)
    model.grid_power_export.fix(1.0)
    model.deaerator_makeup_water.fix(2.0)

    assert pyomo.value(model.fuel_operating_cost["boiler_fuel"]) == pytest.approx(50.0)
    assert pyomo.value(model.total_fuel_operating_cost) == pytest.approx(50.0)
    assert pyomo.value(model.electricity_operating_cost) == pytest.approx(11.0)
    assert pyomo.value(model.water_operating_cost) == pytest.approx(4.0)
    assert pyomo.value(model.total_annualized_cost) == pytest.approx(65.0)


def test_cost_scaling_applies_operating_hours_and_currency_scale() -> None:
    data = UtilitySystemModelData(
        steam_mains=("LP",),
        steam_levels=(
            SteamLevelCandidate(
                name="LP_120",
                steam_main="LP",
                temperature=120.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_90",
                steam_enthalpy=5.0,
                feedwater_enthalpy=1.0,
                steam_flow_upper_bound=20.0,
            ),
        ),
        boilers=(
            BoilerCandidate(
                name="boiler_1",
                vhp_header="VHP_90",
                size_fuel_coefficient=0.0,
                load_fuel_coefficient=1.0,
                min_capacity=1.0,
                max_capacity=10.0,
                minimum_load_fraction=0.2,
            ),
        ),
        deaerator=DeaeratorConfig(
            feedwater_enthalpy=2.0,
            condensate_enthalpy=1.0,
            makeup_water_enthalpy=0.5,
            vent_enthalpy=0.0,
            condensate_return_fraction=0.6,
        ),
        equipment_costs=(
            EquipmentCost(
                name="boiler_cost",
                equipment_type="boiler",
                equipment_name="boiler_1",
                annualization_factor=0.2,
                installation_factor=1.5,
                variable_capital_cost=10.0,
                fixed_capital_cost=100.0,
                variable_maintenance_cost=1.0,
                fixed_maintenance_cost=5.0,
            ),
        ),
        fuel_costs=(
            FuelCost(
                name="boiler_fuel",
                equipment_type="boiler",
                equipment_name="boiler_1",
                unit_cost=5.0,
            ),
        ),
        electricity_cost=ElectricityCost(
            import_unit_cost=4.0,
            export_unit_price=1.0,
        ),
        water_cost=WaterCost(unit_cost=2.0),
        power_demand=25.0,
        operating_hours=8000.0,
        cost_scale=1e-6,
    )
    model = build_utility_system_model(data)

    model.level_selected["LP_120"].fix(0.0)
    model.source_heat_to_steam["LP_120"].fix(0.0)
    model.boiler_selected["boiler_1"].fix(1.0)
    model.boiler_size["boiler_1"].fix(4.0)
    model.boiler_fuel_consumption["boiler_1"].fix(10.0)
    model.grid_power_import.fix(3.0)
    model.grid_power_export.fix(1.0)
    model.deaerator_makeup_water.fix(2.0)

    assert pyomo.value(model.fuel_operating_cost["boiler_fuel"]) == pytest.approx(0.4)
    assert pyomo.value(model.electricity_operating_cost) == pytest.approx(0.088)
    assert pyomo.value(model.water_operating_cost) == pytest.approx(0.032)
    assert pyomo.value(model.total_annualized_capital_cost) == pytest.approx(0.000042)
    assert pyomo.value(model.total_equipment_maintenance_cost) == pytest.approx(
        0.000009
    )


def test_fuel_costs_cover_gas_turbines_and_hrsg_supplementary_firing() -> None:
    data = UtilitySystemModelData(
        steam_mains=("LP",),
        steam_levels=(
            SteamLevelCandidate(
                name="LP_120",
                steam_main="LP",
                temperature=120.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_90",
                steam_enthalpy=5.0,
                feedwater_enthalpy=1.0,
                steam_flow_upper_bound=20.0,
            ),
        ),
        gas_turbines=(
            GasTurbineCandidate(
                name="gt_1",
                fuel_lhv=10.0,
                power_slope=0.3,
                power_intercept=0.0,
                min_fuel_flow=0.0,
                max_fuel_flow=10.0,
                minimum_load_fraction=0.0,
            ),
        ),
        hrsgs=(
            HrsgCandidate(
                name="hrsg_1",
                gas_turbine="gt_1",
                vhp_header="VHP_90",
                steam_generation_efficiency=0.8,
                max_heat_input=20.0,
                supplementary_fuel_lhv=5.0,
                max_supplementary_fuel_flow=10.0,
            ),
        ),
        fuel_costs=(
            FuelCost(
                name="gt_fuel",
                equipment_type="gas_turbine",
                equipment_name="gt_1",
                unit_cost=2.0,
            ),
            FuelCost(
                name="hrsg_supplementary_fuel",
                equipment_type="hrsg_supplementary",
                equipment_name="hrsg_1",
                unit_cost=3.0,
            ),
        ),
        power_demand=0.0,
    )
    model = build_utility_system_model(data)

    model.level_selected["LP_120"].fix(0.0)
    model.source_heat_to_steam["LP_120"].fix(0.0)
    model.gas_turbine_fuel_flow["gt_1"].fix(4.0)
    model.hrsg_supplementary_fuel_flow["hrsg_1"].fix(5.0)

    assert pyomo.value(model.fuel_operating_cost["gt_fuel"]) == pytest.approx(80.0)
    assert pyomo.value(
        model.fuel_operating_cost["hrsg_supplementary_fuel"]
    ) == pytest.approx(75.0)
    assert pyomo.value(model.total_fuel_operating_cost) == pytest.approx(155.0)
    assert pyomo.value(model.total_annualized_cost) == pytest.approx(155.0)


def test_electricity_balance_and_grid_limits_are_explicit() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
        ),
        power_demand=25.0,
        grid_import_limit=20.0,
        grid_export_limit=5.0,
        transmission_efficiency=1.0,
    )
    model = build_utility_system_model(data)

    model.grid_power_import.fix(20.0)
    model.onsite_power_generation.fix(10.0)
    model.grid_power_export.fix(5.0)

    assert pyomo.value(model.electricity_balance.body) == pytest.approx(0.0)
    assert pyomo.value(model.grid_import_limit_constraint.body) == pytest.approx(20.0)
    assert pyomo.value(model.grid_export_limit_constraint.body) == pytest.approx(5.0)


def test_cooling_water_load_and_cost_include_bottom_source_residual() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=20.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
            SteamLevelCandidate(
                name="MP_95",
                steam_main="MP",
                temperature=95.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
        ),
        cooling_water=CoolingWaterConfig(
            unit_cost=2.0,
            process_cooling_load=3.0,
            utility_cooling_load=4.0,
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.source_residual_heat["MP_95"].fix(5.0)
    model.cooling_water_total_load.fix(12.0)

    assert pyomo.value(model.cooling_water_total_load_equation.body) == pytest.approx(
        0.0
    )
    assert pyomo.value(model.cooling_water_operating_cost) == pytest.approx(24.0)


def test_cascades_reset_between_steam_mains() -> None:
    data = UtilitySystemModelData(
        steam_mains=("HP", "MP"),
        steam_levels=(
            SteamLevelCandidate(
                name="HP_185",
                steam_main="HP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
            SteamLevelCandidate(
                name="HP_95",
                steam_main="HP",
                temperature=95.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=5.0,
                sink_heat_demand=4.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
        ),
        power_demand=0.0,
    )
    model = build_utility_system_model(data)

    model.source_residual_heat["HP_95"].fix(7.0)
    model.source_heat_to_steam["MP_185"].fix(5.0)
    model.source_residual_heat["MP_185"].fix(0.0)
    model.sink_residual_heat["HP_95"].fix(9.0)
    model.sink_heat_from_steam["MP_185"].fix(4.0)
    model.hot_oil_heat_to_sink["MP_185"].fix(0.0)
    model.sink_residual_heat["MP_185"].fix(0.0)

    assert pyomo.value(model.source_cascade_balance["MP_185"].body) == pytest.approx(
        0.0
    )
    assert pyomo.value(model.sink_cascade_balance["MP_185"].body) == pytest.approx(0.0)


def test_cooling_water_load_sums_bottom_source_residuals_by_main() -> None:
    data = UtilitySystemModelData(
        steam_mains=("HP", "MP"),
        steam_levels=(
            SteamLevelCandidate(
                name="HP_185",
                steam_main="HP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
            SteamLevelCandidate(
                name="HP_95",
                steam_main="HP",
                temperature=95.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
            SteamLevelCandidate(
                name="MP_95",
                steam_main="MP",
                temperature=95.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
        ),
        cooling_water=CoolingWaterConfig(
            unit_cost=2.0,
            process_cooling_load=1.0,
            utility_cooling_load=2.0,
        ),
        power_demand=0.0,
    )
    model = build_utility_system_model(data)

    model.source_residual_heat["HP_95"].fix(3.0)
    model.source_residual_heat["MP_95"].fix(5.0)
    model.cooling_water_total_load.fix(11.0)

    assert pyomo.value(model.cooling_water_total_load_equation.body) == pytest.approx(
        0.0
    )


def test_hot_oil_supplies_selected_sink_heat_and_adds_fuel_cost() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=6.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
                sink_heat_upper_bound=6.0,
            ),
            SteamLevelCandidate(
                name="MP_95",
                steam_main="MP",
                temperature=95.0,
                source_heat_available=0.0,
                sink_heat_demand=4.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
                sink_heat_upper_bound=4.0,
            ),
        ),
        hot_oil=HotOilConfig(
            fuel_unit_cost=3.0,
            thermal_efficiency=0.75,
            high_temperature_heat_demand=2.0,
            supply_temperature=200.0,
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.hot_oil_selected["MP_185"].fix(1.0)
    model.hot_oil_selected["MP_95"].fix(0.0)
    model.level_selected["MP_185"].fix(0.0)
    model.hot_oil_heat_to_sink["MP_185"].fix(6.0)
    model.hot_oil_heat_to_sink["MP_95"].fix(0.0)
    model.sink_heat_from_steam["MP_185"].fix(0.0)
    model.sink_residual_heat["MP_185"].fix(0.0)
    model.total_hot_oil_heat_load.fix(8.0)
    model.hot_oil_fuel_consumption.fix(8.0 / 0.75)

    assert pyomo.value(model.sink_cascade_balance["MP_185"].body) == pytest.approx(0.0)
    assert pyomo.value(model.hot_oil_heat_to_sink_equation["MP_185"].body) == (
        pytest.approx(0.0)
    )
    assert pyomo.value(model.total_hot_oil_heat_load_equation.body) == pytest.approx(
        0.0
    )
    assert pyomo.value(model.hot_oil_fuel_consumption_equation.body) == pytest.approx(
        0.0
    )
    assert pyomo.value(model.hot_oil_operating_cost) == pytest.approx(32.0)


def test_hot_oil_temperature_order_resets_between_steam_mains() -> None:
    data = UtilitySystemModelData(
        steam_mains=("HP", "MP"),
        steam_levels=(
            SteamLevelCandidate(
                name="HP_185",
                steam_main="HP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=6.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
                sink_heat_upper_bound=6.0,
            ),
            SteamLevelCandidate(
                name="HP_95",
                steam_main="HP",
                temperature=95.0,
                source_heat_available=0.0,
                sink_heat_demand=4.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
                sink_heat_upper_bound=4.0,
            ),
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=6.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
                sink_heat_upper_bound=6.0,
            ),
        ),
        hot_oil=HotOilConfig(
            fuel_unit_cost=3.0,
            thermal_efficiency=0.75,
            supply_temperature=200.0,
        ),
        power_demand=0.0,
    )
    model = build_utility_system_model(data)

    assert "MP_185" not in model.hot_oil_temperature_order
    assert "HP_95" in model.hot_oil_temperature_order


def test_hot_oil_furnace_cost_uses_total_heat_load_and_selection() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=6.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
                sink_heat_upper_bound=6.0,
            ),
            SteamLevelCandidate(
                name="MP_95",
                steam_main="MP",
                temperature=95.0,
                source_heat_available=0.0,
                sink_heat_demand=4.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
                sink_heat_upper_bound=4.0,
            ),
        ),
        hot_oil=HotOilConfig(
            fuel_unit_cost=3.0,
            thermal_efficiency=0.75,
            high_temperature_heat_demand=2.0,
            supply_temperature=200.0,
        ),
        equipment_costs=(
            EquipmentCost(
                name="hot_oil_furnace_cost",
                equipment_type="hot_oil_furnace",
                equipment_name="hot_oil",
                annualization_factor=0.2,
                installation_factor=2.0,
                variable_capital_cost=10.0,
                fixed_capital_cost=100.0,
                variable_maintenance_cost=1.0,
                fixed_maintenance_cost=5.0,
            ),
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.level_selected["MP_185"].fix(0.0)
    model.source_heat_to_steam["MP_185"].fix(0.0)
    model.level_selected["MP_95"].fix(0.0)
    model.source_heat_to_steam["MP_95"].fix(0.0)
    model.hot_oil_furnace_selected.fix(1.0)
    model.total_hot_oil_heat_load.fix(8.0)
    model.hot_oil_fuel_consumption.fix(8.0 / 0.75)

    assert pyomo.value(
        model.equipment_annualized_capital_cost["hot_oil_furnace_cost"]
    ) == pytest.approx(72.0)
    assert pyomo.value(
        model.equipment_maintenance_cost["hot_oil_furnace_cost"]
    ) == pytest.approx(13.0)
    assert pyomo.value(model.total_annualized_cost) == pytest.approx(117.0)


def test_hot_oil_selection_prefers_higher_temperatures_and_excludes_steam() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=6.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
            SteamLevelCandidate(
                name="MP_95",
                steam_main="MP",
                temperature=95.0,
                source_heat_available=0.0,
                sink_heat_demand=4.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
        ),
        hot_oil=HotOilConfig(
            fuel_unit_cost=3.0,
            thermal_efficiency=0.75,
            supply_temperature=200.0,
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.hot_oil_selected["MP_185"].fix(1.0)
    model.hot_oil_selected["MP_95"].fix(1.0)
    model.level_selected["MP_95"].fix(0.0)

    assert pyomo.value(model.hot_oil_temperature_order["MP_95"].body) == (
        pytest.approx(0.0)
    )
    assert pyomo.value(model.hot_oil_excludes_steam_level["MP_95"].body) == (
        pytest.approx(1.0)
    )


def test_vhp_turbine_and_letdown_connections_feed_selected_header() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
                steam_flow_upper_bound=10.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_90",
                steam_enthalpy=5.0,
                feedwater_enthalpy=1.0,
                steam_flow_upper_bound=20.0,
            ),
        ),
        vhp_turbines=(
            VhpBackPressureTurbineCandidate(
                name="turbine_1",
                vhp_header="VHP_90",
                steam_level="MP_185",
                power_slope=0.5,
                power_intercept=0.2,
                min_capacity=1.0,
                max_capacity=10.0,
                minimum_load_fraction=0.2,
            ),
        ),
        vhp_letdowns=(
            VhpLetdownStationCandidate(
                name="letdown_1",
                vhp_header="VHP_90",
                steam_level="MP_185",
                max_flow=10.0,
            ),
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.vhp_turbine_selected["turbine_1"].fix(1.0)
    model.vhp_turbine_steam_flow["turbine_1"].fix(4.0)
    model.vhp_turbine_power_generation["turbine_1"].fix(1.8)
    model.vhp_letdown_flow["letdown_1"].fix(3.0)
    model.utility_steam_from_vhp["VHP_90", "MP_185"].fix(7.0)

    assert pyomo.value(
        model.vhp_turbine_power_equation["turbine_1"].body
    ) == pytest.approx(0.0)
    assert pyomo.value(
        model.vhp_connection_flow_aggregation["VHP_90", "MP_185"].body
    ) == pytest.approx(0.0)


def test_vhp_utility_steam_requires_configured_connection() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
                steam_flow_upper_bound=10.0,
            ),
            SteamLevelCandidate(
                name="MP_95",
                steam_main="MP",
                temperature=95.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
                steam_flow_upper_bound=10.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_90",
                steam_enthalpy=5.0,
                feedwater_enthalpy=1.0,
                steam_flow_upper_bound=20.0,
            ),
        ),
        vhp_letdowns=(
            VhpLetdownStationCandidate(
                name="letdown_1",
                vhp_header="VHP_90",
                steam_level="MP_185",
                max_flow=10.0,
            ),
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    assert ("VHP_90", "MP_95") in model.vhp_connection_flow_aggregation
    model.utility_steam_from_vhp["VHP_90", "MP_95"].fix(1.0)

    assert pyomo.value(
        model.vhp_connection_flow_aggregation["VHP_90", "MP_95"].body
    ) == pytest.approx(1.0)


def test_vhp_turbine_power_feeds_onsite_power_generation() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_90",
                steam_enthalpy=5.0,
                feedwater_enthalpy=1.0,
                steam_flow_upper_bound=20.0,
            ),
        ),
        vhp_turbines=(
            VhpBackPressureTurbineCandidate(
                name="turbine_1",
                vhp_header="VHP_90",
                steam_level="MP_185",
                power_slope=0.5,
                power_intercept=0.2,
                min_capacity=1.0,
                max_capacity=10.0,
                minimum_load_fraction=0.2,
            ),
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.vhp_turbine_power_generation["turbine_1"].fix(1.8)
    model.onsite_power_generation.fix(1.8)

    assert pyomo.value(model.onsite_power_generation_equation.body) == pytest.approx(
        0.0
    )


def test_vhp_turbine_selection_requires_selected_vhp_and_header() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_90",
                steam_enthalpy=5.0,
                feedwater_enthalpy=1.0,
                steam_flow_upper_bound=20.0,
            ),
        ),
        vhp_turbines=(
            VhpBackPressureTurbineCandidate(
                name="turbine_1",
                vhp_header="VHP_90",
                steam_level="MP_185",
                power_slope=0.5,
                power_intercept=0.2,
                min_capacity=1.0,
                max_capacity=10.0,
                minimum_load_fraction=0.2,
            ),
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.vhp_turbine_selected["turbine_1"].fix(1.0)
    model.vhp_selected["VHP_90"].fix(1.0)
    model.level_selected["MP_185"].fix(1.0)

    assert pyomo.value(
        model.vhp_turbine_requires_selected_vhp["turbine_1"].body
    ) == pytest.approx(0.0)
    assert pyomo.value(
        model.vhp_turbine_requires_selected_level["turbine_1"].body
    ) == pytest.approx(0.0)


def test_gas_turbine_generates_power_and_exhaust_heat() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
        ),
        gas_turbines=(
            GasTurbineCandidate(
                name="gt_1",
                fuel_lhv=10.0,
                power_slope=0.4,
                power_intercept=0.5,
                min_fuel_flow=1.0,
                max_fuel_flow=10.0,
                minimum_load_fraction=0.2,
            ),
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.gas_turbine_selected["gt_1"].fix(1.0)
    model.gas_turbine_fuel_flow["gt_1"].fix(5.0)
    model.gas_turbine_power_generation["gt_1"].fix(1.5)
    model.gas_turbine_exhaust_heat["gt_1"].fix(48.5)

    assert pyomo.value(model.gas_turbine_power_equation["gt_1"].body) == pytest.approx(
        0.0
    )
    assert pyomo.value(
        model.gas_turbine_exhaust_heat_equation["gt_1"].body
    ) == pytest.approx(0.0)


def test_hrsg_uses_gas_turbine_exhaust_to_generate_vhp_steam() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_90",
                steam_enthalpy=5.0,
                feedwater_enthalpy=1.0,
                steam_flow_upper_bound=20.0,
            ),
        ),
        gas_turbines=(
            GasTurbineCandidate(
                name="gt_1",
                fuel_lhv=10.0,
                power_slope=0.4,
                power_intercept=0.5,
                min_fuel_flow=1.0,
                max_fuel_flow=10.0,
                minimum_load_fraction=0.2,
            ),
        ),
        hrsgs=(
            HrsgCandidate(
                name="hrsg_1",
                gas_turbine="gt_1",
                vhp_header="VHP_90",
                steam_generation_efficiency=0.8,
                max_heat_input=50.0,
            ),
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.gas_turbine_exhaust_heat["gt_1"].fix(20.0)
    model.hrsg_exhaust_heat_input["hrsg_1"].fix(20.0)
    model.hrsg_heat_input["hrsg_1"].fix(20.0)
    model.hrsg_steam_generation["hrsg_1"].fix(4.0)
    model.utility_steam_from_vhp["VHP_90", "MP_185"].fix(4.0)

    assert pyomo.value(model.hrsg_total_heat_input_equation["hrsg_1"].body) == (
        pytest.approx(0.0)
    )
    assert pyomo.value(model.hrsg_steam_generation_equation["hrsg_1"].body) == (
        pytest.approx(0.0)
    )
    assert pyomo.value(model.hrsg_heat_from_exhaust["hrsg_1"].body) == pytest.approx(
        0.0
    )
    assert pyomo.value(model.vhp_mass_balance["VHP_90"].body) == pytest.approx(0.0)


def test_hrsg_supplementary_firing_adds_heat_input() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_90",
                steam_enthalpy=5.0,
                feedwater_enthalpy=1.0,
                steam_flow_upper_bound=20.0,
            ),
        ),
        gas_turbines=(
            GasTurbineCandidate(
                name="gt_1",
                fuel_lhv=10.0,
                power_slope=0.4,
                power_intercept=0.5,
                min_fuel_flow=1.0,
                max_fuel_flow=10.0,
                minimum_load_fraction=0.2,
            ),
        ),
        hrsgs=(
            HrsgCandidate(
                name="hrsg_1",
                gas_turbine="gt_1",
                vhp_header="VHP_90",
                steam_generation_efficiency=0.8,
                max_heat_input=50.0,
                supplementary_fuel_lhv=10.0,
                supplementary_firing_efficiency=0.9,
                max_supplementary_fuel_flow=2.0,
            ),
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.gas_turbine_selected["gt_1"].fix(1.0)
    model.gas_turbine_exhaust_heat["gt_1"].fix(20.0)
    model.hrsg_exhaust_heat_input["hrsg_1"].fix(20.0)
    model.hrsg_supplementary_firing_selected["hrsg_1"].fix(1.0)
    model.hrsg_supplementary_fuel_flow["hrsg_1"].fix(1.0)
    model.hrsg_heat_input["hrsg_1"].fix(29.0)
    model.hrsg_steam_generation["hrsg_1"].fix(5.8)

    assert pyomo.value(model.hrsg_total_heat_input_equation["hrsg_1"].body) == (
        pytest.approx(0.0)
    )
    assert pyomo.value(model.hrsg_steam_generation_equation["hrsg_1"].body) == (
        pytest.approx(0.0)
    )
    assert pyomo.value(
        model.hrsg_supplementary_fuel_upper_bound["hrsg_1"].body
    ) == pytest.approx(-1.0)
    assert pyomo.value(
        model.hrsg_supplementary_firing_requires_gas_turbine["hrsg_1"].body
    ) == pytest.approx(0.0)


def test_gas_turbine_power_feeds_onsite_power_generation() -> None:
    data = UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_185",
                steam_main="MP",
                temperature=185.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=2.0,
                use_enthalpy_delta=3.0,
            ),
        ),
        gas_turbines=(
            GasTurbineCandidate(
                name="gt_1",
                fuel_lhv=10.0,
                power_slope=0.4,
                power_intercept=0.5,
                min_fuel_flow=1.0,
                max_fuel_flow=10.0,
                minimum_load_fraction=0.2,
            ),
        ),
        power_demand=25.0,
    )
    model = build_utility_system_model(data)

    model.gas_turbine_power_generation["gt_1"].fix(1.5)
    model.onsite_power_generation.fix(1.5)

    assert pyomo.value(model.onsite_power_generation_equation.body) == pytest.approx(
        0.0
    )
