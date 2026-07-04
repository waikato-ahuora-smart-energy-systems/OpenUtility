"""Pyomo construction for the static STYLE model."""

from __future__ import annotations

from collections.abc import Mapping

import pyomo.environ as pyo

from ._pyomo_indices import (
    boilers_by_vhp as _boilers_by_vhp,
    flash_level_by_name as _flash_level_by_name,
    flash_route_by_name as _flash_route_by_name,
    flash_routes_by_source as _flash_routes_by_source,
    flash_routes_by_target as _flash_routes_by_target,
    hrsgs_by_vhp as _hrsgs_by_vhp,
    steam_main_letdowns_by_source as _steam_main_letdowns_by_source,
    steam_main_letdowns_by_target as _steam_main_letdowns_by_target,
    steam_main_turbines_by_source as _steam_main_turbines_by_source,
    steam_main_turbines_by_target as _steam_main_turbines_by_target,
    vhp_letdowns_by_pair as _vhp_letdowns_by_pair,
    vhp_sources_by_vhp as _vhp_sources_by_vhp,
    vhp_turbines_by_pair as _vhp_turbines_by_pair,
)
from .data import (
    BoilerCandidate,
    EquipmentCost,
    FlashSteamRecoveryLevel,
    FlashSteamRecoveryRoute,
    FuelCost,
    GasTurbineCandidate,
    HrsgCandidate,
    SteamMainBackPressureTurbineCandidate,
    SteamMainLetdownStationCandidate,
    SteamLevelCandidate,
    StyleModelData,
    VhpBackPressureTurbineCandidate,
    VhpLetdownStationCandidate,
    VhpSteamCandidate,
    VhpSteamSourceCandidate,
)


def build_static_style_model(data: StyleModelData) -> pyo.ConcreteModel:
    """Build the current static STYLE Pyomo model slice."""

    levels = tuple(data.steam_levels)
    level_names = tuple(level.name for level in levels)
    level_by_name = {level.name: level for level in levels}
    vhp_source_by_name = {source.name: source for source in data.vhp_sources}
    boiler_by_name = {boiler.name: boiler for boiler in data.boilers}
    turbine_by_name = {turbine.name: turbine for turbine in data.vhp_turbines}
    letdown_by_name = {letdown.name: letdown for letdown in data.vhp_letdowns}
    steam_main_turbine_by_name = {
        turbine.name: turbine for turbine in data.steam_main_turbines
    }
    steam_main_letdown_by_name = {
        letdown.name: letdown for letdown in data.steam_main_letdowns
    }
    gas_turbine_by_name = {turbine.name: turbine for turbine in data.gas_turbines}
    hrsg_by_name = {hrsg.name: hrsg for hrsg in data.hrsgs}
    flash_level_by_name = _flash_level_by_name(data)
    flash_route_by_name = _flash_route_by_name(data)
    vhp_by_name = {header.name: header for header in data.vhp_headers}
    previous_level = _previous_level_names_by_main(data)
    bottom_levels = _bottom_level_names_by_main(data)

    model = pyo.ConcreteModel(name="STYLE static utility synthesis")
    _add_sets(model, data, level_names)
    _add_parameters(
        model,
        data,
        level_by_name,
        vhp_source_by_name,
        boiler_by_name,
        turbine_by_name,
        letdown_by_name,
        steam_main_turbine_by_name,
        steam_main_letdown_by_name,
        gas_turbine_by_name,
        hrsg_by_name,
        flash_level_by_name,
        flash_route_by_name,
        vhp_by_name,
    )
    _add_variables(model)
    _add_source_cascade_constraints(model, data, previous_level)
    _add_sink_cascade_constraints(model, data, previous_level)
    _add_cooling_water_constraints(model, data, bottom_levels)
    _add_hot_oil_constraints(model, data, previous_level)
    _add_flash_steam_recovery_constraints(model, data)
    _add_steam_main_balance_constraints(model, data)
    _add_vhp_constraints(model, data)
    _add_vhp_source_constraints(model, data)
    _add_boiler_constraints(model, data)
    _add_vhp_connection_constraints(model, data)
    _add_steam_main_connection_constraints(model, data)
    _add_gas_turbine_constraints(model)
    _add_hrsg_constraints(model, data)
    _add_deaerator_constraints(model, data)
    _add_power_generation_constraints(model, data)
    _add_electricity_constraints(model, data)
    _add_level_selection_constraints(model, data)
    _add_equipment_cost_expressions(model, data)
    _add_operating_cost_expressions(model, data)
    _add_objective(model)
    return model


def _add_sets(
    model: pyo.ConcreteModel,
    data: StyleModelData,
    level_names: tuple[str, ...],
) -> None:
    model.STEAM_MAINS = pyo.Set(initialize=data.steam_mains, ordered=True)
    model.STEAM_LEVELS = pyo.Set(initialize=level_names, ordered=True)
    model.VHP_HEADERS = pyo.Set(
        initialize=tuple(header.name for header in data.vhp_headers),
        ordered=True,
    )
    model.VHP_SOURCES = pyo.Set(
        initialize=tuple(source.name for source in data.vhp_sources),
        ordered=True,
    )
    model.BOILERS = pyo.Set(
        initialize=tuple(boiler.name for boiler in data.boilers),
        ordered=True,
    )
    model.VHP_TURBINES = pyo.Set(
        initialize=tuple(turbine.name for turbine in data.vhp_turbines),
        ordered=True,
    )
    model.VHP_LETDOWNS = pyo.Set(
        initialize=tuple(letdown.name for letdown in data.vhp_letdowns),
        ordered=True,
    )
    model.STEAM_MAIN_TURBINES = pyo.Set(
        initialize=tuple(turbine.name for turbine in data.steam_main_turbines),
        ordered=True,
    )
    model.STEAM_MAIN_LETDOWNS = pyo.Set(
        initialize=tuple(letdown.name for letdown in data.steam_main_letdowns),
        ordered=True,
    )
    model.GAS_TURBINES = pyo.Set(
        initialize=tuple(turbine.name for turbine in data.gas_turbines),
        ordered=True,
    )
    model.HRSGS = pyo.Set(
        initialize=tuple(hrsg.name for hrsg in data.hrsgs),
        ordered=True,
    )
    model.FLASH_ROUTES = pyo.Set(
        initialize=(
            ()
            if data.flash_steam_recovery is None
            else tuple(route.name for route in data.flash_steam_recovery.routes)
        ),
        ordered=True,
    )
    model.EQUIPMENT_COSTS = pyo.Set(
        initialize=tuple(cost.name for cost in data.equipment_costs),
        ordered=True,
    )
    model.FUEL_COSTS = pyo.Set(
        initialize=tuple(cost.name for cost in data.fuel_costs),
        ordered=True,
    )


