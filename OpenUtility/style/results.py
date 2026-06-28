"""Result extraction and benchmark comparison helpers for STYLE models."""

from __future__ import annotations

from dataclasses import dataclass

import pyomo.environ as pyo

from OpenUtility.benchmarks import Contribution2BestConfiguration, ThesisStyleResult


@dataclass(frozen=True)
class StaticStyleResult:
    """Compact solved-result summary for a static STYLE model."""

    case_study: str
    scenario: str
    utility_steam_flow: float
    fuel_consumption: float
    power_generation: float
    steam_turbine_power: float
    gas_turbine_power: float
    operating_cost: float
    maintenance_cost: float
    capital_cost: float
    total_annualized_cost: float
    fuel_cost: float | None = None
    hot_oil_operating_cost: float | None = None


@dataclass(frozen=True)
class StaticStyleFuelConsumptionFamily:
    """Fuel consumption attributed to one STYLE equipment family."""

    equipment_family: str
    fuel_consumption: float
    included_in_table_fuel_consumption: bool


@dataclass(frozen=True)
class StaticStyleFuelConsumptionEquipment:
    """Fuel consumption attributed to one STYLE equipment item."""

    equipment_family: str
    equipment_name: str
    fuel_variable: str
    fuel_multiplier: float
    fuel_consumption: float
    included_in_table_fuel_consumption: bool


@dataclass(frozen=True)
class StaticStyleFuelCapacityContext:
    """Capacity context for one STYLE fuel-consuming equipment item."""

    equipment_family: str
    equipment_name: str
    selection_variable: str | None
    selected: bool | None
    capacity_basis: str | None
    actual_capacity_basis_value: float | None
    capacity_value: float | None
    capacity_utilization: float | None


@dataclass(frozen=True)
class StaticStyleOperatingCostComponent:
    """Operating cost attributed to one reportable STYLE component bucket."""

    component: str
    operating_cost: float


@dataclass(frozen=True)
class StaticStyleBenchmarkDeviation:
    """Field-level deviation between extracted and benchmark STYLE results."""

    field: str
    actual: float
    benchmark: float
    absolute_deviation: float
    within_tolerance: bool


@dataclass(frozen=True)
class StaticStyleBenchmarkComparison:
    """Comparison of an extracted static STYLE result against a thesis benchmark."""

    actual: StaticStyleResult
    benchmark: ThesisStyleResult
    deviations: tuple[StaticStyleBenchmarkDeviation, ...]

    @property
    def within_tolerance(self) -> bool:
        """Whether all compared fields are within tolerance."""

        return all(deviation.within_tolerance for deviation in self.deviations)

    @property
    def max_absolute_deviation(self) -> float:
        """Largest absolute field deviation."""

        return max(
            (deviation.absolute_deviation for deviation in self.deviations),
            default=0.0,
        )

    def deviation_for(self, field: str) -> StaticStyleBenchmarkDeviation:
        """Return the deviation record for a named field."""

        for deviation in self.deviations:
            if deviation.field == field:
                return deviation
        raise KeyError(f"No benchmark deviation for field {field!r}.")


@dataclass(frozen=True)
class StaticStyleBestConfigurationComparison:
    """Comparison against a Contribution 2 case-study 2 configuration row."""

    actual: StaticStyleResult
    benchmark: Contribution2BestConfiguration
    deviations: tuple[StaticStyleBenchmarkDeviation, ...]

    @property
    def within_tolerance(self) -> bool:
        """Whether all compared fields are within tolerance."""

        return all(deviation.within_tolerance for deviation in self.deviations)

    @property
    def max_absolute_deviation(self) -> float:
        """Largest absolute field deviation."""

        return max(
            (deviation.absolute_deviation for deviation in self.deviations),
            default=0.0,
        )

    def deviation_for(self, field: str) -> StaticStyleBenchmarkDeviation:
        """Return the deviation record for a named field."""

        for deviation in self.deviations:
            if deviation.field == field:
                return deviation
        raise KeyError(f"No best-configuration deviation for field {field!r}.")


