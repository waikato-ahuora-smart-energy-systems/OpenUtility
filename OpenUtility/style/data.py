"""Typed inputs for the STYLE static synthesis model."""

from __future__ import annotations

from dataclasses import dataclass


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
            _require_non_negative(self.source_heat_upper_bound, "source_heat_upper_bound")
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
class StyleModelData:
    """Static STYLE model input data for Pyomo construction."""

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


def _require_name(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")


def _require_positive(value: float, label: str) -> None:
    if value <= 0.0:
        raise ValueError(f"{label} must be positive")


def _require_non_negative(value: float, label: str) -> None:
    if value < 0.0:
        raise ValueError(f"{label} must be non-negative")


def _require_fraction(value: float, label: str) -> None:
    if value < 0.0 or value >= 1.0:
        raise ValueError(f"{label} must be in the interval [0, 1)")