def _add_parameters(
    model: pyo.ConcreteModel,
    data: StyleModelData,
    level_by_name: Mapping[str, SteamLevelCandidate],
    vhp_source_by_name: Mapping[str, VhpSteamSourceCandidate],
    boiler_by_name: Mapping[str, BoilerCandidate],
    turbine_by_name: Mapping[str, VhpBackPressureTurbineCandidate],
    letdown_by_name: Mapping[str, VhpLetdownStationCandidate],
    steam_main_turbine_by_name: Mapping[str, SteamMainBackPressureTurbineCandidate],
    steam_main_letdown_by_name: Mapping[str, SteamMainLetdownStationCandidate],
    gas_turbine_by_name: Mapping[str, GasTurbineCandidate],
    hrsg_by_name: Mapping[str, HrsgCandidate],
    flash_level_by_name: Mapping[str, FlashSteamRecoveryLevel],
    flash_route_by_name: Mapping[str, FlashSteamRecoveryRoute],
    vhp_by_name: Mapping[str, VhpSteamCandidate],
) -> None:
    fuel_consumption_factor_by_key = {
        (factor.equipment_type, factor.equipment_name): factor.factor
        for factor in data.fuel_consumption_factors
    }
    model.power_demand = pyo.Param(initialize=float(data.power_demand), mutable=False)
    model.operating_hours = pyo.Param(
        initialize=float(data.operating_hours),
        mutable=False,
    )
    model.cost_scale = pyo.Param(initialize=float(data.cost_scale), mutable=False)
    model.utility_steam_flow_adjustment = pyo.Param(
        initialize=float(data.utility_steam_flow_adjustment),
        mutable=False,
    )
    model.auxiliary_operating_cost_adjustment = pyo.Param(
        initialize=sum(
            adjustment.amount
            for adjustment in data.operating_cost_adjustments
            if adjustment.component == "auxiliary_or_unallocated"
        ),
        mutable=False,
    )
    model.deaerator_feedwater_enthalpy = pyo.Param(
        initialize=(
            0.0 if data.deaerator is None else data.deaerator.feedwater_enthalpy
        ),
        mutable=False,
    )
    model.deaerator_condensate_enthalpy = pyo.Param(
        initialize=(
            0.0 if data.deaerator is None else data.deaerator.condensate_enthalpy
        ),
        mutable=False,
    )
    model.deaerator_makeup_water_enthalpy = pyo.Param(
        initialize=(
            0.0 if data.deaerator is None else data.deaerator.makeup_water_enthalpy
        ),
        mutable=False,
    )
    model.deaerator_vent_enthalpy = pyo.Param(
        initialize=0.0 if data.deaerator is None else data.deaerator.vent_enthalpy,
        mutable=False,
    )
    model.deaerator_condensate_return_fraction = pyo.Param(
        initialize=(
            0.0 if data.deaerator is None else data.deaerator.condensate_return_fraction
        ),
        mutable=False,
    )
    model.deaerator_vent_fraction = pyo.Param(
        initialize=0.0 if data.deaerator is None else data.deaerator.vent_fraction,
        mutable=False,
    )
    model.flash_condensate_return_fraction = pyo.Param(
        initialize=(
            0.0
            if data.flash_steam_recovery is None
            else data.flash_steam_recovery.condensate_return_fraction
        ),
        mutable=False,
    )
    model.cooling_water_unit_cost = pyo.Param(
        initialize=0.0 if data.cooling_water is None else data.cooling_water.unit_cost,
        mutable=False,
    )
    model.cooling_water_process_load = pyo.Param(
        initialize=(
            0.0
            if data.cooling_water is None
            else data.cooling_water.process_cooling_load
        ),
        mutable=False,
    )
    model.cooling_water_utility_load = pyo.Param(
        initialize=(
            0.0
            if data.cooling_water is None
            else data.cooling_water.utility_cooling_load
        ),
        mutable=False,
    )
    model.hot_oil_fuel_unit_cost = pyo.Param(
        initialize=0.0 if data.hot_oil is None else data.hot_oil.fuel_unit_cost,
        mutable=False,
    )
    model.hot_oil_thermal_efficiency = pyo.Param(
        initialize=1.0 if data.hot_oil is None else data.hot_oil.thermal_efficiency,
        mutable=False,
    )
    model.hot_oil_fuel_consumption_factor = pyo.Param(
        initialize=fuel_consumption_factor_by_key.get(
            ("hot_oil", "hot_oil_furnace"),
            1.0,
        ),
        mutable=False,
    )
    model.hot_oil_high_temperature_heat_demand = pyo.Param(
        initialize=(
            0.0 if data.hot_oil is None else data.hot_oil.high_temperature_heat_demand
        ),
        mutable=False,
    )
    model.electricity_import_unit_cost = pyo.Param(
        initialize=(
            0.0
            if data.electricity_cost is None
            else data.electricity_cost.import_unit_cost
        ),
        mutable=False,
    )
    model.electricity_export_unit_price = pyo.Param(
        initialize=(
            0.0
            if data.electricity_cost is None
            else data.electricity_cost.export_unit_price
        ),
        mutable=False,
    )
    model.makeup_water_unit_cost = pyo.Param(
        initialize=0.0 if data.water_cost is None else data.water_cost.unit_cost,
        mutable=False,
    )
    model.source_heat_available = pyo.Param(
        model.STEAM_LEVELS,
        initialize=lambda _, level: level_by_name[level].source_heat_available,
    )
    model.sink_heat_demand = pyo.Param(
        model.STEAM_LEVELS,
        initialize=lambda _, level: level_by_name[level].sink_heat_demand,
    )
    model.generation_enthalpy_delta = pyo.Param(
        model.STEAM_LEVELS,
        initialize=lambda _, level: level_by_name[level].generation_enthalpy_delta,
    )
    model.use_enthalpy_delta = pyo.Param(
        model.STEAM_LEVELS,
        initialize=lambda _, level: level_by_name[level].use_enthalpy_delta,
    )
    model.source_heat_upper_bound = pyo.Param(
        model.STEAM_LEVELS,
        initialize=lambda _, level: _source_heat_upper_bound(
            level_by_name[level],
            data,
        ),
    )
    model.sink_heat_upper_bound = pyo.Param(
        model.STEAM_LEVELS,
        initialize=lambda _, level: _sink_heat_upper_bound(level_by_name[level], data),
    )
    model.steam_enthalpy_for_use = pyo.Param(
        model.STEAM_LEVELS,
        initialize=lambda _, level: _steam_enthalpy_for_use(level_by_name[level]),
    )
    model.feedwater_enthalpy = pyo.Param(
        model.STEAM_LEVELS,
        initialize=lambda _, level: level_by_name[level].feedwater_enthalpy,
    )
    model.flash_saturated_vapor_enthalpy = pyo.Param(
        model.STEAM_LEVELS,
        initialize=lambda _, level: (
            flash_level_by_name[level].saturated_vapor_enthalpy
            if level in flash_level_by_name
            else 0.0
        ),
    )
    model.flash_saturated_liquid_enthalpy = pyo.Param(
        model.STEAM_LEVELS,
        initialize=lambda _, level: (
            flash_level_by_name[level].saturated_liquid_enthalpy
            if level in flash_level_by_name
            else 0.0
        ),
    )
    model.generated_steam_enthalpy = pyo.Param(
        model.STEAM_LEVELS,
        initialize=lambda _, level: _generated_steam_enthalpy(level_by_name[level]),
    )
    model.main_steam_enthalpy = pyo.Param(
        model.STEAM_LEVELS,
        initialize=lambda _, level: _main_steam_enthalpy(level_by_name[level]),
    )
    model.utility_steam_enthalpy = pyo.Param(
        model.STEAM_LEVELS,
        initialize=lambda _, level: _utility_steam_enthalpy(level_by_name[level]),
    )
    model.steam_flow_upper_bound = pyo.Param(
        model.STEAM_LEVELS,
        initialize=lambda _, level: _steam_flow_upper_bound(level_by_name[level], data),
    )
    model.annualized_level_cost = pyo.Param(
        model.STEAM_LEVELS,
        initialize=lambda _, level: level_by_name[level].annualized_level_cost,
    )
    model.operating_cost_per_heat = pyo.Param(
        model.STEAM_LEVELS,
        initialize=lambda _, level: level_by_name[level].operating_cost_per_heat,
    )
    model.vhp_steam_enthalpy = pyo.Param(
        model.VHP_HEADERS,
        initialize=lambda _, vhp: vhp_by_name[vhp].steam_enthalpy,
    )
    model.vhp_feedwater_enthalpy = pyo.Param(
        model.VHP_HEADERS,
        initialize=lambda _, vhp: vhp_by_name[vhp].feedwater_enthalpy,
    )
    model.vhp_steam_flow_upper_bound = pyo.Param(
        model.VHP_HEADERS,
        initialize=lambda _, vhp: vhp_by_name[vhp].steam_flow_upper_bound,
    )
    model.vhp_source_min_capacity = pyo.Param(
        model.VHP_SOURCES,
        initialize=lambda _, source: vhp_source_by_name[source].min_capacity,
    )
    model.vhp_source_max_capacity = pyo.Param(
        model.VHP_SOURCES,
        initialize=lambda _, source: vhp_source_by_name[source].max_capacity,
    )
    model.vhp_source_min_load_fraction = pyo.Param(
        model.VHP_SOURCES,
        initialize=lambda _, source: vhp_source_by_name[source].minimum_load_fraction,
    )
    model.vhp_source_fuel_consumption_per_steam = pyo.Param(
        model.VHP_SOURCES,
        initialize=lambda _, source: (
            vhp_source_by_name[source].fuel_consumption_per_steam
        ),
    )
    model.vhp_source_fuel_consumption_factor = pyo.Param(
        model.VHP_SOURCES,
        initialize=lambda _, source: fuel_consumption_factor_by_key.get(
            ("vhp_source", source),
            1.0,
        ),
    )
    model.vhp_source_must_select = pyo.Param(
        model.VHP_SOURCES,
        initialize=lambda _, source: 1 if vhp_source_by_name[source].must_select else 0,
    )
    model.boiler_size_fuel_coefficient = pyo.Param(
        model.BOILERS,
        initialize=lambda _, boiler: boiler_by_name[boiler].size_fuel_coefficient,
    )
    model.boiler_load_fuel_coefficient = pyo.Param(
        model.BOILERS,
        initialize=lambda _, boiler: boiler_by_name[boiler].load_fuel_coefficient,
    )
    model.boiler_min_capacity = pyo.Param(
        model.BOILERS,
        initialize=lambda _, boiler: boiler_by_name[boiler].min_capacity,
    )
    model.boiler_max_capacity = pyo.Param(
        model.BOILERS,
        initialize=lambda _, boiler: boiler_by_name[boiler].max_capacity,
    )
    model.boiler_min_load_fraction = pyo.Param(
        model.BOILERS,
        initialize=lambda _, boiler: boiler_by_name[boiler].minimum_load_fraction,
    )
    model.boiler_blowdown_fraction = pyo.Param(
        model.BOILERS,
        initialize=lambda _, boiler: boiler_by_name[boiler].blowdown_fraction,
    )
    model.boiler_blowdown_enthalpy_delta = pyo.Param(
        model.BOILERS,
        initialize=lambda _, boiler: boiler_by_name[boiler].blowdown_enthalpy_delta,
    )
    model.boiler_must_select = pyo.Param(
        model.BOILERS,
        initialize=lambda _, boiler: 1 if boiler_by_name[boiler].must_select else 0,
    )
    model.boiler_fuel_consumption_factor = pyo.Param(
        model.BOILERS,
        initialize=lambda _, boiler: fuel_consumption_factor_by_key.get(
            ("boiler", boiler),
            1.0,
        ),
    )
    model.vhp_turbine_power_slope = pyo.Param(
        model.VHP_TURBINES,
        initialize=lambda _, turbine: turbine_by_name[turbine].power_slope,
    )
    model.vhp_turbine_power_intercept = pyo.Param(
        model.VHP_TURBINES,
        initialize=lambda _, turbine: turbine_by_name[turbine].power_intercept,
    )
    model.vhp_turbine_min_capacity = pyo.Param(
        model.VHP_TURBINES,
        initialize=lambda _, turbine: turbine_by_name[turbine].min_capacity,
    )
    model.vhp_turbine_max_capacity = pyo.Param(
        model.VHP_TURBINES,
        initialize=lambda _, turbine: turbine_by_name[turbine].max_capacity,
    )
    model.vhp_turbine_min_load_fraction = pyo.Param(
        model.VHP_TURBINES,
        initialize=lambda _, turbine: turbine_by_name[turbine].minimum_load_fraction,
    )
    model.vhp_turbine_must_select = pyo.Param(
        model.VHP_TURBINES,
        initialize=lambda _, turbine: 1 if turbine_by_name[turbine].must_select else 0,
    )
    model.vhp_letdown_max_flow = pyo.Param(
        model.VHP_LETDOWNS,
        initialize=lambda _, letdown: letdown_by_name[letdown].max_flow,
    )
    model.steam_main_turbine_power_slope = pyo.Param(
        model.STEAM_MAIN_TURBINES,
        initialize=lambda _, turbine: steam_main_turbine_by_name[turbine].power_slope,
    )
    model.steam_main_turbine_power_intercept = pyo.Param(
        model.STEAM_MAIN_TURBINES,
        initialize=lambda _, turbine: (
            steam_main_turbine_by_name[turbine].power_intercept
        ),
    )
    model.steam_main_turbine_min_capacity = pyo.Param(
        model.STEAM_MAIN_TURBINES,
        initialize=lambda _, turbine: steam_main_turbine_by_name[turbine].min_capacity,
    )
    model.steam_main_turbine_max_capacity = pyo.Param(
        model.STEAM_MAIN_TURBINES,
        initialize=lambda _, turbine: steam_main_turbine_by_name[turbine].max_capacity,
    )
    model.steam_main_turbine_min_load_fraction = pyo.Param(
        model.STEAM_MAIN_TURBINES,
        initialize=lambda _, turbine: (
            steam_main_turbine_by_name[turbine].minimum_load_fraction
        ),
    )
    model.steam_main_turbine_must_select = pyo.Param(
        model.STEAM_MAIN_TURBINES,
        initialize=lambda _, turbine: (
            1 if steam_main_turbine_by_name[turbine].must_select else 0
        ),
    )
    model.steam_main_letdown_max_flow = pyo.Param(
        model.STEAM_MAIN_LETDOWNS,
        initialize=lambda _, letdown: steam_main_letdown_by_name[letdown].max_flow,
    )
    model.gas_turbine_fuel_lhv = pyo.Param(
        model.GAS_TURBINES,
        initialize=lambda _, turbine: gas_turbine_by_name[turbine].fuel_lhv,
    )
    model.gas_turbine_power_slope = pyo.Param(
        model.GAS_TURBINES,
        initialize=lambda _, turbine: gas_turbine_by_name[turbine].power_slope,
    )
    model.gas_turbine_power_intercept = pyo.Param(
        model.GAS_TURBINES,
        initialize=lambda _, turbine: gas_turbine_by_name[turbine].power_intercept,
    )
    model.gas_turbine_min_fuel_flow = pyo.Param(
        model.GAS_TURBINES,
        initialize=lambda _, turbine: gas_turbine_by_name[turbine].min_fuel_flow,
    )
    model.gas_turbine_max_fuel_flow = pyo.Param(
        model.GAS_TURBINES,
        initialize=lambda _, turbine: gas_turbine_by_name[turbine].max_fuel_flow,
    )
    model.gas_turbine_min_load_fraction = pyo.Param(
        model.GAS_TURBINES,
        initialize=lambda _, turbine: (
            gas_turbine_by_name[turbine].minimum_load_fraction
        ),
    )
    model.gas_turbine_must_select = pyo.Param(
        model.GAS_TURBINES,
        initialize=lambda _, turbine: (
            1 if gas_turbine_by_name[turbine].must_select else 0
        ),
    )
    model.gas_turbine_fuel_consumption_factor = pyo.Param(
        model.GAS_TURBINES,
        initialize=lambda _, turbine: fuel_consumption_factor_by_key.get(
            ("gas_turbine", turbine),
            1.0,
        ),
    )
    model.hrsg_steam_generation_efficiency = pyo.Param(
        model.HRSGS,
        initialize=lambda _, hrsg: hrsg_by_name[hrsg].steam_generation_efficiency,
    )
    model.hrsg_max_heat_input = pyo.Param(
        model.HRSGS,
        initialize=lambda _, hrsg: hrsg_by_name[hrsg].max_heat_input,
    )
    model.hrsg_supplementary_fuel_lhv = pyo.Param(
        model.HRSGS,
        initialize=lambda _, hrsg: hrsg_by_name[hrsg].supplementary_fuel_lhv,
    )
    model.hrsg_supplementary_firing_efficiency = pyo.Param(
        model.HRSGS,
        initialize=lambda _, hrsg: hrsg_by_name[hrsg].supplementary_firing_efficiency,
    )
    model.hrsg_max_supplementary_fuel_flow = pyo.Param(
        model.HRSGS,
        initialize=lambda _, hrsg: hrsg_by_name[hrsg].max_supplementary_fuel_flow,
    )
    model.hrsg_must_select = pyo.Param(
        model.HRSGS,
        initialize=lambda _, hrsg: 1 if hrsg_by_name[hrsg].must_select else 0,
    )
    model.hrsg_supplementary_fuel_consumption_factor = pyo.Param(
        model.HRSGS,
        initialize=lambda _, hrsg: fuel_consumption_factor_by_key.get(
            ("hrsg_supplementary", hrsg),
            1.0,
        ),
    )
    model.flash_route_max_flow = pyo.Param(
        model.FLASH_ROUTES,
        initialize=lambda _, route: flash_route_by_name[route].max_flow,
    )