def extract_static_style_result(
    model: pyo.ConcreteModel,
    *,
    case_study: str,
    scenario: str,
) -> StaticStyleResult:
    """Extract a compact static STYLE result summary from a solved Pyomo model."""

    steam_turbine_power = _sum_component(model, "vhp_turbine_power_generation") + (
        _sum_component(model, "steam_main_turbine_power_generation")
    )
    gas_turbine_power = _sum_component(model, "gas_turbine_power_generation")
    power_generation = _value_or_sum(
        model,
        "onsite_power_generation",
        steam_turbine_power + gas_turbine_power,
    )
    capital_cost = _component_value(model, "total_annualized_capital_cost")
    maintenance_cost = _component_value(model, "total_equipment_maintenance_cost")
    operating_cost = _operating_cost(model)
    return StaticStyleResult(
        case_study=case_study,
        scenario=scenario,
        utility_steam_flow=(
            _sum_component(model, "utility_steam_to_header")
            + _component_value(model, "utility_steam_flow_adjustment")
        ),
        fuel_consumption=_fuel_consumption(model),
        power_generation=power_generation,
        steam_turbine_power=steam_turbine_power,
        gas_turbine_power=gas_turbine_power,
        operating_cost=operating_cost,
        maintenance_cost=maintenance_cost,
        capital_cost=capital_cost,
        total_annualized_cost=_component_value(model, "total_annualized_cost"),
        fuel_cost=_component_value(model, "total_fuel_operating_cost"),
        hot_oil_operating_cost=_component_value(model, "hot_oil_operating_cost"),
    )


def static_style_fuel_consumption_by_family(
    model: pyo.ConcreteModel,
) -> tuple[StaticStyleFuelConsumptionFamily, ...]:
    """Return model fuel consumption grouped by equipment family."""

    boiler = _sum_component_with_factor(
        model,
        "boiler_fuel_consumption",
        "boiler_fuel_consumption_factor",
    )
    gas_turbine = _sum_indexed_product(
        model,
        "gas_turbine_fuel_flow",
        "gas_turbine_fuel_lhv",
        factor_name="gas_turbine_fuel_consumption_factor",
    )
    hrsg_supplementary = _sum_indexed_product(
        model,
        "hrsg_supplementary_fuel_flow",
        "hrsg_supplementary_fuel_lhv",
        factor_name="hrsg_supplementary_fuel_consumption_factor",
    )
    vhp_source = _sum_component_with_factor(
        model,
        "vhp_source_fuel_consumption",
        "vhp_source_fuel_consumption_factor",
    )
    table_total = boiler + gas_turbine + hrsg_supplementary + vhp_source
    return (
        StaticStyleFuelConsumptionFamily(
            equipment_family="boiler",
            fuel_consumption=boiler,
            included_in_table_fuel_consumption=True,
        ),
        StaticStyleFuelConsumptionFamily(
            equipment_family="gas_turbine",
            fuel_consumption=gas_turbine,
            included_in_table_fuel_consumption=True,
        ),
        StaticStyleFuelConsumptionFamily(
            equipment_family="hrsg_supplementary",
            fuel_consumption=hrsg_supplementary,
            included_in_table_fuel_consumption=True,
        ),
        StaticStyleFuelConsumptionFamily(
            equipment_family="vhp_source",
            fuel_consumption=vhp_source,
            included_in_table_fuel_consumption=True,
        ),
        StaticStyleFuelConsumptionFamily(
            equipment_family="hot_oil",
            fuel_consumption=_sum_component_with_factor(
                model,
                "hot_oil_fuel_consumption",
                "hot_oil_fuel_consumption_factor",
            ),
            included_in_table_fuel_consumption=False,
        ),
        StaticStyleFuelConsumptionFamily(
            equipment_family="table_total",
            fuel_consumption=table_total,
            included_in_table_fuel_consumption=True,
        ),
    )


