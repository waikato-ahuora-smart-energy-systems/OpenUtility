"""Typed inputs for the utility-system synthesis model."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math
from typing import Any


HPR_SCHEMA_VERSIONS = {"1.0"}
HPR_MODES = {"heat_pump", "refrigeration"}
HPR_INTERPOLATION_TOPOLOGIES = {"ordered_part_load_curve"}
HPR_REFERENCE_CAPACITY_BASES = {"q_source", "q_sink"}
HPR_COP_CONVENTIONS = {"heating", "cooling"}
HPR_REFRIGERATION_ROUTING_MODES = {
    "recovery_only",
    "rejection_only",
    "split",
}
HPR_REQUIRED_UNITS = {
    "source_temperature": "degC",
    "sink_temperature": "degC",
    "q_source": "kW",
    "q_sink": "kW",
    "electric_power": "kW",
}
THERMAL_NODE_TYPES = {"source", "sink", "cooling", "rejection"}


@dataclass(frozen=True)
class ThermalNode:
    """Generic thermal service node used by HPR candidates."""

    name: str
    temperature: float
    node_type: str
    heating_unit_cost: float = 0.0
    cooling_unit_cost: float = 0.0
    rejection_unit_cost: float = 0.0

    def __post_init__(self) -> None:
        _require_name(self.name, "thermal node name")
        _require_finite(self.temperature, "thermal node temperature")
        if self.node_type not in THERMAL_NODE_TYPES:
            raise ValueError(
                f"thermal node type must be one of {sorted(THERMAL_NODE_TYPES)!r}"
            )
        _require_non_negative(self.heating_unit_cost, "heating_unit_cost")
        _require_non_negative(self.cooling_unit_cost, "cooling_unit_cost")
        _require_non_negative(self.rejection_unit_cost, "rejection_unit_cost")


@dataclass(frozen=True)
class OperatingPeriod:
    """One operating period with node-keyed thermal data."""

    name: str
    hours: float
    power_demand: float = 0.0
    electricity_import_unit_cost: float = 0.0
    electricity_export_unit_price: float = 0.0
    source_heat_available: Mapping[str, float] | None = None
    heating_demand: Mapping[str, float] | None = None
    cooling_demand: Mapping[str, float] | None = None
    rejection_capacity: Mapping[str, float] | None = None
    node_temperatures: Mapping[str, float] | None = None

    def __post_init__(self) -> None:
        _require_name(self.name, "operating period name")
        _require_positive(self.hours, "hours")
        _require_non_negative(self.power_demand, "power_demand")
        _require_non_negative(
            self.electricity_import_unit_cost,
            "electricity_import_unit_cost",
        )
        _require_non_negative(
            self.electricity_export_unit_price,
            "electricity_export_unit_price",
        )
        _require_non_negative_mapping(self.source_heat_available, "source heat")
        _require_non_negative_mapping(self.heating_demand, "heating demand")
        _require_non_negative_mapping(self.cooling_demand, "cooling demand")
        _require_non_negative_mapping(self.rejection_capacity, "rejection capacity")
        _require_finite_mapping(self.node_temperatures, "node temperatures")


@dataclass(frozen=True)
class HprPerformancePoint:
    """One HPR part-load point on a temperature-compatible curve."""

    name: str
    curve_id: str
    source_temperature: float
    sink_temperature: float
    load_fraction: float
    q_source: float
    q_sink: float
    electric_power: float
    cop: float | None = None

    def __post_init__(self) -> None:
        _require_name(self.name, "HPR performance point name")
        _require_name(self.curve_id, "HPR curve id")
        _require_finite(self.source_temperature, "source_temperature")
        _require_finite(self.sink_temperature, "sink_temperature")
        _require_fraction_inclusive(self.load_fraction, "load_fraction")
        _require_non_negative(self.q_source, "q_source")
        _require_non_negative(self.q_sink, "q_sink")
        _require_non_negative(self.electric_power, "electric_power")
        if self.load_fraction > 0.0 and self.electric_power <= 0.0:
            raise ValueError("electric_power must be positive for active HPR points")
        if self.cop is not None:
            _require_positive(self.cop, "cop")
            if self.electric_power <= 0.0:
                raise ValueError("electric_power must be positive for HPR COP checks")


@dataclass(frozen=True)
class HprPerformanceMap:
    """Versioned plain-data HPR performance map."""

    schema_version: str
    map_id: str
    mode: str
    units: Mapping[str, str]
    reference_capacity: float
    reference_capacity_basis: str
    interpolation_topology: str
    thermodynamic_backend: str
    model_id: str
    provenance: Mapping[str, Any]
    points: tuple[HprPerformancePoint, ...]
    cop_convention: str
    energy_balance_tolerance: float = 1e-6
    temperature_match_tolerance: float = 1e-6

    def __post_init__(self) -> None:
        _require_hpr_schema_version(self.schema_version)
        _require_name(self.map_id, "HPR map_id")
        _require_hpr_mode(self.mode)
        _require_positive(self.reference_capacity, "reference_capacity")
        _require_reference_capacity_basis(self.reference_capacity_basis)
        _validate_mode_capacity_basis(self.mode, self.reference_capacity_basis)
        if self.interpolation_topology not in HPR_INTERPOLATION_TOPOLOGIES:
            raise ValueError(
                "HPR interpolation_topology must be one of "
                f"{sorted(HPR_INTERPOLATION_TOPOLOGIES)!r}"
            )
        _require_name(self.thermodynamic_backend, "thermodynamic_backend")
        _require_name(self.model_id, "model_id")
        _require_hpr_cop_convention(self.cop_convention)
        _validate_mode_cop_convention(self.mode, self.cop_convention)
        _require_non_negative(
            self.energy_balance_tolerance,
            "energy_balance_tolerance",
        )
        _require_non_negative(
            self.temperature_match_tolerance,
            "temperature_match_tolerance",
        )
        _validate_hpr_units(self.units)
        if not self.provenance:
            raise ValueError("HPR map provenance must not be empty")
        if not self.points:
            raise ValueError("HPR performance map requires at least one point")
        point_names = [point.name for point in self.points]
        if len(set(point_names)) != len(point_names):
            raise ValueError("HPR performance point names must be unique per map")
        for point in self.points:
            _validate_hpr_energy_balance(point, self.energy_balance_tolerance)
            _validate_hpr_cop(point, self.cop_convention, self.energy_balance_tolerance)
            _validate_hpr_reference_capacity_point(
                point,
                self.reference_capacity,
                self.reference_capacity_basis,
                self.energy_balance_tolerance,
            )
        _validate_hpr_ordered_curves(self.points)


@dataclass(frozen=True)
class HprCandidate:
    """Fixed-capacity HPR optimization candidate."""

    name: str
    mode: str
    map_id: str
    source_node: str
    sink_node: str | None = None
    rejection_node: str | None = None
    fixed_capacity: float = 0.0
    minimum_load_fraction: float = 0.0
    variable_operating_cost_per_q_useful: float = 0.0
    must_select: bool = False
    refrigeration_routing: str = "rejection_only"

    def __post_init__(self) -> None:
        _require_name(self.name, "HPR candidate name")
        _require_hpr_mode(self.mode)
        _require_name(self.map_id, "HPR candidate map_id")
        _require_name(self.source_node, "HPR source_node")
        _require_non_negative(self.fixed_capacity, "fixed_capacity")
        _require_fraction(self.minimum_load_fraction, "minimum_load_fraction")
        _require_non_negative(
            self.variable_operating_cost_per_q_useful,
            "variable_operating_cost_per_q_useful",
        )
        if self.mode == "heat_pump":
            _require_name(self.sink_node or "", "HPR sink_node")
            if self.rejection_node is not None:
                _require_name(self.rejection_node, "HPR rejection_node")
            return
        if self.refrigeration_routing not in HPR_REFRIGERATION_ROUTING_MODES:
            raise ValueError(
                "HPR refrigeration_routing must be one of "
                f"{sorted(HPR_REFRIGERATION_ROUTING_MODES)!r}"
            )
        if self.refrigeration_routing in {"recovery_only", "split"}:
            _require_name(self.sink_node or "", "HPR recovery sink_node")
        if self.refrigeration_routing in {"rejection_only", "split"}:
            _require_name(self.rejection_node or "", "HPR rejection_node")


def hpr_performance_map_from_mapping(
    values: Mapping[str, Any],
) -> HprPerformanceMap:
    """Decode a versioned HPR performance map from plain mapping data."""

    _reject_unknown_keys(
        values,
        {
            "schema_version",
            "map_id",
            "mode",
            "units",
            "reference_capacity",
            "reference_capacity_basis",
            "interpolation_topology",
            "thermodynamic_backend",
            "model_id",
            "provenance",
            "points",
            "cop_convention",
            "energy_balance_tolerance",
            "temperature_match_tolerance",
        },
        "HPR performance map",
    )
    raw_points = values.get("points")
    if not isinstance(raw_points, tuple | list):
        raise ValueError("HPR performance map points must be a sequence")
    points: list[HprPerformancePoint] = []
    for point in raw_points:
        if not isinstance(point, Mapping):
            raise ValueError("HPR performance map points must be mappings")
        _reject_unknown_keys(
            point,
            {
                "name",
                "curve_id",
                "source_temperature",
                "sink_temperature",
                "load_fraction",
                "q_source",
                "q_sink",
                "electric_power",
                "cop",
            },
            "HPR performance point",
        )
        points.append(
            HprPerformancePoint(
                name=_required_string(point, "name"),
                curve_id=_required_string(point, "curve_id"),
                source_temperature=float(point["source_temperature"]),
                sink_temperature=float(point["sink_temperature"]),
                load_fraction=float(point["load_fraction"]),
                q_source=float(point["q_source"]),
                q_sink=float(point["q_sink"]),
                electric_power=float(point["electric_power"]),
                cop=_optional_float(point.get("cop")),
            )
        )
    return HprPerformanceMap(
        schema_version=_required_string(values, "schema_version"),
        map_id=_required_string(values, "map_id"),
        mode=_required_string(values, "mode"),
        units=_required_string_mapping(values, "units"),
        reference_capacity=float(values.get("reference_capacity", 0.0)),
        reference_capacity_basis=_required_string(values, "reference_capacity_basis"),
        interpolation_topology=_required_string(values, "interpolation_topology"),
        thermodynamic_backend=_required_string(values, "thermodynamic_backend"),
        model_id=_required_string(values, "model_id"),
        provenance=_required_mapping(values, "provenance"),
        points=tuple(points),
        cop_convention=_required_string(values, "cop_convention"),
        energy_balance_tolerance=float(values.get("energy_balance_tolerance", 1e-6)),
        temperature_match_tolerance=float(
            values.get("temperature_match_tolerance", 1e-6)
        ),
    )


@dataclass(frozen=True)
class VhpSteamCandidate:
    """Potential very-high-pressure steam generation condition."""

    name: str
    steam_enthalpy: float
    feedwater_enthalpy: float
    steam_flow_upper_bound: float

    def __post_init__(self) -> None:
        _require_name(self.name, "VHP header name")
        _require_positive(self.steam_enthalpy, "steam_enthalpy")
        _require_non_negative(self.feedwater_enthalpy, "feedwater_enthalpy")
        _require_positive(self.steam_flow_upper_bound, "steam_flow_upper_bound")


@dataclass(frozen=True)
class VhpSteamSourceCandidate:
    """Generic VHP steam source for calibration or external utility supply."""

    name: str
    vhp_header: str
    min_capacity: float
    max_capacity: float
    minimum_load_fraction: float
    fuel_consumption_per_steam: float = 0.0
    must_select: bool = False

    def __post_init__(self) -> None:
        _require_name(self.name, "VHP steam source name")
        _require_name(self.vhp_header, "VHP steam source header")
        _require_non_negative(self.min_capacity, "min_capacity")
        _require_positive(self.max_capacity, "max_capacity")
        if self.min_capacity > self.max_capacity:
            raise ValueError("min_capacity must not exceed max_capacity")
        _require_fraction(self.minimum_load_fraction, "minimum_load_fraction")
        _require_non_negative(
            self.fuel_consumption_per_steam,
            "fuel_consumption_per_steam",
        )


@dataclass(frozen=True)
class BoilerCandidate:
    """Candidate boiler unit feeding one VHP steam condition."""

    name: str
    vhp_header: str
    size_fuel_coefficient: float
    load_fuel_coefficient: float
    min_capacity: float
    max_capacity: float
    minimum_load_fraction: float
    blowdown_fraction: float = 0.0
    blowdown_enthalpy_delta: float = 0.0
    must_select: bool = False

    def __post_init__(self) -> None:
        _require_name(self.name, "boiler name")
        _require_name(self.vhp_header, "boiler VHP header")
        _require_non_negative(self.size_fuel_coefficient, "size_fuel_coefficient")
        _require_non_negative(self.load_fuel_coefficient, "load_fuel_coefficient")
        _require_non_negative(self.min_capacity, "min_capacity")
        _require_positive(self.max_capacity, "max_capacity")
        if self.min_capacity > self.max_capacity:
            raise ValueError("min_capacity must not exceed max_capacity")
        _require_fraction(self.minimum_load_fraction, "minimum_load_fraction")
        _require_fraction(self.blowdown_fraction, "blowdown_fraction")
        _require_non_negative(self.blowdown_enthalpy_delta, "blowdown_enthalpy_delta")


@dataclass(frozen=True)
class VhpBackPressureTurbineCandidate:
    """Back-pressure turbine connecting a VHP header to a steam main."""

    name: str
    vhp_header: str
    steam_level: str
    power_slope: float
    power_intercept: float
    min_capacity: float
    max_capacity: float
    minimum_load_fraction: float
    must_select: bool = False

    def __post_init__(self) -> None:
        _require_name(self.name, "VHP turbine name")
        _require_name(self.vhp_header, "VHP turbine header")
        _require_name(self.steam_level, "VHP turbine steam level")
        _require_non_negative(self.power_slope, "power_slope")
        _require_non_negative(self.power_intercept, "power_intercept")
        _require_non_negative(self.min_capacity, "min_capacity")
        _require_positive(self.max_capacity, "max_capacity")
        if self.min_capacity > self.max_capacity:
            raise ValueError("min_capacity must not exceed max_capacity")
        _require_fraction(self.minimum_load_fraction, "minimum_load_fraction")


@dataclass(frozen=True)
class VhpLetdownStationCandidate:
    """Let-down station connecting a VHP header to a steam main."""

    name: str
    vhp_header: str
    steam_level: str
    max_flow: float

    def __post_init__(self) -> None:
        _require_name(self.name, "VHP letdown name")
        _require_name(self.vhp_header, "VHP letdown header")
        _require_name(self.steam_level, "VHP letdown steam level")
        _require_positive(self.max_flow, "max_flow")


@dataclass(frozen=True)
class SteamMainBackPressureTurbineCandidate:
    """Back-pressure turbine connecting one steam main level to a lower level."""

    name: str
    source_level: str
    target_level: str
    power_slope: float
    power_intercept: float
    min_capacity: float
    max_capacity: float
    minimum_load_fraction: float
    must_select: bool = False

    def __post_init__(self) -> None:
        _require_name(self.name, "steam-main turbine name")
        _require_name(self.source_level, "steam-main turbine source level")
        _require_name(self.target_level, "steam-main turbine target level")
        if self.source_level == self.target_level:
            raise ValueError("source_level and target_level must differ")
        _require_non_negative(self.power_slope, "power_slope")
        _require_non_negative(self.power_intercept, "power_intercept")
        _require_non_negative(self.min_capacity, "min_capacity")
        _require_positive(self.max_capacity, "max_capacity")
        if self.min_capacity > self.max_capacity:
            raise ValueError("min_capacity must not exceed max_capacity")
        _require_fraction(self.minimum_load_fraction, "minimum_load_fraction")


@dataclass(frozen=True)
class SteamMainLetdownStationCandidate:
    """Let-down station connecting one steam main level to a lower level."""

    name: str
    source_level: str
    target_level: str
    max_flow: float

    def __post_init__(self) -> None:
        _require_name(self.name, "steam-main letdown name")
        _require_name(self.source_level, "steam-main letdown source level")
        _require_name(self.target_level, "steam-main letdown target level")
        if self.source_level == self.target_level:
            raise ValueError("source_level and target_level must differ")
        _require_positive(self.max_flow, "max_flow")


@dataclass(frozen=True)
class GasTurbineCandidate:
    """Candidate gas turbine producing power and exhaust heat."""

    name: str
    fuel_lhv: float
    power_slope: float
    power_intercept: float
    min_fuel_flow: float
    max_fuel_flow: float
    minimum_load_fraction: float
    must_select: bool = False

    def __post_init__(self) -> None:
        _require_name(self.name, "gas turbine name")
        _require_positive(self.fuel_lhv, "fuel_lhv")
        _require_non_negative(self.power_slope, "power_slope")
        _require_non_negative(self.power_intercept, "power_intercept")
        _require_non_negative(self.min_fuel_flow, "min_fuel_flow")
        _require_positive(self.max_fuel_flow, "max_fuel_flow")
        if self.min_fuel_flow > self.max_fuel_flow:
            raise ValueError("min_fuel_flow must not exceed max_fuel_flow")
        _require_fraction(self.minimum_load_fraction, "minimum_load_fraction")


@dataclass(frozen=True)
class HrsgCandidate:
    """Heat recovery steam generator linked to one gas turbine and VHP header."""

    name: str
    gas_turbine: str
    vhp_header: str
    steam_generation_efficiency: float
    max_heat_input: float
    supplementary_fuel_lhv: float = 0.0
    supplementary_firing_efficiency: float = 1.0
    max_supplementary_fuel_flow: float = 0.0
    must_select: bool = False

    def __post_init__(self) -> None:
        _require_name(self.name, "HRSG name")
        _require_name(self.gas_turbine, "HRSG gas turbine")
        _require_name(self.vhp_header, "HRSG VHP header")
        _require_positive(
            self.steam_generation_efficiency,
            "steam_generation_efficiency",
        )
        _require_positive(self.max_heat_input, "max_heat_input")
        _require_non_negative(self.supplementary_fuel_lhv, "supplementary_fuel_lhv")
        _require_positive(
            self.supplementary_firing_efficiency,
            "supplementary_firing_efficiency",
        )
        _require_non_negative(
            self.max_supplementary_fuel_flow,
            "max_supplementary_fuel_flow",
        )
        if (
            self.max_supplementary_fuel_flow > 0.0
            and self.supplementary_fuel_lhv == 0.0
        ):
            raise ValueError(
                "supplementary_fuel_lhv must be positive when supplementary "
                "firing is available"
            )


@dataclass(frozen=True)
class DeaeratorConfig:
    """Steam deaerator feedwater, condensate, and makeup-water parameters."""

    feedwater_enthalpy: float
    condensate_enthalpy: float
    makeup_water_enthalpy: float
    vent_enthalpy: float
    condensate_return_fraction: float
    vent_fraction: float = 0.0

    def __post_init__(self) -> None:
        _require_positive(self.feedwater_enthalpy, "feedwater_enthalpy")
        _require_non_negative(self.condensate_enthalpy, "condensate_enthalpy")
        _require_non_negative(self.makeup_water_enthalpy, "makeup_water_enthalpy")
        _require_non_negative(self.vent_enthalpy, "vent_enthalpy")
        _require_fraction(
            self.condensate_return_fraction,
            "condensate_return_fraction",
        )
        _require_fraction(self.vent_fraction, "vent_fraction")


@dataclass(frozen=True)
class FlashSteamRecoveryLevel:
    """Saturated flash-steam properties for one steam level."""

    steam_level: str
    saturated_vapor_enthalpy: float
    saturated_liquid_enthalpy: float

    def __post_init__(self) -> None:
        _require_name(self.steam_level, "flash steam level")
        _require_positive(
            self.saturated_vapor_enthalpy,
            "saturated_vapor_enthalpy",
        )
        _require_non_negative(
            self.saturated_liquid_enthalpy,
            "saturated_liquid_enthalpy",
        )


@dataclass(frozen=True)
class FlashSteamRecoveryRoute:
    """Permitted condensate flash route from one steam level to another."""

    name: str
    source_level: str
    target_level: str
    max_flow: float

    def __post_init__(self) -> None:
        _require_name(self.name, "flash steam recovery route name")
        _require_name(self.source_level, "flash steam recovery source level")
        _require_name(self.target_level, "flash steam recovery target level")
        _require_positive(self.max_flow, "max_flow")
        if self.source_level == self.target_level:
            raise ValueError("flash recovery source_level and target_level must differ")


@dataclass(frozen=True)
class FlashSteamRecoveryConfig:
    """Flash steam recovery network for process-heating use only."""

    levels: tuple[FlashSteamRecoveryLevel, ...]
    routes: tuple[FlashSteamRecoveryRoute, ...]
    condensate_return_fraction: float

    def __post_init__(self) -> None:
        if not self.levels:
            raise ValueError("at least one flash steam recovery level is required")
        if not self.routes:
            raise ValueError("at least one flash steam recovery route is required")
        level_names = [level.steam_level for level in self.levels]
        if len(set(level_names)) != len(level_names):
            raise ValueError("flash steam recovery levels must be unique")
        route_names = [route.name for route in self.routes]
        if len(set(route_names)) != len(route_names):
            raise ValueError("flash steam recovery route names must be unique")
        configured_levels = set(level_names)
        for route in self.routes:
            if route.source_level not in configured_levels:
                raise ValueError(
                    f"flash route {route.name!r} references unconfigured source "
                    f"level {route.source_level!r}"
                )
            if route.target_level not in configured_levels:
                raise ValueError(
                    f"flash route {route.name!r} references unconfigured target "
                    f"level {route.target_level!r}"
                )
        _require_fraction(
            self.condensate_return_fraction,
            "condensate_return_fraction",
        )


@dataclass(frozen=True)
class CoolingWaterConfig:
    """Cooling-water utility cost and fixed-load parameters."""

    unit_cost: float
    process_cooling_load: float = 0.0
    utility_cooling_load: float = 0.0

    def __post_init__(self) -> None:
        _require_non_negative(self.unit_cost, "unit_cost")
        _require_non_negative(self.process_cooling_load, "process_cooling_load")
        _require_non_negative(self.utility_cooling_load, "utility_cooling_load")


@dataclass(frozen=True)
class HotOilConfig:
    """Fired hot-oil utility cost and heat-load parameters."""

    fuel_unit_cost: float
    thermal_efficiency: float
    high_temperature_heat_demand: float = 0.0
    supply_temperature: float | None = None

    def __post_init__(self) -> None:
        _require_non_negative(self.fuel_unit_cost, "fuel_unit_cost")
        _require_positive(self.thermal_efficiency, "thermal_efficiency")
        _require_non_negative(
            self.high_temperature_heat_demand,
            "high_temperature_heat_demand",
        )


@dataclass(frozen=True)
class EquipmentCost:
    """Annualized capital and maintenance cost coefficients for equipment."""

    name: str
    equipment_type: str
    equipment_name: str
    annualization_factor: float
    installation_factor: float
    variable_capital_cost: float
    fixed_capital_cost: float
    variable_maintenance_cost: float = 0.0
    fixed_maintenance_cost: float = 0.0

    def __post_init__(self) -> None:
        _require_name(self.name, "equipment cost name")
        _require_name(self.equipment_type, "equipment type")
        _require_name(self.equipment_name, "equipment name")
        _require_non_negative(self.annualization_factor, "annualization_factor")
        _require_non_negative(self.installation_factor, "installation_factor")
        _require_non_negative(self.variable_capital_cost, "variable_capital_cost")
        _require_non_negative(self.fixed_capital_cost, "fixed_capital_cost")
        _require_non_negative(
            self.variable_maintenance_cost,
            "variable_maintenance_cost",
        )
        _require_non_negative(
            self.fixed_maintenance_cost,
            "fixed_maintenance_cost",
        )


@dataclass(frozen=True)
class FuelCost:
    """Fuel operating cost coefficient for one fuel-consuming unit."""

    name: str
    equipment_type: str
    equipment_name: str
    unit_cost: float

    def __post_init__(self) -> None:
        _require_name(self.name, "fuel cost name")
        _require_name(self.equipment_type, "fuel cost equipment type")
        _require_name(self.equipment_name, "fuel cost equipment name")
        _require_non_negative(self.unit_cost, "unit_cost")


@dataclass(frozen=True)
class ElectricityCost:
    """Electricity import tariff and export revenue parameters."""

    import_unit_cost: float = 0.0
    export_unit_price: float = 0.0

    def __post_init__(self) -> None:
        _require_non_negative(self.import_unit_cost, "import_unit_cost")
        _require_non_negative(self.export_unit_price, "export_unit_price")


@dataclass(frozen=True)
class WaterCost:
    """Treated makeup-water unit cost."""

    unit_cost: float

    def __post_init__(self) -> None:
        _require_non_negative(self.unit_cost, "unit_cost")


@dataclass(frozen=True)
class SteamLevelCandidate:
    """Potential steam level located at a shifted-temperature interval."""

    name: str
    steam_main: str
    temperature: float
    source_heat_available: float
    sink_heat_demand: float
    generation_enthalpy_delta: float
    use_enthalpy_delta: float
    source_heat_upper_bound: float | None = None
    sink_heat_upper_bound: float | None = None
    steam_enthalpy_for_use: float | None = None
    generated_steam_enthalpy: float | None = None
    main_steam_enthalpy: float | None = None
    utility_steam_enthalpy: float | None = None
    feedwater_enthalpy: float = 0.0
    steam_flow_upper_bound: float | None = None
    annualized_level_cost: float = 0.0
    operating_cost_per_heat: float = 0.0

    def __post_init__(self) -> None:
        _require_name(self.name, "steam level name")
        _require_name(self.steam_main, "steam main")
        _require_positive(self.generation_enthalpy_delta, "generation_enthalpy_delta")
        _require_positive(self.use_enthalpy_delta, "use_enthalpy_delta")
        _require_non_negative(self.source_heat_available, "source_heat_available")
        _require_non_negative(self.sink_heat_demand, "sink_heat_demand")
        _require_non_negative(self.annualized_level_cost, "annualized_level_cost")
        _require_non_negative(self.operating_cost_per_heat, "operating_cost_per_heat")
        if self.source_heat_upper_bound is not None:
            _require_non_negative(
                self.source_heat_upper_bound, "source_heat_upper_bound"
            )
        if self.sink_heat_upper_bound is not None:
            _require_non_negative(self.sink_heat_upper_bound, "sink_heat_upper_bound")
        if self.steam_enthalpy_for_use is not None:
            _require_positive(self.steam_enthalpy_for_use, "steam_enthalpy_for_use")
        if self.generated_steam_enthalpy is not None:
            _require_positive(
                self.generated_steam_enthalpy,
                "generated_steam_enthalpy",
            )
        if self.main_steam_enthalpy is not None:
            _require_positive(self.main_steam_enthalpy, "main_steam_enthalpy")
        if self.utility_steam_enthalpy is not None:
            _require_positive(self.utility_steam_enthalpy, "utility_steam_enthalpy")
        _require_non_negative(self.feedwater_enthalpy, "feedwater_enthalpy")
        if self.steam_flow_upper_bound is not None:
            _require_non_negative(self.steam_flow_upper_bound, "steam_flow_upper_bound")


@dataclass(frozen=True)
class FuelConsumptionAccountingFactor:
    """Optional Table 2-9 fuel-consumption reporting factor for equipment."""

    equipment_type: str
    equipment_name: str
    factor: float

    def __post_init__(self) -> None:
        _require_name(self.equipment_type, "fuel factor equipment type")
        _require_name(self.equipment_name, "fuel factor equipment name")
        _require_positive(self.factor, "fuel consumption accounting factor")


@dataclass(frozen=True)
class OperatingCostAccountingAdjustment:
    """Optional Table 2-9 operating-cost accounting adjustment."""

    component: str
    amount: float

    def __post_init__(self) -> None:
        _require_name(self.component, "operating cost adjustment component")


@dataclass(frozen=True)
class UtilitySystemModelData:
    """Static utility-system model input data for Pyomo construction."""

    steam_mains: tuple[str, ...]
    steam_levels: tuple[SteamLevelCandidate, ...]
    power_demand: float
    vhp_headers: tuple[VhpSteamCandidate, ...] = ()
    vhp_sources: tuple[VhpSteamSourceCandidate, ...] = ()
    boilers: tuple[BoilerCandidate, ...] = ()
    vhp_turbines: tuple[VhpBackPressureTurbineCandidate, ...] = ()
    vhp_letdowns: tuple[VhpLetdownStationCandidate, ...] = ()
    steam_main_turbines: tuple[SteamMainBackPressureTurbineCandidate, ...] = ()
    steam_main_letdowns: tuple[SteamMainLetdownStationCandidate, ...] = ()
    gas_turbines: tuple[GasTurbineCandidate, ...] = ()
    hrsgs: tuple[HrsgCandidate, ...] = ()
    deaerator: DeaeratorConfig | None = None
    flash_steam_recovery: FlashSteamRecoveryConfig | None = None
    cooling_water: CoolingWaterConfig | None = None
    hot_oil: HotOilConfig | None = None
    equipment_costs: tuple[EquipmentCost, ...] = ()
    fuel_costs: tuple[FuelCost, ...] = ()
    electricity_cost: ElectricityCost | None = None
    water_cost: WaterCost | None = None
    grid_import_limit: float | None = None
    grid_export_limit: float | None = None
    operating_hours: float = 1.0
    cost_scale: float = 1.0
    transmission_efficiency: float = 1.0
    source_heat_loss_fraction: float = 0.0
    sink_heat_loss_fraction: float = 0.0
    utility_steam_flow_adjustment: float = 0.0
    fuel_consumption_factors: tuple[FuelConsumptionAccountingFactor, ...] = ()
    operating_cost_adjustments: tuple[OperatingCostAccountingAdjustment, ...] = ()
    thermal_nodes: tuple[ThermalNode, ...] = ()
    periods: tuple[OperatingPeriod, ...] = ()
    hpr_performance_maps: tuple[HprPerformanceMap, ...] = ()
    hpr_candidates: tuple[HprCandidate, ...] = ()

    def __post_init__(self) -> None:
        if not self.steam_mains:
            raise ValueError("at least one steam main is required")
        if not self.steam_levels:
            raise ValueError("at least one steam level candidate is required")
        for steam_main in self.steam_mains:
            _require_name(steam_main, "steam main")
        if len(set(self.steam_mains)) != len(self.steam_mains):
            raise ValueError("steam mains must be unique")

        level_names = [level.name for level in self.steam_levels]
        if len(set(level_names)) != len(level_names):
            raise ValueError("steam level candidate names must be unique")
        steam_main_set = set(self.steam_mains)
        for level in self.steam_levels:
            if level.steam_main not in steam_main_set:
                raise ValueError(
                    f"steam level {level.name!r} references unknown steam main "
                    f"{level.steam_main!r}"
                )
        _require_non_negative(self.power_demand, "power_demand")
        self._validate_vhp_headers()
        self._validate_vhp_sources()
        self._validate_boilers()
        self._validate_vhp_turbines()
        self._validate_vhp_letdowns()
        self._validate_steam_main_turbines()
        self._validate_steam_main_letdowns()
        self._validate_gas_turbines()
        self._validate_hrsgs()
        self._validate_flash_steam_recovery()
        self._validate_equipment_costs()
        self._validate_fuel_costs()
        if self.grid_import_limit is not None:
            _require_non_negative(self.grid_import_limit, "grid_import_limit")
        if self.grid_export_limit is not None:
            _require_non_negative(self.grid_export_limit, "grid_export_limit")
        _require_positive(self.operating_hours, "operating_hours")
        _require_positive(self.cost_scale, "cost_scale")
        _require_positive(self.transmission_efficiency, "transmission_efficiency")
        _require_fraction(self.source_heat_loss_fraction, "source_heat_loss_fraction")
        _require_fraction(self.sink_heat_loss_fraction, "sink_heat_loss_fraction")
        self._validate_fuel_consumption_factors()
        self._validate_operating_cost_adjustments()
        self._validate_periods()
        self._validate_thermal_nodes()
        self._validate_hpr_performance_maps()
        self._validate_hpr_candidates()

    def _validate_vhp_headers(self) -> None:
        header_names = [header.name for header in self.vhp_headers]
        if len(set(header_names)) != len(header_names):
            raise ValueError("VHP header names must be unique")

    def _validate_vhp_sources(self) -> None:
        source_names = [source.name for source in self.vhp_sources]
        if len(set(source_names)) != len(source_names):
            raise ValueError("VHP steam source names must be unique")
        header_names = {header.name for header in self.vhp_headers}
        for source in self.vhp_sources:
            if source.vhp_header not in header_names:
                raise ValueError(
                    f"VHP steam source {source.name!r} references unknown VHP "
                    f"header {source.vhp_header!r}"
                )

    def _validate_boilers(self) -> None:
        boiler_names = [boiler.name for boiler in self.boilers]
        if len(set(boiler_names)) != len(boiler_names):
            raise ValueError("boiler names must be unique")
        header_names = {header.name for header in self.vhp_headers}
        for boiler in self.boilers:
            if boiler.vhp_header not in header_names:
                raise ValueError(
                    f"boiler {boiler.name!r} references unknown VHP header "
                    f"{boiler.vhp_header!r}"
                )

    def _validate_vhp_turbines(self) -> None:
        turbine_names = [turbine.name for turbine in self.vhp_turbines]
        if len(set(turbine_names)) != len(turbine_names):
            raise ValueError("VHP turbine names must be unique")
        header_names = {header.name for header in self.vhp_headers}
        level_names = {level.name for level in self.steam_levels}
        for turbine in self.vhp_turbines:
            if turbine.vhp_header not in header_names:
                raise ValueError(
                    f"VHP turbine {turbine.name!r} references unknown VHP header "
                    f"{turbine.vhp_header!r}"
                )
            if turbine.steam_level not in level_names:
                raise ValueError(
                    f"VHP turbine {turbine.name!r} references unknown steam level "
                    f"{turbine.steam_level!r}"
                )

    def _validate_vhp_letdowns(self) -> None:
        letdown_names = [letdown.name for letdown in self.vhp_letdowns]
        if len(set(letdown_names)) != len(letdown_names):
            raise ValueError("VHP letdown names must be unique")
        header_names = {header.name for header in self.vhp_headers}
        level_names = {level.name for level in self.steam_levels}
        for letdown in self.vhp_letdowns:
            if letdown.vhp_header not in header_names:
                raise ValueError(
                    f"VHP letdown {letdown.name!r} references unknown VHP header "
                    f"{letdown.vhp_header!r}"
                )
            if letdown.steam_level not in level_names:
                raise ValueError(
                    f"VHP letdown {letdown.name!r} references unknown steam level "
                    f"{letdown.steam_level!r}"
                )

    def _validate_steam_main_turbines(self) -> None:
        turbine_names = [turbine.name for turbine in self.steam_main_turbines]
        if len(set(turbine_names)) != len(turbine_names):
            raise ValueError("steam-main turbine names must be unique")
        level_names = {level.name for level in self.steam_levels}
        for turbine in self.steam_main_turbines:
            if turbine.source_level not in level_names:
                raise ValueError(
                    f"steam-main turbine {turbine.name!r} references unknown "
                    f"source level {turbine.source_level!r}"
                )
            if turbine.target_level not in level_names:
                raise ValueError(
                    f"steam-main turbine {turbine.name!r} references unknown "
                    f"target level {turbine.target_level!r}"
                )

    def _validate_steam_main_letdowns(self) -> None:
        letdown_names = [letdown.name for letdown in self.steam_main_letdowns]
        if len(set(letdown_names)) != len(letdown_names):
            raise ValueError("steam-main letdown names must be unique")
        level_names = {level.name for level in self.steam_levels}
        for letdown in self.steam_main_letdowns:
            if letdown.source_level not in level_names:
                raise ValueError(
                    f"steam-main letdown {letdown.name!r} references unknown "
                    f"source level {letdown.source_level!r}"
                )
            if letdown.target_level not in level_names:
                raise ValueError(
                    f"steam-main letdown {letdown.name!r} references unknown "
                    f"target level {letdown.target_level!r}"
                )

    def _validate_gas_turbines(self) -> None:
        gas_turbine_names = [turbine.name for turbine in self.gas_turbines]
        if len(set(gas_turbine_names)) != len(gas_turbine_names):
            raise ValueError("gas turbine names must be unique")

    def _validate_hrsgs(self) -> None:
        hrsg_names = [hrsg.name for hrsg in self.hrsgs]
        if len(set(hrsg_names)) != len(hrsg_names):
            raise ValueError("HRSG names must be unique")
        gas_turbine_names = {turbine.name for turbine in self.gas_turbines}
        header_names = {header.name for header in self.vhp_headers}
        for hrsg in self.hrsgs:
            if hrsg.gas_turbine not in gas_turbine_names:
                raise ValueError(
                    f"HRSG {hrsg.name!r} references unknown gas turbine "
                    f"{hrsg.gas_turbine!r}"
                )
            if hrsg.vhp_header not in header_names:
                raise ValueError(
                    f"HRSG {hrsg.name!r} references unknown VHP header "
                    f"{hrsg.vhp_header!r}"
                )

    def _validate_flash_steam_recovery(self) -> None:
        if self.flash_steam_recovery is None:
            return
        level_names = {level.name for level in self.steam_levels}
        for level in self.flash_steam_recovery.levels:
            if level.steam_level not in level_names:
                raise ValueError(
                    f"flash steam recovery references unknown steam level "
                    f"{level.steam_level!r}"
                )

    def _validate_equipment_costs(self) -> None:
        cost_names = [cost.name for cost in self.equipment_costs]
        if len(set(cost_names)) != len(cost_names):
            raise ValueError("equipment cost names must be unique")
        equipment_targets = {
            "boiler": {boiler.name for boiler in self.boilers},
            "gas_turbine": {turbine.name for turbine in self.gas_turbines},
            "hpr": {candidate.name for candidate in self.hpr_candidates},
            "hot_oil_furnace": {"hot_oil"} if self.hot_oil is not None else set(),
            "hrsg": {hrsg.name for hrsg in self.hrsgs},
            "steam_main_turbine": {
                turbine.name for turbine in self.steam_main_turbines
            },
            "vhp_source": {source.name for source in self.vhp_sources},
            "vhp_turbine": {turbine.name for turbine in self.vhp_turbines},
        }
        for cost in self.equipment_costs:
            target_names = equipment_targets.get(cost.equipment_type)
            if target_names is None:
                raise ValueError(
                    f"unsupported equipment cost type {cost.equipment_type!r}"
                )
            if cost.equipment_name not in target_names:
                raise ValueError(
                    f"equipment cost {cost.name!r} references unknown "
                    f"{cost.equipment_type} {cost.equipment_name!r}"
                )

    def _validate_fuel_costs(self) -> None:
        cost_names = [cost.name for cost in self.fuel_costs]
        if len(set(cost_names)) != len(cost_names):
            raise ValueError("fuel cost names must be unique")
        boiler_names = {boiler.name for boiler in self.boilers}
        gas_turbine_names = {turbine.name for turbine in self.gas_turbines}
        hrsg_names = {hrsg.name for hrsg in self.hrsgs}
        vhp_source_names = {source.name for source in self.vhp_sources}
        for cost in self.fuel_costs:
            if cost.equipment_type == "boiler":
                if cost.equipment_name not in boiler_names:
                    raise ValueError(
                        f"fuel cost {cost.name!r} references unknown boiler "
                        f"{cost.equipment_name!r}"
                    )
            elif cost.equipment_type == "gas_turbine":
                if cost.equipment_name not in gas_turbine_names:
                    raise ValueError(
                        f"fuel cost {cost.name!r} references unknown gas turbine "
                        f"{cost.equipment_name!r}"
                    )
            elif cost.equipment_type == "hrsg_supplementary":
                if cost.equipment_name not in hrsg_names:
                    raise ValueError(
                        f"fuel cost {cost.name!r} references unknown HRSG "
                        f"{cost.equipment_name!r}"
                    )
            elif cost.equipment_type == "vhp_source":
                if cost.equipment_name not in vhp_source_names:
                    raise ValueError(
                        f"fuel cost {cost.name!r} references unknown VHP steam "
                        f"source {cost.equipment_name!r}"
                    )
            else:
                raise ValueError(f"unsupported fuel cost type {cost.equipment_type!r}")

    def _validate_fuel_consumption_factors(self) -> None:
        allowed_types = {
            "boiler",
            "gas_turbine",
            "hrsg_supplementary",
            "hot_oil",
            "vhp_source",
        }
        keys = []
        for factor in self.fuel_consumption_factors:
            if factor.equipment_type not in allowed_types:
                raise ValueError(
                    "fuel consumption factor equipment type must be one of "
                    f"{sorted(allowed_types)!r}"
                )
            keys.append((factor.equipment_type, factor.equipment_name))
        if len(set(keys)) != len(keys):
            raise ValueError("fuel consumption factor equipment targets must be unique")

    def _validate_operating_cost_adjustments(self) -> None:
        allowed_components = {"auxiliary_or_unallocated"}
        components = []
        for adjustment in self.operating_cost_adjustments:
            if adjustment.component not in allowed_components:
                raise ValueError(
                    "operating cost adjustment component must be one of "
                    f"{sorted(allowed_components)!r}"
                )
            components.append(adjustment.component)
        if len(set(components)) != len(components):
            raise ValueError("operating cost adjustment components must be unique")

    def _validate_periods(self) -> None:
        period_names = [period.name for period in self.periods]
        if len(set(period_names)) != len(period_names):
            raise ValueError("operating period names must be unique")

    def _validate_thermal_nodes(self) -> None:
        node_names = [node.name for node in self.thermal_nodes]
        if len(set(node_names)) != len(node_names):
            raise ValueError("thermal node names must be unique")
        node_name_set = set(node_names)
        for period in self.periods:
            for field_name, values in (
                ("source_heat_available", period.source_heat_available),
                ("heating_demand", period.heating_demand),
                ("cooling_demand", period.cooling_demand),
                ("rejection_capacity", period.rejection_capacity),
                ("node_temperatures", period.node_temperatures),
            ):
                for node_name in _mapping_keys(values):
                    if node_name not in node_name_set:
                        raise ValueError(
                            f"operating period {period.name!r} {field_name} "
                            f"references unknown thermal node {node_name!r}"
                        )

    def _validate_hpr_performance_maps(self) -> None:
        map_ids = [
            performance_map.map_id for performance_map in self.hpr_performance_maps
        ]
        if len(set(map_ids)) != len(map_ids):
            raise ValueError("HPR performance map IDs must be unique")

    def _validate_hpr_candidates(self) -> None:
        candidate_names = [candidate.name for candidate in self.hpr_candidates]
        if len(set(candidate_names)) != len(candidate_names):
            raise ValueError("HPR candidate names must be unique")
        node_names = {node.name for node in self.thermal_nodes}
        maps_by_id = {
            performance_map.map_id: performance_map
            for performance_map in self.hpr_performance_maps
        }
        for candidate in self.hpr_candidates:
            if candidate.map_id not in maps_by_id:
                raise ValueError(
                    f"HPR candidate {candidate.name!r} references unknown map "
                    f"{candidate.map_id!r}"
                )
            if candidate.mode != maps_by_id[candidate.map_id].mode:
                raise ValueError(
                    f"HPR candidate {candidate.name!r} mode does not match map "
                    f"{candidate.map_id!r}"
                )
            for label, node_name in (
                ("source_node", candidate.source_node),
                ("sink_node", candidate.sink_node),
                ("rejection_node", candidate.rejection_node),
            ):
                if node_name is not None and node_name not in node_names:
                    raise ValueError(
                        f"HPR candidate {candidate.name!r} {label} references "
                        f"unknown thermal node {node_name!r}"
                    )


def _require_name(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")


def _require_positive(value: float, label: str) -> None:
    _require_finite(value, label)
    if value <= 0.0:
        raise ValueError(f"{label} must be positive")


def _require_non_negative(value: float, label: str) -> None:
    _require_finite(value, label)
    if value < 0.0:
        raise ValueError(f"{label} must be non-negative")


def _require_fraction(value: float, label: str) -> None:
    _require_finite(value, label)
    if value < 0.0 or value >= 1.0:
        raise ValueError(f"{label} must be in the interval [0, 1)")


def _require_fraction_inclusive(value: float, label: str) -> None:
    _require_finite(value, label)
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{label} must be in the interval [0, 1]")


def _require_finite(value: float, label: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")


def _require_hpr_schema_version(value: str) -> None:
    _require_name(value, "HPR map schema_version")
    if value not in HPR_SCHEMA_VERSIONS:
        raise ValueError(
            f"HPR map schema_version must be one of {sorted(HPR_SCHEMA_VERSIONS)!r}"
        )


def _require_hpr_mode(value: str) -> None:
    if value not in HPR_MODES:
        raise ValueError(f"HPR mode must be one of {sorted(HPR_MODES)!r}")


def _require_reference_capacity_basis(value: str) -> None:
    if value not in HPR_REFERENCE_CAPACITY_BASES:
        raise ValueError(
            "HPR reference_capacity_basis must be one of "
            f"{sorted(HPR_REFERENCE_CAPACITY_BASES)!r}"
        )


def _require_hpr_cop_convention(value: str) -> None:
    if value not in HPR_COP_CONVENTIONS:
        raise ValueError(
            f"HPR cop_convention must be one of {sorted(HPR_COP_CONVENTIONS)!r}"
        )


def _validate_mode_capacity_basis(mode: str, basis: str) -> None:
    expected_basis = "q_sink" if mode == "heat_pump" else "q_source"
    if basis != expected_basis:
        raise ValueError(
            f"HPR {mode} reference_capacity_basis must be {expected_basis!r}"
        )


def _validate_mode_cop_convention(mode: str, convention: str) -> None:
    expected_convention = "heating" if mode == "heat_pump" else "cooling"
    if convention != expected_convention:
        raise ValueError(f"HPR {mode} cop_convention must be {expected_convention!r}")


def _require_non_negative_mapping(
    values: Mapping[str, float] | None,
    label: str,
) -> None:
    if values is None:
        return
    for key, value in values.items():
        _require_name(key, f"{label} key")
        _require_non_negative(value, f"{label} value")


def _require_finite_mapping(
    values: Mapping[str, float] | None,
    label: str,
) -> None:
    if values is None:
        return
    for key, value in values.items():
        _require_name(key, f"{label} key")
        _require_finite(value, f"{label} value")


def _mapping_keys(values: Mapping[str, object] | None) -> tuple[str, ...]:
    if values is None:
        return ()
    return tuple(values.keys())


def _validate_hpr_units(units: Mapping[str, str]) -> None:
    missing_units = sorted(set(HPR_REQUIRED_UNITS).difference(units))
    if missing_units:
        raise ValueError(f"HPR map units are missing {missing_units!r}")
    unknown_units = sorted(set(units).difference(HPR_REQUIRED_UNITS))
    if unknown_units:
        raise ValueError(f"HPR map units include unknown keys {unknown_units!r}")
    for key, expected_value in HPR_REQUIRED_UNITS.items():
        value = units[key]
        _require_name(key, "HPR unit key")
        _require_name(value, f"HPR unit {key!r}")
        if value != expected_value:
            raise ValueError(
                f"HPR map unit {key!r} must be {expected_value!r}, got {value!r}"
            )


def _validate_hpr_energy_balance(
    point: HprPerformancePoint,
    tolerance: float,
) -> None:
    residual = abs(point.q_sink - point.q_source - point.electric_power)
    if residual > tolerance:
        raise ValueError(
            f"HPR performance point {point.name!r} violates "
            "q_sink = q_source + electric_power"
        )


def _validate_hpr_cop(
    point: HprPerformancePoint,
    convention: str,
    tolerance: float,
) -> None:
    if point.cop is None:
        return
    useful_duty = point.q_sink if convention == "heating" else point.q_source
    residual = abs(point.cop - useful_duty / point.electric_power)
    if residual > tolerance:
        raise ValueError(
            f"HPR performance point {point.name!r} violates {convention} COP"
        )


def _validate_hpr_reference_capacity_point(
    point: HprPerformancePoint,
    reference_capacity: float,
    basis: str,
    tolerance: float,
) -> None:
    useful_duty = point.q_sink if basis == "q_sink" else point.q_source
    expected = point.load_fraction * reference_capacity
    if abs(useful_duty - expected) > tolerance:
        raise ValueError(
            f"HPR performance point {point.name!r} {basis} must equal "
            "load_fraction * reference_capacity"
        )


def _validate_hpr_ordered_curves(points: tuple[HprPerformancePoint, ...]) -> None:
    coordinate_keys = [
        (
            point.curve_id,
            point.source_temperature,
            point.sink_temperature,
            point.load_fraction,
        )
        for point in points
    ]
    if len(set(coordinate_keys)) != len(coordinate_keys):
        raise ValueError("HPR performance point coordinates must be unique")

    points_by_curve: dict[str, list[HprPerformancePoint]] = {}
    for point in points:
        points_by_curve.setdefault(point.curve_id, []).append(point)
    for curve_id, curve_points in points_by_curve.items():
        source_temperatures = {point.source_temperature for point in curve_points}
        sink_temperatures = {point.sink_temperature for point in curve_points}
        if len(source_temperatures) != 1 or len(sink_temperatures) != 1:
            raise ValueError(
                f"HPR curve {curve_id!r} must use one source/sink temperature pair"
            )
        load_fractions = [point.load_fraction for point in curve_points]
        if any(
            current >= next_value
            for current, next_value in zip(load_fractions, load_fractions[1:])
        ):
            raise ValueError(
                f"HPR curve {curve_id!r} load_fraction values must be strictly "
                "increasing"
            )


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _required_mapping(values: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = values.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"HPR performance map {key} must be a mapping")
    return dict(value)


def _required_string_mapping(values: Mapping[str, Any], key: str) -> Mapping[str, str]:
    value = _required_mapping(values, key)
    for item_key, item_value in value.items():
        if not isinstance(item_key, str) or not isinstance(item_value, str):
            raise ValueError(f"HPR performance map {key} must be a string mapping")
    return dict(value)


def _required_string(values: Mapping[str, Any], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str):
        raise ValueError(f"HPR performance map {key} must be a string")
    return value


def _reject_unknown_keys(
    values: Mapping[str, Any],
    allowed_keys: set[str],
    label: str,
) -> None:
    unknown_keys = sorted(set(values).difference(allowed_keys))
    if unknown_keys:
        raise ValueError(f"{label} includes unknown keys {unknown_keys!r}")