def _add_variables(model: pyo.ConcreteModel) -> None:
    model.level_selected = pyo.Var(model.STEAM_LEVELS, domain=pyo.Binary)
    model.source_heat_to_steam = pyo.Var(
        model.STEAM_LEVELS, domain=pyo.NonNegativeReals
    )
    model.source_residual_heat = pyo.Var(
        model.STEAM_LEVELS, domain=pyo.NonNegativeReals
    )
    model.source_steam_generated = pyo.Var(
        model.STEAM_LEVELS,
        domain=pyo.NonNegativeReals,
    )
    model.process_steam_to_sink = pyo.Var(
        model.STEAM_LEVELS,
        domain=pyo.NonNegativeReals,
    )
    model.feedwater_to_desuperheat = pyo.Var(
        model.STEAM_LEVELS,
        domain=pyo.NonNegativeReals,
    )
    model.sink_steam_used = pyo.Var(model.STEAM_LEVELS, domain=pyo.NonNegativeReals)
    model.flash_steam_to_sink = pyo.Var(
        model.STEAM_LEVELS,
        domain=pyo.NonNegativeReals,
        initialize=0.0,
    )
    model.flash_condensate_inlet = pyo.Var(
        model.STEAM_LEVELS,
        domain=pyo.NonNegativeReals,
        initialize=0.0,
    )
    model.flash_steam_recovered = pyo.Var(
        model.FLASH_ROUTES,
        domain=pyo.NonNegativeReals,
    )
    model.flash_liquid_recovered = pyo.Var(
        model.FLASH_ROUTES,
        domain=pyo.NonNegativeReals,
    )
    model.cooling_water_total_load = pyo.Var(
        domain=pyo.NonNegativeReals,
        initialize=0.0,
    )
    model.hot_oil_selected = pyo.Var(model.STEAM_LEVELS, domain=pyo.Binary)
    model.hot_oil_heat_to_sink = pyo.Var(
        model.STEAM_LEVELS,
        domain=pyo.NonNegativeReals,
        initialize=0.0,
    )
    model.hot_oil_furnace_selected = pyo.Var(domain=pyo.Binary)
    model.total_hot_oil_heat_load = pyo.Var(
        domain=pyo.NonNegativeReals,
        initialize=0.0,
    )
    model.hot_oil_fuel_consumption = pyo.Var(
        domain=pyo.NonNegativeReals,
        initialize=0.0,
    )
    model.sink_heat_from_steam = pyo.Var(
        model.STEAM_LEVELS,
        domain=pyo.NonNegativeReals,
    )
    model.sink_residual_heat = pyo.Var(
        model.STEAM_LEVELS,
        domain=pyo.NonNegativeReals,
    )
    model.utility_steam_to_header = pyo.Var(
        model.STEAM_LEVELS,
        domain=pyo.NonNegativeReals,
    )
    model.feedwater_to_header = pyo.Var(
        model.STEAM_LEVELS,
        domain=pyo.NonNegativeReals,
    )
    model.deaerator_steam_from_header = pyo.Var(
        model.STEAM_LEVELS,
        domain=pyo.NonNegativeReals,
        initialize=0.0,
    )
    model.header_steam_export = pyo.Var(
        model.STEAM_LEVELS,
        domain=pyo.NonNegativeReals,
    )
    model.utility_steam_from_vhp = pyo.Var(
        model.VHP_HEADERS,
        model.STEAM_LEVELS,
        domain=pyo.NonNegativeReals,
    )
    model.vhp_selected = pyo.Var(model.VHP_HEADERS, domain=pyo.Binary)
    model.vhp_source_selected = pyo.Var(model.VHP_SOURCES, domain=pyo.Binary)
    model.vhp_source_steam_generation = pyo.Var(
        model.VHP_SOURCES,
        domain=pyo.NonNegativeReals,
    )
    model.vhp_source_fuel_consumption = pyo.Var(
        model.VHP_SOURCES,
        domain=pyo.NonNegativeReals,
    )
    model.boiler_selected = pyo.Var(model.BOILERS, domain=pyo.Binary)
    model.boiler_size = pyo.Var(model.BOILERS, domain=pyo.NonNegativeReals)
    model.boiler_steam_generation = pyo.Var(
        model.BOILERS,
        domain=pyo.NonNegativeReals,
    )
    model.boiler_fuel_consumption = pyo.Var(
        model.BOILERS,
        domain=pyo.NonNegativeReals,
    )
    model.vhp_turbine_selected = pyo.Var(model.VHP_TURBINES, domain=pyo.Binary)
    model.vhp_turbine_steam_flow = pyo.Var(
        model.VHP_TURBINES,
        domain=pyo.NonNegativeReals,
    )
    model.vhp_turbine_power_generation = pyo.Var(
        model.VHP_TURBINES,
        domain=pyo.NonNegativeReals,
    )
    model.vhp_letdown_flow = pyo.Var(
        model.VHP_LETDOWNS,
        domain=pyo.NonNegativeReals,
    )
    model.steam_main_turbine_selected = pyo.Var(
        model.STEAM_MAIN_TURBINES,
        domain=pyo.Binary,
    )
    model.steam_main_turbine_steam_flow = pyo.Var(
        model.STEAM_MAIN_TURBINES,
        domain=pyo.NonNegativeReals,
    )
    model.steam_main_turbine_power_generation = pyo.Var(
        model.STEAM_MAIN_TURBINES,
        domain=pyo.NonNegativeReals,
    )
    model.steam_main_letdown_flow = pyo.Var(
        model.STEAM_MAIN_LETDOWNS,
        domain=pyo.NonNegativeReals,
    )
    model.gas_turbine_selected = pyo.Var(model.GAS_TURBINES, domain=pyo.Binary)
    model.gas_turbine_fuel_flow = pyo.Var(
        model.GAS_TURBINES,
        domain=pyo.NonNegativeReals,
    )
    model.gas_turbine_power_generation = pyo.Var(
        model.GAS_TURBINES,
        domain=pyo.NonNegativeReals,
    )
    model.gas_turbine_exhaust_heat = pyo.Var(
        model.GAS_TURBINES,
        domain=pyo.NonNegativeReals,
    )
    model.hrsg_selected = pyo.Var(model.HRSGS, domain=pyo.Binary)
    model.hrsg_heat_input = pyo.Var(model.HRSGS, domain=pyo.NonNegativeReals)
    model.hrsg_exhaust_heat_input = pyo.Var(
        model.HRSGS,
        domain=pyo.NonNegativeReals,
    )
    model.hrsg_supplementary_firing_selected = pyo.Var(
        model.HRSGS,
        domain=pyo.Binary,
    )
    model.hrsg_supplementary_fuel_flow = pyo.Var(
        model.HRSGS,
        domain=pyo.NonNegativeReals,
    )
    model.hrsg_steam_generation = pyo.Var(model.HRSGS, domain=pyo.NonNegativeReals)
    model.grid_power_import = pyo.Var(domain=pyo.NonNegativeReals)
    model.grid_power_export = pyo.Var(domain=pyo.NonNegativeReals)
    model.onsite_power_generation = pyo.Var(domain=pyo.NonNegativeReals)
    model.deaerator_feedwater_requirement = pyo.Var(
        domain=pyo.NonNegativeReals,
        initialize=0.0,
    )
    model.deaerator_condensate_return = pyo.Var(
        domain=pyo.NonNegativeReals,
        initialize=0.0,
    )
    model.deaerator_makeup_water = pyo.Var(
        domain=pyo.NonNegativeReals,
        initialize=0.0,
    )


def _add_source_cascade_constraints(
    model: pyo.ConcreteModel,
    data: StyleModelData,
    previous_level: Mapping[str, str | None],
) -> None:
    def source_cascade_balance_rule(m: pyo.ConcreteModel, level: str):
        incoming_heat = m.source_heat_available[level]
        if previous_level[level] is not None:
            incoming_heat += m.source_residual_heat[previous_level[level]]
        return (
            incoming_heat
            - m.source_heat_to_steam[level]
            - m.source_residual_heat[level]
            == 0.0
        )

    def source_steam_generation_rule(m: pyo.ConcreteModel, level: str):
        usable_heat = (1.0 - data.source_heat_loss_fraction) * m.source_heat_to_steam[
            level
        ]
        return usable_heat == (
            m.source_steam_generated[level] * m.generation_enthalpy_delta[level]
        )

    model.source_cascade_balance = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=source_cascade_balance_rule,
    )
    model.source_steam_generation = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=source_steam_generation_rule,
    )


def _add_sink_cascade_constraints(
    model: pyo.ConcreteModel,
    data: StyleModelData,
    previous_level: Mapping[str, str | None],
) -> None:
    def sink_process_steam_mass_balance_rule(m: pyo.ConcreteModel, level: str):
        return (
            m.process_steam_to_sink[level]
            + m.feedwater_to_desuperheat[level]
            + m.flash_steam_to_sink[level]
            == m.sink_steam_used[level]
        )

    def sink_process_steam_energy_balance_rule(m: pyo.ConcreteModel, level: str):
        useful_process_steam_heat = (
            (1.0 - data.sink_heat_loss_fraction)
            * m.process_steam_to_sink[level]
            * m.steam_enthalpy_for_use[level]
        )
        desuperheating_heat = (
            m.feedwater_to_desuperheat[level] * m.feedwater_enthalpy[level]
        )
        flash_steam_heat = (
            m.flash_steam_to_sink[level] * m.flash_saturated_vapor_enthalpy[level]
        )
        return (
            useful_process_steam_heat + desuperheating_heat + flash_steam_heat
            == m.sink_steam_used[level] * m.use_enthalpy_delta[level]
        )

    def sink_steam_use_rule(m: pyo.ConcreteModel, level: str):
        return (
            m.sink_heat_from_steam[level]
            == m.sink_steam_used[level] * m.use_enthalpy_delta[level]
        )

    def sink_cascade_balance_rule(m: pyo.ConcreteModel, level: str):
        incoming_heat = m.sink_heat_from_steam[level] + m.hot_oil_heat_to_sink[level]
        if previous_level[level] is not None:
            incoming_heat += m.sink_residual_heat[previous_level[level]]
        return incoming_heat == m.sink_heat_demand[level] + m.sink_residual_heat[level]

    model.sink_process_steam_mass_balance = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=sink_process_steam_mass_balance_rule,
    )
    model.sink_process_steam_energy_balance = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=sink_process_steam_energy_balance_rule,
    )
    model.sink_steam_use = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=sink_steam_use_rule,
    )
    model.sink_cascade_balance = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=sink_cascade_balance_rule,
    )


def _add_cooling_water_constraints(
    model: pyo.ConcreteModel,
    data: StyleModelData,
    bottom_levels: tuple[str, ...],
) -> None:
    def cooling_water_total_load_equation_rule(m: pyo.ConcreteModel):
        return m.cooling_water_total_load == (
            m.cooling_water_process_load
            + m.cooling_water_utility_load
            + sum(m.source_residual_heat[level] for level in bottom_levels)
        )

    model.cooling_water_total_load_equation = pyo.Constraint(
        rule=cooling_water_total_load_equation_rule,
    )
    if data.cooling_water is None:
        model.cooling_water_operating_cost = pyo.Expression(expr=0.0)
    else:
        model.cooling_water_operating_cost = pyo.Expression(
            expr=(
                model.cooling_water_total_load
                * model.cooling_water_unit_cost
                * model.operating_hours
                * model.cost_scale
            ),
        )