def static_style_fuel_consumption_by_equipment(
    model: pyo.ConcreteModel,
) -> tuple[StaticStyleFuelConsumptionEquipment, ...]:
    """Return model fuel consumption by individual equipment item."""

    rows: list[StaticStyleFuelConsumptionEquipment] = []
    rows.extend(
        _indexed_fuel_consumption_equipment(
            model,
            equipment_family="boiler",
            variable_name="boiler_fuel_consumption",
            factor_name="boiler_fuel_consumption_factor",
            included_in_table_fuel_consumption=True,
        ),
    )
    rows.extend(
        _indexed_product_fuel_consumption_equipment(
            model,
            equipment_family="gas_turbine",
            variable_name="gas_turbine_fuel_flow",
            parameter_name="gas_turbine_fuel_lhv",
            factor_name="gas_turbine_fuel_consumption_factor",
            included_in_table_fuel_consumption=True,
        ),
    )
    rows.extend(
        _indexed_product_fuel_consumption_equipment(
            model,
            equipment_family="hrsg_supplementary",
            variable_name="hrsg_supplementary_fuel_flow",
            parameter_name="hrsg_supplementary_fuel_lhv",
            factor_name="hrsg_supplementary_fuel_consumption_factor",
            included_in_table_fuel_consumption=True,
        ),
    )
    rows.extend(
        _indexed_fuel_consumption_equipment(
            model,
            equipment_family="vhp_source",
            variable_name="vhp_source_fuel_consumption",
            factor_name="vhp_source_fuel_consumption_factor",
            included_in_table_fuel_consumption=True,
        ),
    )
    hot_oil_row = _scalar_fuel_consumption_equipment(
        model,
        equipment_family="hot_oil",
        equipment_name="hot_oil_furnace",
        variable_name="hot_oil_fuel_consumption",
        factor_name="hot_oil_fuel_consumption_factor",
        included_in_table_fuel_consumption=False,
    )
    if hot_oil_row is not None:
        rows.append(hot_oil_row)
    return tuple(rows)


def static_style_fuel_capacity_context_by_equipment(
    model: pyo.ConcreteModel,
) -> tuple[StaticStyleFuelCapacityContext, ...]:
    """Return capacity context for individual fuel-consuming equipment."""

    rows: list[StaticStyleFuelCapacityContext] = []
    rows.extend(_boiler_fuel_capacity_context_rows(model))
    rows.extend(
        _indexed_product_fuel_capacity_context_rows(
            model,
            equipment_family="gas_turbine",
            variable_name="gas_turbine_fuel_flow",
            parameter_name="gas_turbine_fuel_lhv",
            capacity_parameter_name="gas_turbine_max_fuel_flow",
            selection_variable_name="gas_turbine_selected",
        ),
    )
    rows.extend(
        _indexed_product_fuel_capacity_context_rows(
            model,
            equipment_family="hrsg_supplementary",
            variable_name="hrsg_supplementary_fuel_flow",
            parameter_name="hrsg_supplementary_fuel_lhv",
            capacity_parameter_name="hrsg_max_supplementary_fuel_flow",
            selection_variable_name="hrsg_supplementary_firing_selected",
        ),
    )
    rows.extend(_vhp_source_fuel_capacity_context_rows(model))
    hot_oil_row = _hot_oil_fuel_capacity_context_row(model)
    if hot_oil_row is not None:
        rows.append(hot_oil_row)
    return tuple(rows)


def static_style_operating_cost_components(
    model: pyo.ConcreteModel,
) -> tuple[StaticStyleOperatingCostComponent, ...]:
    """Return reportable operating-cost component buckets."""

    fuel = _component_value(model, "total_fuel_operating_cost")
    hot_oil = _component_value(model, "hot_oil_operating_cost")
    electricity = _component_value(model, "electricity_operating_cost")
    total = _operating_cost(model)
    auxiliary = total - fuel - hot_oil - electricity
    return (
        StaticStyleOperatingCostComponent("fuel", fuel),
        StaticStyleOperatingCostComponent("hot_oil", hot_oil),
        StaticStyleOperatingCostComponent("electricity", electricity),
        StaticStyleOperatingCostComponent("auxiliary_or_unallocated", auxiliary),
        StaticStyleOperatingCostComponent("total", total),
    )


