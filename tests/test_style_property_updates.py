from __future__ import annotations

import pytest

from OpenUtility.style import (
    CoolPropSteamPropertyProvider,
    SteamLevelCandidate,
    SteamLevelPropertyTarget,
    SteamPropertyUpdateSpec,
    SteamTurbinePropertyTarget,
    StyleModelData,
    VhpBackPressureTurbineCandidate,
    VhpHeaderPropertyTarget,
    VhpSteamCandidate,
    apply_steam_property_update,
    build_static_style_model,
    run_successive_milp_property_updates,
    SteamMainBackPressureTurbineCandidate,
    SteamMainLetdownStationCandidate,
    steam_main_superheating_balances_from_model,
    steam_property_update_spec_from_stage4_model,
    steam_property_update_spec_from_model,
)


class FakeSteamProperties:
    def enthalpy(self, *, pressure: float, temperature: float) -> float:
        return 10.0 * pressure + temperature

    def temperature(self, *, pressure: float, enthalpy: float) -> float:
        return enthalpy - 10.0 * pressure

    def isentropic_enthalpy_change(
        self,
        *,
        inlet_pressure: float,
        outlet_pressure: float,
        inlet_temperature: float,
    ) -> float:
        return inlet_pressure - outlet_pressure + inlet_temperature / 1000.0


def test_apply_steam_property_update_replaces_pseudo_parameters_immutably() -> None:
    data = _style_data()
    spec = _property_spec(180.0)

    update = apply_steam_property_update(data, spec, FakeSteamProperties())

    level = update.data.steam_levels[0]
    assert data.steam_levels[0].main_steam_enthalpy is None
    assert level.main_steam_enthalpy == pytest.approx(210.0)
    assert level.utility_steam_enthalpy == pytest.approx(210.0)
    assert level.generated_steam_enthalpy == pytest.approx(185.0)
    assert level.steam_enthalpy_for_use == pytest.approx(175.0)
    assert update.data.vhp_headers[0].steam_enthalpy == pytest.approx(1470.0)
    assert update.snapshot.level_temperatures == {"MP_3": 180.0}
    assert update.snapshot.vhp_temperatures == {"VHP_90": 570.0}
    assert update.snapshot.isentropic_enthalpy_deltas == {
        "VHP_ST_1": pytest.approx(87.57),
    }


def test_coolprop_steam_property_provider_uses_bar_celsius_and_mwh_per_tonne() -> None:
    properties = CoolPropSteamPropertyProvider()

    assert properties.enthalpy(pressure=100.0, temperature=570.0) == pytest.approx(
        0.9866,
        abs=1e-4,
    )
    assert properties.temperature(pressure=100.0, enthalpy=0.1231664) == pytest.approx(
        104.0,
        abs=1e-3,
    )
    assert properties.isentropic_enthalpy_change(
        inlet_pressure=100.0,
        outlet_pressure=20.0,
        inlet_temperature=570.0,
    ) == pytest.approx(0.1385, abs=1e-4)


def test_coolprop_steam_property_provider_returns_saturated_enthalpies() -> None:
    properties = CoolPropSteamPropertyProvider()

    vapor, liquid = properties.saturated_enthalpies(pressure=20.0)

    assert vapor == pytest.approx(0.7773, abs=1e-4)
    assert liquid == pytest.approx(0.2524, abs=1e-4)


def test_apply_steam_property_update_rejects_unknown_targets() -> None:
    spec = SteamPropertyUpdateSpec(
        levels=(
            SteamLevelPropertyTarget(
                steam_level="unknown",
                pressure=3.0,
                main_temperature=180.0,
                minimum_temperature=170.0,
            ),
        ),
    )

    with pytest.raises(ValueError, match="unknown steam level"):
        apply_steam_property_update(_style_data(), spec, FakeSteamProperties())


def test_successive_milp_property_updates_stop_when_temperatures_converge() -> None:
    seen_main_enthalpies = []
    temperatures = iter((182.0, 183.0, 183.05))

    def solve(data: StyleModelData, iteration: int) -> SteamPropertyUpdateSpec:
        seen_main_enthalpies.append(
            (iteration, data.steam_levels[0].main_steam_enthalpy)
        )
        return _property_spec(next(temperatures))

    run = run_successive_milp_property_updates(
        _style_data(),
        initial_spec=_property_spec(180.0),
        solve=solve,
        properties=FakeSteamProperties(),
        convergence_tolerance=0.1,
        max_iterations=5,
    )

    assert run.converged is True
    assert len(run.iterations) == 3
    assert run.iterations[-1].max_temperature_change == pytest.approx(0.05)
    assert run.final_update.snapshot.level_temperatures["MP_3"] == pytest.approx(
        183.05,
    )
    assert run.final_update.data.steam_levels[0].main_steam_enthalpy == pytest.approx(
        213.05,
    )
    assert seen_main_enthalpies == [
        (1, pytest.approx(210.0)),
        (2, pytest.approx(212.0)),
        (3, pytest.approx(213.0)),
    ]