def _add_hot_oil_constraints(
    model: pyo.ConcreteModel,
    data: StyleModelData,
    previous_level: Mapping[str, str | None],
) -> None:
    hot_oil_capable_levels = _hot_oil_capable_levels(data)

    if data.hot_oil is None:

        def hot_oil_selected_disabled_rule(m: pyo.ConcreteModel, level: str):
            return m.hot_oil_selected[level] == 0.0

        def hot_oil_heat_disabled_rule(m: pyo.ConcreteModel, level: str):
            return m.hot_oil_heat_to_sink[level] == 0.0

        model.hot_oil_selected_disabled = pyo.Constraint(
            model.STEAM_LEVELS,
            rule=hot_oil_selected_disabled_rule,
        )
        model.hot_oil_heat_disabled = pyo.Constraint(
            model.STEAM_LEVELS,
            rule=hot_oil_heat_disabled_rule,
        )
        model.total_hot_oil_heat_load_disabled = pyo.Constraint(
            expr=model.total_hot_oil_heat_load == 0.0,
        )
        model.hot_oil_furnace_disabled = pyo.Constraint(
            expr=model.hot_oil_furnace_selected == 0.0,
        )
        model.hot_oil_fuel_consumption_disabled = pyo.Constraint(
            expr=model.hot_oil_fuel_consumption == 0.0,
        )
        model.hot_oil_operating_cost = pyo.Expression(expr=0.0)
        return

    def hot_oil_heat_to_sink_equation_rule(m: pyo.ConcreteModel, level: str):
        if level not in hot_oil_capable_levels:
            return m.hot_oil_heat_to_sink[level] == 0.0
        return (
            m.hot_oil_heat_to_sink[level]
            == m.sink_heat_demand[level] * m.hot_oil_selected[level]
        )

    def total_hot_oil_heat_load_equation_rule(m: pyo.ConcreteModel):
        return m.total_hot_oil_heat_load == (
            m.hot_oil_high_temperature_heat_demand
            + sum(m.hot_oil_heat_to_sink[level] for level in m.STEAM_LEVELS)
        )

    def hot_oil_fuel_consumption_equation_rule(m: pyo.ConcreteModel):
        return (
            m.hot_oil_fuel_consumption * m.hot_oil_thermal_efficiency
            == m.total_hot_oil_heat_load
        )

    def hot_oil_furnace_heat_load_upper_bound_rule(m: pyo.ConcreteModel):
        return m.total_hot_oil_heat_load <= (
            _hot_oil_heat_load_upper_bound(data) * m.hot_oil_furnace_selected
        )

    def hot_oil_temperature_order_rule(m: pyo.ConcreteModel, level: str):
        previous = previous_level[level]
        if previous is None:
            return pyo.Constraint.Skip
        return m.hot_oil_selected[level] <= m.hot_oil_selected[previous]

    def hot_oil_excludes_steam_level_rule(m: pyo.ConcreteModel, level: str):
        return m.hot_oil_selected[level] + m.level_selected[level] <= 1

    def hot_oil_requires_capable_level_rule(m: pyo.ConcreteModel, level: str):
        if level in hot_oil_capable_levels:
            return pyo.Constraint.Skip
        return m.hot_oil_selected[level] == 0.0

    model.hot_oil_heat_to_sink_equation = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=hot_oil_heat_to_sink_equation_rule,
    )
    model.total_hot_oil_heat_load_equation = pyo.Constraint(
        rule=total_hot_oil_heat_load_equation_rule,
    )
    model.hot_oil_fuel_consumption_equation = pyo.Constraint(
        rule=hot_oil_fuel_consumption_equation_rule,
    )
    model.hot_oil_furnace_heat_load_upper_bound = pyo.Constraint(
        rule=hot_oil_furnace_heat_load_upper_bound_rule,
    )
    model.hot_oil_temperature_order = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=hot_oil_temperature_order_rule,
    )
    model.hot_oil_excludes_steam_level = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=hot_oil_excludes_steam_level_rule,
    )
    model.hot_oil_requires_capable_level = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=hot_oil_requires_capable_level_rule,
    )
    model.hot_oil_operating_cost = pyo.Expression(
        expr=(
            model.hot_oil_fuel_consumption
            * model.hot_oil_fuel_unit_cost
            * model.operating_hours
            * model.cost_scale
        ),
    )


def _add_flash_steam_recovery_constraints(
    model: pyo.ConcreteModel,
    data: StyleModelData,
) -> None:
    if data.flash_steam_recovery is None:

        def flash_steam_to_sink_disabled_rule(m: pyo.ConcreteModel, level: str):
            return m.flash_steam_to_sink[level] == 0.0

        def flash_condensate_inlet_disabled_rule(m: pyo.ConcreteModel, level: str):
            return m.flash_condensate_inlet[level] == 0.0

        model.flash_steam_to_sink_disabled = pyo.Constraint(
            model.STEAM_LEVELS,
            rule=flash_steam_to_sink_disabled_rule,
        )
        model.flash_condensate_inlet_disabled = pyo.Constraint(
            model.STEAM_LEVELS,
            rule=flash_condensate_inlet_disabled_rule,
        )
        return

    route_source = {
        route.name: route.source_level for route in data.flash_steam_recovery.routes
    }
    route_target = {
        route.name: route.target_level for route in data.flash_steam_recovery.routes
    }
    routes_by_source = _flash_routes_by_source(data)
    routes_by_target = _flash_routes_by_target(data)

    def flash_steam_to_sink_balance_rule(m: pyo.ConcreteModel, level: str):
        incoming_routes = routes_by_target[level]
        return m.flash_steam_to_sink[level] == sum(
            m.flash_steam_recovered[route] for route in incoming_routes
        )

    def flash_condensate_inlet_balance_rule(m: pyo.ConcreteModel, level: str):
        outgoing_routes = routes_by_source[level]
        if not outgoing_routes:
            return m.flash_condensate_inlet[level] == 0.0
        incoming_liquid = sum(
            m.flash_liquid_recovered[route] for route in routes_by_target[level]
        )
        return m.flash_condensate_inlet[level] == (
            m.flash_condensate_return_fraction * m.sink_steam_used[level]
            + incoming_liquid
        )

    def flash_recovery_route_mass_balance_rule(m: pyo.ConcreteModel, level: str):
        outgoing_routes = routes_by_source[level]
        if not outgoing_routes:
            return pyo.Constraint.Skip
        recovered = sum(
            m.flash_steam_recovered[route] + m.flash_liquid_recovered[route]
            for route in outgoing_routes
        )
        return recovered == m.flash_condensate_inlet[level]

    def flash_recovery_route_energy_balance_rule(m: pyo.ConcreteModel, level: str):
        outgoing_routes = routes_by_source[level]
        if not outgoing_routes:
            return pyo.Constraint.Skip
        recovered_heat = sum(
            m.flash_steam_recovered[route]
            * m.flash_saturated_vapor_enthalpy[route_target[route]]
            + m.flash_liquid_recovered[route]
            * m.flash_saturated_liquid_enthalpy[route_target[route]]
            for route in outgoing_routes
        )
        inlet_heat = (
            m.flash_condensate_inlet[level] * m.flash_saturated_liquid_enthalpy[level]
        )
        return recovered_heat == inlet_heat

    def flash_route_flow_upper_bound_rule(m: pyo.ConcreteModel, route: str):
        return (
            m.flash_steam_recovered[route] + m.flash_liquid_recovered[route]
            <= m.flash_route_max_flow[route]
        )

    def flash_steam_to_sink_requires_selected_header_rule(
        m: pyo.ConcreteModel,
        level: str,
    ):
        return (
            m.flash_steam_to_sink[level]
            <= m.steam_flow_upper_bound[level] * m.level_selected[level]
        )

    def flash_source_requires_selected_header_rule(
        m: pyo.ConcreteModel,
        route: str,
    ):
        return (
            m.flash_steam_recovered[route] + m.flash_liquid_recovered[route]
            <= m.flash_route_max_flow[route] * m.level_selected[route_source[route]]
        )

    model.flash_steam_to_sink_balance = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=flash_steam_to_sink_balance_rule,
    )
    model.flash_condensate_inlet_balance = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=flash_condensate_inlet_balance_rule,
    )
    model.flash_recovery_route_mass_balance = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=flash_recovery_route_mass_balance_rule,
    )
    model.flash_recovery_route_energy_balance = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=flash_recovery_route_energy_balance_rule,
    )
    model.flash_route_flow_upper_bound = pyo.Constraint(
        model.FLASH_ROUTES,
        rule=flash_route_flow_upper_bound_rule,
    )
    model.flash_steam_to_sink_requires_selected_header = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=flash_steam_to_sink_requires_selected_header_rule,
    )
    model.flash_source_requires_selected_header = pyo.Constraint(
        model.FLASH_ROUTES,
        rule=flash_source_requires_selected_header_rule,
    )


def _add_steam_main_balance_constraints(
    model: pyo.ConcreteModel,
    data: StyleModelData,
) -> None:
    turbines_by_source = _steam_main_turbines_by_source(data)
    turbines_by_target = _steam_main_turbines_by_target(data)
    letdowns_by_source = _steam_main_letdowns_by_source(data)
    letdowns_by_target = _steam_main_letdowns_by_target(data)
    turbine_source = {
        turbine.name: turbine.source_level for turbine in data.steam_main_turbines
    }
    letdown_source = {
        letdown.name: letdown.source_level for letdown in data.steam_main_letdowns
    }

    def steam_main_mass_balance_rule(m: pyo.ConcreteModel, level: str):
        incoming_turbines = sum(
            m.steam_main_turbine_steam_flow[turbine]
            for turbine in turbines_by_target[level]
        )
        incoming_letdowns = sum(
            m.steam_main_letdown_flow[letdown] for letdown in letdowns_by_target[level]
        )
        outgoing_turbines = sum(
            m.steam_main_turbine_steam_flow[turbine]
            for turbine in turbines_by_source[level]
        )
        outgoing_letdowns = sum(
            m.steam_main_letdown_flow[letdown] for letdown in letdowns_by_source[level]
        )
        return (
            m.source_steam_generated[level]
            + m.utility_steam_to_header[level]
            + m.feedwater_to_header[level]
            + incoming_turbines
            + incoming_letdowns
            == m.process_steam_to_sink[level]
            + m.header_steam_export[level]
            + m.deaerator_steam_from_header[level]
            + outgoing_turbines
            + outgoing_letdowns
        )

    def steam_main_energy_balance_rule(m: pyo.ConcreteModel, level: str):
        steam_generation_heat = (
            m.source_steam_generated[level] * m.generated_steam_enthalpy[level]
        )
        utility_import_heat = (
            m.utility_steam_to_header[level] * m.utility_steam_enthalpy[level]
        )
        feedwater_heat = m.feedwater_to_header[level] * m.feedwater_enthalpy[level]
        incoming_turbine_heat = sum(
            m.steam_main_turbine_steam_flow[turbine]
            * m.main_steam_enthalpy[turbine_source[turbine]]
            - m.steam_main_turbine_power_generation[turbine]
            for turbine in turbines_by_target[level]
        )
        incoming_letdown_heat = sum(
            m.steam_main_letdown_flow[letdown]
            * m.main_steam_enthalpy[letdown_source[letdown]]
            for letdown in letdowns_by_target[level]
        )
        outgoing_transfer_flow = sum(
            m.steam_main_turbine_steam_flow[turbine]
            for turbine in turbines_by_source[level]
        ) + sum(
            m.steam_main_letdown_flow[letdown] for letdown in letdowns_by_source[level]
        )
        header_output_heat = (
            m.process_steam_to_sink[level]
            + m.header_steam_export[level]
            + m.deaerator_steam_from_header[level]
            + outgoing_transfer_flow
        ) * m.main_steam_enthalpy[level]
        return (
            steam_generation_heat
            + utility_import_heat
            + feedwater_heat
            + incoming_turbine_heat
            + incoming_letdown_heat
            == header_output_heat
        )

    model.steam_main_mass_balance = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=steam_main_mass_balance_rule,
    )
    model.steam_main_energy_balance = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=steam_main_energy_balance_rule,
    )


