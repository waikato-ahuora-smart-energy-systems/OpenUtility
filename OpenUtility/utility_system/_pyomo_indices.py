"""Index/grouping helpers for static utility-system Pyomo model construction."""

from __future__ import annotations

from .data import (
    FlashSteamRecoveryLevel,
    FlashSteamRecoveryRoute,
    UtilitySystemModelData,
)


def vhp_sources_by_vhp(data: UtilitySystemModelData) -> dict[str, tuple[str, ...]]:
    return {
        vhp.name: tuple(
            source.name for source in data.vhp_sources if source.vhp_header == vhp.name
        )
        for vhp in data.vhp_headers
    }


def boilers_by_vhp(data: UtilitySystemModelData) -> dict[str, tuple[str, ...]]:
    return {
        vhp.name: tuple(
            boiler.name for boiler in data.boilers if boiler.vhp_header == vhp.name
        )
        for vhp in data.vhp_headers
    }


def hrsgs_by_vhp(data: UtilitySystemModelData) -> dict[str, tuple[str, ...]]:
    return {
        vhp.name: tuple(hrsg.name for hrsg in data.hrsgs if hrsg.vhp_header == vhp.name)
        for vhp in data.vhp_headers
    }


def flash_level_by_name(
    data: UtilitySystemModelData,
) -> dict[str, FlashSteamRecoveryLevel]:
    if data.flash_steam_recovery is None:
        return {}
    return {level.steam_level: level for level in data.flash_steam_recovery.levels}


def flash_route_by_name(
    data: UtilitySystemModelData,
) -> dict[str, FlashSteamRecoveryRoute]:
    if data.flash_steam_recovery is None:
        return {}
    return {route.name: route for route in data.flash_steam_recovery.routes}


def flash_routes_by_source(data: UtilitySystemModelData) -> dict[str, tuple[str, ...]]:
    if data.flash_steam_recovery is None:
        return {level.name: () for level in data.steam_levels}
    return {
        level.name: tuple(
            route.name
            for route in data.flash_steam_recovery.routes
            if route.source_level == level.name
        )
        for level in data.steam_levels
    }


def flash_routes_by_target(data: UtilitySystemModelData) -> dict[str, tuple[str, ...]]:
    if data.flash_steam_recovery is None:
        return {level.name: () for level in data.steam_levels}
    return {
        level.name: tuple(
            route.name
            for route in data.flash_steam_recovery.routes
            if route.target_level == level.name
        )
        for level in data.steam_levels
    }


def vhp_turbines_by_pair(
    data: UtilitySystemModelData,
) -> dict[tuple[str, str], tuple[str, ...]]:
    return {
        (vhp.name, level.name): tuple(
            turbine.name
            for turbine in data.vhp_turbines
            if turbine.vhp_header == vhp.name and turbine.steam_level == level.name
        )
        for vhp in data.vhp_headers
        for level in data.steam_levels
    }


def vhp_letdowns_by_pair(
    data: UtilitySystemModelData,
) -> dict[tuple[str, str], tuple[str, ...]]:
    return {
        (vhp.name, level.name): tuple(
            letdown.name
            for letdown in data.vhp_letdowns
            if letdown.vhp_header == vhp.name and letdown.steam_level == level.name
        )
        for vhp in data.vhp_headers
        for level in data.steam_levels
    }


def steam_main_turbines_by_source(
    data: UtilitySystemModelData,
) -> dict[str, tuple[str, ...]]:
    return {
        level.name: tuple(
            turbine.name
            for turbine in data.steam_main_turbines
            if turbine.source_level == level.name
        )
        for level in data.steam_levels
    }


def steam_main_turbines_by_target(
    data: UtilitySystemModelData,
) -> dict[str, tuple[str, ...]]:
    return {
        level.name: tuple(
            turbine.name
            for turbine in data.steam_main_turbines
            if turbine.target_level == level.name
        )
        for level in data.steam_levels
    }


def steam_main_letdowns_by_source(
    data: UtilitySystemModelData,
) -> dict[str, tuple[str, ...]]:
    return {
        level.name: tuple(
            letdown.name
            for letdown in data.steam_main_letdowns
            if letdown.source_level == level.name
        )
        for level in data.steam_levels
    }


def steam_main_letdowns_by_target(
    data: UtilitySystemModelData,
) -> dict[str, tuple[str, ...]]:
    return {
        level.name: tuple(
            letdown.name
            for letdown in data.steam_main_letdowns
            if letdown.target_level == level.name
        )
        for level in data.steam_levels
    }