def test_successive_milp_property_updates_report_nonconvergence() -> None:
    temperatures = iter((182.0, 184.0))

    def solve(_: StyleModelData, __: int) -> SteamPropertyUpdateSpec:
        return _property_spec(next(temperatures))

    run = run_successive_milp_property_updates(
        _style_data(),
        initial_spec=_property_spec(180.0),
        solve=solve,
        properties=FakeSteamProperties(),
        convergence_tolerance=0.1,
        max_iterations=2,
    )

    assert run.converged is False
    assert len(run.iterations) == 2
    assert run.iterations[-1].max_temperature_change == pytest.approx(2.0)


def test_steam_property_update_spec_from_model_uses_selected_pyomo_options() -> None:
    data = _style_data_with_two_levels()
    model = build_static_style_model(data)
    model.level_selected["HP_12"].fix(0.0)
    model.level_selected["MP_3"].fix(1.0)
    model.vhp_selected["VHP_90"].fix(1.0)
    model.vhp_turbine_selected["VHP_to_HP"].fix(0.0)
    model.vhp_turbine_selected["VHP_to_MP"].fix(1.0)

    spec = steam_property_update_spec_from_model(
        data,
        model,
        level_targets=(
            SteamLevelPropertyTarget(
                steam_level="HP_12",
                pressure=12.0,
                main_temperature=220.0,
                minimum_temperature=210.0,
            ),
            SteamLevelPropertyTarget(
                steam_level="MP_3",
                pressure=3.0,
                main_temperature=180.0,
                minimum_temperature=170.0,
                process_generation_temperature=155.0,
                process_use_temperature=145.0,
            ),
        ),
        vhp_targets=(
            VhpHeaderPropertyTarget(
                vhp_header="VHP_90",
                pressure=90.0,
                temperature=570.0,
                maximum_temperature=570.0,
            ),
        ),
    )

    assert spec.levels == (
        SteamLevelPropertyTarget(
            steam_level="MP_3",
            pressure=3.0,
            main_temperature=180.0,
            minimum_temperature=170.0,
            process_generation_temperature=155.0,
            process_use_temperature=145.0,
        ),
    )
    assert spec.vhp_headers == (
        VhpHeaderPropertyTarget(
            vhp_header="VHP_90",
            pressure=90.0,
            temperature=570.0,
            maximum_temperature=570.0,
        ),
    )
    assert spec.turbines == (
        SteamTurbinePropertyTarget(
            name="VHP_to_MP",
            inlet_pressure=90.0,
            outlet_pressure=3.0,
            inlet_temperature=570.0,
        ),
    )


def test_steam_property_update_spec_from_model_rejects_missing_level_target() -> None:
    data = _style_data_with_two_levels()
    model = build_static_style_model(data)
    model.level_selected["HP_12"].fix(0.0)
    model.level_selected["MP_3"].fix(1.0)
    model.vhp_selected["VHP_90"].fix(1.0)
    model.vhp_turbine_selected["VHP_to_HP"].fix(0.0)
    model.vhp_turbine_selected["VHP_to_MP"].fix(0.0)

    with pytest.raises(ValueError, match="missing property target for steam level"):
        steam_property_update_spec_from_model(
            data,
            model,
            level_targets=(),
            vhp_targets=(
                VhpHeaderPropertyTarget(
                    vhp_header="VHP_90",
                    pressure=90.0,
                    temperature=570.0,
                ),
            ),
        )


def test_steam_main_superheating_balances_from_solved_model_flows() -> None:
    data = _stage4_style_data()
    model = build_static_style_model(data)
    _fix_stage4_solution(model)

    balances = steam_main_superheating_balances_from_model(
        data,
        model,
        level_targets=(
            SteamLevelPropertyTarget(
                steam_level="MP_3",
                pressure=3.0,
                main_temperature=180.0,
                minimum_temperature=170.0,
                process_generation_temperature=155.0,
                process_use_temperature=145.0,
            ),
        ),
        vhp_targets=(
            VhpHeaderPropertyTarget(
                vhp_header="VHP_12",
                pressure=12.0,
                temperature=200.0,
            ),
        ),
        properties=FakeSteamProperties(),
    )

    assert len(balances) == 1
    balance = balances[0]
    assert balance.steam_level == "MP_3"
    assert balance.source_steam_mass == pytest.approx(1.0)
    assert balance.utility_steam_mass == pytest.approx(2.0)
    assert balance.feedwater_mass == pytest.approx(1.0)
    assert balance.outlet_mass == pytest.approx(4.0)
    assert balance.inlet_heat == pytest.approx(835.0)
    assert balance.calculated_enthalpy == pytest.approx(208.75)
    assert balance.calculated_temperature == pytest.approx(178.75)
    assert balance.superheat_margin == pytest.approx(8.75)
    assert balance.minimum_temperature_satisfied is True