def _add_vhp_constraints(model: pyo.ConcreteModel, data: StyleModelData) -> None:
    vhp_sources_by_vhp = _vhp_sources_by_vhp(data)
    boilers_by_vhp = _boilers_by_vhp(data)
    hrsgs_by_vhp = _hrsgs_by_vhp(data)

    def vhp_mass_balance_rule(m: pyo.ConcreteModel, vhp: str):
        source_generated = sum(
            m.vhp_source_steam_generation[source] for source in vhp_sources_by_vhp[vhp]
        )
        boiler_generated = sum(
            m.boiler_steam_generation[boiler] for boiler in boilers_by_vhp[vhp]
        )
        hrsg_generated = sum(
            m.hrsg_steam_generation[hrsg] for hrsg in hrsgs_by_vhp[vhp]
        )
        distributed = sum(
            m.utility_steam_from_vhp[vhp, level] for level in m.STEAM_LEVELS
        )
        return source_generated + boiler_generated + hrsg_generated == distributed

    def vhp_energy_balance_rule(m: pyo.ConcreteModel, vhp: str):
        source_generated = sum(
            m.vhp_source_steam_generation[source] * m.vhp_steam_enthalpy[vhp]
            for source in vhp_sources_by_vhp[vhp]
        )
        boiler_generated = sum(
            m.boiler_steam_generation[boiler] * m.vhp_steam_enthalpy[vhp]
            for boiler in boilers_by_vhp[vhp]
        )
        hrsg_generated = sum(
            m.hrsg_steam_generation[hrsg] * m.vhp_steam_enthalpy[vhp]
            for hrsg in hrsgs_by_vhp[vhp]
        )
        distributed = sum(
            m.utility_steam_from_vhp[vhp, level] * m.vhp_steam_enthalpy[vhp]
            for level in m.STEAM_LEVELS
        )
        return source_generated + boiler_generated + hrsg_generated == distributed

    def one_vhp_header_selected_rule(m: pyo.ConcreteModel):
        if len(m.VHP_HEADERS) == 0:
            return pyo.Constraint.Skip
        return sum(m.vhp_selected[vhp] for vhp in m.VHP_HEADERS) == 1

    def utility_steam_from_vhp_aggregation_rule(m: pyo.ConcreteModel, level: str):
        return m.utility_steam_to_header[level] == sum(
            m.utility_steam_from_vhp[vhp, level] for vhp in m.VHP_HEADERS
        )

    def utility_steam_from_vhp_requires_selected_vhp_rule(
        m: pyo.ConcreteModel,
        vhp: str,
        level: str,
    ):
        return (
            m.utility_steam_from_vhp[vhp, level]
            <= m.vhp_steam_flow_upper_bound[vhp] * m.vhp_selected[vhp]
        )

    def utility_steam_from_vhp_requires_selected_level_rule(
        m: pyo.ConcreteModel,
        vhp: str,
        level: str,
    ):
        return (
            m.utility_steam_from_vhp[vhp, level]
            <= m.vhp_steam_flow_upper_bound[vhp] * m.level_selected[level]
        )

    model.vhp_mass_balance = pyo.Constraint(
        model.VHP_HEADERS,
        rule=vhp_mass_balance_rule,
    )
    model.vhp_energy_balance = pyo.Constraint(
        model.VHP_HEADERS,
        rule=vhp_energy_balance_rule,
    )
    model.one_vhp_header_selected = pyo.Constraint(
        rule=one_vhp_header_selected_rule,
    )
    model.utility_steam_from_vhp_aggregation = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=utility_steam_from_vhp_aggregation_rule,
    )
    model.utility_steam_from_vhp_requires_selected_vhp = pyo.Constraint(
        model.VHP_HEADERS,
        model.STEAM_LEVELS,
        rule=utility_steam_from_vhp_requires_selected_vhp_rule,
    )
    model.utility_steam_from_vhp_requires_selected_level = pyo.Constraint(
        model.VHP_HEADERS,
        model.STEAM_LEVELS,
        rule=utility_steam_from_vhp_requires_selected_level_rule,
    )


def _add_vhp_source_constraints(
    model: pyo.ConcreteModel,
    data: StyleModelData,
) -> None:
    source_vhp = {source.name: source.vhp_header for source in data.vhp_sources}

    def vhp_source_fuel_consumption_equation_rule(
        m: pyo.ConcreteModel,
        source: str,
    ):
        return m.vhp_source_fuel_consumption[source] == (
            m.vhp_source_fuel_consumption_per_steam[source]
            * m.vhp_source_steam_generation[source]
        )

    def vhp_source_generation_lower_bound_rule(
        m: pyo.ConcreteModel,
        source: str,
    ):
        return (
            m.vhp_source_steam_generation[source]
            >= m.vhp_source_min_capacity[source] * m.vhp_source_selected[source]
        )

    def vhp_source_generation_upper_bound_rule(
        m: pyo.ConcreteModel,
        source: str,
    ):
        return (
            m.vhp_source_steam_generation[source]
            <= m.vhp_source_max_capacity[source] * m.vhp_source_selected[source]
        )

    def vhp_source_minimum_load_fraction_rule(
        m: pyo.ConcreteModel,
        source: str,
    ):
        return m.vhp_source_steam_generation[source] >= (
            m.vhp_source_min_load_fraction[source]
            * m.vhp_source_max_capacity[source]
            * m.vhp_source_selected[source]
        )

    def vhp_source_requires_selected_vhp_rule(
        m: pyo.ConcreteModel,
        source: str,
    ):
        return m.vhp_source_selected[source] <= m.vhp_selected[source_vhp[source]]

    def vhp_source_must_select_rule(m: pyo.ConcreteModel, source: str):
        return m.vhp_source_selected[source] >= m.vhp_source_must_select[source]

    model.vhp_source_fuel_consumption_equation = pyo.Constraint(
        model.VHP_SOURCES,
        rule=vhp_source_fuel_consumption_equation_rule,
    )
    model.vhp_source_generation_lower_bound = pyo.Constraint(
        model.VHP_SOURCES,
        rule=vhp_source_generation_lower_bound_rule,
    )
    model.vhp_source_generation_upper_bound = pyo.Constraint(
        model.VHP_SOURCES,
        rule=vhp_source_generation_upper_bound_rule,
    )
    model.vhp_source_minimum_load_fraction = pyo.Constraint(
        model.VHP_SOURCES,
        rule=vhp_source_minimum_load_fraction_rule,
    )
    model.vhp_source_requires_selected_vhp = pyo.Constraint(
        model.VHP_SOURCES,
        rule=vhp_source_requires_selected_vhp_rule,
    )
    model.vhp_source_must_select_constraint = pyo.Constraint(
        model.VHP_SOURCES,
        rule=vhp_source_must_select_rule,
    )


def _add_boiler_constraints(model: pyo.ConcreteModel, data: StyleModelData) -> None:
    boiler_vhp = {boiler.name: boiler.vhp_header for boiler in data.boilers}

    def boiler_fuel_consumption_equation_rule(m: pyo.ConcreteModel, boiler: str):
        vhp = boiler_vhp[boiler]
        generation_enthalpy_delta = (
            m.vhp_steam_enthalpy[vhp] - m.vhp_feedwater_enthalpy[vhp]
        )
        fuel_from_size_and_load = generation_enthalpy_delta * (
            m.boiler_size_fuel_coefficient[boiler] * m.boiler_size[boiler]
            + m.boiler_load_fuel_coefficient[boiler] * m.boiler_steam_generation[boiler]
        )
        blowdown_fuel = (
            m.boiler_blowdown_fraction[boiler]
            * m.boiler_steam_generation[boiler]
            * m.boiler_blowdown_enthalpy_delta[boiler]
        )
        return m.boiler_fuel_consumption[boiler] == (
            fuel_from_size_and_load + blowdown_fuel
        )

    def boiler_size_lower_bound_rule(m: pyo.ConcreteModel, boiler: str):
        return (
            m.boiler_size[boiler]
            >= m.boiler_min_capacity[boiler] * m.boiler_selected[boiler]
        )

    def boiler_size_upper_bound_rule(m: pyo.ConcreteModel, boiler: str):
        return (
            m.boiler_size[boiler]
            <= m.boiler_max_capacity[boiler] * m.boiler_selected[boiler]
        )

    def boiler_load_lower_bound_rule(m: pyo.ConcreteModel, boiler: str):
        return (
            m.boiler_steam_generation[boiler]
            >= m.boiler_min_capacity[boiler] * m.boiler_selected[boiler]
        )

    def boiler_load_upper_bound_rule(m: pyo.ConcreteModel, boiler: str):
        return (
            m.boiler_steam_generation[boiler]
            <= m.boiler_max_capacity[boiler] * m.boiler_selected[boiler]
        )

    def boiler_minimum_load_fraction_rule(m: pyo.ConcreteModel, boiler: str):
        return m.boiler_steam_generation[boiler] >= (
            m.boiler_min_load_fraction[boiler] * m.boiler_size[boiler]
        )

    def boiler_must_select_rule(m: pyo.ConcreteModel, boiler: str):
        return m.boiler_selected[boiler] >= m.boiler_must_select[boiler]

    model.boiler_fuel_consumption_equation = pyo.Constraint(
        model.BOILERS,
        rule=boiler_fuel_consumption_equation_rule,
    )
    model.boiler_size_lower_bound = pyo.Constraint(
        model.BOILERS,
        rule=boiler_size_lower_bound_rule,
    )
    model.boiler_size_upper_bound = pyo.Constraint(
        model.BOILERS,
        rule=boiler_size_upper_bound_rule,
    )
    model.boiler_load_lower_bound = pyo.Constraint(
        model.BOILERS,
        rule=boiler_load_lower_bound_rule,
    )
    model.boiler_load_upper_bound = pyo.Constraint(
        model.BOILERS,
        rule=boiler_load_upper_bound_rule,
    )
    model.boiler_minimum_load_fraction = pyo.Constraint(
        model.BOILERS,
        rule=boiler_minimum_load_fraction_rule,
    )
    model.boiler_must_select_constraint = pyo.Constraint(
        model.BOILERS,
        rule=boiler_must_select_rule,
    )