def compare_static_style_result_to_benchmark(
    result: StaticStyleResult,
    benchmark: ThesisStyleResult,
    *,
    absolute_tolerance: float = 1e-6,
) -> StaticStyleBenchmarkComparison:
    """Compare extracted static STYLE values against a thesis benchmark row."""

    if result.case_study != benchmark.case_study or result.scenario != benchmark.scenario:
        raise ValueError("result and benchmark identify different STYLE scenarios")
    fields = (
        "utility_steam_flow",
        "fuel_consumption",
        "power_generation",
        "operating_cost",
        "maintenance_cost",
        "capital_cost",
        "total_annualized_cost",
    )
    deviations = tuple(
        _benchmark_deviation(
            field,
            getattr(result, field),
            _benchmark_value(benchmark, field),
            absolute_tolerance,
        )
        for field in fields
        if _benchmark_value(benchmark, field) is not None
    )
    return StaticStyleBenchmarkComparison(
        actual=result,
        benchmark=benchmark,
        deviations=deviations,
    )


def compare_static_style_result_to_best_configuration(
    result: StaticStyleResult,
    benchmark: Contribution2BestConfiguration,
    *,
    absolute_tolerance: float = 1e-6,
) -> StaticStyleBestConfigurationComparison:
    """Compare extracted STYLE values to a Contribution 2 best-configuration row."""

    fields = (
        ("utility_steam_flow", "utility_steam_generation"),
        ("fuel_consumption", "fuel_consumption"),
        ("power_generation", "power_generation"),
        ("steam_turbine_power", "steam_turbine_power"),
        ("gas_turbine_power", "gas_turbine_power"),
        ("operating_cost", "operating_cost"),
        ("maintenance_cost", "maintenance_cost"),
        ("capital_cost", "capital_cost"),
        ("total_annualized_cost", "total_cost"),
    )
    deviations = tuple(
        _benchmark_deviation(
            result_field,
            getattr(result, result_field),
            getattr(benchmark, benchmark_field),
            absolute_tolerance,
        )
        for result_field, benchmark_field in fields
    ) + tuple(
        _benchmark_deviation(
            result_field,
            actual,
            benchmark_value,
            absolute_tolerance,
        )
        for result_field, benchmark_field in (
            ("fuel_cost", "fuel_cost"),
            ("hot_oil_operating_cost", "hot_oil_operating_cost"),
        )
        if (actual := getattr(result, result_field)) is not None
        if (benchmark_value := getattr(benchmark, benchmark_field)) is not None
    )
    return StaticStyleBestConfigurationComparison(
        actual=result,
        benchmark=benchmark,
        deviations=deviations,
    )


def _benchmark_deviation(
    field: str,
    actual: float,
    benchmark: float,
    absolute_tolerance: float,
) -> StaticStyleBenchmarkDeviation:
    absolute_deviation = abs(actual - benchmark)
    return StaticStyleBenchmarkDeviation(
        field=field,
        actual=actual,
        benchmark=benchmark,
        absolute_deviation=absolute_deviation,
        within_tolerance=absolute_deviation <= absolute_tolerance,
    )


def _benchmark_value(benchmark: ThesisStyleResult, field: str) -> float | None:
    value = getattr(benchmark, field)
    return None if value is None else float(value)


def _operating_cost(model: pyo.ConcreteModel) -> float:
    level_operating_cost = sum(
        _component_value(model, "operating_cost_per_heat", level)
        * _component_value(model, "source_heat_to_steam", level)
        for level in _set_items(model, "STEAM_LEVELS")
    )
    return (
        level_operating_cost
        + _component_value(model, "total_fuel_operating_cost")
        + _component_value(model, "cooling_water_operating_cost")
        + _component_value(model, "hot_oil_operating_cost")
        + _component_value(model, "electricity_operating_cost")
        + _component_value(model, "water_operating_cost")
        + _component_value(model, "auxiliary_operating_cost_adjustment")
    )