def test_stage4_model_spec_uses_calculated_superheating_temperatures() -> None:
    data = _stage4_style_data()
    model = build_static_style_model(data)
    _fix_stage4_solution(model)

    spec = steam_property_update_spec_from_stage4_model(
        data,
        model,
        level_targets=(
            SteamLevelPropertyTarget(
                steam_level="MP_3",
                pressure=3.0,
                main_temperature=180.0,
                minimum_temperature=170.0,
                process_generation_temperature=155.0,
                process_use_temperature=145.0,
            ),
        ),
        vhp_targets=(
            VhpHeaderPropertyTarget(
                vhp_header="VHP_12",
                pressure=12.0,
                temperature=200.0,
            ),
        ),
        properties=FakeSteamProperties(),
    )

    assert spec.levels == (
        SteamLevelPropertyTarget(
            steam_level="MP_3",
            pressure=3.0,
            main_temperature=178.75,
            minimum_temperature=170.0,
            process_generation_temperature=155.0,
            process_use_temperature=145.0,
        ),
    )
    assert spec.vhp_headers == (
        VhpHeaderPropertyTarget(
            vhp_header="VHP_12",
            pressure=12.0,
            temperature=200.0,
        ),
    )
    assert spec.turbines == (
        SteamTurbinePropertyTarget(
            name="VHP_to_MP",
            inlet_pressure=12.0,
            outlet_pressure=3.0,
            inlet_temperature=200.0,
        ),
    )


def test_stage4_superheating_balance_includes_inter_header_connections() -> None:
    data = _stage4_inter_header_style_data()
    model = build_static_style_model(data)
    _fix_stage4_inter_header_solution(model)

    balances = steam_main_superheating_balances_from_model(
        data,
        model,
        level_targets=(
            SteamLevelPropertyTarget(
                steam_level="HP_12",
                pressure=12.0,
                main_temperature=220.0,
                minimum_temperature=210.0,
            ),
            SteamLevelPropertyTarget(
                steam_level="MP_3",
                pressure=3.0,
                main_temperature=180.0,
                minimum_temperature=170.0,
                process_generation_temperature=155.0,
            ),
        ),
        vhp_targets=(),
        properties=FakeSteamProperties(),
    )

    assert tuple(balance.steam_level for balance in balances) == ("HP_12", "MP_3")
    hp_balance, mp_balance = balances
    assert hp_balance.calculated_enthalpy == pytest.approx(340.0)
    assert hp_balance.calculated_temperature == pytest.approx(220.0)
    assert mp_balance.source_steam_mass == pytest.approx(1.0)
    assert mp_balance.utility_steam_mass == pytest.approx(3.0)
    assert mp_balance.feedwater_mass == pytest.approx(1.0)
    assert mp_balance.outlet_mass == pytest.approx(5.0)
    assert mp_balance.inlet_heat == pytest.approx(1205.0)
    assert mp_balance.calculated_enthalpy == pytest.approx(241.0)
    assert mp_balance.calculated_temperature == pytest.approx(211.0)
    assert mp_balance.minimum_temperature_satisfied is True


def _style_data() -> StyleModelData:
    return StyleModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_3",
                steam_main="MP",
                temperature=134.0,
                source_heat_available=10.0,
                sink_heat_demand=5.0,
                generation_enthalpy_delta=1.0,
                use_enthalpy_delta=1.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_90",
                steam_enthalpy=1.0,
                feedwater_enthalpy=0.5,
                steam_flow_upper_bound=100.0,
            ),
        ),
        power_demand=0.0,
    )