def _add_vhp_connection_constraints(
    model: pyo.ConcreteModel,
    data: StyleModelData,
) -> None:
    turbines_by_pair = _vhp_turbines_by_pair(data)
    letdowns_by_pair = _vhp_letdowns_by_pair(data)
    turbine_vhp = {turbine.name: turbine.vhp_header for turbine in data.vhp_turbines}
    turbine_level = {turbine.name: turbine.steam_level for turbine in data.vhp_turbines}
    letdown_vhp = {letdown.name: letdown.vhp_header for letdown in data.vhp_letdowns}
    letdown_level = {letdown.name: letdown.steam_level for letdown in data.vhp_letdowns}

    def vhp_turbine_power_equation_rule(m: pyo.ConcreteModel, turbine: str):
        return m.vhp_turbine_power_generation[turbine] == (
            m.vhp_turbine_power_slope[turbine] * m.vhp_turbine_steam_flow[turbine]
            - m.vhp_turbine_power_intercept[turbine] * m.vhp_turbine_selected[turbine]
        )

    def vhp_turbine_flow_lower_bound_rule(m: pyo.ConcreteModel, turbine: str):
        return m.vhp_turbine_steam_flow[turbine] >= (
            m.vhp_turbine_min_capacity[turbine] * m.vhp_turbine_selected[turbine]
        )

    def vhp_turbine_flow_upper_bound_rule(m: pyo.ConcreteModel, turbine: str):
        return m.vhp_turbine_steam_flow[turbine] <= (
            m.vhp_turbine_max_capacity[turbine] * m.vhp_turbine_selected[turbine]
        )

    def vhp_turbine_minimum_load_fraction_rule(
        m: pyo.ConcreteModel,
        turbine: str,
    ):
        return m.vhp_turbine_steam_flow[turbine] >= (
            m.vhp_turbine_min_load_fraction[turbine]
            * m.vhp_turbine_max_capacity[turbine]
            * m.vhp_turbine_selected[turbine]
        )

    def vhp_turbine_requires_selected_vhp_rule(
        m: pyo.ConcreteModel,
        turbine: str,
    ):
        return m.vhp_turbine_selected[turbine] <= m.vhp_selected[turbine_vhp[turbine]]

    def vhp_turbine_requires_selected_level_rule(
        m: pyo.ConcreteModel,
        turbine: str,
    ):
        return (
            m.vhp_turbine_selected[turbine] <= m.level_selected[turbine_level[turbine]]
        )

    def vhp_turbine_must_select_rule(m: pyo.ConcreteModel, turbine: str):
        return m.vhp_turbine_selected[turbine] >= m.vhp_turbine_must_select[turbine]

    def vhp_letdown_requires_selected_vhp_rule(m: pyo.ConcreteModel, letdown: str):
        return (
            m.vhp_letdown_flow[letdown]
            <= m.vhp_letdown_max_flow[letdown] * m.vhp_selected[letdown_vhp[letdown]]
        )

    def vhp_letdown_requires_selected_level_rule(
        m: pyo.ConcreteModel,
        letdown: str,
    ):
        return (
            m.vhp_letdown_flow[letdown]
            <= m.vhp_letdown_max_flow[letdown]
            * m.level_selected[letdown_level[letdown]]
        )

    def vhp_connection_flow_aggregation_rule(
        m: pyo.ConcreteModel,
        vhp: str,
        level: str,
    ):
        turbine_names = turbines_by_pair[(vhp, level)]
        letdown_names = letdowns_by_pair[(vhp, level)]
        turbine_flow = sum(m.vhp_turbine_steam_flow[name] for name in turbine_names)
        letdown_flow = sum(m.vhp_letdown_flow[name] for name in letdown_names)
        return m.utility_steam_from_vhp[vhp, level] == turbine_flow + letdown_flow

    model.vhp_turbine_power_equation = pyo.Constraint(
        model.VHP_TURBINES,
        rule=vhp_turbine_power_equation_rule,
    )
    model.vhp_turbine_flow_lower_bound = pyo.Constraint(
        model.VHP_TURBINES,
        rule=vhp_turbine_flow_lower_bound_rule,
    )
    model.vhp_turbine_flow_upper_bound = pyo.Constraint(
        model.VHP_TURBINES,
        rule=vhp_turbine_flow_upper_bound_rule,
    )
    model.vhp_turbine_minimum_load_fraction = pyo.Constraint(
        model.VHP_TURBINES,
        rule=vhp_turbine_minimum_load_fraction_rule,
    )
    model.vhp_turbine_requires_selected_vhp = pyo.Constraint(
        model.VHP_TURBINES,
        rule=vhp_turbine_requires_selected_vhp_rule,
    )
    model.vhp_turbine_requires_selected_level = pyo.Constraint(
        model.VHP_TURBINES,
        rule=vhp_turbine_requires_selected_level_rule,
    )
    model.vhp_turbine_must_select_constraint = pyo.Constraint(
        model.VHP_TURBINES,
        rule=vhp_turbine_must_select_rule,
    )
    model.vhp_letdown_requires_selected_vhp = pyo.Constraint(
        model.VHP_LETDOWNS,
        rule=vhp_letdown_requires_selected_vhp_rule,
    )
    model.vhp_letdown_requires_selected_level = pyo.Constraint(
        model.VHP_LETDOWNS,
        rule=vhp_letdown_requires_selected_level_rule,
    )
    model.vhp_connection_flow_aggregation = pyo.Constraint(
        model.VHP_HEADERS,
        model.STEAM_LEVELS,
        rule=vhp_connection_flow_aggregation_rule,
    )


def _add_steam_main_connection_constraints(
    model: pyo.ConcreteModel,
    data: StyleModelData,
) -> None:
    turbine_source = {
        turbine.name: turbine.source_level for turbine in data.steam_main_turbines
    }
    turbine_target = {
        turbine.name: turbine.target_level for turbine in data.steam_main_turbines
    }
    letdown_source = {
        letdown.name: letdown.source_level for letdown in data.steam_main_letdowns
    }
    letdown_target = {
        letdown.name: letdown.target_level for letdown in data.steam_main_letdowns
    }

    def steam_main_turbine_power_equation_rule(
        m: pyo.ConcreteModel,
        turbine: str,
    ):
        return m.steam_main_turbine_power_generation[turbine] == (
            m.steam_main_turbine_power_slope[turbine]
            * m.steam_main_turbine_steam_flow[turbine]
            - m.steam_main_turbine_power_intercept[turbine]
            * m.steam_main_turbine_selected[turbine]
        )

    def steam_main_turbine_flow_lower_bound_rule(
        m: pyo.ConcreteModel,
        turbine: str,
    ):
        return m.steam_main_turbine_steam_flow[turbine] >= (
            m.steam_main_turbine_min_capacity[turbine]
            * m.steam_main_turbine_selected[turbine]
        )

    def steam_main_turbine_flow_upper_bound_rule(
        m: pyo.ConcreteModel,
        turbine: str,
    ):
        return m.steam_main_turbine_steam_flow[turbine] <= (
            m.steam_main_turbine_max_capacity[turbine]
            * m.steam_main_turbine_selected[turbine]
        )

    def steam_main_turbine_minimum_load_fraction_rule(
        m: pyo.ConcreteModel,
        turbine: str,
    ):
        return m.steam_main_turbine_steam_flow[turbine] >= (
            m.steam_main_turbine_min_load_fraction[turbine]
            * m.steam_main_turbine_max_capacity[turbine]
            * m.steam_main_turbine_selected[turbine]
        )

    def steam_main_turbine_requires_source_level_rule(
        m: pyo.ConcreteModel,
        turbine: str,
    ):
        return (
            m.steam_main_turbine_selected[turbine]
            <= m.level_selected[turbine_source[turbine]]
        )

    def steam_main_turbine_requires_target_level_rule(
        m: pyo.ConcreteModel,
        turbine: str,
    ):
        return (
            m.steam_main_turbine_selected[turbine]
            <= m.level_selected[turbine_target[turbine]]
        )

    def steam_main_turbine_must_select_rule(
        m: pyo.ConcreteModel,
        turbine: str,
    ):
        return (
            m.steam_main_turbine_selected[turbine]
            >= m.steam_main_turbine_must_select[turbine]
        )

    def steam_main_letdown_requires_source_level_rule(
        m: pyo.ConcreteModel,
        letdown: str,
    ):
        return (
            m.steam_main_letdown_flow[letdown]
            <= m.steam_main_letdown_max_flow[letdown]
            * m.level_selected[letdown_source[letdown]]
        )

    def steam_main_letdown_requires_target_level_rule(
        m: pyo.ConcreteModel,
        letdown: str,
    ):
        return (
            m.steam_main_letdown_flow[letdown]
            <= m.steam_main_letdown_max_flow[letdown]
            * m.level_selected[letdown_target[letdown]]
        )

    model.steam_main_turbine_power_equation = pyo.Constraint(
        model.STEAM_MAIN_TURBINES,
        rule=steam_main_turbine_power_equation_rule,
    )
    model.steam_main_turbine_flow_lower_bound = pyo.Constraint(
        model.STEAM_MAIN_TURBINES,
        rule=steam_main_turbine_flow_lower_bound_rule,
    )
    model.steam_main_turbine_flow_upper_bound = pyo.Constraint(
        model.STEAM_MAIN_TURBINES,
        rule=steam_main_turbine_flow_upper_bound_rule,
    )
    model.steam_main_turbine_minimum_load_fraction = pyo.Constraint(
        model.STEAM_MAIN_TURBINES,
        rule=steam_main_turbine_minimum_load_fraction_rule,
    )
    model.steam_main_turbine_requires_source_level = pyo.Constraint(
        model.STEAM_MAIN_TURBINES,
        rule=steam_main_turbine_requires_source_level_rule,
    )
    model.steam_main_turbine_requires_target_level = pyo.Constraint(
        model.STEAM_MAIN_TURBINES,
        rule=steam_main_turbine_requires_target_level_rule,
    )
    model.steam_main_turbine_must_select_constraint = pyo.Constraint(
        model.STEAM_MAIN_TURBINES,
        rule=steam_main_turbine_must_select_rule,
    )
    model.steam_main_letdown_requires_source_level = pyo.Constraint(
        model.STEAM_MAIN_LETDOWNS,
        rule=steam_main_letdown_requires_source_level_rule,
    )
    model.steam_main_letdown_requires_target_level = pyo.Constraint(
        model.STEAM_MAIN_LETDOWNS,
        rule=steam_main_letdown_requires_target_level_rule,
    )


def _add_gas_turbine_constraints(model: pyo.ConcreteModel) -> None:
    def gas_turbine_power_equation_rule(m: pyo.ConcreteModel, turbine: str):
        return m.gas_turbine_power_generation[turbine] == (
            m.gas_turbine_power_slope[turbine] * m.gas_turbine_fuel_flow[turbine]
            - m.gas_turbine_power_intercept[turbine] * m.gas_turbine_selected[turbine]
        )

    def gas_turbine_exhaust_heat_equation_rule(
        m: pyo.ConcreteModel,
        turbine: str,
    ):
        return m.gas_turbine_exhaust_heat[turbine] == (
            m.gas_turbine_fuel_lhv[turbine] * m.gas_turbine_fuel_flow[turbine]
            - m.gas_turbine_power_generation[turbine]
        )

    def gas_turbine_fuel_lower_bound_rule(m: pyo.ConcreteModel, turbine: str):
        return m.gas_turbine_fuel_flow[turbine] >= (
            m.gas_turbine_min_fuel_flow[turbine] * m.gas_turbine_selected[turbine]
        )

    def gas_turbine_fuel_upper_bound_rule(m: pyo.ConcreteModel, turbine: str):
        return m.gas_turbine_fuel_flow[turbine] <= (
            m.gas_turbine_max_fuel_flow[turbine] * m.gas_turbine_selected[turbine]
        )

    def gas_turbine_minimum_load_fraction_rule(
        m: pyo.ConcreteModel,
        turbine: str,
    ):
        return m.gas_turbine_fuel_flow[turbine] >= (
            m.gas_turbine_min_load_fraction[turbine]
            * m.gas_turbine_max_fuel_flow[turbine]
            * m.gas_turbine_selected[turbine]
        )

    def gas_turbine_must_select_rule(m: pyo.ConcreteModel, turbine: str):
        return m.gas_turbine_selected[turbine] >= m.gas_turbine_must_select[turbine]

    model.gas_turbine_power_equation = pyo.Constraint(
        model.GAS_TURBINES,
        rule=gas_turbine_power_equation_rule,
    )
    model.gas_turbine_exhaust_heat_equation = pyo.Constraint(
        model.GAS_TURBINES,
        rule=gas_turbine_exhaust_heat_equation_rule,
    )
    model.gas_turbine_fuel_lower_bound = pyo.Constraint(
        model.GAS_TURBINES,
        rule=gas_turbine_fuel_lower_bound_rule,
    )
    model.gas_turbine_fuel_upper_bound = pyo.Constraint(
        model.GAS_TURBINES,
        rule=gas_turbine_fuel_upper_bound_rule,
    )
    model.gas_turbine_minimum_load_fraction = pyo.Constraint(
        model.GAS_TURBINES,
        rule=gas_turbine_minimum_load_fraction_rule,
    )
    model.gas_turbine_must_select_constraint = pyo.Constraint(
        model.GAS_TURBINES,
        rule=gas_turbine_must_select_rule,
    )