def _fuel_consumption(model: pyo.ConcreteModel) -> float:
    return (
        _sum_component_with_factor(
            model,
            "vhp_source_fuel_consumption",
            "vhp_source_fuel_consumption_factor",
        )
        + _sum_component_with_factor(
            model,
            "boiler_fuel_consumption",
            "boiler_fuel_consumption_factor",
        )
        + _sum_indexed_product(
            model,
            "gas_turbine_fuel_flow",
            "gas_turbine_fuel_lhv",
            factor_name="gas_turbine_fuel_consumption_factor",
        )
        + _sum_indexed_product(
            model,
            "hrsg_supplementary_fuel_flow",
            "hrsg_supplementary_fuel_lhv",
            factor_name="hrsg_supplementary_fuel_consumption_factor",
        )
    )


def _value_or_sum(
    model: pyo.ConcreteModel,
    component_name: str,
    fallback: float,
) -> float:
    value = _component_value_or_none(model, component_name)
    return fallback if value is None else value


def _sum_component(model: pyo.ConcreteModel, component_name: str) -> float:
    if not hasattr(model, component_name):
        return 0.0
    component = getattr(model, component_name)
    if not component.is_indexed():
        value = _component_value_or_none(model, component_name)
        return 0.0 if value is None else value
    return sum(
        _component_value(model, component_name, index)
        for index in component
    )


def _sum_component_with_factor(
    model: pyo.ConcreteModel,
    component_name: str,
    factor_name: str,
) -> float:
    if not hasattr(model, component_name):
        return 0.0
    component = getattr(model, component_name)
    if not component.is_indexed():
        value = _component_value_or_none(model, component_name)
        return 0.0 if value is None else value * _fuel_consumption_factor(
            model,
            factor_name,
        )
    return sum(
        _component_value(model, component_name, index)
        * _fuel_consumption_factor(model, factor_name, index)
        for index in component
    )


def _sum_indexed_product(
    model: pyo.ConcreteModel,
    variable_name: str,
    parameter_name: str,
    *,
    factor_name: str | None = None,
) -> float:
    if not hasattr(model, variable_name):
        return 0.0
    variable = getattr(model, variable_name)
    if not variable.is_indexed():
        factor = 1.0 if factor_name is None else _fuel_consumption_factor(
            model,
            factor_name,
        )
        return (
            _component_value(model, variable_name)
            * _component_value(model, parameter_name)
            * factor
        )
    return sum(
        _component_value(model, variable_name, index)
        * _component_value(model, parameter_name, index)
        * (
            1.0
            if factor_name is None
            else _fuel_consumption_factor(model, factor_name, index)
        )
        for index in variable
    )


def _indexed_fuel_consumption_equipment(
    model: pyo.ConcreteModel,
    *,
    equipment_family: str,
    variable_name: str,
    factor_name: str,
    included_in_table_fuel_consumption: bool,
) -> tuple[StaticStyleFuelConsumptionEquipment, ...]:
    return tuple(
        StaticStyleFuelConsumptionEquipment(
            equipment_family=equipment_family,
            equipment_name=_format_index(index),
            fuel_variable=_component_label(variable_name, index),
            fuel_multiplier=_fuel_consumption_factor(model, factor_name, index),
            fuel_consumption=_component_value(model, variable_name, index)
            * _fuel_consumption_factor(model, factor_name, index),
            included_in_table_fuel_consumption=included_in_table_fuel_consumption,
        )
        for index in _indexed_component_indices(model, variable_name)
    )


def _indexed_product_fuel_consumption_equipment(
    model: pyo.ConcreteModel,
    *,
    equipment_family: str,
    variable_name: str,
    parameter_name: str,
    factor_name: str,
    included_in_table_fuel_consumption: bool,
) -> tuple[StaticStyleFuelConsumptionEquipment, ...]:
    return tuple(
        _indexed_product_fuel_consumption_equipment_row(
            model,
            equipment_family=equipment_family,
            variable_name=variable_name,
            parameter_name=parameter_name,
            factor_name=factor_name,
            index=index,
            included_in_table_fuel_consumption=included_in_table_fuel_consumption,
        )
        for index in _indexed_component_indices(model, variable_name)
    )