def _stage4_inter_header_style_data() -> StyleModelData:
    return StyleModelData(
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
            ),
            SteamLevelCandidate(
                name="MP_3",
                steam_main="MP",
                temperature=134.0,
                source_heat_available=10.0,
                sink_heat_demand=5.0,
                generation_enthalpy_delta=1.0,
                use_enthalpy_delta=1.0,
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


def _fix_stage4_inter_header_solution(model) -> None:
    model.level_selected["HP_12"].fix(1.0)
    model.level_selected["MP_3"].fix(1.0)
    model.source_steam_generated["HP_12"].fix(3.0)
    model.feedwater_to_header["HP_12"].fix(0.0)
    model.process_steam_to_sink["HP_12"].fix(0.0)
    model.header_steam_export["HP_12"].fix(0.0)
    model.deaerator_steam_from_header["HP_12"].fix(0.0)
    model.source_steam_generated["MP_3"].fix(1.0)
    model.feedwater_to_header["MP_3"].fix(1.0)
    model.process_steam_to_sink["MP_3"].fix(5.0)
    model.header_steam_export["MP_3"].fix(0.0)
    model.deaerator_steam_from_header["MP_3"].fix(0.0)
    model.steam_main_turbine_selected["HP_to_MP_ST"].fix(1.0)
    model.steam_main_turbine_steam_flow["HP_to_MP_ST"].fix(2.0)
    model.steam_main_turbine_power_generation["HP_to_MP_ST"].fix(20.0)
    model.steam_main_letdown_flow["HP_to_MP_LD"].fix(1.0)


def _stage4_style_data() -> StyleModelData:
    return StyleModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_3",
                steam_main="MP",
                temperature=134.0,
                source_heat_available=10.0,
                sink_heat_demand=5.0,
                generation_enthalpy_delta=1.0,
                use_enthalpy_delta=1.0,
                feedwater_enthalpy=20.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_12",
                steam_enthalpy=1.0,
                feedwater_enthalpy=0.5,
                steam_flow_upper_bound=100.0,
            ),
        ),
        vhp_turbines=(
            VhpBackPressureTurbineCandidate(
                name="VHP_to_MP",
                vhp_header="VHP_12",
                steam_level="MP_3",
                power_slope=0.1,
                power_intercept=0.0,
                min_capacity=0.0,
                max_capacity=100.0,
                minimum_load_fraction=0.0,
            ),
        ),
        power_demand=0.0,
    )


def _fix_stage4_solution(model) -> None:
    model.level_selected["MP_3"].fix(1.0)
    model.vhp_selected["VHP_12"].fix(1.0)
    model.source_steam_generated["MP_3"].fix(1.0)
    model.feedwater_to_header["MP_3"].fix(1.0)
    model.process_steam_to_sink["MP_3"].fix(4.0)
    model.header_steam_export["MP_3"].fix(0.0)
    model.deaerator_steam_from_header["MP_3"].fix(0.0)
    model.utility_steam_from_vhp["VHP_12", "MP_3"].fix(2.0)
    model.vhp_turbine_selected["VHP_to_MP"].fix(1.0)
    model.vhp_turbine_steam_flow["VHP_to_MP"].fix(2.0)
    model.vhp_turbine_power_generation["VHP_to_MP"].fix(10.0)


def _style_data_with_two_levels() -> StyleModelData:
    return StyleModelData(
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
            ),
            SteamLevelCandidate(
                name="MP_3",
                steam_main="MP",
                temperature=134.0,
                source_heat_available=10.0,
                sink_heat_demand=5.0,
                generation_enthalpy_delta=1.0,
                use_enthalpy_delta=1.0,
            ),
        ),
        vhp_headers=(
            VhpSteamCandidate(
                name="VHP_90",
                steam_enthalpy=1.0,
                feedwater_enthalpy=0.5,
                steam_flow_upper_bound=100.0,
            ),
        ),
        vhp_turbines=(
            VhpBackPressureTurbineCandidate(
                name="VHP_to_HP",
                vhp_header="VHP_90",
                steam_level="HP_12",
                power_slope=0.1,
                power_intercept=0.0,
                min_capacity=0.0,
                max_capacity=100.0,
                minimum_load_fraction=0.0,
            ),
            VhpBackPressureTurbineCandidate(
                name="VHP_to_MP",
                vhp_header="VHP_90",
                steam_level="MP_3",
                power_slope=0.1,
                power_intercept=0.0,
                min_capacity=0.0,
                max_capacity=100.0,
                minimum_load_fraction=0.0,
            ),
        ),
        power_demand=0.0,
    )


def _property_spec(main_temperature: float) -> SteamPropertyUpdateSpec:
    return SteamPropertyUpdateSpec(
        levels=(
            SteamLevelPropertyTarget(
                steam_level="MP_3",
                pressure=3.0,
                main_temperature=main_temperature,
                minimum_temperature=170.0,
                process_generation_temperature=155.0,
                process_use_temperature=145.0,
            ),
        ),
        vhp_headers=(
            VhpHeaderPropertyTarget(
                vhp_header="VHP_90",
                pressure=90.0,
                temperature=570.0,
                maximum_temperature=570.0,
            ),
        ),
        turbines=(
            SteamTurbinePropertyTarget(
                name="VHP_ST_1",
                inlet_pressure=90.0,
                outlet_pressure=3.0,
                inlet_temperature=570.0,
            ),
        ),
    )