def _add_hrsg_constraints(
    model: pyo.ConcreteModel,
    data: StyleModelData,
) -> None:
    hrsg_gas_turbine = {hrsg.name: hrsg.gas_turbine for hrsg in data.hrsgs}
    hrsg_vhp = {hrsg.name: hrsg.vhp_header for hrsg in data.hrsgs}

    def hrsg_total_heat_input_equation_rule(m: pyo.ConcreteModel, hrsg: str):
        supplementary_heat = 0.0
        if pyo.value(m.hrsg_max_supplementary_fuel_flow[hrsg]) > 0.0:
            supplementary_heat = (
                m.hrsg_supplementary_firing_efficiency[hrsg]
                * m.hrsg_supplementary_fuel_lhv[hrsg]
                * m.hrsg_supplementary_fuel_flow[hrsg]
            )
        return m.hrsg_heat_input[hrsg] == (
            m.hrsg_exhaust_heat_input[hrsg] + supplementary_heat
        )

    def hrsg_steam_generation_equation_rule(m: pyo.ConcreteModel, hrsg: str):
        vhp = hrsg_vhp[hrsg]
        generation_enthalpy_delta = (
            m.vhp_steam_enthalpy[vhp] - m.vhp_feedwater_enthalpy[vhp]
        )
        return (
            m.hrsg_steam_generation_efficiency[hrsg] * m.hrsg_heat_input[hrsg]
            == m.hrsg_steam_generation[hrsg] * generation_enthalpy_delta
        )

    def hrsg_heat_from_exhaust_rule(m: pyo.ConcreteModel, hrsg: str):
        turbine = hrsg_gas_turbine[hrsg]
        return m.hrsg_exhaust_heat_input[hrsg] <= m.gas_turbine_exhaust_heat[turbine]

    def hrsg_heat_input_upper_bound_rule(m: pyo.ConcreteModel, hrsg: str):
        return (
            m.hrsg_heat_input[hrsg]
            <= m.hrsg_max_heat_input[hrsg] * m.hrsg_selected[hrsg]
        )

    def hrsg_requires_selected_vhp_rule(m: pyo.ConcreteModel, hrsg: str):
        return m.hrsg_selected[hrsg] <= m.vhp_selected[hrsg_vhp[hrsg]]

    def hrsg_requires_selected_gas_turbine_rule(m: pyo.ConcreteModel, hrsg: str):
        turbine = hrsg_gas_turbine[hrsg]
        return m.hrsg_selected[hrsg] <= m.gas_turbine_selected[turbine]

    def hrsg_must_select_rule(m: pyo.ConcreteModel, hrsg: str):
        return m.hrsg_selected[hrsg] >= m.hrsg_must_select[hrsg]

    def hrsg_supplementary_fuel_upper_bound_rule(
        m: pyo.ConcreteModel,
        hrsg: str,
    ):
        return m.hrsg_supplementary_fuel_flow[hrsg] <= (
            m.hrsg_max_supplementary_fuel_flow[hrsg]
            * m.hrsg_supplementary_firing_selected[hrsg]
        )

    def hrsg_supplementary_firing_requires_gas_turbine_rule(
        m: pyo.ConcreteModel,
        hrsg: str,
    ):
        turbine = hrsg_gas_turbine[hrsg]
        return (
            m.hrsg_supplementary_firing_selected[hrsg]
            <= m.gas_turbine_selected[turbine]
        )

    def hrsg_supplementary_firing_requires_hrsg_rule(
        m: pyo.ConcreteModel,
        hrsg: str,
    ):
        return m.hrsg_supplementary_firing_selected[hrsg] <= m.hrsg_selected[hrsg]

    model.hrsg_total_heat_input_equation = pyo.Constraint(
        model.HRSGS,
        rule=hrsg_total_heat_input_equation_rule,
    )
    model.hrsg_steam_generation_equation = pyo.Constraint(
        model.HRSGS,
        rule=hrsg_steam_generation_equation_rule,
    )
    model.hrsg_heat_from_exhaust = pyo.Constraint(
        model.HRSGS,
        rule=hrsg_heat_from_exhaust_rule,
    )
    model.hrsg_heat_input_upper_bound = pyo.Constraint(
        model.HRSGS,
        rule=hrsg_heat_input_upper_bound_rule,
    )
    model.hrsg_requires_selected_vhp = pyo.Constraint(
        model.HRSGS,
        rule=hrsg_requires_selected_vhp_rule,
    )
    model.hrsg_requires_selected_gas_turbine = pyo.Constraint(
        model.HRSGS,
        rule=hrsg_requires_selected_gas_turbine_rule,
    )
    model.hrsg_must_select_constraint = pyo.Constraint(
        model.HRSGS,
        rule=hrsg_must_select_rule,
    )
    model.hrsg_supplementary_fuel_upper_bound = pyo.Constraint(
        model.HRSGS,
        rule=hrsg_supplementary_fuel_upper_bound_rule,
    )
    model.hrsg_supplementary_firing_requires_gas_turbine = pyo.Constraint(
        model.HRSGS,
        rule=hrsg_supplementary_firing_requires_gas_turbine_rule,
    )
    model.hrsg_supplementary_firing_requires_hrsg = pyo.Constraint(
        model.HRSGS,
        rule=hrsg_supplementary_firing_requires_hrsg_rule,
    )


def _add_deaerator_constraints(
    model: pyo.ConcreteModel,
    data: StyleModelData,
) -> None:
    if data.deaerator is None:

        def deaerator_steam_disabled_rule(m: pyo.ConcreteModel, level: str):
            return m.deaerator_steam_from_header[level] == 0.0

        model.deaerator_steam_disabled = pyo.Constraint(
            model.STEAM_LEVELS,
            rule=deaerator_steam_disabled_rule,
        )
        model.deaerator_feedwater_requirement_disabled = pyo.Constraint(
            expr=model.deaerator_feedwater_requirement == 0.0,
        )
        model.deaerator_condensate_return_disabled = pyo.Constraint(
            expr=model.deaerator_condensate_return == 0.0,
        )
        model.deaerator_makeup_water_disabled = pyo.Constraint(
            expr=model.deaerator_makeup_water == 0.0,
        )
        return

    def deaerator_feedwater_requirement_equation_rule(m: pyo.ConcreteModel):
        steam_level_requirement = sum(
            m.source_steam_generated[level]
            + m.feedwater_to_desuperheat[level]
            + m.feedwater_to_header[level]
            for level in m.STEAM_LEVELS
        )
        boiler_requirement = sum(
            m.boiler_steam_generation[boiler] for boiler in m.BOILERS
        )
        hrsg_requirement = sum(m.hrsg_steam_generation[hrsg] for hrsg in m.HRSGS)
        vhp_source_requirement = sum(
            m.vhp_source_steam_generation[source] for source in m.VHP_SOURCES
        )
        return m.deaerator_feedwater_requirement == (
            steam_level_requirement
            + boiler_requirement
            + hrsg_requirement
            + vhp_source_requirement
        )

    def deaerator_condensate_return_equation_rule(m: pyo.ConcreteModel):
        return m.deaerator_condensate_return == (
            m.deaerator_condensate_return_fraction * m.deaerator_feedwater_requirement
        )

    def deaerator_makeup_water_equation_rule(m: pyo.ConcreteModel):
        deaerator_steam = sum(
            m.deaerator_steam_from_header[level] for level in m.STEAM_LEVELS
        )
        return m.deaerator_makeup_water == (
            m.deaerator_feedwater_requirement
            - m.deaerator_condensate_return
            - (1.0 - m.deaerator_vent_fraction) * deaerator_steam
        )

    def deaerator_energy_balance_rule(m: pyo.ConcreteModel):
        deaerator_steam = sum(
            m.deaerator_steam_from_header[level] for level in m.STEAM_LEVELS
        )
        steam_heat = sum(
            m.deaerator_steam_from_header[level] * m.main_steam_enthalpy[level]
            for level in m.STEAM_LEVELS
        )
        feedwater_heat = (
            m.deaerator_feedwater_requirement * m.deaerator_feedwater_enthalpy
        )
        vent_heat = (
            m.deaerator_vent_fraction * deaerator_steam * m.deaerator_vent_enthalpy
        )
        condensate_heat = (
            m.deaerator_condensate_return * m.deaerator_condensate_enthalpy
        )
        makeup_heat = m.deaerator_makeup_water * m.deaerator_makeup_water_enthalpy
        return feedwater_heat + vent_heat == (
            condensate_heat + makeup_heat + steam_heat
        )

    def deaerator_steam_requires_selected_header_rule(
        m: pyo.ConcreteModel,
        level: str,
    ):
        return (
            m.deaerator_steam_from_header[level]
            <= m.steam_flow_upper_bound[level] * m.level_selected[level]
        )

    model.deaerator_feedwater_requirement_equation = pyo.Constraint(
        rule=deaerator_feedwater_requirement_equation_rule,
    )
    model.deaerator_condensate_return_equation = pyo.Constraint(
        rule=deaerator_condensate_return_equation_rule,
    )
    model.deaerator_makeup_water_equation = pyo.Constraint(
        rule=deaerator_makeup_water_equation_rule,
    )
    model.deaerator_energy_balance = pyo.Constraint(
        rule=deaerator_energy_balance_rule,
    )
    model.deaerator_steam_requires_selected_header = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=deaerator_steam_requires_selected_header_rule,
    )


def _add_power_generation_constraints(
    model: pyo.ConcreteModel,
    data: StyleModelData,
) -> None:
    def onsite_power_generation_equation_rule(m: pyo.ConcreteModel):
        if (
            len(data.vhp_turbines) == 0
            and len(data.steam_main_turbines) == 0
            and len(data.gas_turbines) == 0
        ):
            return pyo.Constraint.Skip
        turbine_power = sum(
            m.vhp_turbine_power_generation[turbine] for turbine in m.VHP_TURBINES
        ) + sum(
            m.steam_main_turbine_power_generation[turbine]
            for turbine in m.STEAM_MAIN_TURBINES
        )
        gas_turbine_power = sum(
            m.gas_turbine_power_generation[turbine] for turbine in m.GAS_TURBINES
        )
        return m.onsite_power_generation == turbine_power + gas_turbine_power

    model.onsite_power_generation_equation = pyo.Constraint(
        rule=onsite_power_generation_equation_rule,
    )


def _add_electricity_constraints(
    model: pyo.ConcreteModel,
    data: StyleModelData,
) -> None:
    def electricity_balance_rule(m: pyo.ConcreteModel):
        return (
            data.transmission_efficiency
            * (m.grid_power_import + m.onsite_power_generation - m.grid_power_export)
            - m.power_demand
            == 0.0
        )

    def grid_import_limit_rule(m: pyo.ConcreteModel):
        if data.grid_import_limit is None:
            return pyo.Constraint.Skip
        return m.grid_power_import <= data.grid_import_limit

    def grid_export_limit_rule(m: pyo.ConcreteModel):
        if data.grid_export_limit is None:
            return pyo.Constraint.Skip
        return m.grid_power_export <= data.grid_export_limit

    model.electricity_balance = pyo.Constraint(rule=electricity_balance_rule)
    model.grid_import_limit_constraint = pyo.Constraint(rule=grid_import_limit_rule)
    model.grid_export_limit_constraint = pyo.Constraint(rule=grid_export_limit_rule)


