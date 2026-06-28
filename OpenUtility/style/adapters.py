"""Adapters from OpenUtility thermal profiles into STYLE model data."""

from __future__ import annotations

from ..thermal import HeatIntervalProfile
from .data import SteamLevelCandidate, StyleModelData


def style_model_data_from_heat_profile(
    profile: HeatIntervalProfile,
    *,
    steam_main: str,
    power_demand: float,
    generation_enthalpy_delta: float,
    use_enthalpy_delta: float,
    steam_enthalpy_for_use: float | None = None,
    feedwater_enthalpy: float = 0.0,
    source_heat_loss_fraction: float = 0.0,
    sink_heat_loss_fraction: float = 0.0,
) -> StyleModelData:
    """Create single-main STYLE data from a shifted heat interval profile."""

    intervals = tuple(profile.intervals)
    source_values = tuple(_profile_value(profile.source_heat, interval.key) for interval in intervals)
    sink_values = tuple(_profile_value(profile.sink_heat, interval.key) for interval in intervals)
    source_bounds = _prefix_sums(source_values)
    sink_bounds = _suffix_sums(sink_values)

    return StyleModelData(
        steam_mains=(steam_main,),
        steam_levels=tuple(
            SteamLevelCandidate(
                name=f"{steam_main}_{_format_level_temperature(interval.lower)}",
                steam_main=steam_main,
                temperature=interval.lower,
                source_heat_available=source_values[index],
                sink_heat_demand=sink_values[index],
                generation_enthalpy_delta=generation_enthalpy_delta,
                use_enthalpy_delta=use_enthalpy_delta,
                source_heat_upper_bound=source_bounds[index],
                sink_heat_upper_bound=sink_bounds[index],
                steam_enthalpy_for_use=steam_enthalpy_for_use,
                feedwater_enthalpy=feedwater_enthalpy,
            )
            for index, interval in enumerate(intervals)
        ),
        power_demand=power_demand,
        source_heat_loss_fraction=source_heat_loss_fraction,
        sink_heat_loss_fraction=sink_heat_loss_fraction,
    )


def style_model_data_from_heat_profile_for_steam_mains(
    profile: HeatIntervalProfile,
    *,
    steam_mains: tuple[str, ...],
    power_demand: float,
    generation_enthalpy_delta: float,
    use_enthalpy_delta: float,
    steam_enthalpy_for_use: float | None = None,
    feedwater_enthalpy: float = 0.0,
    heat_load_steam_main: str | None = None,
    source_heat_loss_fraction: float = 0.0,
    sink_heat_loss_fraction: float = 0.0,
) -> StyleModelData:
    """Create physical interval candidates for each supplied steam main."""

    if not steam_mains:
        raise ValueError("at least one steam main is required")
    if heat_load_steam_main is not None and heat_load_steam_main not in steam_mains:
        raise ValueError(
            f"heat-load steam main {heat_load_steam_main!r} is not in steam_mains"
        )
    single_main_data = tuple(
        style_model_data_from_heat_profile(
            _heat_profile_for_steam_main(
                profile,
                steam_main=steam_main,
                heat_load_steam_main=heat_load_steam_main,
            ),
            steam_main=steam_main,
            power_demand=power_demand,
            generation_enthalpy_delta=generation_enthalpy_delta,
            use_enthalpy_delta=use_enthalpy_delta,
            steam_enthalpy_for_use=steam_enthalpy_for_use,
            feedwater_enthalpy=feedwater_enthalpy,
            source_heat_loss_fraction=source_heat_loss_fraction,
            sink_heat_loss_fraction=sink_heat_loss_fraction,
        )
        for steam_main in steam_mains
    )
    return StyleModelData(
        steam_mains=steam_mains,
        steam_levels=tuple(
            level
            for data in single_main_data
            for level in data.steam_levels
        ),
        power_demand=power_demand,
        source_heat_loss_fraction=source_heat_loss_fraction,
        sink_heat_loss_fraction=sink_heat_loss_fraction,
    )


def _heat_profile_for_steam_main(
    profile: HeatIntervalProfile,
    *,
    steam_main: str,
    heat_load_steam_main: str | None,
) -> HeatIntervalProfile:
    if heat_load_steam_main is None or steam_main == heat_load_steam_main:
        return profile
    return _zero_heat_profile(profile)


def _zero_heat_profile(profile: HeatIntervalProfile) -> HeatIntervalProfile:
    return HeatIntervalProfile(
        intervals=tuple(profile.intervals),
        source_heat={interval.key: 0.0 for interval in profile.intervals},
        sink_heat={interval.key: 0.0 for interval in profile.intervals},
    )


def _profile_value(values: dict[tuple[float, float], float], key: tuple[float, float]) -> float:
    return float(values.get(key, 0.0))


def _prefix_sums(values: tuple[float, ...]) -> tuple[float, ...]:
    total = 0.0
    result: list[float] = []
    for value in values:
        total += value
        result.append(total)
    return tuple(result)


def _suffix_sums(values: tuple[float, ...]) -> tuple[float, ...]:
    total = 0.0
    result: list[float] = []
    for value in reversed(values):
        total += value
        result.append(total)
    return tuple(reversed(result))


def _format_level_temperature(value: float) -> str:
    return f"{value:g}".replace("-", "m").replace(".", "p")