def _indexed_product_fuel_consumption_equipment_row(
    model: pyo.ConcreteModel,
    *,
    equipment_family: str,
    variable_name: str,
    parameter_name: str,
    factor_name: str,
    index: object,
    included_in_table_fuel_consumption: bool,
) -> StaticStyleFuelConsumptionEquipment:
    multiplier = _component_value(model, parameter_name, index) * (
        _fuel_consumption_factor(model, factor_name, index)
    )
    return StaticStyleFuelConsumptionEquipment(
        equipment_family=equipment_family,
        equipment_name=_format_index(index),
        fuel_variable=_component_label(variable_name, index),
        fuel_multiplier=multiplier,
        fuel_consumption=_component_value(model, variable_name, index) * multiplier,
        included_in_table_fuel_consumption=included_in_table_fuel_consumption,
    )


def _boiler_fuel_capacity_context_rows(
    model: pyo.ConcreteModel,
) -> tuple[StaticStyleFuelCapacityContext, ...]:
    return tuple(
        StaticStyleFuelCapacityContext(
            equipment_family="boiler",
            equipment_name=_format_index(index),
            selection_variable=_component_label("boiler_selected", index),
            selected=_component_bool_value(model, "boiler_selected", index),
            capacity_basis="steam_generation",
            actual_capacity_basis_value=_component_value_or_none(
                model,
                "boiler_steam_generation",
                index,
            ),
            capacity_value=_component_value_or_none(
                model,
                "boiler_max_capacity",
                index,
            ),
            capacity_utilization=_capacity_utilization(
                _component_value_or_none(model, "boiler_steam_generation", index),
                _component_value_or_none(model, "boiler_max_capacity", index),
            ),
        )
        for index in _indexed_component_indices(model, "boiler_fuel_consumption")
        if hasattr(model, "boiler_steam_generation")
    )


def _indexed_product_fuel_capacity_context_rows(
    model: pyo.ConcreteModel,
    *,
    equipment_family: str,
    variable_name: str,
    parameter_name: str,
    capacity_parameter_name: str,
    selection_variable_name: str,
) -> tuple[StaticStyleFuelCapacityContext, ...]:
    return tuple(
        _indexed_product_fuel_capacity_context_row(
            model,
            equipment_family=equipment_family,
            variable_name=variable_name,
            parameter_name=parameter_name,
            capacity_parameter_name=capacity_parameter_name,
            selection_variable_name=selection_variable_name,
            index=index,
        )
        for index in _indexed_component_indices(model, variable_name)
        if hasattr(model, capacity_parameter_name)
    )


def _indexed_product_fuel_capacity_context_row(
    model: pyo.ConcreteModel,
    *,
    equipment_family: str,
    variable_name: str,
    parameter_name: str,
    capacity_parameter_name: str,
    selection_variable_name: str,
    index: object,
) -> StaticStyleFuelCapacityContext:
    multiplier = _component_value(model, parameter_name, index)
    actual = _component_value(model, variable_name, index) * multiplier
    capacity = _component_value(model, capacity_parameter_name, index) * multiplier
    return StaticStyleFuelCapacityContext(
        equipment_family=equipment_family,
        equipment_name=_format_index(index),
        selection_variable=_component_label(selection_variable_name, index),
        selected=_component_bool_value(model, selection_variable_name, index),
        capacity_basis="fuel_consumption",
        actual_capacity_basis_value=actual,
        capacity_value=capacity,
        capacity_utilization=_capacity_utilization(actual, capacity),
    )


def _vhp_source_fuel_capacity_context_rows(
    model: pyo.ConcreteModel,
) -> tuple[StaticStyleFuelCapacityContext, ...]:
    return tuple(
        _vhp_source_fuel_capacity_context_row(model, index)
        for index in _indexed_component_indices(model, "vhp_source_fuel_consumption")
        if hasattr(model, "vhp_source_max_capacity")
    )