def _add_level_selection_constraints(
    model: pyo.ConcreteModel,
    data: StyleModelData,
) -> None:
    levels_by_main = {
        steam_main: tuple(
            level.name for level in data.steam_levels if level.steam_main == steam_main
        )
        for steam_main in data.steam_mains
    }

    def source_heat_requires_selected_rule(m: pyo.ConcreteModel, level: str):
        return (
            m.source_heat_to_steam[level]
            <= m.source_heat_upper_bound[level] * m.level_selected[level]
        )

    def source_residual_requires_unselected_rule(m: pyo.ConcreteModel, level: str):
        return m.source_residual_heat[level] <= m.source_heat_upper_bound[level]

    def sink_heat_requires_selected_rule(m: pyo.ConcreteModel, level: str):
        return (
            m.sink_heat_from_steam[level]
            <= m.sink_heat_upper_bound[level] * m.level_selected[level]
        )

    def sink_residual_requires_unselected_rule(m: pyo.ConcreteModel, level: str):
        return m.sink_residual_heat[level] <= m.sink_heat_upper_bound[level]

    def utility_steam_requires_selected_header_rule(
        m: pyo.ConcreteModel,
        level: str,
    ):
        return (
            m.utility_steam_to_header[level]
            <= m.steam_flow_upper_bound[level] * m.level_selected[level]
        )

    def header_feedwater_requires_selected_header_rule(
        m: pyo.ConcreteModel,
        level: str,
    ):
        return (
            m.feedwater_to_header[level]
            <= m.steam_flow_upper_bound[level] * m.level_selected[level]
        )

    def header_export_requires_selected_header_rule(m: pyo.ConcreteModel, level: str):
        return (
            m.header_steam_export[level]
            <= m.steam_flow_upper_bound[level] * m.level_selected[level]
        )

    def one_level_per_main_rule(m: pyo.ConcreteModel, steam_main: str):
        return sum(m.level_selected[level] for level in levels_by_main[steam_main]) <= 1

    model.source_heat_requires_selected = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=source_heat_requires_selected_rule,
    )
    model.source_residual_requires_unselected = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=source_residual_requires_unselected_rule,
    )
    model.sink_heat_requires_selected = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=sink_heat_requires_selected_rule,
    )
    model.sink_residual_requires_unselected = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=sink_residual_requires_unselected_rule,
    )
    model.utility_steam_requires_selected_header = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=utility_steam_requires_selected_header_rule,
    )
    model.header_feedwater_requires_selected_header = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=header_feedwater_requires_selected_header_rule,
    )
    model.header_export_requires_selected_header = pyo.Constraint(
        model.STEAM_LEVELS,
        rule=header_export_requires_selected_header_rule,
    )
    model.one_level_per_main = pyo.Constraint(
        model.STEAM_MAINS,
        rule=one_level_per_main_rule,
    )


def _add_equipment_cost_expressions(
    model: pyo.ConcreteModel,
    data: StyleModelData,
) -> None:
    cost_by_name = {cost.name: cost for cost in data.equipment_costs}

    def equipment_annualized_capital_cost_rule(
        m: pyo.ConcreteModel,
        cost_name: str,
    ):
        cost = cost_by_name[cost_name]
        selected = _equipment_selected_expression(m, cost)
        size = _equipment_size_expression(m, cost)
        installed_capital = cost.installation_factor * (
            cost.variable_capital_cost * size + cost.fixed_capital_cost * selected
        )
        return cost.annualization_factor * installed_capital * m.cost_scale

    def equipment_maintenance_cost_rule(m: pyo.ConcreteModel, cost_name: str):
        cost = cost_by_name[cost_name]
        selected = _equipment_selected_expression(m, cost)
        size = _equipment_size_expression(m, cost)
        return (
            cost.variable_maintenance_cost * size
            + cost.fixed_maintenance_cost * selected
        ) * m.cost_scale

    model.equipment_annualized_capital_cost = pyo.Expression(
        model.EQUIPMENT_COSTS,
        rule=equipment_annualized_capital_cost_rule,
    )
    model.equipment_maintenance_cost = pyo.Expression(
        model.EQUIPMENT_COSTS,
        rule=equipment_maintenance_cost_rule,
    )
    model.total_annualized_capital_cost = pyo.Expression(
        expr=sum(
            model.equipment_annualized_capital_cost[cost_name]
            for cost_name in model.EQUIPMENT_COSTS
        ),
    )
    model.total_equipment_maintenance_cost = pyo.Expression(
        expr=sum(
            model.equipment_maintenance_cost[cost_name]
            for cost_name in model.EQUIPMENT_COSTS
        ),
    )


def _add_operating_cost_expressions(
    model: pyo.ConcreteModel,
    data: StyleModelData,
) -> None:
    fuel_cost_by_name = {cost.name: cost for cost in data.fuel_costs}

    def fuel_operating_cost_rule(m: pyo.ConcreteModel, cost_name: str):
        cost = fuel_cost_by_name[cost_name]
        return (
            _fuel_consumption_expression(m, cost)
            * cost.unit_cost
            * m.operating_hours
            * m.cost_scale
        )

    model.fuel_operating_cost = pyo.Expression(
        model.FUEL_COSTS,
        rule=fuel_operating_cost_rule,
    )
    model.total_fuel_operating_cost = pyo.Expression(
        expr=sum(
            model.fuel_operating_cost[cost_name] for cost_name in model.FUEL_COSTS
        ),
    )
    if data.electricity_cost is None:
        model.electricity_operating_cost = pyo.Expression(expr=0.0)
    else:
        model.electricity_operating_cost = pyo.Expression(
            expr=(
                model.grid_power_import * model.electricity_import_unit_cost
                - model.grid_power_export * model.electricity_export_unit_price
            )
            * model.operating_hours
            * model.cost_scale,
        )
    if data.water_cost is None:
        model.water_operating_cost = pyo.Expression(expr=0.0)
    else:
        model.water_operating_cost = pyo.Expression(
            expr=(
                model.deaerator_makeup_water
                * model.makeup_water_unit_cost
                * model.operating_hours
                * model.cost_scale
            ),
        )


def _add_objective(model: pyo.ConcreteModel) -> None:
    model.total_annualized_cost = pyo.Expression(
        expr=sum(
            model.annualized_level_cost[level]
            * model.level_selected[level]
            * model.cost_scale
            + model.operating_cost_per_heat[level]
            * model.source_heat_to_steam[level]
            * model.operating_hours
            * model.cost_scale
            for level in model.STEAM_LEVELS
        )
        + model.total_annualized_capital_cost
        + model.total_equipment_maintenance_cost
        + model.cooling_water_operating_cost
        + model.hot_oil_operating_cost
        + model.total_fuel_operating_cost
        + model.electricity_operating_cost
        + model.water_operating_cost
        + model.auxiliary_operating_cost_adjustment
    )
    model.objective = pyo.Objective(
        expr=model.total_annualized_cost,
        sense=pyo.minimize,
    )


def _previous_level_names_by_main(data: StyleModelData) -> dict[str, str | None]:
    previous_level: dict[str, str | None] = {}
    for steam_main in data.steam_mains:
        previous: str | None = None
        for level in data.steam_levels:
            if level.steam_main != steam_main:
                continue
            previous_level[level.name] = previous
            previous = level.name
    return previous_level


def _bottom_level_names_by_main(data: StyleModelData) -> tuple[str, ...]:
    bottom_levels: list[str] = []
    for steam_main in data.steam_mains:
        level_names = tuple(
            level.name for level in data.steam_levels if level.steam_main == steam_main
        )
        if not level_names:
            raise ValueError(f"steam main {steam_main!r} has no steam levels")
        bottom_levels.append(level_names[-1])
    return tuple(bottom_levels)


def _source_heat_upper_bound(
    level: SteamLevelCandidate,
    data: StyleModelData,
) -> float:
    if level.source_heat_upper_bound is not None:
        return level.source_heat_upper_bound
    return sum(candidate.source_heat_available for candidate in data.steam_levels)


def _sink_heat_upper_bound(
    level: SteamLevelCandidate,
    data: StyleModelData,
) -> float:
    if level.sink_heat_upper_bound is not None:
        return level.sink_heat_upper_bound
    return sum(candidate.sink_heat_demand for candidate in data.steam_levels)


def _steam_enthalpy_for_use(level: SteamLevelCandidate) -> float:
    if level.steam_enthalpy_for_use is not None:
        return level.steam_enthalpy_for_use
    return level.use_enthalpy_delta


def _generated_steam_enthalpy(level: SteamLevelCandidate) -> float:
    if level.generated_steam_enthalpy is not None:
        return level.generated_steam_enthalpy
    return level.generation_enthalpy_delta


def _main_steam_enthalpy(level: SteamLevelCandidate) -> float:
    if level.main_steam_enthalpy is not None:
        return level.main_steam_enthalpy
    return _steam_enthalpy_for_use(level)


def _utility_steam_enthalpy(level: SteamLevelCandidate) -> float:
    if level.utility_steam_enthalpy is not None:
        return level.utility_steam_enthalpy
    return _main_steam_enthalpy(level)


def _steam_flow_upper_bound(
    level: SteamLevelCandidate,
    data: StyleModelData,
) -> float:
    if level.steam_flow_upper_bound is not None:
        return level.steam_flow_upper_bound
    heat_based_bound = sum(
        candidate.source_heat_available + candidate.sink_heat_demand
        for candidate in data.steam_levels
    )
    enthalpy_bound = min(
        level.generation_enthalpy_delta,
        level.use_enthalpy_delta,
    )
    if enthalpy_bound <= 0.0:
        return heat_based_bound
    return heat_based_bound / enthalpy_bound


def _hot_oil_capable_levels(data: StyleModelData) -> set[str]:
    if data.hot_oil is None:
        return set()
    if data.hot_oil.supply_temperature is None:
        return {level.name for level in data.steam_levels}
    return {
        level.name
        for level in data.steam_levels
        if level.temperature < data.hot_oil.supply_temperature
    }


def _hot_oil_heat_load_upper_bound(data: StyleModelData) -> float:
    if data.hot_oil is None:
        return 0.0
    capable_levels = _hot_oil_capable_levels(data)
    return data.hot_oil.high_temperature_heat_demand + sum(
        level.sink_heat_demand
        for level in data.steam_levels
        if level.name in capable_levels
    )


def _equipment_selected_expression(
    model: pyo.ConcreteModel,
    cost: EquipmentCost,
):
    if cost.equipment_type == "boiler":
        return model.boiler_selected[cost.equipment_name]
    if cost.equipment_type == "gas_turbine":
        return model.gas_turbine_selected[cost.equipment_name]
    if cost.equipment_type == "hot_oil_furnace":
        return model.hot_oil_furnace_selected
    if cost.equipment_type == "hrsg":
        return model.hrsg_selected[cost.equipment_name]
    if cost.equipment_type == "vhp_source":
        return model.vhp_source_selected[cost.equipment_name]
    if cost.equipment_type == "vhp_turbine":
        return model.vhp_turbine_selected[cost.equipment_name]
    if cost.equipment_type == "steam_main_turbine":
        return model.steam_main_turbine_selected[cost.equipment_name]
    raise ValueError(f"unsupported equipment cost type {cost.equipment_type!r}")


def _equipment_size_expression(
    model: pyo.ConcreteModel,
    cost: EquipmentCost,
):
    if cost.equipment_type == "boiler":
        return model.boiler_size[cost.equipment_name]
    if cost.equipment_type == "gas_turbine":
        return model.gas_turbine_power_generation[cost.equipment_name]
    if cost.equipment_type == "hot_oil_furnace":
        return model.total_hot_oil_heat_load
    if cost.equipment_type == "hrsg":
        return model.hrsg_heat_input[cost.equipment_name]
    if cost.equipment_type == "vhp_source":
        return model.vhp_source_steam_generation[cost.equipment_name]
    if cost.equipment_type == "vhp_turbine":
        return model.vhp_turbine_power_generation[cost.equipment_name]
    if cost.equipment_type == "steam_main_turbine":
        return model.steam_main_turbine_power_generation[cost.equipment_name]
    raise ValueError(f"unsupported equipment cost type {cost.equipment_type!r}")


def _fuel_consumption_expression(
    model: pyo.ConcreteModel,
    cost: FuelCost,
):
    if cost.equipment_type == "boiler":
        return model.boiler_fuel_consumption[cost.equipment_name]
    if cost.equipment_type == "gas_turbine":
        return (
            model.gas_turbine_fuel_flow[cost.equipment_name]
            * model.gas_turbine_fuel_lhv[cost.equipment_name]
        )
    if cost.equipment_type == "hrsg_supplementary":
        return (
            model.hrsg_supplementary_fuel_flow[cost.equipment_name]
            * model.hrsg_supplementary_fuel_lhv[cost.equipment_name]
        )
    if cost.equipment_type == "vhp_source":
        return model.vhp_source_fuel_consumption[cost.equipment_name]
    raise ValueError(f"unsupported fuel cost type {cost.equipment_type!r}")
