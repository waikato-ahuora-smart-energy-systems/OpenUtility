"""Steam-property pseudo-parameter updates for successive utility-system MILP runs."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, replace
import math
from typing import Protocol

import pyomo.environ as pyo

from .data import UtilitySystemModelData


class SteamPropertyProvider(Protocol):
    """Boundary for steam-table or equation-of-state property calculations."""

    def enthalpy(self, *, pressure: float, temperature: float) -> float:
        """Return specific enthalpy at the supplied pressure and temperature."""

    def temperature(self, *, pressure: float, enthalpy: float) -> float:
        """Return temperature at the supplied pressure and specific enthalpy."""

    def isentropic_enthalpy_change(
        self,
        *,
        inlet_pressure: float,
        outlet_pressure: float,
        inlet_temperature: float,
    ) -> float:
        """Return isentropic enthalpy change across a steam turbine."""

    def saturated_enthalpies(self, *, pressure: float) -> tuple[float, float]:
        """Return saturated vapor and liquid enthalpies at the supplied pressure."""


class CoolPropSteamPropertyProvider:
    """Steam-property provider backed by CoolProp water properties.

    Pressures are supplied in bar, temperatures in degrees Celsius, and
    enthalpies are returned in MWh/t to match the utility-system model energy basis.
    """

    def __init__(self, *, fluid: str = "Water") -> None:
        from CoolProp.CoolProp import PropsSI

        self._props_si = PropsSI
        self._fluid = fluid

    def enthalpy(self, *, pressure: float, temperature: float) -> float:
        """Return specific enthalpy in MWh/t."""

        enthalpy_j_per_kg = self._props_si(
            "Hmass",
            "P",
            _bar_to_pascal(pressure),
            "T",
            _celsius_to_kelvin(temperature),
            self._fluid,
        )
        return _j_per_kg_to_mwh_per_tonne(enthalpy_j_per_kg)

    def temperature(self, *, pressure: float, enthalpy: float) -> float:
        """Return temperature in degrees Celsius."""

        temperature_kelvin = self._props_si(
            "T",
            "P",
            _bar_to_pascal(pressure),
            "Hmass",
            _mwh_per_tonne_to_j_per_kg(enthalpy),
            self._fluid,
        )
        return _kelvin_to_celsius(temperature_kelvin)

    def saturated_enthalpies(self, *, pressure: float) -> tuple[float, float]:
        """Return saturated vapor and liquid enthalpies in MWh/t."""

        pressure_pa = _bar_to_pascal(pressure)
        vapor_enthalpy = self._props_si(
            "Hmass",
            "P",
            pressure_pa,
            "Q",
            1,
            self._fluid,
        )
        liquid_enthalpy = self._props_si(
            "Hmass",
            "P",
            pressure_pa,
            "Q",
            0,
            self._fluid,
        )
        return (
            _j_per_kg_to_mwh_per_tonne(vapor_enthalpy),
            _j_per_kg_to_mwh_per_tonne(liquid_enthalpy),
        )

    def isentropic_enthalpy_change(
        self,
        *,
        inlet_pressure: float,
        outlet_pressure: float,
        inlet_temperature: float,
    ) -> float:
        """Return isentropic enthalpy drop in MWh/t."""

        inlet_pressure_pa = _bar_to_pascal(inlet_pressure)
        outlet_pressure_pa = _bar_to_pascal(outlet_pressure)
        inlet_temperature_k = _celsius_to_kelvin(inlet_temperature)
        inlet_entropy = self._props_si(
            "Smass",
            "P",
            inlet_pressure_pa,
            "T",
            inlet_temperature_k,
            self._fluid,
        )
        inlet_enthalpy = self._props_si(
            "Hmass",
            "P",
            inlet_pressure_pa,
            "T",
            inlet_temperature_k,
            self._fluid,
        )
        outlet_enthalpy = self._props_si(
            "Hmass",
            "P",
            outlet_pressure_pa,
            "Smass",
            inlet_entropy,
            self._fluid,
        )
        return _j_per_kg_to_mwh_per_tonne(inlet_enthalpy - outlet_enthalpy)


@dataclass(frozen=True)
class SteamLevelPropertyTarget:
    """Calculated steam-main conditions used as pseudo-parameters."""

    steam_level: str
    pressure: float
    main_temperature: float
    minimum_temperature: float
    process_generation_temperature: float | None = None
    process_use_temperature: float | None = None

    def __post_init__(self) -> None:
        _require_name(self.steam_level, "steam_level")
        _require_positive(self.pressure, "pressure")
        _require_positive(self.main_temperature, "main_temperature")
        _require_positive(self.minimum_temperature, "minimum_temperature")
        if self.main_temperature < self.minimum_temperature:
            raise ValueError("main_temperature must satisfy minimum_temperature")
        if self.process_generation_temperature is not None:
            _require_positive(
                self.process_generation_temperature,
                "process_generation_temperature",
            )
        if self.process_use_temperature is not None:
            _require_positive(self.process_use_temperature, "process_use_temperature")


@dataclass(frozen=True)
class VhpHeaderPropertyTarget:
    """Calculated VHP header conditions used as pseudo-parameters."""

    vhp_header: str
    pressure: float
    temperature: float
    maximum_temperature: float | None = None

    def __post_init__(self) -> None:
        _require_name(self.vhp_header, "vhp_header")
        _require_positive(self.pressure, "pressure")
        _require_positive(self.temperature, "temperature")
        if self.maximum_temperature is not None:
            _require_positive(self.maximum_temperature, "maximum_temperature")
            if self.temperature > self.maximum_temperature:
                raise ValueError("temperature must not exceed maximum_temperature")


@dataclass(frozen=True)
class SteamTurbinePropertyTarget:
    """Steam turbine condition for isentropic enthalpy-difference updates."""

    name: str
    inlet_pressure: float
    outlet_pressure: float
    inlet_temperature: float

    def __post_init__(self) -> None:
        _require_name(self.name, "steam turbine property target name")
        _require_positive(self.inlet_pressure, "inlet_pressure")
        _require_positive(self.outlet_pressure, "outlet_pressure")
        _require_positive(self.inlet_temperature, "inlet_temperature")
        if self.inlet_pressure <= self.outlet_pressure:
            raise ValueError("inlet_pressure must exceed outlet_pressure")


@dataclass(frozen=True)
class SteamPropertyUpdateSpec:
    """Property-update inputs extracted after a utility-system MILP solve."""

    levels: tuple[SteamLevelPropertyTarget, ...] = ()
    vhp_headers: tuple[VhpHeaderPropertyTarget, ...] = ()
    turbines: tuple[SteamTurbinePropertyTarget, ...] = ()

    def __post_init__(self) -> None:
        if not self.levels and not self.vhp_headers:
            raise ValueError(
                "at least one steam level or VHP header target is required"
            )
        _require_unique(
            (target.steam_level for target in self.levels),
            "steam level property targets",
        )
        _require_unique(
            (target.vhp_header for target in self.vhp_headers),
            "VHP header property targets",
        )
        _require_unique(
            (target.name for target in self.turbines),
            "steam turbine property targets",
        )


@dataclass(frozen=True)
class SteamPropertySnapshot:
    """Steam pseudo-parameters calculated for one MILP/property iteration."""

    level_temperatures: Mapping[str, float]
    level_main_enthalpies: Mapping[str, float]
    level_generation_enthalpies: Mapping[str, float]
    level_use_enthalpies: Mapping[str, float]
    vhp_temperatures: Mapping[str, float]
    vhp_enthalpies: Mapping[str, float]
    isentropic_enthalpy_deltas: Mapping[str, float]


@dataclass(frozen=True)
class SteamPropertyUpdate:
    """Updated utility-system data plus the calculated steam-property snapshot."""

    data: UtilitySystemModelData
    snapshot: SteamPropertySnapshot


@dataclass(frozen=True)
class SteamMainSuperheatingBalance:
    """Stage 4 steam-main energy balance and calculated superheat temperature."""

    steam_level: str
    pressure: float
    minimum_temperature: float
    source_steam_mass: float
    utility_steam_mass: float
    feedwater_mass: float
    outlet_mass: float
    inlet_heat: float
    calculated_enthalpy: float
    calculated_temperature: float

    @property
    def superheat_margin(self) -> float:
        """Temperature margin above the required minimum superheat temperature."""

        return self.calculated_temperature - self.minimum_temperature

    @property
    def minimum_temperature_satisfied(self) -> bool:
        """Whether the calculated temperature satisfies the minimum superheat."""

        return self.superheat_margin >= 0.0


@dataclass(frozen=True)
class SuccessiveMilpIteration:
    """One MILP solve followed by a steam-property pseudo-parameter update."""

    iteration: int
    input_data: UtilitySystemModelData
    update: SteamPropertyUpdate
    max_temperature_change: float
    converged: bool


@dataclass(frozen=True)
class SuccessiveMilpRun:
    """Result of a successive MILP steam-property update run."""

    initial_update: SteamPropertyUpdate
    iterations: tuple[SuccessiveMilpIteration, ...]
    final_update: SteamPropertyUpdate
    converged: bool


SuccessiveMilpSolve = Callable[[UtilitySystemModelData, int], SteamPropertyUpdateSpec]


def apply_steam_property_update(
    data: UtilitySystemModelData,
    spec: SteamPropertyUpdateSpec,
    properties: SteamPropertyProvider,
) -> SteamPropertyUpdate:
    """Return utility-system data with steam pseudo-parameters recalculated from `spec`."""

    level_targets = {target.steam_level: target for target in spec.levels}
    vhp_targets = {target.vhp_header: target for target in spec.vhp_headers}
    _require_known_targets(level_targets, (level.name for level in data.steam_levels))
    _require_known_targets(vhp_targets, (header.name for header in data.vhp_headers))

    level_temperatures: dict[str, float] = {}
    level_main_enthalpies: dict[str, float] = {}
    level_generation_enthalpies: dict[str, float] = {}
    level_use_enthalpies: dict[str, float] = {}

    updated_levels = []
    for level in data.steam_levels:
        target = level_targets.get(level.name)
        if target is None:
            updated_levels.append(level)
            continue

        main_enthalpy = properties.enthalpy(
            pressure=target.pressure,
            temperature=target.main_temperature,
        )
        generation_enthalpy = properties.enthalpy(
            pressure=target.pressure,
            temperature=target.process_generation_temperature
            if target.process_generation_temperature is not None
            else target.main_temperature,
        )
        use_enthalpy = properties.enthalpy(
            pressure=target.pressure,
            temperature=target.process_use_temperature
            if target.process_use_temperature is not None
            else target.main_temperature,
        )
        updated_levels.append(
            replace(
                level,
                generated_steam_enthalpy=generation_enthalpy,
                steam_enthalpy_for_use=use_enthalpy,
                main_steam_enthalpy=main_enthalpy,
                utility_steam_enthalpy=main_enthalpy,
            ),
        )
        level_temperatures[level.name] = target.main_temperature
        level_main_enthalpies[level.name] = main_enthalpy
        level_generation_enthalpies[level.name] = generation_enthalpy
        level_use_enthalpies[level.name] = use_enthalpy

    vhp_temperatures: dict[str, float] = {}
    vhp_enthalpies: dict[str, float] = {}
    updated_vhp_headers = []
    for header in data.vhp_headers:
        vhp_target = vhp_targets.get(header.name)
        if vhp_target is None:
            updated_vhp_headers.append(header)
            continue

        steam_enthalpy = properties.enthalpy(
            pressure=vhp_target.pressure,
            temperature=vhp_target.temperature,
        )
        updated_vhp_headers.append(replace(header, steam_enthalpy=steam_enthalpy))
        vhp_temperatures[header.name] = vhp_target.temperature
        vhp_enthalpies[header.name] = steam_enthalpy

    isentropic_enthalpy_deltas = {
        target.name: properties.isentropic_enthalpy_change(
            inlet_pressure=target.inlet_pressure,
            outlet_pressure=target.outlet_pressure,
            inlet_temperature=target.inlet_temperature,
        )
        for target in spec.turbines
    }

    return SteamPropertyUpdate(
        data=replace(
            data,
            steam_levels=tuple(updated_levels),
            vhp_headers=tuple(updated_vhp_headers),
        ),
        snapshot=SteamPropertySnapshot(
            level_temperatures=level_temperatures,
            level_main_enthalpies=level_main_enthalpies,
            level_generation_enthalpies=level_generation_enthalpies,
            level_use_enthalpies=level_use_enthalpies,
            vhp_temperatures=vhp_temperatures,
            vhp_enthalpies=vhp_enthalpies,
            isentropic_enthalpy_deltas=isentropic_enthalpy_deltas,
        ),
    )


def run_successive_milp_property_updates(
    data: UtilitySystemModelData,
    *,
    initial_spec: SteamPropertyUpdateSpec,
    solve: SuccessiveMilpSolve,
    properties: SteamPropertyProvider,
    convergence_tolerance: float,
    max_iterations: int,
) -> SuccessiveMilpRun:
    """Repeat MILP solves and steam-property updates until temperatures converge."""

    _require_non_negative(convergence_tolerance, "convergence_tolerance")
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")

    initial_update = apply_steam_property_update(data, initial_spec, properties)
    current_update = initial_update
    previous_snapshot = initial_update.snapshot
    iterations: list[SuccessiveMilpIteration] = []
    converged = False

    for iteration_number in range(1, max_iterations + 1):
        input_data = current_update.data
        next_spec = solve(input_data, iteration_number)
        next_update = apply_steam_property_update(input_data, next_spec, properties)
        max_temperature_change = _max_temperature_change(
            previous_snapshot,
            next_update.snapshot,
        )
        converged = max_temperature_change <= convergence_tolerance
        iterations.append(
            SuccessiveMilpIteration(
                iteration=iteration_number,
                input_data=input_data,
                update=next_update,
                max_temperature_change=max_temperature_change,
                converged=converged,
            ),
        )
        current_update = next_update
        previous_snapshot = next_update.snapshot
        if converged:
            break

    return SuccessiveMilpRun(
        initial_update=initial_update,
        iterations=tuple(iterations),
        final_update=current_update,
        converged=converged,
    )


def steam_property_update_spec_from_model(
    data: UtilitySystemModelData,
    model: pyo.ConcreteModel,
    *,
    level_targets: tuple[SteamLevelPropertyTarget, ...],
    vhp_targets: tuple[VhpHeaderPropertyTarget, ...],
    selection_tolerance: float = 1e-6,
) -> SteamPropertyUpdateSpec:
    """Extract selected steam-property update targets from a solved utility-system model."""

    _require_non_negative(selection_tolerance, "selection_tolerance")
    _require_unique(
        (target.steam_level for target in level_targets),
        "steam level property targets",
    )
    _require_unique(
        (target.vhp_header for target in vhp_targets),
        "VHP header property targets",
    )
    level_target_by_name = {target.steam_level: target for target in level_targets}
    vhp_target_by_name = {target.vhp_header: target for target in vhp_targets}

    selected_levels = _selected_component_names(
        model,
        "level_selected",
        (level.name for level in data.steam_levels),
        selection_tolerance,
    )
    selected_vhp_headers = _selected_component_names(
        model,
        "vhp_selected",
        (header.name for header in data.vhp_headers),
        selection_tolerance,
    )
    level_targets_for_update = tuple(
        _target_for_selected_name(
            level_target_by_name,
            name,
            "steam level",
        )
        for name in selected_levels
    )
    vhp_targets_for_update = tuple(
        _target_for_selected_name(vhp_target_by_name, name, "VHP header")
        for name in selected_vhp_headers
    )
    turbine_targets = tuple(
        _steam_turbine_property_target(
            turbine.name,
            turbine.vhp_header,
            turbine.steam_level,
            level_target_by_name,
            vhp_target_by_name,
        )
        for turbine in data.vhp_turbines
        if _component_value(
            model,
            "vhp_turbine_selected",
            turbine.name,
        )
        > selection_tolerance
    ) + tuple(
        _steam_main_turbine_property_target(
            turbine.name,
            turbine.source_level,
            turbine.target_level,
            level_target_by_name,
        )
        for turbine in data.steam_main_turbines
        if _component_value(
            model,
            "steam_main_turbine_selected",
            turbine.name,
        )
        > selection_tolerance
    )

    return SteamPropertyUpdateSpec(
        levels=level_targets_for_update,
        vhp_headers=vhp_targets_for_update,
        turbines=turbine_targets,
    )


def steam_main_superheating_balances_from_model(
    data: UtilitySystemModelData,
    model: pyo.ConcreteModel,
    *,
    level_targets: tuple[SteamLevelPropertyTarget, ...],
    vhp_targets: tuple[VhpHeaderPropertyTarget, ...],
    properties: SteamPropertyProvider,
    mechanical_efficiency: float = 1.0,
    selection_tolerance: float = 1e-6,
) -> tuple[SteamMainSuperheatingBalance, ...]:
    """Calculate Stage 4 steam-main superheating balances from solved flows."""

    _require_positive(mechanical_efficiency, "mechanical_efficiency")
    _require_non_negative(selection_tolerance, "selection_tolerance")
    level_target_by_name = _level_target_by_name(level_targets)
    vhp_target_by_name = _vhp_target_by_name(vhp_targets)
    selected_levels = _selected_component_names(
        model,
        "level_selected",
        (level.name for level in data.steam_levels),
        selection_tolerance,
    )
    balances = []
    calculated_enthalpies: dict[str, float] = {}
    for level_name in selected_levels:
        balance = _steam_main_superheating_balance(
            data,
            model,
            level_name,
            level_target_by_name,
            vhp_target_by_name,
            properties,
            mechanical_efficiency,
            selection_tolerance,
            calculated_enthalpies,
        )
        balances.append(balance)
        calculated_enthalpies[level_name] = balance.calculated_enthalpy
    return tuple(balances)


def steam_property_update_spec_from_stage4_model(
    data: UtilitySystemModelData,
    model: pyo.ConcreteModel,
    *,
    level_targets: tuple[SteamLevelPropertyTarget, ...],
    vhp_targets: tuple[VhpHeaderPropertyTarget, ...],
    properties: SteamPropertyProvider,
    mechanical_efficiency: float = 1.0,
    selection_tolerance: float = 1e-6,
) -> SteamPropertyUpdateSpec:
    """Build a property update spec with Stage 4 calculated steam temperatures."""

    balances = steam_main_superheating_balances_from_model(
        data,
        model,
        level_targets=level_targets,
        vhp_targets=vhp_targets,
        properties=properties,
        mechanical_efficiency=mechanical_efficiency,
        selection_tolerance=selection_tolerance,
    )
    level_target_by_name = _level_target_by_name(level_targets)
    calculated_level_targets = tuple(
        replace(
            level_target_by_name[balance.steam_level],
            main_temperature=balance.calculated_temperature,
        )
        for balance in balances
    )
    base_spec = steam_property_update_spec_from_model(
        data,
        model,
        level_targets=calculated_level_targets,
        vhp_targets=vhp_targets,
        selection_tolerance=selection_tolerance,
    )
    return base_spec


def _max_temperature_change(
    previous: SteamPropertySnapshot,
    current: SteamPropertySnapshot,
) -> float:
    previous_values = _temperature_values(previous)
    current_values = _temperature_values(current)
    if previous_values.keys() != current_values.keys():
        return math.inf
    return max(
        (abs(current_values[key] - previous_values[key]) for key in current_values),
        default=0.0,
    )


def _temperature_values(
    snapshot: SteamPropertySnapshot,
) -> dict[tuple[str, str], float]:
    values = {
        ("steam_level", name): temperature
        for name, temperature in snapshot.level_temperatures.items()
    }
    values.update(
        {
            ("vhp_header", name): temperature
            for name, temperature in snapshot.vhp_temperatures.items()
        },
    )
    return values


def _require_known_targets(
    targets: Mapping[str, object],
    configured_names: Iterable[object],
) -> None:
    configured = set(configured_names)
    for name in targets:
        if name not in configured:
            raise ValueError(f"unknown steam level or VHP header target {name!r}")


def _level_target_by_name(
    targets: tuple[SteamLevelPropertyTarget, ...],
) -> dict[str, SteamLevelPropertyTarget]:
    _require_unique(
        (target.steam_level for target in targets),
        "steam level property targets",
    )
    return {target.steam_level: target for target in targets}


def _vhp_target_by_name(
    targets: tuple[VhpHeaderPropertyTarget, ...],
) -> dict[str, VhpHeaderPropertyTarget]:
    _require_unique(
        (target.vhp_header for target in targets),
        "VHP header property targets",
    )
    return {target.vhp_header: target for target in targets}


def _steam_main_superheating_balance(
    data: UtilitySystemModelData,
    model: pyo.ConcreteModel,
    level_name: str,
    level_targets: Mapping[str, SteamLevelPropertyTarget],
    vhp_targets: Mapping[str, VhpHeaderPropertyTarget],
    properties: SteamPropertyProvider,
    mechanical_efficiency: float,
    selection_tolerance: float,
    calculated_enthalpies: Mapping[str, float],
) -> SteamMainSuperheatingBalance:
    level_target = _target_for_selected_name(
        level_targets,
        level_name,
        "steam level",
    )
    source_steam_mass = _component_value(model, "source_steam_generated", level_name)
    feedwater_mass = _component_value(model, "feedwater_to_header", level_name)
    outgoing_transfer_mass = _outgoing_inter_header_steam_mass(
        data,
        model,
        level_name,
    )
    outlet_mass = (
        _component_value(model, "process_steam_to_sink", level_name)
        + _component_value(model, "header_steam_export", level_name)
        + _component_value(model, "deaerator_steam_from_header", level_name)
        + outgoing_transfer_mass
    )
    if outlet_mass <= selection_tolerance:
        raise ValueError(f"selected steam level {level_name!r} has no outgoing steam")

    utility_steam_mass, utility_steam_heat = _utility_steam_into_level(
        data,
        model,
        level_name,
        vhp_targets,
        properties,
        mechanical_efficiency,
        selection_tolerance,
    )
    inter_header_mass, inter_header_heat = _inter_header_steam_into_level(
        data,
        model,
        level_name,
        level_targets,
        properties,
        mechanical_efficiency,
        selection_tolerance,
        calculated_enthalpies,
    )
    source_steam_heat = source_steam_mass * properties.enthalpy(
        pressure=level_target.pressure,
        temperature=level_target.process_generation_temperature
        if level_target.process_generation_temperature is not None
        else level_target.main_temperature,
    )
    feedwater_heat = feedwater_mass * _component_value(
        model,
        "feedwater_enthalpy",
        level_name,
    )
    inlet_heat = (
        source_steam_heat + utility_steam_heat + inter_header_heat + feedwater_heat
    )
    calculated_enthalpy = inlet_heat / outlet_mass
    calculated_temperature = properties.temperature(
        pressure=level_target.pressure,
        enthalpy=calculated_enthalpy,
    )
    return SteamMainSuperheatingBalance(
        steam_level=level_name,
        pressure=level_target.pressure,
        minimum_temperature=level_target.minimum_temperature,
        source_steam_mass=source_steam_mass,
        utility_steam_mass=utility_steam_mass + inter_header_mass,
        feedwater_mass=feedwater_mass,
        outlet_mass=outlet_mass,
        inlet_heat=inlet_heat,
        calculated_enthalpy=calculated_enthalpy,
        calculated_temperature=calculated_temperature,
    )


def _utility_steam_into_level(
    data: UtilitySystemModelData,
    model: pyo.ConcreteModel,
    level_name: str,
    vhp_targets: Mapping[str, VhpHeaderPropertyTarget],
    properties: SteamPropertyProvider,
    mechanical_efficiency: float,
    selection_tolerance: float,
) -> tuple[float, float]:
    total_utility_mass = 0.0
    total_utility_heat = 0.0
    for header in data.vhp_headers:
        vhp_target = vhp_targets.get(header.name)
        if vhp_target is None:
            continue
        vhp_enthalpy = properties.enthalpy(
            pressure=vhp_target.pressure,
            temperature=vhp_target.temperature,
        )
        aggregate_mass = _component_value(
            model,
            "utility_steam_from_vhp",
            (header.name, level_name),
        )
        detailed_mass, detailed_heat = _detailed_vhp_connection_heat(
            data,
            model,
            header.name,
            level_name,
            vhp_enthalpy,
            mechanical_efficiency,
            selection_tolerance,
        )
        residual_mass = max(0.0, aggregate_mass - detailed_mass)
        total_utility_mass += aggregate_mass
        total_utility_heat += detailed_heat + residual_mass * vhp_enthalpy
    return total_utility_mass, total_utility_heat


def _detailed_vhp_connection_heat(
    data: UtilitySystemModelData,
    model: pyo.ConcreteModel,
    vhp_header: str,
    level_name: str,
    vhp_enthalpy: float,
    mechanical_efficiency: float,
    selection_tolerance: float,
) -> tuple[float, float]:
    total_mass = 0.0
    total_heat = 0.0
    for turbine in data.vhp_turbines:
        if turbine.vhp_header != vhp_header or turbine.steam_level != level_name:
            continue
        flow = _component_value(model, "vhp_turbine_steam_flow", turbine.name)
        if flow <= selection_tolerance:
            continue
        power = _component_value(model, "vhp_turbine_power_generation", turbine.name)
        total_mass += flow
        total_heat += flow * vhp_enthalpy - power / mechanical_efficiency
    for letdown in data.vhp_letdowns:
        if letdown.vhp_header != vhp_header or letdown.steam_level != level_name:
            continue
        flow = _component_value(model, "vhp_letdown_flow", letdown.name)
        if flow <= selection_tolerance:
            continue
        total_mass += flow
        total_heat += flow * vhp_enthalpy
    return total_mass, total_heat


def _inter_header_steam_into_level(
    data: UtilitySystemModelData,
    model: pyo.ConcreteModel,
    level_name: str,
    level_targets: Mapping[str, SteamLevelPropertyTarget],
    properties: SteamPropertyProvider,
    mechanical_efficiency: float,
    selection_tolerance: float,
    calculated_enthalpies: Mapping[str, float],
) -> tuple[float, float]:
    total_mass = 0.0
    total_heat = 0.0
    for turbine in data.steam_main_turbines:
        if turbine.target_level != level_name:
            continue
        flow = _component_value(model, "steam_main_turbine_steam_flow", turbine.name)
        if flow <= selection_tolerance:
            continue
        power = _component_value(
            model,
            "steam_main_turbine_power_generation",
            turbine.name,
        )
        source_enthalpy = _source_level_enthalpy(
            turbine.source_level,
            level_targets,
            properties,
            calculated_enthalpies,
        )
        total_mass += flow
        total_heat += flow * source_enthalpy - power / mechanical_efficiency
    for letdown in data.steam_main_letdowns:
        if letdown.target_level != level_name:
            continue
        flow = _component_value(model, "steam_main_letdown_flow", letdown.name)
        if flow <= selection_tolerance:
            continue
        source_enthalpy = _source_level_enthalpy(
            letdown.source_level,
            level_targets,
            properties,
            calculated_enthalpies,
        )
        total_mass += flow
        total_heat += flow * source_enthalpy
    return total_mass, total_heat


def _outgoing_inter_header_steam_mass(
    data: UtilitySystemModelData,
    model: pyo.ConcreteModel,
    level_name: str,
) -> float:
    turbine_flow = sum(
        _component_value(model, "steam_main_turbine_steam_flow", turbine.name)
        for turbine in data.steam_main_turbines
        if turbine.source_level == level_name
    )
    letdown_flow = sum(
        _component_value(model, "steam_main_letdown_flow", letdown.name)
        for letdown in data.steam_main_letdowns
        if letdown.source_level == level_name
    )
    return turbine_flow + letdown_flow


def _source_level_enthalpy(
    level_name: str,
    level_targets: Mapping[str, SteamLevelPropertyTarget],
    properties: SteamPropertyProvider,
    calculated_enthalpies: Mapping[str, float],
) -> float:
    if level_name in calculated_enthalpies:
        return calculated_enthalpies[level_name]
    level_target = _target_for_selected_name(level_targets, level_name, "steam level")
    return properties.enthalpy(
        pressure=level_target.pressure,
        temperature=level_target.main_temperature,
    )


def _selected_component_names(
    model: pyo.ConcreteModel,
    component_name: str,
    candidate_names: object,
    selection_tolerance: float,
) -> tuple[str, ...]:
    return tuple(
        name
        for name in candidate_names
        if _component_value(model, component_name, name) > selection_tolerance
    )


def _component_value(
    model: pyo.ConcreteModel,
    component_name: str,
    index: object,
) -> float:
    if not hasattr(model, component_name):
        raise ValueError(f"model is missing component {component_name!r}")
    component = getattr(model, component_name)
    value = pyo.value(component[index], exception=False)
    if value is None:
        raise ValueError(f"model component {component_name}[{index!r}] has no value")
    return float(value)


def _target_for_selected_name(
    targets: Mapping[str, object],
    name: str,
    label: str,
):
    try:
        return targets[name]
    except KeyError as exc:
        raise ValueError(f"missing property target for {label} {name!r}") from exc


def _steam_turbine_property_target(
    name: str,
    vhp_header: str,
    steam_level: str,
    level_targets: Mapping[str, SteamLevelPropertyTarget],
    vhp_targets: Mapping[str, VhpHeaderPropertyTarget],
) -> SteamTurbinePropertyTarget:
    vhp_target = _target_for_selected_name(vhp_targets, vhp_header, "VHP header")
    level_target = _target_for_selected_name(
        level_targets,
        steam_level,
        "steam level",
    )
    return SteamTurbinePropertyTarget(
        name=name,
        inlet_pressure=vhp_target.pressure,
        outlet_pressure=level_target.pressure,
        inlet_temperature=vhp_target.temperature,
    )


def _steam_main_turbine_property_target(
    name: str,
    source_level: str,
    target_level: str,
    level_targets: Mapping[str, SteamLevelPropertyTarget],
) -> SteamTurbinePropertyTarget:
    source_target = _target_for_selected_name(
        level_targets,
        source_level,
        "steam level",
    )
    target_target = _target_for_selected_name(
        level_targets,
        target_level,
        "steam level",
    )
    return SteamTurbinePropertyTarget(
        name=name,
        inlet_pressure=source_target.pressure,
        outlet_pressure=target_target.pressure,
        inlet_temperature=source_target.main_temperature,
    )


def _require_unique(values: Iterable[object], label: str) -> None:
    materialized: tuple[object, ...] = tuple(values)
    if len(set(materialized)) != len(materialized):
        raise ValueError(f"{label} must be unique")


def _require_name(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")


def _require_positive(value: float, label: str) -> None:
    if value <= 0:
        raise ValueError(f"{label} must be positive")


def _require_non_negative(value: float, label: str) -> None:
    if value < 0:
        raise ValueError(f"{label} must be non-negative")


def _bar_to_pascal(pressure: float) -> float:
    return pressure * 100_000.0


def _celsius_to_kelvin(temperature: float) -> float:
    return temperature + 273.15


def _kelvin_to_celsius(temperature: float) -> float:
    return temperature - 273.15


def _j_per_kg_to_mwh_per_tonne(enthalpy: float) -> float:
    return enthalpy / 3_600_000.0


def _mwh_per_tonne_to_j_per_kg(enthalpy: float) -> float:
    return enthalpy * 3_600_000.0