def _vhp_source_fuel_capacity_context_row(
    model: pyo.ConcreteModel,
    index: object,
) -> StaticStyleFuelCapacityContext:
    actual = _component_value(model, "vhp_source_fuel_consumption", index)
    capacity = _component_value(model, "vhp_source_max_capacity", index) * (
        _component_value(model, "vhp_source_fuel_consumption_per_steam", index)
    )
    return StaticStyleFuelCapacityContext(
        equipment_family="vhp_source",
        equipment_name=_format_index(index),
        selection_variable=_component_label("vhp_source_selected", index),
        selected=_component_bool_value(model, "vhp_source_selected", index),
        capacity_basis="fuel_consumption",
        actual_capacity_basis_value=actual,
        capacity_value=capacity,
        capacity_utilization=_capacity_utilization(actual, capacity),
    )


def _hot_oil_fuel_capacity_context_row(
    model: pyo.ConcreteModel,
) -> StaticStyleFuelCapacityContext | None:
    if not hasattr(model, "hot_oil_fuel_consumption"):
        return None
    return StaticStyleFuelCapacityContext(
        equipment_family="hot_oil",
        equipment_name="hot_oil_furnace",
        selection_variable="hot_oil_furnace_selected"
        if hasattr(model, "hot_oil_furnace_selected")
        else None,
        selected=_component_bool_value(model, "hot_oil_furnace_selected"),
        capacity_basis="heat_load",
        actual_capacity_basis_value=_component_value_or_none(
            model,
            "total_hot_oil_heat_load",
        ),
        capacity_value=None,
        capacity_utilization=None,
    )


def _component_bool_value(
    model: pyo.ConcreteModel,
    component_name: str,
    index: object | None = None,
) -> bool | None:
    if not hasattr(model, component_name):
        return None
    value = _component_value_or_none(model, component_name, index)
    if value is None:
        return None
    return value >= 0.5


def _capacity_utilization(
    actual: float | None,
    capacity: float | None,
) -> float | None:
    if actual is None or capacity is None or capacity == 0.0:
        return None
    return actual / capacity


def _scalar_fuel_consumption_equipment(
    model: pyo.ConcreteModel,
    *,
    equipment_family: str,
    equipment_name: str,
    variable_name: str,
    factor_name: str,
    included_in_table_fuel_consumption: bool,
) -> StaticStyleFuelConsumptionEquipment | None:
    if not hasattr(model, variable_name):
        return None
    return StaticStyleFuelConsumptionEquipment(
        equipment_family=equipment_family,
        equipment_name=equipment_name,
        fuel_variable=variable_name,
        fuel_multiplier=_fuel_consumption_factor(model, factor_name),
        fuel_consumption=_component_value(model, variable_name)
        * _fuel_consumption_factor(model, factor_name),
        included_in_table_fuel_consumption=included_in_table_fuel_consumption,
    )


def _indexed_component_indices(
    model: pyo.ConcreteModel,
    component_name: str,
) -> tuple[object, ...]:
    if not hasattr(model, component_name):
        return ()
    component = getattr(model, component_name)
    if not component.is_indexed():
        return ()
    return tuple(component)


def _component_label(component_name: str, index: object) -> str:
    return f"{component_name}[{_format_index(index)}]"


def _format_index(index: object) -> str:
    if isinstance(index, tuple):
        return ",".join(str(part) for part in index)
    return str(index)


def _fuel_consumption_factor(
    model: pyo.ConcreteModel,
    factor_name: str,
    index: object | None = None,
) -> float:
    if not hasattr(model, factor_name):
        return 1.0
    return _component_value(model, factor_name, index)


def _set_items(model: pyo.ConcreteModel, set_name: str) -> tuple[object, ...]:
    if not hasattr(model, set_name):
        return ()
    return tuple(getattr(model, set_name).data())


def _component_value(
    model: pyo.ConcreteModel,
    component_name: str,
    index: object | None = None,
) -> float:
    value = _component_value_or_none(model, component_name, index)
    if value is None:
        label = component_name if index is None else f"{component_name}[{index!r}]"
        raise ValueError(f"model component {label} has no value")
    return value


def _component_value_or_none(
    model: pyo.ConcreteModel,
    component_name: str,
    index: object | None = None,
) -> float | None:
    if not hasattr(model, component_name):
        return 0.0
    component = getattr(model, component_name)
    item = component if index is None else component[index]
    value = pyo.value(item, exception=False)
    return None if value is None else float(value)
