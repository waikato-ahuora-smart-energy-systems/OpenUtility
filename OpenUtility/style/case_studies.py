"""STYLE case-study data builders from extracted benchmark fixtures."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from case_study.jimenez_romero_utility_system_optimization.benchmarks import (
    CONTRIBUTION2_CASE_STUDY_2_BEST_CONFIGURATIONS,
    STYLE_GAS_TURBINE_AMBIENT_CORRECTION,
    STYLE_GAS_TURBINE_FULL_LOAD_COEFFICIENTS,
    STYLE_CASE_STUDY_2_EQUIPMENT_COSTS,
    STYLE_CASE_STUDY_2_RESOURCES,
    STYLE_CASE_STUDY_2_SITE_CONFIG,
    STYLE_CASE_STUDY_2_STREAMS,
    StyleGasTurbineFullLoadCoefficient,
    StyleEquipmentCostCoefficient,
    StyleResource,
    get_contribution2_case_study2_best_configuration,
    get_style_result,
)
from OpenUtility.thermal import (
    HeatIntervalProfile,
    build_temperature_intervals,
    heat_content_by_interval,
    openpinch_streams_from_case_study_streams,
)

from .adapters import (
    style_model_data_from_heat_profile,
    style_model_data_from_heat_profile_for_steam_mains,
)
from .data import (
    BoilerCandidate,
    CoolingWaterConfig,
    ElectricityCost,
    EquipmentCost,
    FlashSteamRecoveryConfig,
    FlashSteamRecoveryLevel,
    FlashSteamRecoveryRoute,
    FuelCost,
    FuelConsumptionAccountingFactor,
    GasTurbineCandidate,
    HotOilConfig,
    HrsgCandidate,
    OperatingCostAccountingAdjustment,
    SteamMainBackPressureTurbineCandidate,
    SteamMainLetdownStationCandidate,
    SteamLevelCandidate,
    StyleModelData,
    VhpBackPressureTurbineCandidate,
    VhpLetdownStationCandidate,
    VhpSteamCandidate,
    VhpSteamSourceCandidate,
    WaterCost,
)
from .properties import (
    CoolPropSteamPropertyProvider,
    SteamLevelPropertyTarget,
    SteamPropertyProvider,
    SteamPropertyUpdateSpec,
    VhpHeaderPropertyTarget,
    apply_steam_property_update,
)
from .runner import StaticStyleScenario
from .scenarios import StaticStyleScenarioCatalog


_DEFAULT_MODEL_EQUIPMENT_TYPES = {
    "boiler": "boiler",
    "gas-turbine": "gas_turbine",
    "hot-oil-furnace": "hot_oil_furnace",
    "hrsg": "hrsg",
}


def style_case_study_2_heat_interval_profile(
    *,
    precision: int = 10,
    use_openpinch_streams: bool = True,
) -> HeatIntervalProfile:
    """Build the shifted heat-interval profile for STYLE case study 2."""

    streams = STYLE_CASE_STUDY_2_STREAMS
    if use_openpinch_streams:
        try:
            streams = openpinch_streams_from_case_study_streams(
                STYLE_CASE_STUDY_2_STREAMS,
            )
        except ImportError:
            streams = STYLE_CASE_STUDY_2_STREAMS
    intervals = build_temperature_intervals(
        streams,
        precision=precision,
    )
    return heat_content_by_interval(streams, intervals)


def style_case_study_2_base_model_data(
    *,
    steam_main: str,
    generation_enthalpy_delta: float,
    use_enthalpy_delta: float,
    steam_enthalpy_for_use: float | None = None,
    feedwater_enthalpy: float = 0.0,
) -> StyleModelData:
    """Create base STYLE model data from case-study 2 stream and site fixtures."""

    profile = style_case_study_2_heat_interval_profile()
    base_data = style_model_data_from_heat_profile(
        profile,
        steam_main=steam_main,
        power_demand=STYLE_CASE_STUDY_2_SITE_CONFIG.power_demand,
        generation_enthalpy_delta=generation_enthalpy_delta,
        use_enthalpy_delta=use_enthalpy_delta,
        steam_enthalpy_for_use=steam_enthalpy_for_use,
        feedwater_enthalpy=feedwater_enthalpy,
    )
    return replace(
        base_data,
        grid_export_limit=STYLE_CASE_STUDY_2_SITE_CONFIG.max_power_export,
        operating_hours=STYLE_CASE_STUDY_2_SITE_CONFIG.operating_hours,
        cost_scale=1e-6,
        electricity_cost=style_case_study_2_electricity_cost(),
        cooling_water=style_case_study_2_cooling_water_config(),
        water_cost=style_case_study_2_water_cost(),
    )


def style_case_study_2_static_scenario(
    *,
    scenario: str,
    steam_main: str,
    generation_enthalpy_delta: float,
    use_enthalpy_delta: float,
    steam_enthalpy_for_use: float | None = None,
    feedwater_enthalpy: float = 0.0,
    absolute_tolerance: float = 1e-6,
) -> StaticStyleScenario:
    """Create an explicitly parameterized static STYLE case-study 2 scenario."""

    return StaticStyleScenario(
        case_study="case-study-2",
        scenario=scenario,
        data=style_case_study_2_base_model_data(
            steam_main=steam_main,
            generation_enthalpy_delta=generation_enthalpy_delta,
            use_enthalpy_delta=use_enthalpy_delta,
            steam_enthalpy_for_use=steam_enthalpy_for_use,
            feedwater_enthalpy=feedwater_enthalpy,
        ),
        benchmark=get_style_result("case-study-2", scenario),
        absolute_tolerance=absolute_tolerance,
    )


def style_case_study_2_gas_turbine_scenario_data(
    *,
    steam_main: str,
    generation_enthalpy_delta: float,
    use_enthalpy_delta: float,
    gas_turbine_name: str,
    turbine_type: str,
    fuel: str,
    max_power_generation: float,
    minimum_load_fraction: float = 0.0,
    ambient_temperature: float = 15.0,
    steam_enthalpy_for_use: float | None = None,
    feedwater_enthalpy: float = 0.0,
) -> StyleModelData:
    """Return case-study 2 base data with one derived gas-turbine option."""

    base_data = style_case_study_2_base_model_data(
        steam_main=steam_main,
        generation_enthalpy_delta=generation_enthalpy_delta,
        use_enthalpy_delta=use_enthalpy_delta,
        steam_enthalpy_for_use=steam_enthalpy_for_use,
        feedwater_enthalpy=feedwater_enthalpy,
    )
    gas_turbine = style_case_study_2_gas_turbine_candidate(
        name=gas_turbine_name,
        turbine_type=turbine_type,
        fuel=fuel,
        max_power_generation=max_power_generation,
        minimum_load_fraction=minimum_load_fraction,
        ambient_temperature=ambient_temperature,
    )
    return replace(
        base_data,
        gas_turbines=(gas_turbine,),
        fuel_costs=(
            style_case_study_2_fuel_cost(
                fuel,
                equipment_type="gas_turbine",
                equipment_name=gas_turbine_name,
            ),
        ),
        equipment_costs=(
            style_case_study_2_equipment_cost_input(
                equipment_type="gas-turbine",
                subtype=turbine_type,
                equipment_name=gas_turbine_name,
                design_size=max_power_generation,
            ),
        ),
    )


def style_case_study_2_boiler_candidate(
    *,
    name: str,
    vhp_header: str,
    max_steam_generation: float,
    thermal_efficiency: float,
    min_capacity: float = 0.0,
    minimum_load_fraction: float = 0.0,
    size_fuel_coefficient: float = 0.0,
    blowdown_fraction: float = 0.0,
    blowdown_enthalpy_delta: float = 0.0,
) -> BoilerCandidate:
    """Create a case-study 2 boiler candidate from explicit performance inputs."""

    return BoilerCandidate(
        name=name,
        vhp_header=vhp_header,
        size_fuel_coefficient=size_fuel_coefficient,
        load_fuel_coefficient=1.0 / thermal_efficiency,
        min_capacity=min_capacity,
        max_capacity=max_steam_generation,
        minimum_load_fraction=minimum_load_fraction,
        blowdown_fraction=blowdown_fraction,
        blowdown_enthalpy_delta=blowdown_enthalpy_delta,
    )


def style_case_study_2_vhp_enthalpies(
    *,
    steam_temperature: float,
    pressure: float | None = None,
    feedwater_temperature: float | None = None,
    properties: SteamPropertyProvider | None = None,
) -> tuple[float, float]:
    """Return VHP steam and feedwater enthalpies in MWh/t for case study 2."""

    provider = CoolPropSteamPropertyProvider() if properties is None else properties
    resolved_pressure = (
        STYLE_CASE_STUDY_2_SITE_CONFIG.vhp_pressure if pressure is None else pressure
    )
    resolved_feedwater_temperature = (
        STYLE_CASE_STUDY_2_SITE_CONFIG.boiler_feedwater_temperature
        if feedwater_temperature is None
        else feedwater_temperature
    )
    return (
        provider.enthalpy(
            pressure=resolved_pressure,
            temperature=steam_temperature,
        ),
        provider.enthalpy(
            pressure=resolved_pressure,
            temperature=resolved_feedwater_temperature,
        ),
    )


def style_case_study_2_best_configuration_property_spec(
    scenario: str,
    *,
    steam_level_names: Mapping[str, str] | None = None,
    vhp_header_name: str = "VHP_100",
    minimum_temperature_margin: float = 0.0,
) -> SteamPropertyUpdateSpec:
    """Return property targets from a Contribution 2 case-study 2 configuration."""

    configuration = get_contribution2_case_study2_best_configuration(scenario)
    levels = tuple(
        SteamLevelPropertyTarget(
            steam_level=_best_configuration_steam_level_name(
                steam_main,
                steam_level_names,
            ),
            pressure=pressure,
            main_temperature=temperature,
            minimum_temperature=temperature - minimum_temperature_margin,
        )
        for steam_main, pressure, temperature in zip(
            configuration.steam_mains,
            configuration.pressures,
            configuration.temperatures,
            strict=True,
        )
    )
    return SteamPropertyUpdateSpec(
        levels=levels,
        vhp_headers=(
            VhpHeaderPropertyTarget(
                vhp_header=vhp_header_name,
                pressure=configuration.vhp_pressure,
                temperature=configuration.vhp_temperature,
                maximum_temperature=configuration.vhp_temperature,
            ),
        ),
    )


def style_case_study_2_best_configuration_reported_flow_model_data(
    scenario: str,
    *,
    steam_level_names: Mapping[str, str] | None = None,
    vhp_header_name: str = "VHP_100",
    generation_enthalpy_delta: float | None = 1.0,
    use_enthalpy_delta: float | None = 1.0,
    properties: SteamPropertyProvider | None = None,
) -> StyleModelData:
    """Create a buildable multi-main model skeleton from reported source flows."""

    configuration = get_contribution2_case_study2_best_configuration(scenario)
    provider = CoolPropSteamPropertyProvider() if properties is None else properties
    levels = tuple(
        _best_configuration_steam_level(
            steam_main=steam_main,
            pressure=pressure,
            temperature=temperature,
            process_generation=process_generation,
            process_use=process_use,
            steam_level_names=steam_level_names,
            generation_enthalpy_delta=generation_enthalpy_delta,
            use_enthalpy_delta=use_enthalpy_delta,
            properties=provider,
            utility_steam_generation=configuration.utility_steam_generation,
        )
        for (
            steam_main,
            pressure,
            temperature,
            process_generation,
            process_use,
        ) in zip(
            configuration.steam_mains,
            configuration.pressures,
            configuration.temperatures,
            configuration.process_steam_generation,
            configuration.process_steam_use,
            strict=True,
        )
    )
    vhp_steam_enthalpy, vhp_feedwater_enthalpy = style_case_study_2_vhp_enthalpies(
        steam_temperature=configuration.vhp_temperature,
        pressure=configuration.vhp_pressure,
        properties=provider,
    )
    return StyleModelData(
        steam_mains=configuration.steam_mains,
        steam_levels=levels,
        vhp_headers=(
            VhpSteamCandidate(
                name=vhp_header_name,
                steam_enthalpy=vhp_steam_enthalpy,
                feedwater_enthalpy=vhp_feedwater_enthalpy,
                steam_flow_upper_bound=configuration.utility_steam_generation,
            ),
        ),
        power_demand=STYLE_CASE_STUDY_2_SITE_CONFIG.power_demand,
        grid_export_limit=(
            STYLE_CASE_STUDY_2_SITE_CONFIG.max_power_export
            if configuration.microgrid
            else 0.0
        ),
        operating_hours=STYLE_CASE_STUDY_2_SITE_CONFIG.operating_hours,
        cost_scale=1e-6,
        electricity_cost=style_case_study_2_electricity_cost(),
        cooling_water=style_case_study_2_cooling_water_config(),
        water_cost=style_case_study_2_water_cost(),
    )


def style_case_study_2_best_configuration_physical_profile_model_data(
    scenario: str,
    *,
    turbine_type: str,
    gas_turbine_fuel: str,
    boiler_type: str,
    boiler_fuel: str,
    steam_generation_efficiency: float,
    steam_mains: tuple[str, ...] | None = None,
    steam_main: str | None = None,
    target_steam_level: str | None = None,
    boiler_thermal_efficiency: float | None = None,
    hrsg_supplementary_fuel: str | None = None,
    hrsg_supplementary_firing_efficiency: float = 1.0,
    hot_oil_fuel: str | None = None,
    hot_oil_thermal_efficiency: float | None = None,
    match_reported_hot_oil_operating_cost: bool = False,
    hot_oil_supply_temperature: float | None = None,
    include_flash_steam_recovery: bool = False,
    include_auxiliary_vhp_source: bool = False,
    auxiliary_vhp_source_name: str = "reported-auxiliary-vhp-source",
    auxiliary_vhp_source_fuel_consumption_per_steam: float = 0.0,
    vhp_header_name: str = "VHP_100",
    vhp_turbine_name: str = "reported-vhp-st",
    fix_reported_loads: bool = False,
    allow_unpaid_power_export: bool = False,
    reported_fixed_maintenance_cost: float | None = None,
    reported_capital_cost: float | None = None,
    reported_power_revenue: float | None = None,
    reported_auxiliary_operating_cost: float | None = None,
    match_reported_fuel_cost: bool = False,
    fuel_consumption_factors: Mapping[tuple[str, str], float] | None = None,
    operating_cost_adjustments: Mapping[str, float] | None = None,
    properties: SteamPropertyProvider | None = None,
) -> StyleModelData:
    """Create physical heat-profile data with reported equipment targets."""

    if match_reported_fuel_cost and not fix_reported_loads:
        raise ValueError(
            "match_reported_fuel_cost requires fixed reported loads for "
            "physical-profile data"
        )
    configuration = get_contribution2_case_study2_best_configuration(scenario)
    resolved_steam_mains = _physical_profile_steam_mains(
        configuration,
        steam_mains,
        steam_main,
    )
    provider = CoolPropSteamPropertyProvider() if properties is None else properties
    profile = style_case_study_2_heat_interval_profile()

    def base_profile_data(
        heat_load_steam_main: str | None = None,
    ) -> StyleModelData:
        return style_model_data_from_heat_profile_for_steam_mains(
            profile,
            steam_mains=resolved_steam_mains,
            power_demand=STYLE_CASE_STUDY_2_SITE_CONFIG.power_demand,
            generation_enthalpy_delta=1.0,
            use_enthalpy_delta=1.0,
            heat_load_steam_main=heat_load_steam_main,
        )

    data = base_profile_data()
    target_level = target_steam_level or data.steam_levels[0].name
    try:
        selected_target = _steam_level_by_name(data, target_level)
    except KeyError as exc:
        raise ValueError(
            f"target steam level {target_level!r} is not in base data"
        ) from exc
    reported_level_names = _reported_steam_level_names_by_main(
        data,
        resolved_steam_mains,
        target_level,
    )
    data = base_profile_data(selected_target.steam_main)
    data = replace(
        data,
        grid_export_limit=(
            STYLE_CASE_STUDY_2_SITE_CONFIG.max_power_export
            if configuration.microgrid
            else 0.0
        ),
        operating_hours=STYLE_CASE_STUDY_2_SITE_CONFIG.operating_hours,
        cost_scale=1e-6,
        electricity_cost=style_case_study_2_electricity_cost(),
        cooling_water=style_case_study_2_cooling_water_config(),
        water_cost=style_case_study_2_water_cost(),
    )
    if allow_unpaid_power_export:
        data = _with_unpaid_power_export(data, configuration)
    if reported_power_revenue is not None:
        data = _with_reported_power_revenue(data, configuration, reported_power_revenue)
    vhp_steam_enthalpy, vhp_feedwater_enthalpy = style_case_study_2_vhp_enthalpies(
        steam_temperature=configuration.vhp_temperature,
        pressure=configuration.vhp_pressure,
        properties=provider,
    )
    data = replace(
        data,
        vhp_headers=(
            VhpSteamCandidate(
                name=vhp_header_name,
                steam_enthalpy=vhp_steam_enthalpy,
                feedwater_enthalpy=vhp_feedwater_enthalpy,
                steam_flow_upper_bound=configuration.utility_steam_generation,
            ),
        ),
    )
    data = apply_steam_property_update(
        data,
        SteamPropertyUpdateSpec(
            levels=_reported_steam_level_property_targets(
                configuration,
                data,
                resolved_steam_mains,
                reported_level_names,
            ),
            vhp_headers=(
                VhpHeaderPropertyTarget(
                    vhp_header=vhp_header_name,
                    pressure=configuration.vhp_pressure,
                    temperature=configuration.vhp_temperature,
                    maximum_temperature=configuration.vhp_temperature,
                ),
            ),
        ),
        provider,
    ).data
    data = _with_enthalpy_basis_for_steam_level(data, target_level)
    if include_flash_steam_recovery:
        flash_steam_recovery = (
            style_case_study_2_best_configuration_flash_steam_recovery_config(
                data,
                scenario,
                steam_level_names=reported_level_names,
                properties=properties,
            )
        )
        data = replace(
            _with_flash_steam_recovery_use_basis(
                data,
                configuration,
                flash_steam_recovery,
            ),
            flash_steam_recovery=flash_steam_recovery,
        )
    if hot_oil_fuel is not None:
        if match_reported_hot_oil_operating_cost:
            if fix_reported_loads:
                hot_oil_thermal_efficiency = (
                    _physical_profile_hot_oil_thermal_efficiency_for_reported_operating_cost(
                        data,
                        configuration,
                        fuel=hot_oil_fuel,
                        selected_steam_levels=(target_level,),
                        supply_temperature=hot_oil_supply_temperature,
                    )
                )
            else:
                hot_oil_thermal_efficiency = (
                    style_case_study_2_best_configuration_hot_oil_thermal_efficiency_for_reported_operating_cost(
                        scenario,
                        fuel=hot_oil_fuel,
                    )
                )
        elif hot_oil_thermal_efficiency is None:
            raise ValueError(
                "hot_oil_thermal_efficiency is required when hot_oil_fuel is set"
            )
        data = replace(
            data,
            hot_oil=style_case_study_2_best_configuration_hot_oil_config(
                scenario,
                fuel=hot_oil_fuel,
                thermal_efficiency=hot_oil_thermal_efficiency,
                supply_temperature=hot_oil_supply_temperature,
            ),
        )
    if configuration.boiler_flowrate is not None:
        if boiler_thermal_efficiency is None:
            raise ValueError(
                "boiler_thermal_efficiency is required when the configuration "
                "reports a boiler flowrate"
            )
        data = style_case_study_2_best_configuration_with_boiler(
            data,
            scenario,
            name="reported-boiler",
            boiler_type=boiler_type,
            fuel=boiler_fuel,
            thermal_efficiency=boiler_thermal_efficiency,
            vhp_header=vhp_header_name,
            min_capacity=configuration.boiler_flowrate if fix_reported_loads else 0.0,
        )
    data = style_case_study_2_best_configuration_with_gas_turbine_hrsg(
        data,
        scenario,
        gas_turbine_name="reported-gt",
        turbine_type=turbine_type,
        fuel=gas_turbine_fuel,
        hrsg_name="reported-hrsg",
        steam_generation_efficiency=steam_generation_efficiency,
        hrsg_supplementary_fuel=hrsg_supplementary_fuel,
        hrsg_supplementary_firing_efficiency=hrsg_supplementary_firing_efficiency,
        vhp_header=vhp_header_name,
    )
    if include_auxiliary_vhp_source:
        auxiliary_source = (
            style_case_study_2_best_configuration_auxiliary_vhp_source_candidate(
                scenario,
                name=auxiliary_vhp_source_name,
                vhp_header=vhp_header_name,
                min_capacity=0.0,
                fuel_consumption_per_steam=(
                    auxiliary_vhp_source_fuel_consumption_per_steam
                ),
                must_select=fix_reported_loads,
            )
        )
        data = replace(
            data,
            vhp_sources=(
                *data.vhp_sources,
                replace(
                    auxiliary_source,
                    min_capacity=(
                        auxiliary_source.max_capacity
                        if fix_reported_loads
                        else auxiliary_source.min_capacity
                    ),
                ),
            ),
        )
    data = style_case_study_2_best_configuration_with_vhp_turbine(
        data,
        scenario,
        name=vhp_turbine_name,
        steam_level=target_level,
        vhp_header=vhp_header_name,
        min_flow=configuration.utility_steam_generation if fix_reported_loads else 0.0,
        fixed_maintenance_cost=(
            0.0
            if reported_fixed_maintenance_cost is None
            else reported_fixed_maintenance_cost / data.cost_scale
        ),
    )
    if fix_reported_loads:
        data = _with_required_reported_equipment(
            data,
            boiler_name="reported-boiler"
            if configuration.boiler_flowrate is not None
            else None,
            gas_turbine_name="reported-gt",
            hrsg_name="reported-hrsg",
            vhp_turbine_name=vhp_turbine_name,
        )
    if reported_capital_cost is not None:
        data = _with_reported_capital_cost(data, reported_capital_cost)
    if match_reported_fuel_cost:
        data = _with_reported_fuel_cost_on_physical_basis(data, configuration)
    if reported_auxiliary_operating_cost is not None:
        data = _with_reported_auxiliary_operating_cost(
            data,
            reported_auxiliary_operating_cost,
        )
    if fuel_consumption_factors is not None:
        data = _with_fuel_consumption_accounting_factors(
            data,
            fuel_consumption_factors,
        )
    if operating_cost_adjustments is not None:
        data = _with_operating_cost_accounting_adjustments(
            data,
            operating_cost_adjustments,
        )
    return data


def style_case_study_2_best_configuration_boiler_candidate(
    scenario: str,
    *,
    name: str,
    vhp_header: str,
    thermal_efficiency: float,
    min_capacity: float = 0.0,
    minimum_load_fraction: float = 0.0,
) -> BoilerCandidate:
    """Create a boiler candidate from a reported best-configuration flowrate."""

    boiler_flowrate = _best_configuration_boiler_flowrate(scenario)
    return style_case_study_2_boiler_candidate(
        name=name,
        vhp_header=vhp_header,
        max_steam_generation=boiler_flowrate,
        thermal_efficiency=thermal_efficiency,
        min_capacity=min_capacity,
        minimum_load_fraction=minimum_load_fraction,
    )


def style_case_study_2_best_configuration_with_boiler(
    data: StyleModelData,
    scenario: str,
    *,
    name: str,
    boiler_type: str,
    fuel: str,
    thermal_efficiency: float,
    vhp_header: str | None = None,
    min_capacity: float = 0.0,
    minimum_load_fraction: float = 0.0,
    variable_maintenance_cost: float = 0.0,
    fixed_maintenance_cost: float = 0.0,
) -> StyleModelData:
    """Return data with one boiler derived from a best-configuration row."""

    selected_vhp = _single_or_named_vhp_header(data, vhp_header)
    boiler = style_case_study_2_best_configuration_boiler_candidate(
        scenario,
        name=name,
        vhp_header=selected_vhp.name,
        thermal_efficiency=thermal_efficiency,
        min_capacity=min_capacity,
        minimum_load_fraction=minimum_load_fraction,
    )
    return replace(
        data,
        boilers=(*data.boilers, boiler),
        fuel_costs=(
            *data.fuel_costs,
            style_case_study_2_fuel_cost(
                fuel,
                equipment_type="boiler",
                equipment_name=name,
            ),
        ),
        equipment_costs=(
            *data.equipment_costs,
            style_case_study_2_equipment_cost_input(
                equipment_type="boiler",
                subtype=boiler_type,
                equipment_name=name,
                design_size=boiler.max_capacity,
                variable_maintenance_cost=variable_maintenance_cost,
                fixed_maintenance_cost=fixed_maintenance_cost,
            ),
        ),
    )


def style_case_study_2_best_configuration_gas_turbine_candidate(
    scenario: str,
    *,
    name: str,
    turbine_type: str,
    fuel: str,
    minimum_load_fraction: float = 0.0,
    ambient_temperature: float = 15.0,
) -> GasTurbineCandidate:
    """Create a gas-turbine candidate from reported best-configuration power."""

    configuration = get_contribution2_case_study2_best_configuration(scenario)
    return style_case_study_2_gas_turbine_candidate(
        name=name,
        turbine_type=turbine_type,
        fuel=fuel,
        max_power_generation=configuration.gas_turbine_power,
        minimum_load_fraction=minimum_load_fraction,
        ambient_temperature=ambient_temperature,
    )


def style_case_study_2_best_configuration_hrsg_candidate(
    scenario: str,
    *,
    name: str,
    gas_turbine: GasTurbineCandidate,
    vhp_header: str,
    vhp_steam_enthalpy: float,
    vhp_feedwater_enthalpy: float,
    steam_generation_efficiency: float,
    supplementary_fuel: str | None = None,
    supplementary_firing_efficiency: float = 1.0,
) -> HrsgCandidate:
    """Create an HRSG candidate from reported best-configuration steam flow."""

    configuration = get_contribution2_case_study2_best_configuration(scenario)
    enthalpy_delta = vhp_steam_enthalpy - vhp_feedwater_enthalpy
    if enthalpy_delta <= 0.0:
        raise ValueError("VHP steam enthalpy must exceed feedwater enthalpy")
    max_heat_input = (
        configuration.hrsg_flowrate
        * enthalpy_delta
        / steam_generation_efficiency
    )
    supplementary_fuel_lhv = 0.0
    max_supplementary_fuel_flow = 0.0
    if supplementary_fuel is not None:
        resource = _resource(supplementary_fuel)
        if resource.lower_heating_value is None:
            raise ValueError(
                f"resource {supplementary_fuel!r} does not define a lower heating value"
            )
        supplementary_fuel_lhv = resource.lower_heating_value
        supplementary_heat = max(
            0.0,
            max_heat_input - _gas_turbine_full_load_exhaust_heat(gas_turbine),
        )
        max_supplementary_fuel_flow = supplementary_heat / (
            supplementary_firing_efficiency * supplementary_fuel_lhv
        )
    return HrsgCandidate(
        name=name,
        gas_turbine=gas_turbine.name,
        vhp_header=vhp_header,
        steam_generation_efficiency=steam_generation_efficiency,
        max_heat_input=max_heat_input,
        supplementary_fuel_lhv=supplementary_fuel_lhv,
        supplementary_firing_efficiency=supplementary_firing_efficiency,
        max_supplementary_fuel_flow=max_supplementary_fuel_flow,
    )


def style_case_study_2_best_configuration_hot_oil_config(
    scenario: str,
    *,
    fuel: str,
    thermal_efficiency: float,
    supply_temperature: float | None = None,
) -> HotOilConfig:
    """Create a hot-oil config from a reported best-configuration load."""

    configuration = get_contribution2_case_study2_best_configuration(scenario)
    if configuration.hot_oil_system_load is None:
        raise ValueError(
            f"best configuration {scenario!r} does not report a hot-oil system load"
        )
    resource = _resource(fuel)
    if resource.cost_unit != "eur_per_mwh":
        raise ValueError(f"resource {fuel!r} is not priced per MWh")
    return HotOilConfig(
        fuel_unit_cost=resource.unit_cost,
        thermal_efficiency=thermal_efficiency,
        high_temperature_heat_demand=configuration.hot_oil_system_load,
        supply_temperature=supply_temperature,
    )


def style_case_study_2_best_configuration_hot_oil_thermal_efficiency_for_reported_operating_cost(
    scenario: str,
    *,
    fuel: str,
) -> float:
    """Return hot-oil efficiency that matches the reported operating cost."""

    configuration = get_contribution2_case_study2_best_configuration(scenario)
    if configuration.hot_oil_system_load is None:
        raise ValueError(f"best configuration {scenario!r} does not report hot-oil load")
    if configuration.hot_oil_operating_cost is None:
        raise ValueError(
            f"best configuration {scenario!r} does not report hot-oil cost"
        )
    resource = _resource(fuel)
    if resource.cost_unit != "eur_per_mwh":
        raise ValueError(f"resource {fuel!r} is not priced per MWh")
    return (
        configuration.hot_oil_system_load
        * resource.unit_cost
        * STYLE_CASE_STUDY_2_SITE_CONFIG.operating_hours
        * 1e-6
        / configuration.hot_oil_operating_cost
    )


def _physical_profile_hot_oil_thermal_efficiency_for_reported_operating_cost(
    data: StyleModelData,
    configuration,
    *,
    fuel: str,
    selected_steam_levels: tuple[str, ...],
    supply_temperature: float | None,
) -> float:
    if configuration.hot_oil_system_load is None:
        raise ValueError(
            f"best configuration {configuration.scenario!r} does not report "
            "hot-oil load"
        )
    if configuration.hot_oil_operating_cost is None:
        raise ValueError(
            f"best configuration {configuration.scenario!r} does not report "
            "hot-oil cost"
        )
    resource = _resource(fuel)
    if resource.cost_unit != "eur_per_mwh":
        raise ValueError(f"resource {fuel!r} is not priced per MWh")
    physical_hot_oil_load = (
        configuration.hot_oil_system_load
        + _physical_profile_hot_oil_sink_heat_load(
            data,
            selected_steam_levels=selected_steam_levels,
            supply_temperature=supply_temperature,
        )
    )
    return (
        physical_hot_oil_load
        * resource.unit_cost
        * data.operating_hours
        * data.cost_scale
        / configuration.hot_oil_operating_cost
    )


def _physical_profile_hot_oil_sink_heat_load(
    data: StyleModelData,
    *,
    selected_steam_levels: tuple[str, ...],
    supply_temperature: float | None,
) -> float:
    selected = set(selected_steam_levels)
    return sum(
        level.sink_heat_demand
        for level in data.steam_levels
        if level.name not in selected
        if _hot_oil_can_supply_level(level, supply_temperature)
    )


def _hot_oil_can_supply_level(
    level: SteamLevelCandidate,
    supply_temperature: float | None,
) -> bool:
    return supply_temperature is None or level.temperature < supply_temperature


def style_case_study_2_best_configuration_flash_steam_recovery_config(
    data: StyleModelData,
    scenario: str,
    *,
    steam_level_names: Mapping[str, str] | None = None,
    name_template: str = "{source}-to-{target}-FSR",
    properties: SteamPropertyProvider | None = None,
) -> FlashSteamRecoveryConfig:
    """Create flash-steam recovery config from reported flash-steam flows."""

    configuration = get_contribution2_case_study2_best_configuration(scenario)
    provider = CoolPropSteamPropertyProvider() if properties is None else properties
    pressure_by_main = dict(
        zip(configuration.steam_mains, configuration.pressures, strict=True),
    )
    use_by_main = dict(
        zip(configuration.steam_mains, configuration.process_steam_use, strict=True),
    )
    level_by_name: dict[str, FlashSteamRecoveryLevel] = {}
    routes: list[FlashSteamRecoveryRoute] = []
    condensate_return_fractions: list[float] = []
    for target_index, flash_flow in enumerate(configuration.flash_steam):
        if flash_flow is None:
            continue
        if target_index == 0:
            raise ValueError("reported flash steam requires a higher-pressure source")
        source_main = configuration.steam_mains[target_index - 1]
        target_main = configuration.steam_mains[target_index]
        source_level = _flash_steam_level_name(
            data,
            source_main,
            steam_level_names,
        )
        target_level = _flash_steam_level_name(
            data,
            target_main,
            steam_level_names,
        )
        source_properties = _flash_recovery_level(
            provider,
            source_level,
            pressure_by_main[source_main],
        )
        target_properties = _flash_recovery_level(
            provider,
            target_level,
            pressure_by_main[target_main],
        )
        level_by_name.setdefault(source_level, source_properties)
        level_by_name.setdefault(target_level, target_properties)
        condensate_flow = _flash_condensate_flow(
            flash_flow=flash_flow,
            source_liquid_enthalpy=source_properties.saturated_liquid_enthalpy,
            target_vapor_enthalpy=target_properties.saturated_vapor_enthalpy,
            target_liquid_enthalpy=target_properties.saturated_liquid_enthalpy,
        )
        source_use = use_by_main[source_main]
        if source_use <= 0.0:
            raise ValueError("reported flash steam requires positive source steam use")
        condensate_return_fractions.append(condensate_flow / source_use)
        routes.append(
            FlashSteamRecoveryRoute(
                name=name_template.format(
                    source=source_main,
                    target=target_main,
                    source_level=source_level,
                    target_level=target_level,
                    index=target_index,
                ),
                source_level=source_level,
                target_level=target_level,
                max_flow=condensate_flow,
            ),
        )
    if not routes:
        raise ValueError(f"best configuration {scenario!r} does not report flash steam")
    return FlashSteamRecoveryConfig(
        levels=tuple(level_by_name.values()),
        routes=tuple(routes),
        condensate_return_fraction=max(condensate_return_fractions),
    )


def style_case_study_2_best_configuration_with_gas_turbine_hrsg(
    data: StyleModelData,
    scenario: str,
    *,
    gas_turbine_name: str,
    turbine_type: str,
    fuel: str,
    hrsg_name: str,
    steam_generation_efficiency: float,
    hrsg_supplementary_fuel: str | None = None,
    hrsg_supplementary_firing_efficiency: float = 1.0,
    vhp_header: str | None = None,
    minimum_load_fraction: float = 0.0,
    ambient_temperature: float = 15.0,
    gas_turbine_variable_maintenance_cost: float = 0.0,
    gas_turbine_fixed_maintenance_cost: float = 0.0,
    hrsg_variable_maintenance_cost: float = 0.0,
    hrsg_fixed_maintenance_cost: float = 0.0,
) -> StyleModelData:
    """Return data with reported gas-turbine and HRSG candidates."""

    selected_vhp = _single_or_named_vhp_header(data, vhp_header)
    gas_turbine = style_case_study_2_best_configuration_gas_turbine_candidate(
        scenario,
        name=gas_turbine_name,
        turbine_type=turbine_type,
        fuel=fuel,
        minimum_load_fraction=minimum_load_fraction,
        ambient_temperature=ambient_temperature,
    )
    hrsg = style_case_study_2_best_configuration_hrsg_candidate(
        scenario,
        name=hrsg_name,
        gas_turbine=gas_turbine,
        vhp_header=selected_vhp.name,
        vhp_steam_enthalpy=selected_vhp.steam_enthalpy,
        vhp_feedwater_enthalpy=selected_vhp.feedwater_enthalpy,
        steam_generation_efficiency=steam_generation_efficiency,
        supplementary_fuel=hrsg_supplementary_fuel,
        supplementary_firing_efficiency=hrsg_supplementary_firing_efficiency,
    )
    fuel_costs = (
        *data.fuel_costs,
        style_case_study_2_fuel_cost(
            fuel,
            equipment_type="gas_turbine",
            equipment_name=gas_turbine_name,
        ),
    )
    if (
        hrsg_supplementary_fuel is not None
        and hrsg.max_supplementary_fuel_flow > 0.0
    ):
        fuel_costs = (
            *fuel_costs,
            style_case_study_2_fuel_cost(
                hrsg_supplementary_fuel,
                equipment_type="hrsg_supplementary",
                equipment_name=hrsg_name,
            ),
        )
    return replace(
        data,
        gas_turbines=(*data.gas_turbines, gas_turbine),
        hrsgs=(*data.hrsgs, hrsg),
        fuel_costs=fuel_costs,
        equipment_costs=(
            *data.equipment_costs,
            style_case_study_2_equipment_cost_input(
                equipment_type="gas-turbine",
                subtype=turbine_type,
                equipment_name=gas_turbine_name,
                design_size=_gas_turbine_full_load_power(gas_turbine),
                variable_maintenance_cost=gas_turbine_variable_maintenance_cost,
                fixed_maintenance_cost=gas_turbine_fixed_maintenance_cost,
            ),
            style_case_study_2_hrsg_equipment_cost_input(
                hrsg=hrsg,
                gas_turbine=gas_turbine,
                turbine_type=turbine_type,
                variable_maintenance_cost=hrsg_variable_maintenance_cost,
                fixed_maintenance_cost=hrsg_fixed_maintenance_cost,
            ),
        ),
    )


def style_case_study_2_hrsg_candidate(
    *,
    name: str,
    gas_turbine: GasTurbineCandidate,
    vhp_header: str,
    steam_generation_efficiency: float,
    supplementary_fuel: str | None = None,
    supplementary_firing_efficiency: float = 1.0,
    max_supplementary_fuel_flow: float = 0.0,
) -> HrsgCandidate:
    """Create an HRSG candidate from the derived gas-turbine exhaust envelope."""

    supplementary_fuel_lhv = 0.0
    if supplementary_fuel is not None:
        resource = _resource(supplementary_fuel)
        if resource.lower_heating_value is None:
            raise ValueError(
                f"resource {supplementary_fuel!r} does not define a lower heating value"
            )
        supplementary_fuel_lhv = resource.lower_heating_value
    return HrsgCandidate(
        name=name,
        gas_turbine=gas_turbine.name,
        vhp_header=vhp_header,
        steam_generation_efficiency=steam_generation_efficiency,
        max_heat_input=_gas_turbine_full_load_exhaust_heat(gas_turbine),
        supplementary_fuel_lhv=supplementary_fuel_lhv,
        supplementary_firing_efficiency=supplementary_firing_efficiency,
        max_supplementary_fuel_flow=max_supplementary_fuel_flow,
    )


def style_case_study_2_best_configuration_hrsg_supplementary_firing_efficiency_for_reported_fuel_consumption(
    scenario: str,
    *,
    turbine_type: str,
    gas_turbine_fuel: str,
    steam_generation_efficiency: float,
    boiler_thermal_efficiency: float | None = None,
    auxiliary_vhp_source_fuel_consumption_per_steam: float = 0.0,
    vhp_header_name: str = "VHP_100",
    properties: SteamPropertyProvider | None = None,
) -> float:
    """Return the HRSG supplementary-firing factor matching reported fuel use."""

    configuration = get_contribution2_case_study2_best_configuration(scenario)
    data = style_case_study_2_best_configuration_reported_flow_model_data(
        scenario,
        vhp_header_name=vhp_header_name,
        properties=properties,
    )
    selected_vhp = _single_or_named_vhp_header(data, vhp_header_name)
    gas_turbine = style_case_study_2_best_configuration_gas_turbine_candidate(
        scenario,
        name="reported-gt",
        turbine_type=turbine_type,
        fuel=gas_turbine_fuel,
    )
    vhp_generation_enthalpy = (
        selected_vhp.steam_enthalpy - selected_vhp.feedwater_enthalpy
    )
    reported_hrsg_heat = (
        configuration.hrsg_flowrate
        * vhp_generation_enthalpy
        / steam_generation_efficiency
    )
    supplementary_heat = reported_hrsg_heat - _gas_turbine_full_load_exhaust_heat(
        gas_turbine,
    )
    gas_turbine_fuel_consumption = gas_turbine.max_fuel_flow * gas_turbine.fuel_lhv
    boiler_fuel_consumption = _reported_boiler_fuel_consumption(
        configuration,
        vhp_generation_enthalpy=vhp_generation_enthalpy,
        boiler_thermal_efficiency=boiler_thermal_efficiency,
    )
    auxiliary_fuel_consumption = (
        _reported_unassigned_vhp_generation(configuration)
        * auxiliary_vhp_source_fuel_consumption_per_steam
    )
    target_supplementary_fuel = (
        configuration.fuel_consumption
        - gas_turbine_fuel_consumption
        - boiler_fuel_consumption
        - auxiliary_fuel_consumption
    )
    if supplementary_heat <= 0.0:
        if target_supplementary_fuel <= 1e-9:
            return 1.0
        raise ValueError(
            "reported fuel consumption requires supplementary fuel but the HRSG "
            "does not require supplementary heat"
        )
    if target_supplementary_fuel <= 0.0:
        raise ValueError(
            "reported fuel consumption is below non-HRSG fuel consumption"
        )
    return supplementary_heat / target_supplementary_fuel


def style_case_study_2_gas_turbine_exhaust_flow(
    *,
    gas_turbine: GasTurbineCandidate,
    turbine_type: str,
) -> float:
    """Return full-load gas-turbine exhaust flow in t/h from P1.B coefficients."""

    coefficient = _gas_turbine_full_load_coefficient(turbine_type)
    full_load_power_kw = _gas_turbine_full_load_power(gas_turbine) * 1000.0
    air_flow_kg_per_second = (
        coefficient.air_flow_c * full_load_power_kw + coefficient.air_flow_d
    )
    fuel_flow_kg_per_second = gas_turbine.max_fuel_flow * 1000.0 / 3600.0
    return (air_flow_kg_per_second + fuel_flow_kg_per_second) * 3.6


def style_case_study_2_hrsg_equipment_cost_input(
    *,
    hrsg: HrsgCandidate,
    gas_turbine: GasTurbineCandidate,
    turbine_type: str,
    name: str | None = None,
    variable_maintenance_cost: float = 0.0,
    fixed_maintenance_cost: float = 0.0,
) -> EquipmentCost:
    """Return an HRSG cost input converted to the model heat-input size basis."""

    exhaust_flow = style_case_study_2_gas_turbine_exhaust_flow(
        gas_turbine=gas_turbine,
        turbine_type=turbine_type,
    )
    coefficient = _equipment_cost_coefficient(
        equipment_type="hrsg",
        subtype="all",
        design_size=exhaust_flow,
    )
    return EquipmentCost(
        name=name or f"{hrsg.name}-capital",
        equipment_type="hrsg",
        equipment_name=hrsg.name,
        annualization_factor=style_case_study_2_capital_recovery_factor(),
        installation_factor=STYLE_CASE_STUDY_2_SITE_CONFIG.capital_installation_factor,
        variable_capital_cost=(
            coefficient.variable_cost * exhaust_flow / hrsg.max_heat_input
        ),
        fixed_capital_cost=coefficient.fixed_cost,
        variable_maintenance_cost=variable_maintenance_cost,
        fixed_maintenance_cost=fixed_maintenance_cost,
    )


def style_case_study_2_gas_turbine_hrsg_scenario_data(
    *,
    steam_main: str,
    generation_enthalpy_delta: float,
    use_enthalpy_delta: float,
    gas_turbine_name: str,
    turbine_type: str,
    fuel: str,
    max_power_generation: float,
    vhp_header_name: str,
    vhp_steam_enthalpy: float,
    vhp_feedwater_enthalpy: float,
    steam_generation_efficiency: float,
    minimum_load_fraction: float = 0.0,
    ambient_temperature: float = 15.0,
    steam_enthalpy_for_use: float | None = None,
    feedwater_enthalpy: float = 0.0,
) -> StyleModelData:
    """Return case-study 2 data with derived gas-turbine and HRSG options."""

    data = style_case_study_2_gas_turbine_scenario_data(
        steam_main=steam_main,
        generation_enthalpy_delta=generation_enthalpy_delta,
        use_enthalpy_delta=use_enthalpy_delta,
        gas_turbine_name=gas_turbine_name,
        turbine_type=turbine_type,
        fuel=fuel,
        max_power_generation=max_power_generation,
        minimum_load_fraction=minimum_load_fraction,
        ambient_temperature=ambient_temperature,
        steam_enthalpy_for_use=steam_enthalpy_for_use,
        feedwater_enthalpy=feedwater_enthalpy,
    )
    gas_turbine = data.gas_turbines[0]
    hrsg = style_case_study_2_hrsg_candidate(
        name=f"hrsg-{gas_turbine_name}",
        gas_turbine=gas_turbine,
        vhp_header=vhp_header_name,
        steam_generation_efficiency=steam_generation_efficiency,
    )
    return replace(
        data,
        vhp_headers=(
            VhpSteamCandidate(
                name=vhp_header_name,
                steam_enthalpy=vhp_steam_enthalpy,
                feedwater_enthalpy=vhp_feedwater_enthalpy,
                steam_flow_upper_bound=_hrsg_steam_generation_upper_bound(
                    hrsg=hrsg,
                    steam_enthalpy=vhp_steam_enthalpy,
                    feedwater_enthalpy=vhp_feedwater_enthalpy,
                ),
            ),
        ),
        hrsgs=(hrsg,),
        equipment_costs=(
            *data.equipment_costs,
            style_case_study_2_hrsg_equipment_cost_input(
                hrsg=hrsg,
                gas_turbine=gas_turbine,
                turbine_type=turbine_type,
            ),
        ),
    )


def style_case_study_2_boiler_gas_turbine_hrsg_scenario_data(
    *,
    steam_main: str,
    generation_enthalpy_delta: float,
    use_enthalpy_delta: float,
    gas_turbine_name: str,
    turbine_type: str,
    gas_turbine_fuel: str,
    max_power_generation: float,
    vhp_header_name: str,
    vhp_steam_enthalpy: float,
    vhp_feedwater_enthalpy: float,
    steam_generation_efficiency: float,
    boiler_name: str,
    boiler_type: str,
    boiler_fuel: str,
    boiler_max_steam_generation: float,
    boiler_thermal_efficiency: float,
    minimum_load_fraction: float = 0.0,
    ambient_temperature: float = 15.0,
    boiler_minimum_load_fraction: float = 0.0,
    steam_enthalpy_for_use: float | None = None,
    feedwater_enthalpy: float = 0.0,
) -> StyleModelData:
    """Return case-study 2 data with boiler and gas-turbine/HRSG VHP options."""

    data = style_case_study_2_gas_turbine_hrsg_scenario_data(
        steam_main=steam_main,
        generation_enthalpy_delta=generation_enthalpy_delta,
        use_enthalpy_delta=use_enthalpy_delta,
        gas_turbine_name=gas_turbine_name,
        turbine_type=turbine_type,
        fuel=gas_turbine_fuel,
        max_power_generation=max_power_generation,
        vhp_header_name=vhp_header_name,
        vhp_steam_enthalpy=vhp_steam_enthalpy,
        vhp_feedwater_enthalpy=vhp_feedwater_enthalpy,
        steam_generation_efficiency=steam_generation_efficiency,
        minimum_load_fraction=minimum_load_fraction,
        ambient_temperature=ambient_temperature,
        steam_enthalpy_for_use=steam_enthalpy_for_use,
        feedwater_enthalpy=feedwater_enthalpy,
    )
    boiler = style_case_study_2_boiler_candidate(
        name=boiler_name,
        vhp_header=vhp_header_name,
        max_steam_generation=boiler_max_steam_generation,
        thermal_efficiency=boiler_thermal_efficiency,
        minimum_load_fraction=boiler_minimum_load_fraction,
    )
    vhp_header = data.vhp_headers[0]
    return replace(
        data,
        vhp_headers=(
            replace(
                vhp_header,
                steam_flow_upper_bound=(
                    vhp_header.steam_flow_upper_bound + boiler.max_capacity
                ),
            ),
        ),
        boilers=(boiler,),
        fuel_costs=(
            *data.fuel_costs,
            style_case_study_2_fuel_cost(
                boiler_fuel,
                equipment_type="boiler",
                equipment_name=boiler_name,
            ),
        ),
        equipment_costs=(
            *data.equipment_costs,
            style_case_study_2_equipment_cost_input(
                equipment_type="boiler",
                subtype=boiler_type,
                equipment_name=boiler_name,
                design_size=boiler_max_steam_generation,
            ),
        ),
    )


def style_case_study_2_vhp_letdown_candidate(
    *,
    name: str,
    vhp_header: str,
    steam_level: str,
    max_flow: float,
) -> VhpLetdownStationCandidate:
    """Create a VHP-to-steam-main let-down candidate."""

    return VhpLetdownStationCandidate(
        name=name,
        vhp_header=vhp_header,
        steam_level=steam_level,
        max_flow=max_flow,
    )


def style_case_study_2_vhp_back_pressure_turbine_candidate(
    *,
    name: str,
    vhp_header: str,
    steam_level: str,
    power_slope: float,
    power_intercept: float,
    max_flow: float,
    min_flow: float = 0.0,
    minimum_load_fraction: float = 0.0,
) -> VhpBackPressureTurbineCandidate:
    """Create a VHP-to-steam-main back-pressure turbine candidate."""

    return VhpBackPressureTurbineCandidate(
        name=name,
        vhp_header=vhp_header,
        steam_level=steam_level,
        power_slope=power_slope,
        power_intercept=power_intercept,
        min_capacity=min_flow,
        max_capacity=max_flow,
        minimum_load_fraction=minimum_load_fraction,
    )


def style_case_study_2_vhp_turbine_equipment_cost_input(
    *,
    turbine: VhpBackPressureTurbineCandidate,
    name: str | None = None,
    variable_maintenance_cost: float = 0.0,
    fixed_maintenance_cost: float = 0.0,
) -> EquipmentCost:
    """Map a VHP turbine design power to the case-study 2 steam-turbine cost row."""

    design_power = turbine.power_slope * turbine.max_capacity - turbine.power_intercept
    return style_case_study_2_equipment_cost_input(
        equipment_type="steam-turbine",
        subtype="all",
        equipment_name=turbine.name,
        design_size=design_power,
        model_equipment_type="vhp_turbine",
        name=name,
        variable_maintenance_cost=variable_maintenance_cost,
        fixed_maintenance_cost=fixed_maintenance_cost,
    )


def style_case_study_2_best_configuration_vhp_turbine_candidate(
    scenario: str,
    *,
    name: str,
    vhp_header: str,
    steam_level: str,
    max_flow: float | None = None,
    min_flow: float = 0.0,
    minimum_load_fraction: float = 0.0,
    power_intercept: float = 0.0,
) -> VhpBackPressureTurbineCandidate:
    """Create a VHP turbine candidate from reported best-configuration totals."""

    configuration = get_contribution2_case_study2_best_configuration(scenario)
    resolved_max_flow = (
        configuration.utility_steam_generation if max_flow is None else max_flow
    )
    power_slope = (configuration.steam_turbine_power + power_intercept) / (
        resolved_max_flow
    )
    return style_case_study_2_vhp_back_pressure_turbine_candidate(
        name=name,
        vhp_header=vhp_header,
        steam_level=steam_level,
        power_slope=power_slope,
        power_intercept=power_intercept,
        max_flow=resolved_max_flow,
        min_flow=min_flow,
        minimum_load_fraction=minimum_load_fraction,
    )


def style_case_study_2_best_configuration_with_vhp_turbine(
    data: StyleModelData,
    scenario: str,
    *,
    name: str,
    steam_level: str,
    vhp_header: str | None = None,
    max_flow: float | None = None,
    min_flow: float = 0.0,
    minimum_load_fraction: float = 0.0,
    power_intercept: float = 0.0,
    variable_maintenance_cost: float = 0.0,
    fixed_maintenance_cost: float = 0.0,
) -> StyleModelData:
    """Return data with one VHP turbine derived from a best-configuration row."""

    selected_vhp = _single_or_named_vhp_header(data, vhp_header)
    turbine = style_case_study_2_best_configuration_vhp_turbine_candidate(
        scenario,
        name=name,
        vhp_header=selected_vhp.name,
        steam_level=steam_level,
        max_flow=max_flow,
        min_flow=min_flow,
        minimum_load_fraction=minimum_load_fraction,
        power_intercept=power_intercept,
    )
    return replace(
        data,
        vhp_turbines=(*data.vhp_turbines, turbine),
        equipment_costs=(
            *data.equipment_costs,
            style_case_study_2_vhp_turbine_equipment_cost_input(
                turbine=turbine,
                variable_maintenance_cost=variable_maintenance_cost,
                fixed_maintenance_cost=fixed_maintenance_cost,
            ),
        ),
    )


def style_case_study_2_best_configuration_auxiliary_vhp_source_candidate(
    scenario: str,
    *,
    name: str,
    vhp_header: str,
    min_capacity: float = 0.0,
    max_capacity: float | None = None,
    minimum_load_fraction: float = 0.0,
    fuel_consumption_per_steam: float = 0.0,
    must_select: bool = False,
) -> VhpSteamSourceCandidate:
    """Create an auxiliary VHP source for reported generation not assigned to units."""

    configuration = get_contribution2_case_study2_best_configuration(scenario)
    unassigned_generation = _reported_unassigned_vhp_generation(configuration)
    if unassigned_generation <= 0.0:
        raise ValueError(
            f"best configuration {scenario!r} has no unassigned VHP generation"
        )
    resolved_max_capacity = (
        unassigned_generation if max_capacity is None else max_capacity
    )
    return VhpSteamSourceCandidate(
        name=name,
        vhp_header=vhp_header,
        min_capacity=min_capacity,
        max_capacity=resolved_max_capacity,
        minimum_load_fraction=minimum_load_fraction,
        fuel_consumption_per_steam=fuel_consumption_per_steam,
        must_select=must_select,
    )


def style_case_study_2_best_configuration_with_auxiliary_vhp_source(
    data: StyleModelData,
    scenario: str,
    *,
    name: str,
    vhp_header: str | None = None,
    min_capacity: float = 0.0,
    max_capacity: float | None = None,
    minimum_load_fraction: float = 0.0,
    fuel_consumption_per_steam: float = 0.0,
    must_select: bool = False,
) -> StyleModelData:
    """Return data with an auxiliary source for unassigned VHP steam generation."""

    selected_vhp = _single_or_named_vhp_header(data, vhp_header)
    source = style_case_study_2_best_configuration_auxiliary_vhp_source_candidate(
        scenario,
        name=name,
        vhp_header=selected_vhp.name,
        min_capacity=min_capacity,
        max_capacity=max_capacity,
        minimum_load_fraction=minimum_load_fraction,
        fuel_consumption_per_steam=fuel_consumption_per_steam,
        must_select=must_select,
    )
    return replace(data, vhp_sources=(*data.vhp_sources, source))


def style_case_study_2_best_configuration_inter_main_letdown_candidates(
    data: StyleModelData,
    scenario: str,
    *,
    name_template: str = "{source}-to-{target}-LD",
    tolerance: float = 1e-9,
) -> tuple[SteamMainLetdownStationCandidate, ...]:
    """Create adjacent steam-main let-downs from reported net steam balances."""

    configuration = get_contribution2_case_study2_best_configuration(scenario)
    carry_forward = configuration.utility_steam_generation
    letdowns: list[SteamMainLetdownStationCandidate] = []
    for index, source_main in enumerate(configuration.steam_mains[:-1]):
        source_generation = configuration.process_steam_generation[index] or 0.0
        carry_forward += source_generation - configuration.process_steam_use[index]
        if carry_forward <= tolerance:
            carry_forward = 0.0
            continue

        target_main = configuration.steam_mains[index + 1]
        source_level = _single_level_name_for_steam_main(data, source_main)
        target_level = _single_level_name_for_steam_main(data, target_main)
        letdowns.append(
            SteamMainLetdownStationCandidate(
                name=name_template.format(
                    source=source_main,
                    target=target_main,
                    source_level=source_level,
                    target_level=target_level,
                    index=index + 1,
                ),
                source_level=source_level,
                target_level=target_level,
                max_flow=carry_forward,
            ),
        )
    return tuple(letdowns)


def style_case_study_2_best_configuration_with_inter_main_letdowns(
    data: StyleModelData,
    scenario: str,
    *,
    name_template: str = "{source}-to-{target}-LD",
    tolerance: float = 1e-9,
) -> StyleModelData:
    """Return data with adjacent reported steam-main let-down connections."""

    letdowns = style_case_study_2_best_configuration_inter_main_letdown_candidates(
        data,
        scenario,
        name_template=name_template,
        tolerance=tolerance,
    )
    return replace(
        data,
        steam_main_letdowns=(*data.steam_main_letdowns, *letdowns),
    )


def style_case_study_2_best_configuration_reported_equipment_model_data(
    scenario: str,
    *,
    turbine_type: str,
    gas_turbine_fuel: str,
    boiler_type: str,
    boiler_fuel: str,
    steam_generation_efficiency: float,
    boiler_thermal_efficiency: float | None = None,
    steam_level_names: Mapping[str, str] | None = None,
    vhp_header_name: str = "VHP_100",
    boiler_name: str = "reported-boiler",
    gas_turbine_name: str = "reported-gt",
    hrsg_name: str = "reported-hrsg",
    hrsg_supplementary_fuel: str | None = None,
    hrsg_supplementary_firing_efficiency: float = 1.0,
    match_reported_fuel_consumption: bool = False,
    match_reported_fuel_cost: bool = False,
    include_auxiliary_vhp_source: bool = False,
    auxiliary_vhp_source_name: str = "reported-auxiliary-vhp-source",
    auxiliary_vhp_source_fuel_consumption_per_steam: float = 0.0,
    hot_oil_fuel: str | None = None,
    hot_oil_thermal_efficiency: float | None = None,
    match_reported_hot_oil_operating_cost: bool = False,
    hot_oil_supply_temperature: float | None = None,
    include_flash_steam_recovery: bool = False,
    vhp_turbine_name: str = "reported-vhp-st",
    vhp_turbine_steam_level: str | None = None,
    generation_enthalpy_delta: float | None = None,
    use_enthalpy_delta: float | None = None,
    fix_reported_loads: bool = False,
    allow_unpaid_power_export: bool = False,
    reported_fixed_maintenance_cost: float | None = None,
    reported_power_revenue: float | None = None,
    reported_auxiliary_operating_cost: float | None = None,
    reported_capital_cost: float | None = None,
    match_reported_economics: bool = False,
    properties: SteamPropertyProvider | None = None,
) -> StyleModelData:
    """Create reported best-configuration flow data with reported equipment."""

    configuration = get_contribution2_case_study2_best_configuration(scenario)
    if match_reported_economics:
        match_reported_fuel_consumption = True
        match_reported_fuel_cost = True
        if hot_oil_fuel is not None and configuration.hot_oil_operating_cost is not None:
            match_reported_hot_oil_operating_cost = True
        if reported_fixed_maintenance_cost is None:
            reported_fixed_maintenance_cost = configuration.maintenance_cost
        if reported_power_revenue is None and configuration.power_revenue is not None:
            reported_power_revenue = configuration.power_revenue
        if reported_auxiliary_operating_cost is None:
            reported_auxiliary_operating_cost = (
                _reported_auxiliary_operating_cost(configuration)
            )
        if reported_capital_cost is None:
            reported_capital_cost = configuration.capital_cost
    data = style_case_study_2_best_configuration_reported_flow_model_data(
        scenario,
        steam_level_names=steam_level_names,
        vhp_header_name=vhp_header_name,
        generation_enthalpy_delta=generation_enthalpy_delta,
        use_enthalpy_delta=use_enthalpy_delta,
        properties=properties,
    )
    if allow_unpaid_power_export:
        data = _with_unpaid_power_export(data, configuration)
    if reported_power_revenue is not None:
        data = _with_reported_power_revenue(data, configuration, reported_power_revenue)
    if reported_auxiliary_operating_cost is not None:
        data = _with_reported_auxiliary_operating_cost(
            data,
            reported_auxiliary_operating_cost,
        )
    if hot_oil_fuel is not None:
        if match_reported_hot_oil_operating_cost:
            hot_oil_thermal_efficiency = (
                style_case_study_2_best_configuration_hot_oil_thermal_efficiency_for_reported_operating_cost(
                    scenario,
                    fuel=hot_oil_fuel,
                )
            )
        elif hot_oil_thermal_efficiency is None:
            raise ValueError(
                "hot_oil_thermal_efficiency is required when hot_oil_fuel is set"
            )
        data = replace(
            data,
            hot_oil=style_case_study_2_best_configuration_hot_oil_config(
                scenario,
                fuel=hot_oil_fuel,
                thermal_efficiency=hot_oil_thermal_efficiency,
                supply_temperature=hot_oil_supply_temperature,
            ),
        )
    if include_flash_steam_recovery:
        flash_steam_recovery = (
            style_case_study_2_best_configuration_flash_steam_recovery_config(
                data,
                scenario,
                properties=properties,
            )
        )
        data = replace(
            _with_flash_steam_recovery_use_basis(
                data,
                configuration,
                flash_steam_recovery,
            ),
            flash_steam_recovery=flash_steam_recovery,
        )
    if configuration.boiler_flowrate is not None:
        if boiler_thermal_efficiency is None:
            raise ValueError(
                "boiler_thermal_efficiency is required when the configuration "
                "reports a boiler flowrate"
            )
        data = style_case_study_2_best_configuration_with_boiler(
            data,
            scenario,
            name=boiler_name,
            boiler_type=boiler_type,
            fuel=boiler_fuel,
            thermal_efficiency=boiler_thermal_efficiency,
            vhp_header=vhp_header_name,
            min_capacity=configuration.boiler_flowrate if fix_reported_loads else 0.0,
        )
    if match_reported_fuel_consumption:
        if hrsg_supplementary_fuel is None:
            raise ValueError(
                "hrsg_supplementary_fuel is required to match reported fuel "
                "consumption"
            )
        hrsg_supplementary_firing_efficiency = (
            style_case_study_2_best_configuration_hrsg_supplementary_firing_efficiency_for_reported_fuel_consumption(
                scenario,
                turbine_type=turbine_type,
                gas_turbine_fuel=gas_turbine_fuel,
                steam_generation_efficiency=steam_generation_efficiency,
                boiler_thermal_efficiency=boiler_thermal_efficiency,
                auxiliary_vhp_source_fuel_consumption_per_steam=(
                    auxiliary_vhp_source_fuel_consumption_per_steam
                ),
                vhp_header_name=vhp_header_name,
                properties=properties,
            )
        )
    data = style_case_study_2_best_configuration_with_gas_turbine_hrsg(
        data,
        scenario,
        gas_turbine_name=gas_turbine_name,
        turbine_type=turbine_type,
        fuel=gas_turbine_fuel,
        hrsg_name=hrsg_name,
        steam_generation_efficiency=steam_generation_efficiency,
        hrsg_supplementary_fuel=hrsg_supplementary_fuel,
        hrsg_supplementary_firing_efficiency=hrsg_supplementary_firing_efficiency,
        vhp_header=vhp_header_name,
    )
    if match_reported_fuel_cost:
        data = _with_reported_fuel_cost(data, configuration)
    if include_auxiliary_vhp_source:
        auxiliary_source = (
            style_case_study_2_best_configuration_auxiliary_vhp_source_candidate(
                scenario,
                name=auxiliary_vhp_source_name,
                vhp_header=vhp_header_name,
                min_capacity=0.0,
                fuel_consumption_per_steam=(
                    auxiliary_vhp_source_fuel_consumption_per_steam
                ),
                must_select=fix_reported_loads,
            )
        )
        data = replace(
            data,
            vhp_sources=(
                *data.vhp_sources,
                replace(
                    auxiliary_source,
                    min_capacity=(
                        auxiliary_source.max_capacity
                        if fix_reported_loads
                        else auxiliary_source.min_capacity
                    ),
                ),
            ),
        )
    data = style_case_study_2_best_configuration_with_vhp_turbine(
        data,
        scenario,
        name=vhp_turbine_name,
        steam_level=vhp_turbine_steam_level or data.steam_levels[0].name,
        vhp_header=vhp_header_name,
        min_flow=configuration.utility_steam_generation if fix_reported_loads else 0.0,
        fixed_maintenance_cost=(
            0.0
            if reported_fixed_maintenance_cost is None
            else reported_fixed_maintenance_cost / data.cost_scale
        ),
    )
    if fix_reported_loads:
        data = _with_required_reported_equipment(
            data,
            boiler_name=boiler_name if configuration.boiler_flowrate is not None else None,
            gas_turbine_name=gas_turbine_name,
            hrsg_name=hrsg_name,
            vhp_turbine_name=vhp_turbine_name,
        )
    if reported_capital_cost is not None:
        data = _with_reported_capital_cost(data, reported_capital_cost)
    return style_case_study_2_best_configuration_with_inter_main_letdowns(
        data,
        scenario,
    )


def style_case_study_2_with_vhp_letdown(
    data: StyleModelData,
    *,
    name: str,
    steam_level: str,
    vhp_header: str | None = None,
    max_flow: float | None = None,
) -> StyleModelData:
    """Return case-study 2 data with one additional VHP let-down connection."""

    selected_vhp = _single_or_named_vhp_header(data, vhp_header)
    return replace(
        data,
        vhp_letdowns=(
            *data.vhp_letdowns,
            style_case_study_2_vhp_letdown_candidate(
                name=name,
                vhp_header=selected_vhp.name,
                steam_level=steam_level,
                max_flow=(
                    selected_vhp.steam_flow_upper_bound
                    if max_flow is None
                    else max_flow
                ),
            ),
        ),
    )


def style_case_study_2_with_vhp_back_pressure_turbine(
    data: StyleModelData,
    *,
    name: str,
    steam_level: str,
    power_slope: float,
    power_intercept: float,
    vhp_header: str | None = None,
    max_flow: float | None = None,
    min_flow: float = 0.0,
    minimum_load_fraction: float = 0.0,
    variable_maintenance_cost: float = 0.0,
    fixed_maintenance_cost: float = 0.0,
) -> StyleModelData:
    """Return case-study 2 data with one additional VHP turbine connection."""

    selected_vhp = _single_or_named_vhp_header(data, vhp_header)
    turbine = style_case_study_2_vhp_back_pressure_turbine_candidate(
        name=name,
        vhp_header=selected_vhp.name,
        steam_level=steam_level,
        power_slope=power_slope,
        power_intercept=power_intercept,
        max_flow=selected_vhp.steam_flow_upper_bound if max_flow is None else max_flow,
        min_flow=min_flow,
        minimum_load_fraction=minimum_load_fraction,
    )
    return replace(
        data,
        vhp_turbines=(*data.vhp_turbines, turbine),
        equipment_costs=(
            *data.equipment_costs,
            style_case_study_2_vhp_turbine_equipment_cost_input(
                turbine=turbine,
                variable_maintenance_cost=variable_maintenance_cost,
                fixed_maintenance_cost=fixed_maintenance_cost,
            ),
        ),
    )


def style_case_study_2_contribution2_best_configuration_catalog(
    *,
    turbine_type: str = "industrial",
    gas_turbine_fuel: str = "natural-gas",
    boiler_type: str = "packaged",
    boiler_fuel: str = "natural-gas",
    boiler_thermal_efficiency: float = 0.85,
    steam_generation_efficiency: float = 0.8,
    hrsg_supplementary_fuel: str = "natural-gas",
    hot_oil_fuel: str = "natural-gas",
    match_reported_economics: bool = True,
) -> StaticStyleScenarioCatalog:
    """Return calibrated Contribution 2 case-study 2 best-configuration rows."""

    scenarios = tuple(
        StaticStyleScenario(
            case_study="contribution-2-case-study-2",
            scenario=configuration.scenario,
            data=style_case_study_2_best_configuration_reported_equipment_model_data(
                configuration.scenario,
                turbine_type=turbine_type,
                gas_turbine_fuel=gas_turbine_fuel,
                boiler_type=boiler_type,
                boiler_fuel=boiler_fuel,
                boiler_thermal_efficiency=(
                    boiler_thermal_efficiency
                    if configuration.boiler_flowrate is not None
                    else None
                ),
                steam_generation_efficiency=steam_generation_efficiency,
                hrsg_supplementary_fuel=hrsg_supplementary_fuel,
                hot_oil_fuel=(
                    hot_oil_fuel
                    if configuration.hot_oil_system_load is not None
                    else None
                ),
                include_flash_steam_recovery=any(
                    flash is not None for flash in configuration.flash_steam
                ),
                include_auxiliary_vhp_source=(
                    _reported_unassigned_vhp_generation(configuration) > 1e-9
                ),
                fix_reported_loads=True,
                allow_unpaid_power_export=not configuration.microgrid,
                match_reported_economics=match_reported_economics,
            ),
            absolute_tolerance=_contribution2_best_configuration_tolerance(
                configuration.scenario,
            ),
        )
        for configuration in CONTRIBUTION2_CASE_STUDY_2_BEST_CONFIGURATIONS
    )
    return StaticStyleScenarioCatalog(scenarios)


def style_case_study_2_contribution2_physical_profile_catalog(
    *,
    turbine_type: str = "industrial",
    gas_turbine_fuel: str = "natural-gas",
    boiler_type: str = "packaged",
    boiler_fuel: str = "natural-gas",
    boiler_thermal_efficiency: float = 0.85,
    steam_generation_efficiency: float = 0.8,
    hrsg_supplementary_fuel: str = "natural-gas",
    hot_oil_fuel: str = "natural-gas",
    hot_oil_thermal_efficiency: float = 0.85,
    calibrated: bool = True,
    fuel_consumption_factors_by_scenario: Mapping[
        str,
        Mapping[tuple[str, str], float],
    ]
    | None = None,
    operating_cost_adjustments_by_scenario: Mapping[
        str,
        Mapping[str, float],
    ]
    | None = None,
) -> StaticStyleScenarioCatalog:
    """Return physical-profile Contribution 2 case-study 2 rows."""

    scenarios = tuple(
        StaticStyleScenario(
            case_study="contribution-2-case-study-2-physical-profile",
            scenario=configuration.scenario,
            data=style_case_study_2_best_configuration_physical_profile_model_data(
                configuration.scenario,
                turbine_type=turbine_type,
                gas_turbine_fuel=gas_turbine_fuel,
                boiler_type=boiler_type,
                boiler_fuel=boiler_fuel,
                boiler_thermal_efficiency=(
                    boiler_thermal_efficiency
                    if configuration.boiler_flowrate is not None
                    else None
                ),
                steam_generation_efficiency=steam_generation_efficiency,
                hrsg_supplementary_fuel=hrsg_supplementary_fuel,
                hot_oil_fuel=(
                    hot_oil_fuel
                    if configuration.hot_oil_system_load is not None
                    else None
                ),
                hot_oil_thermal_efficiency=(
                    hot_oil_thermal_efficiency
                    if configuration.hot_oil_system_load is not None
                    else None
                ),
                include_flash_steam_recovery=any(
                    flash is not None for flash in configuration.flash_steam
                ),
                **_physical_profile_calibration_kwargs(configuration, calibrated),
                fuel_consumption_factors=(
                    {}
                    if fuel_consumption_factors_by_scenario is None
                    else fuel_consumption_factors_by_scenario.get(
                        configuration.scenario,
                        {},
                    )
                ),
                operating_cost_adjustments=(
                    {}
                    if operating_cost_adjustments_by_scenario is None
                    else operating_cost_adjustments_by_scenario.get(
                        configuration.scenario,
                        {},
                    )
                ),
            ),
            absolute_tolerance=_contribution2_best_configuration_tolerance(
                configuration.scenario,
            ),
        )
        for configuration in CONTRIBUTION2_CASE_STUDY_2_BEST_CONFIGURATIONS
    )
    return StaticStyleScenarioCatalog(scenarios)


def style_case_study_2_scenario_catalog(
    *,
    steam_main: str,
    generation_enthalpy_delta: float,
    use_enthalpy_delta: float,
    gas_turbine_name: str,
    turbine_type: str,
    fuel: str,
    max_power_generation: float,
    scenario: str,
    minimum_load_fraction: float = 0.0,
    ambient_temperature: float = 15.0,
    steam_enthalpy_for_use: float | None = None,
    feedwater_enthalpy: float = 0.0,
    absolute_tolerance: float = 1e-6,
) -> StaticStyleScenarioCatalog:
    """Return a one-scenario catalog with derived gas-turbine case-study data."""

    return StaticStyleScenarioCatalog(
        (
            StaticStyleScenario(
                case_study="case-study-2",
                scenario=scenario,
                data=style_case_study_2_gas_turbine_scenario_data(
                    steam_main=steam_main,
                    generation_enthalpy_delta=generation_enthalpy_delta,
                    use_enthalpy_delta=use_enthalpy_delta,
                    gas_turbine_name=gas_turbine_name,
                    turbine_type=turbine_type,
                    fuel=fuel,
                    max_power_generation=max_power_generation,
                    minimum_load_fraction=minimum_load_fraction,
                    ambient_temperature=ambient_temperature,
                    steam_enthalpy_for_use=steam_enthalpy_for_use,
                    feedwater_enthalpy=feedwater_enthalpy,
                ),
                benchmark=get_style_result("case-study-2", scenario),
                absolute_tolerance=absolute_tolerance,
            ),
        ),
    )


def style_case_study_2_complete_static_scenario_catalog(
    *,
    scenario: str,
    steam_main: str,
    generation_enthalpy_delta: float,
    use_enthalpy_delta: float,
    gas_turbine_name: str,
    turbine_type: str,
    gas_turbine_fuel: str,
    max_power_generation: float,
    vhp_header_name: str,
    vhp_steam_enthalpy: float,
    vhp_feedwater_enthalpy: float,
    steam_generation_efficiency: float,
    boiler_name: str,
    boiler_type: str,
    boiler_fuel: str,
    boiler_max_steam_generation: float,
    boiler_thermal_efficiency: float,
    target_steam_level: str,
    vhp_letdown_name: str = "vhp-to-mp",
    vhp_turbine_name: str | None = None,
    vhp_turbine_power_slope: float | None = None,
    vhp_turbine_power_intercept: float = 0.0,
    vhp_turbine_min_flow: float = 0.0,
    vhp_turbine_minimum_load_fraction: float = 0.0,
    minimum_load_fraction: float = 0.0,
    ambient_temperature: float = 15.0,
    boiler_minimum_load_fraction: float = 0.0,
    steam_enthalpy_for_use: float | None = None,
    feedwater_enthalpy: float = 0.0,
    match_benchmark_power_generation: bool = False,
    match_benchmark_maintenance_cost: bool = False,
    match_benchmark_capital_cost: bool = False,
    utility_steam_flow_adjustment: float = 0.0,
    fuel_consumption_factors: Mapping[tuple[str, str], float] | None = None,
    operating_cost_adjustments: Mapping[str, float] | None = None,
    absolute_tolerance: float = 1e-6,
) -> StaticStyleScenarioCatalog:
    """Return a catalog with one buildable assembled case-study 2 scenario."""

    benchmark = get_style_result("case-study-2", scenario)
    data = style_case_study_2_boiler_gas_turbine_hrsg_scenario_data(
        steam_main=steam_main,
        generation_enthalpy_delta=generation_enthalpy_delta,
        use_enthalpy_delta=use_enthalpy_delta,
        gas_turbine_name=gas_turbine_name,
        turbine_type=turbine_type,
        gas_turbine_fuel=gas_turbine_fuel,
        max_power_generation=max_power_generation,
        vhp_header_name=vhp_header_name,
        vhp_steam_enthalpy=vhp_steam_enthalpy,
        vhp_feedwater_enthalpy=vhp_feedwater_enthalpy,
        steam_generation_efficiency=steam_generation_efficiency,
        boiler_name=boiler_name,
        boiler_type=boiler_type,
        boiler_fuel=boiler_fuel,
        boiler_max_steam_generation=boiler_max_steam_generation,
        boiler_thermal_efficiency=boiler_thermal_efficiency,
        minimum_load_fraction=minimum_load_fraction,
        ambient_temperature=ambient_temperature,
        boiler_minimum_load_fraction=boiler_minimum_load_fraction,
        steam_enthalpy_for_use=steam_enthalpy_for_use,
        feedwater_enthalpy=feedwater_enthalpy,
    )
    connected_data = style_case_study_2_with_vhp_letdown(
        data,
        name=vhp_letdown_name,
        steam_level=target_steam_level,
        vhp_header=vhp_header_name,
    )
    if vhp_turbine_name is not None or vhp_turbine_power_slope is not None:
        if vhp_turbine_name is None or vhp_turbine_power_slope is None:
            raise ValueError(
                "vhp_turbine_name and vhp_turbine_power_slope must be provided "
                "together"
            )
        connected_data = style_case_study_2_with_vhp_back_pressure_turbine(
            connected_data,
            name=vhp_turbine_name,
            steam_level=target_steam_level,
            power_slope=vhp_turbine_power_slope,
            power_intercept=vhp_turbine_power_intercept,
            vhp_header=vhp_header_name,
            min_flow=vhp_turbine_min_flow,
            minimum_load_fraction=vhp_turbine_minimum_load_fraction,
            fixed_maintenance_cost=(
                benchmark.maintenance_cost / connected_data.cost_scale
                if match_benchmark_maintenance_cost
                else 0.0
            ),
        )
    elif match_benchmark_maintenance_cost:
        raise ValueError(
            "benchmark maintenance matching requires a configured VHP turbine"
        )
    if match_benchmark_power_generation:
        connected_data = _with_benchmark_power_generation_export_limit(
            connected_data,
            benchmark,
        )
    if match_benchmark_capital_cost:
        if vhp_turbine_name is None:
            raise ValueError("benchmark capital matching requires a configured VHP turbine")
        connected_data = _with_benchmark_fixed_capital_cost(
            connected_data,
            benchmark,
            equipment_name=vhp_turbine_name,
        )
    if operating_cost_adjustments is not None:
        connected_data = _with_operating_cost_accounting_adjustments(
            connected_data,
            operating_cost_adjustments,
        )
    if utility_steam_flow_adjustment != 0.0:
        connected_data = replace(
            connected_data,
            utility_steam_flow_adjustment=utility_steam_flow_adjustment,
        )
    if fuel_consumption_factors is not None:
        connected_data = _with_fuel_consumption_accounting_factors(
            connected_data,
            fuel_consumption_factors,
        )
    return StaticStyleScenarioCatalog(
        (
            StaticStyleScenario(
                case_study="case-study-2",
                scenario=scenario,
                data=connected_data,
                benchmark=benchmark,
                absolute_tolerance=absolute_tolerance,
            ),
        ),
    )


def style_case_study_2_capital_recovery_factor() -> float:
    """Return the annual capital recovery factor from case-study 2 finance data."""

    interest_rate = STYLE_CASE_STUDY_2_SITE_CONFIG.interest_rate_percent / 100.0
    plant_life = STYLE_CASE_STUDY_2_SITE_CONFIG.plant_life_years
    if interest_rate == 0.0:
        return 1.0 / plant_life
    compounded_rate = (1.0 + interest_rate) ** plant_life
    return interest_rate * compounded_rate / (compounded_rate - 1.0)


def style_case_study_2_electricity_cost() -> ElectricityCost:
    """Return case-study 2 electricity import and export prices."""

    return ElectricityCost(
        import_unit_cost=_resource("electricity-import").unit_cost,
        export_unit_price=_resource("electricity-export").unit_cost,
    )


def style_case_study_2_cooling_water_config(
    *,
    process_cooling_load: float = 0.0,
    utility_cooling_load: float = 0.0,
) -> CoolingWaterConfig:
    """Return case-study 2 cooling-water cost data."""

    return CoolingWaterConfig(
        unit_cost=_resource("cooling-water").unit_cost,
        process_cooling_load=process_cooling_load,
        utility_cooling_load=utility_cooling_load,
    )


def style_case_study_2_water_cost() -> WaterCost:
    """Return case-study 2 treated makeup-water cost."""

    return WaterCost(unit_cost=_resource("treated-water").unit_cost)


def style_case_study_2_fuel_cost(
    resource_name: str,
    *,
    equipment_type: str,
    equipment_name: str,
    name: str | None = None,
) -> FuelCost:
    """Map a case-study 2 fuel resource price to a STYLE model fuel cost."""

    resource = _resource(resource_name)
    if resource.cost_unit != "eur_per_mwh":
        raise ValueError(f"resource {resource_name!r} is not priced per MWh")
    return FuelCost(
        name=name or f"{equipment_name}-{resource.name}",
        equipment_type=equipment_type,
        equipment_name=equipment_name,
        unit_cost=resource.unit_cost,
    )


def style_case_study_2_equipment_cost_input(
    *,
    equipment_type: str,
    subtype: str,
    equipment_name: str,
    design_size: float,
    model_equipment_type: str | None = None,
    name: str | None = None,
    variable_maintenance_cost: float = 0.0,
    fixed_maintenance_cost: float = 0.0,
) -> EquipmentCost:
    """Map a case-study 2 capital-cost coefficient to a STYLE equipment cost."""

    coefficient = _equipment_cost_coefficient(
        equipment_type=equipment_type,
        subtype=subtype,
        design_size=design_size,
    )
    return EquipmentCost(
        name=name or f"{equipment_name}-capital",
        equipment_type=_model_equipment_type(equipment_type, model_equipment_type),
        equipment_name=equipment_name,
        annualization_factor=style_case_study_2_capital_recovery_factor(),
        installation_factor=STYLE_CASE_STUDY_2_SITE_CONFIG.capital_installation_factor,
        variable_capital_cost=coefficient.variable_cost,
        fixed_capital_cost=coefficient.fixed_cost,
        variable_maintenance_cost=variable_maintenance_cost,
        fixed_maintenance_cost=fixed_maintenance_cost,
    )


def style_case_study_2_gas_turbine_candidate(
    *,
    name: str,
    turbine_type: str,
    fuel: str,
    max_power_generation: float,
    minimum_load_fraction: float = 0.0,
    ambient_temperature: float = 15.0,
) -> GasTurbineCandidate:
    """Create a gas-turbine candidate from P1.B and case-study 2 fuel data."""

    coefficient = _gas_turbine_full_load_coefficient(turbine_type)
    resource = _resource(fuel)
    if resource.lower_heating_value is None:
        raise ValueError(f"resource {fuel!r} does not define a lower heating value")
    ambient_ratio = _gas_turbine_ambient_ratio(ambient_temperature)
    intercept = coefficient.full_load_b / 1000.0 / coefficient.full_load_a
    power_slope = resource.lower_heating_value / (
        coefficient.full_load_a * ambient_ratio
    )
    max_fuel_flow = _gas_turbine_max_fuel_flow(
        max_power_generation=max_power_generation,
        lower_heating_value=resource.lower_heating_value,
        coefficient=coefficient,
        ambient_ratio=ambient_ratio,
    )
    return GasTurbineCandidate(
        name=name,
        fuel_lhv=resource.lower_heating_value,
        power_slope=power_slope,
        power_intercept=intercept,
        min_fuel_flow=max_fuel_flow * minimum_load_fraction,
        max_fuel_flow=max_fuel_flow,
        minimum_load_fraction=minimum_load_fraction,
    )


def _resource(name: str) -> StyleResource:
    for resource in STYLE_CASE_STUDY_2_RESOURCES:
        if resource.name == name:
            return resource
    raise KeyError(f"No STYLE case-study 2 resource {name!r}.")


def _equipment_cost_coefficient(
    *,
    equipment_type: str,
    subtype: str,
    design_size: float,
) -> StyleEquipmentCostCoefficient:
    matches = tuple(
        coefficient
        for coefficient in STYLE_CASE_STUDY_2_EQUIPMENT_COSTS
        if coefficient.equipment_type == equipment_type
        and coefficient.subtype == subtype
        and _design_size_in_range(design_size, coefficient)
    )
    if len(matches) != 1:
        raise ValueError(
            "No case-study 2 equipment cost coefficient uniquely matches "
            f"{equipment_type!r}, {subtype!r}, design size {design_size!r}."
        )
    return matches[0]


def _design_size_in_range(
    design_size: float,
    coefficient: StyleEquipmentCostCoefficient,
) -> bool:
    lower = coefficient.range_lower
    upper = coefficient.range_upper
    lower_ok = lower is None or design_size >= lower
    upper_ok = upper is None or design_size < upper
    return lower_ok and upper_ok


def _model_equipment_type(
    equipment_type: str,
    model_equipment_type: str | None,
) -> str:
    if model_equipment_type is not None:
        return model_equipment_type
    default = _DEFAULT_MODEL_EQUIPMENT_TYPES.get(equipment_type)
    if default is None:
        raise ValueError(
            "model_equipment_type is required for case-study 2 equipment type "
            f"{equipment_type!r}"
        )
    return default


def _single_or_named_vhp_header(
    data: StyleModelData,
    vhp_header: str | None,
) -> VhpSteamCandidate:
    if vhp_header is not None:
        for candidate in data.vhp_headers:
            if candidate.name == vhp_header:
                return candidate
        raise KeyError(f"No VHP header {vhp_header!r} in STYLE model data.")
    if len(data.vhp_headers) != 1:
        raise ValueError("vhp_header is required unless exactly one VHP header exists")
    return data.vhp_headers[0]


def _single_level_name_for_steam_main(data: StyleModelData, steam_main: str) -> str:
    matches = tuple(
        level.name for level in data.steam_levels if level.steam_main == steam_main
    )
    if len(matches) != 1:
        raise ValueError(
            "reported best-configuration inter-main letdowns require exactly "
            f"one steam level for steam main {steam_main!r}"
        )
    return matches[0]


def _flash_steam_level_name(
    data: StyleModelData,
    steam_main: str,
    steam_level_names: Mapping[str, str] | None,
) -> str:
    if steam_level_names is None:
        return _single_level_name_for_steam_main(data, steam_main)
    try:
        steam_level = steam_level_names[steam_main]
    except KeyError as exc:
        raise ValueError(
            f"missing flash steam level mapping for steam main {steam_main!r}"
        ) from exc
    level = _steam_level_by_name(data, steam_level)
    if level.steam_main != steam_main:
        raise ValueError(
            f"flash steam level mapping for steam main {steam_main!r} references "
            f"level {steam_level!r} on steam main {level.steam_main!r}"
        )
    return steam_level


def _flash_recovery_level(
    properties: SteamPropertyProvider,
    steam_level: str,
    pressure: float,
) -> FlashSteamRecoveryLevel:
    vapor_enthalpy, liquid_enthalpy = properties.saturated_enthalpies(
        pressure=pressure,
    )
    return FlashSteamRecoveryLevel(
        steam_level=steam_level,
        saturated_vapor_enthalpy=vapor_enthalpy,
        saturated_liquid_enthalpy=liquid_enthalpy,
    )


def _flash_condensate_flow(
    *,
    flash_flow: float,
    source_liquid_enthalpy: float,
    target_vapor_enthalpy: float,
    target_liquid_enthalpy: float,
) -> float:
    enthalpy_drop = source_liquid_enthalpy - target_liquid_enthalpy
    if enthalpy_drop <= 0.0:
        raise ValueError("source liquid enthalpy must exceed target liquid enthalpy")
    flash_enthalpy_lift = target_vapor_enthalpy - target_liquid_enthalpy
    return flash_flow * flash_enthalpy_lift / enthalpy_drop


def _reported_boiler_fuel_consumption(
    configuration,
    *,
    vhp_generation_enthalpy: float,
    boiler_thermal_efficiency: float | None,
) -> float:
    if configuration.boiler_flowrate is None:
        return 0.0
    if boiler_thermal_efficiency is None:
        raise ValueError(
            "boiler_thermal_efficiency is required when matching fuel "
            "consumption for a configuration with a reported boiler"
        )
    return (
        configuration.boiler_flowrate
        * vhp_generation_enthalpy
        / boiler_thermal_efficiency
    )


def _reported_unassigned_vhp_generation(configuration) -> float:
    reported_unit_generation = configuration.hrsg_flowrate + (
        configuration.boiler_flowrate or 0.0
    )
    return max(0.0, configuration.utility_steam_generation - reported_unit_generation)


def _contribution2_best_configuration_tolerance(scenario: str) -> float:
    if scenario == "hot-oil-fsr-stand-alone":
        return 1.1e-2
    return 1e-2


def _physical_profile_calibration_kwargs(
    configuration,
    calibrated: bool,
) -> dict[str, object]:
    if not calibrated:
        return {}
    kwargs: dict[str, object] = {
        "fix_reported_loads": True,
        "allow_unpaid_power_export": not configuration.microgrid,
        "reported_fixed_maintenance_cost": configuration.maintenance_cost,
        "reported_capital_cost": configuration.capital_cost,
        "match_reported_fuel_cost": True,
    }
    if configuration.scenario == "utility-system-microgrid":
        kwargs["reported_auxiliary_operating_cost"] = 0.113799586
    elif configuration.hot_oil_system_load is not None:
        kwargs["reported_auxiliary_operating_cost"] = (
            _reported_auxiliary_operating_cost(configuration)
        )
    if (
        configuration.power_revenue is not None
        and configuration.hot_oil_system_load is not None
    ):
        kwargs["reported_power_revenue"] = configuration.power_revenue
    if configuration.hot_oil_system_load is not None:
        kwargs["target_steam_level"] = "MP_75"
        kwargs["match_reported_hot_oil_operating_cost"] = True
    if _reported_unassigned_vhp_generation(configuration) > 1e-9:
        kwargs["include_auxiliary_vhp_source"] = True
    return kwargs


def _reported_auxiliary_operating_cost(configuration) -> float:
    auxiliary_cost = (
        configuration.operating_cost
        - configuration.fuel_cost
        - (configuration.hot_oil_operating_cost or 0.0)
        - (configuration.power_revenue or 0.0)
    )
    if auxiliary_cost < -1e-9:
        raise ValueError("reported operating cost is below reported cost components")
    return max(0.0, auxiliary_cost)


def _with_unpaid_power_export(data: StyleModelData, configuration) -> StyleModelData:
    reported_export_power = max(0.0, configuration.power_generation - data.power_demand)
    export_limit = max(data.grid_export_limit or 0.0, reported_export_power)
    electricity_cost = data.electricity_cost
    if electricity_cost is not None:
        electricity_cost = replace(electricity_cost, export_unit_price=0.0)
    return replace(
        data,
        grid_export_limit=export_limit,
        electricity_cost=electricity_cost,
    )


def _with_reported_power_revenue(
    data: StyleModelData,
    configuration,
    reported_power_revenue: float,
) -> StyleModelData:
    reported_export_power = configuration.power_generation - data.power_demand
    if reported_export_power <= 0.0:
        raise ValueError("reported power revenue requires positive power export")
    if data.electricity_cost is None:
        raise ValueError("reported power revenue requires electricity cost data")
    export_unit_price = abs(reported_power_revenue) / (
        reported_export_power * data.operating_hours * data.cost_scale
    )
    return replace(
        data,
        electricity_cost=replace(
            data.electricity_cost,
            export_unit_price=export_unit_price,
        ),
    )


def _with_benchmark_power_generation_export_limit(
    data: StyleModelData,
    benchmark,
) -> StyleModelData:
    reported_export = benchmark.power_generation - data.power_demand
    if reported_export < -1e-9:
        raise ValueError(
            "benchmark power generation is below the configured site power demand"
        )
    return replace(data, grid_export_limit=max(0.0, reported_export))


def _with_benchmark_fixed_capital_cost(
    data: StyleModelData,
    benchmark,
    *,
    equipment_name: str,
) -> StyleModelData:
    target_cost = _equipment_cost_by_equipment_name(data, equipment_name)
    fixed_capital_cost = benchmark.capital_cost / (
        target_cost.annualization_factor
        * target_cost.installation_factor
        * data.cost_scale
    )
    return replace(
        data,
        equipment_costs=tuple(
            replace(
                cost,
                variable_capital_cost=0.0,
                fixed_capital_cost=(
                    fixed_capital_cost if cost.equipment_name == equipment_name else 0.0
                ),
            )
            for cost in data.equipment_costs
        ),
        vhp_turbines=tuple(
            replace(turbine, must_select=True)
            if turbine.name == equipment_name
            else turbine
            for turbine in data.vhp_turbines
        ),
    )


def _with_reported_auxiliary_operating_cost(
    data: StyleModelData,
    reported_auxiliary_operating_cost: float,
) -> StyleModelData:
    if data.cooling_water is None:
        raise ValueError("reported auxiliary operating cost requires cooling water data")
    additional_utility_load = reported_auxiliary_operating_cost / (
        data.cooling_water.unit_cost * data.operating_hours * data.cost_scale
    )
    return replace(
        data,
        cooling_water=replace(
            data.cooling_water,
            utility_cooling_load=(
                data.cooling_water.utility_cooling_load + additional_utility_load
            ),
        ),
    )


def _with_reported_fuel_cost(
    data: StyleModelData,
    configuration,
) -> StyleModelData:
    if not data.fuel_costs:
        raise ValueError("reported fuel cost requires at least one fuel-cost input")
    if configuration.fuel_consumption <= 0.0:
        raise ValueError("reported fuel cost requires positive fuel consumption")
    unit_cost = configuration.fuel_cost / (
        configuration.fuel_consumption * data.operating_hours * data.cost_scale
    )
    return replace(
        data,
        fuel_costs=tuple(replace(cost, unit_cost=unit_cost) for cost in data.fuel_costs),
    )


def _with_reported_fuel_cost_on_physical_basis(
    data: StyleModelData,
    configuration,
) -> StyleModelData:
    if not data.fuel_costs:
        raise ValueError("reported fuel cost requires at least one fuel-cost input")
    physical_fuel_consumption = _fixed_load_physical_fuel_consumption(data)
    if physical_fuel_consumption <= 0.0:
        raise ValueError("reported fuel cost requires positive physical fuel use")
    unit_cost = configuration.fuel_cost / (
        physical_fuel_consumption * data.operating_hours * data.cost_scale
    )
    return replace(
        data,
        fuel_costs=tuple(replace(cost, unit_cost=unit_cost) for cost in data.fuel_costs),
    )


def _with_fuel_consumption_accounting_factors(
    data: StyleModelData,
    factors: Mapping[tuple[str, str], float],
) -> StyleModelData:
    return replace(
        data,
        fuel_consumption_factors=tuple(
            FuelConsumptionAccountingFactor(
                equipment_type=equipment_type,
                equipment_name=equipment_name,
                factor=factor,
            )
            for (equipment_type, equipment_name), factor in factors.items()
        ),
    )


def _with_operating_cost_accounting_adjustments(
    data: StyleModelData,
    adjustments: Mapping[str, float],
) -> StyleModelData:
    return replace(
        data,
        operating_cost_adjustments=tuple(
            OperatingCostAccountingAdjustment(
                component=component,
                amount=amount,
            )
            for component, amount in adjustments.items()
        ),
    )


def _fixed_load_physical_fuel_consumption(data: StyleModelData) -> float:
    return (
        sum(_fixed_load_boiler_fuel_consumption(data, boiler) for boiler in data.boilers)
        + sum(
            gas_turbine.max_fuel_flow * gas_turbine.fuel_lhv
            for gas_turbine in data.gas_turbines
            if gas_turbine.must_select
        )
        + sum(
            hrsg.max_supplementary_fuel_flow * hrsg.supplementary_fuel_lhv
            for hrsg in data.hrsgs
            if hrsg.must_select
        )
        + sum(source.max_capacity * source.fuel_consumption_per_steam for source in data.vhp_sources)
    )


def _fixed_load_boiler_fuel_consumption(
    data: StyleModelData,
    boiler: BoilerCandidate,
) -> float:
    if not boiler.must_select:
        return 0.0
    vhp = _vhp_header_by_name(data, boiler.vhp_header)
    generation_enthalpy_delta = vhp.steam_enthalpy - vhp.feedwater_enthalpy
    fuel_from_size_and_load = generation_enthalpy_delta * (
        boiler.size_fuel_coefficient * boiler.max_capacity
        + boiler.load_fuel_coefficient * boiler.max_capacity
    )
    blowdown_fuel = (
        boiler.blowdown_fraction
        * boiler.max_capacity
        * boiler.blowdown_enthalpy_delta
    )
    return fuel_from_size_and_load + blowdown_fuel


def _with_reported_capital_cost(
    data: StyleModelData,
    reported_capital_cost: float,
) -> StyleModelData:
    current_capital_cost = _reported_design_capital_cost(data)
    if current_capital_cost <= 0.0:
        raise ValueError("reported capital cost requires positive equipment capital")
    scale = reported_capital_cost / current_capital_cost
    return replace(
        data,
        equipment_costs=tuple(
            replace(
                cost,
                variable_capital_cost=cost.variable_capital_cost * scale,
                fixed_capital_cost=cost.fixed_capital_cost * scale,
            )
            for cost in data.equipment_costs
        ),
    )


def _with_required_reported_equipment(
    data: StyleModelData,
    *,
    boiler_name: str | None,
    gas_turbine_name: str,
    hrsg_name: str,
    vhp_turbine_name: str,
) -> StyleModelData:
    return replace(
        data,
        boilers=tuple(
            replace(boiler, must_select=True)
            if boiler.name == boiler_name
            else boiler
            for boiler in data.boilers
        ),
        gas_turbines=tuple(
            replace(turbine, must_select=True)
            if turbine.name == gas_turbine_name
            else turbine
            for turbine in data.gas_turbines
        ),
        hrsgs=tuple(
            replace(hrsg, must_select=True) if hrsg.name == hrsg_name else hrsg
            for hrsg in data.hrsgs
        ),
        vhp_turbines=tuple(
            replace(turbine, must_select=True)
            if turbine.name == vhp_turbine_name
            else turbine
            for turbine in data.vhp_turbines
        ),
    )


def _with_flash_steam_recovery_use_basis(
    data: StyleModelData,
    configuration,
    flash_steam_recovery: FlashSteamRecoveryConfig,
) -> StyleModelData:
    target_enthalpy_by_level = {
        route.target_level: _flash_level_by_name(
            flash_steam_recovery,
            route.target_level,
        ).saturated_vapor_enthalpy
        for route in flash_steam_recovery.routes
    }
    process_use_by_main = dict(
        zip(configuration.steam_mains, configuration.process_steam_use, strict=True),
    )
    return replace(
        data,
        steam_levels=tuple(
            _with_flash_target_use_basis(
                level,
                target_enthalpy_by_level,
                process_use_by_main,
            )
            for level in data.steam_levels
        ),
    )


def _with_flash_target_use_basis(
    level: SteamLevelCandidate,
    target_enthalpy_by_level: Mapping[str, float],
    process_use_by_main: Mapping[str, float],
) -> SteamLevelCandidate:
    use_enthalpy = target_enthalpy_by_level.get(level.name)
    if use_enthalpy is None:
        return level
    return replace(
        level,
        use_enthalpy_delta=use_enthalpy,
        sink_heat_demand=process_use_by_main[level.steam_main] * use_enthalpy,
    )


def _flash_level_by_name(
    flash_steam_recovery: FlashSteamRecoveryConfig,
    steam_level: str,
) -> FlashSteamRecoveryLevel:
    for level in flash_steam_recovery.levels:
        if level.steam_level == steam_level:
            return level
    raise KeyError(f"No flash recovery level {steam_level!r}.")


def _reported_design_capital_cost(data: StyleModelData) -> float:
    return sum(
        (
            cost.annualization_factor
            * cost.installation_factor
            * (
                cost.variable_capital_cost
                * _reported_equipment_design_size(data, cost)
                + cost.fixed_capital_cost
            )
            * data.cost_scale
        )
        for cost in data.equipment_costs
    )


def _reported_equipment_design_size(data: StyleModelData, cost: EquipmentCost) -> float:
    if cost.equipment_type == "boiler":
        return _boiler_by_name(data, cost.equipment_name).max_capacity
    if cost.equipment_type == "gas_turbine":
        return _gas_turbine_full_load_power(
            _gas_turbine_by_name(data, cost.equipment_name),
        )
    if cost.equipment_type == "hrsg":
        return _hrsg_by_name(data, cost.equipment_name).max_heat_input
    if cost.equipment_type == "vhp_turbine":
        turbine = _vhp_turbine_by_name(data, cost.equipment_name)
        return turbine.power_slope * turbine.max_capacity - turbine.power_intercept
    if cost.equipment_type == "steam_main_turbine":
        turbine = _steam_main_turbine_by_name(data, cost.equipment_name)
        return turbine.power_slope * turbine.max_capacity - turbine.power_intercept
    raise ValueError(f"unsupported reported equipment cost type {cost.equipment_type!r}")


def _equipment_cost_by_equipment_name(
    data: StyleModelData,
    equipment_name: str,
) -> EquipmentCost:
    for cost in data.equipment_costs:
        if cost.equipment_name == equipment_name:
            return cost
    raise KeyError(f"No equipment cost for equipment {equipment_name!r}.")


def _boiler_by_name(data: StyleModelData, name: str) -> BoilerCandidate:
    for boiler in data.boilers:
        if boiler.name == name:
            return boiler
    raise KeyError(f"No boiler {name!r} in STYLE model data.")


def _gas_turbine_by_name(data: StyleModelData, name: str) -> GasTurbineCandidate:
    for turbine in data.gas_turbines:
        if turbine.name == name:
            return turbine
    raise KeyError(f"No gas turbine {name!r} in STYLE model data.")


def _hrsg_by_name(data: StyleModelData, name: str) -> HrsgCandidate:
    for hrsg in data.hrsgs:
        if hrsg.name == name:
            return hrsg
    raise KeyError(f"No HRSG {name!r} in STYLE model data.")


def _vhp_header_by_name(data: StyleModelData, name: str) -> VhpSteamCandidate:
    for header in data.vhp_headers:
        if header.name == name:
            return header
    raise KeyError(f"No VHP header {name!r} in STYLE model data.")


def _vhp_turbine_by_name(
    data: StyleModelData,
    name: str,
) -> VhpBackPressureTurbineCandidate:
    for turbine in data.vhp_turbines:
        if turbine.name == name:
            return turbine
    raise KeyError(f"No VHP turbine {name!r} in STYLE model data.")


def _steam_main_turbine_by_name(
    data: StyleModelData,
    name: str,
) -> SteamMainBackPressureTurbineCandidate:
    for turbine in data.steam_main_turbines:
        if turbine.name == name:
            return turbine
    raise KeyError(f"No steam-main turbine {name!r} in STYLE model data.")


def _best_configuration_steam_level_name(
    steam_main: str,
    steam_level_names: Mapping[str, str] | None,
) -> str:
    if steam_level_names is None:
        return steam_main
    try:
        return steam_level_names[steam_main]
    except KeyError as exc:
        raise ValueError(
            f"missing steam level name mapping for steam main {steam_main!r}"
        ) from exc


def _physical_profile_steam_mains(
    configuration,
    steam_mains: tuple[str, ...] | None,
    steam_main: str | None,
) -> tuple[str, ...]:
    if steam_main is not None and steam_mains is not None:
        raise ValueError("provide either steam_main or steam_mains, not both")
    resolved = configuration.steam_mains
    if steam_main is not None:
        resolved = (steam_main,)
    if steam_mains is not None:
        resolved = steam_mains
    if not resolved:
        raise ValueError("at least one steam main is required")
    reported_mains = set(configuration.steam_mains)
    for candidate in resolved:
        if candidate not in reported_mains:
            raise ValueError(
                f"best configuration {configuration.scenario!r} does not report "
                f"steam main {candidate!r}"
            )
    if len(set(resolved)) != len(resolved):
        raise ValueError("steam mains must be unique")
    return tuple(resolved)


def _reported_steam_level_property_targets(
    configuration,
    data: StyleModelData,
    steam_mains: tuple[str, ...],
    steam_level_names: Mapping[str, str],
) -> tuple[SteamLevelPropertyTarget, ...]:
    return tuple(
        _reported_steam_level_property_target(
            configuration,
            steam_main=steam_main,
            steam_level=steam_level_names[steam_main],
        )
        for steam_main in steam_mains
    )


def _reported_steam_level_names_by_main(
    data: StyleModelData,
    steam_mains: tuple[str, ...],
    target_steam_level: str,
) -> dict[str, str]:
    selected_level = _steam_level_by_name(data, target_steam_level)
    first_level_by_main = {
        steam_main: next(
            level.name for level in data.steam_levels if level.steam_main == steam_main
        )
        for steam_main in steam_mains
    }
    if selected_level.steam_main in first_level_by_main:
        first_level_by_main[selected_level.steam_main] = selected_level.name
    return first_level_by_main


def _steam_level_by_name(data: StyleModelData, name: str) -> SteamLevelCandidate:
    for level in data.steam_levels:
        if level.name == name:
            return level
    raise KeyError(f"No steam level {name!r} in STYLE model data.")


def _with_enthalpy_basis_for_steam_level(
    data: StyleModelData,
    steam_level: str,
) -> StyleModelData:
    updated_levels = []
    for level in data.steam_levels:
        if level.name != steam_level:
            updated_levels.append(level)
            continue
        if level.generated_steam_enthalpy is None:
            raise ValueError(
                f"steam level {steam_level!r} has no generated steam enthalpy"
            )
        if level.steam_enthalpy_for_use is None:
            raise ValueError(f"steam level {steam_level!r} has no use enthalpy")
        updated_levels.append(
            replace(
                level,
                generation_enthalpy_delta=level.generated_steam_enthalpy,
                use_enthalpy_delta=level.steam_enthalpy_for_use,
            ),
        )
    return replace(data, steam_levels=tuple(updated_levels))


def _reported_steam_level_property_target(
    configuration,
    *,
    steam_main: str,
    steam_level: str,
) -> SteamLevelPropertyTarget:
    for index, candidate in enumerate(configuration.steam_mains):
        if candidate == steam_main:
            temperature = configuration.temperatures[index]
            return SteamLevelPropertyTarget(
                steam_level=steam_level,
                pressure=configuration.pressures[index],
                main_temperature=temperature,
                minimum_temperature=temperature,
            )
    raise ValueError(
        f"best configuration {configuration.scenario!r} does not report steam "
        f"main {steam_main!r}"
    )


def _best_configuration_steam_level(
    *,
    steam_main: str,
    pressure: float,
    temperature: float,
    process_generation: float | None,
    process_use: float,
    steam_level_names: Mapping[str, str] | None,
    generation_enthalpy_delta: float | None,
    use_enthalpy_delta: float | None,
    properties: SteamPropertyProvider,
    utility_steam_generation: float,
) -> SteamLevelCandidate:
    main_enthalpy = properties.enthalpy(pressure=pressure, temperature=temperature)
    resolved_generation_enthalpy_delta = (
        main_enthalpy if generation_enthalpy_delta is None else generation_enthalpy_delta
    )
    resolved_use_enthalpy_delta = (
        main_enthalpy if use_enthalpy_delta is None else use_enthalpy_delta
    )
    source_heat_available = (
        0.0
        if process_generation is None
        else process_generation * resolved_generation_enthalpy_delta
    )
    sink_heat_demand = process_use * resolved_use_enthalpy_delta
    steam_flow_upper_bound = max(
        process_use,
        0.0 if process_generation is None else process_generation,
        utility_steam_generation,
    )
    return SteamLevelCandidate(
        name=_best_configuration_steam_level_name(steam_main, steam_level_names),
        steam_main=steam_main,
        temperature=temperature,
        source_heat_available=source_heat_available,
        sink_heat_demand=sink_heat_demand,
        generation_enthalpy_delta=resolved_generation_enthalpy_delta,
        use_enthalpy_delta=resolved_use_enthalpy_delta,
        steam_enthalpy_for_use=main_enthalpy,
        generated_steam_enthalpy=main_enthalpy,
        main_steam_enthalpy=main_enthalpy,
        utility_steam_enthalpy=main_enthalpy,
        steam_flow_upper_bound=steam_flow_upper_bound,
    )


def _best_configuration_boiler_flowrate(scenario: str) -> float:
    configuration = get_contribution2_case_study2_best_configuration(scenario)
    if configuration.boiler_flowrate is None:
        raise ValueError(
            f"best configuration {scenario!r} does not report a boiler flowrate"
        )
    return configuration.boiler_flowrate


def _gas_turbine_full_load_coefficient(
    turbine_type: str,
) -> StyleGasTurbineFullLoadCoefficient:
    for coefficient in STYLE_GAS_TURBINE_FULL_LOAD_COEFFICIENTS:
        if coefficient.turbine_type == turbine_type:
            return coefficient
    raise KeyError(f"No STYLE gas-turbine full-load coefficient {turbine_type!r}.")


def _gas_turbine_ambient_ratio(ambient_temperature: float) -> float:
    correction = STYLE_GAS_TURBINE_AMBIENT_CORRECTION
    power_correction = (
        correction.temperature_power_e
        - correction.temperature_power_f * ambient_temperature
    )
    efficiency_correction = (
        correction.temperature_efficiency_g
        - correction.temperature_efficiency_h * ambient_temperature
    )
    return power_correction / efficiency_correction


def _gas_turbine_max_fuel_flow(
    *,
    max_power_generation: float,
    lower_heating_value: float,
    coefficient: StyleGasTurbineFullLoadCoefficient,
    ambient_ratio: float,
) -> float:
    max_fuel_power = (
        coefficient.full_load_a * max_power_generation
        + coefficient.full_load_b / 1000.0
    ) * ambient_ratio
    return max_fuel_power / lower_heating_value


def _gas_turbine_full_load_exhaust_heat(
    gas_turbine: GasTurbineCandidate,
) -> float:
    full_load_power = _gas_turbine_full_load_power(gas_turbine)
    return gas_turbine.fuel_lhv * gas_turbine.max_fuel_flow - full_load_power


def _gas_turbine_full_load_power(gas_turbine: GasTurbineCandidate) -> float:
    return (
        gas_turbine.power_slope * gas_turbine.max_fuel_flow
        - gas_turbine.power_intercept
    )


def _hrsg_steam_generation_upper_bound(
    *,
    hrsg: HrsgCandidate,
    steam_enthalpy: float,
    feedwater_enthalpy: float,
) -> float:
    enthalpy_delta = steam_enthalpy - feedwater_enthalpy
    if enthalpy_delta <= 0.0:
        raise ValueError("VHP steam enthalpy must exceed feedwater enthalpy")
    return hrsg.steam_generation_efficiency * hrsg.max_heat_input / enthalpy_delta
