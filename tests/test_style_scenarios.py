from __future__ import annotations

import pytest

from case_study.jimenez_romero_utility_system_optimization.benchmarks import (
    get_style_result,
)
from OpenUtility.style import (
    StaticStyleScenario,
    StaticStyleScenarioCatalog,
    SteamLevelCandidate,
    StyleModelData,
)


def test_static_style_scenario_catalog_returns_registered_scenarios() -> None:
    scenario = StaticStyleScenario(
        case_study="case-study-2",
        scenario="proposed-without-hot-oil",
        data=_minimal_data(),
        benchmark=get_style_result("case-study-2", "proposed-without-hot-oil"),
    )
    catalog = StaticStyleScenarioCatalog((scenario,))

    assert catalog.keys() == (("case-study-2", "proposed-without-hot-oil"),)
    assert catalog.get("case-study-2", "proposed-without-hot-oil") == scenario


def test_static_style_scenario_catalog_rejects_duplicate_keys() -> None:
    scenario = StaticStyleScenario(
        case_study="case-study-2",
        scenario="proposed-without-hot-oil",
        data=_minimal_data(),
    )

    with pytest.raises(ValueError, match="duplicate static STYLE scenario"):
        StaticStyleScenarioCatalog((scenario, scenario))


def test_static_style_scenario_catalog_reports_missing_key() -> None:
    catalog = StaticStyleScenarioCatalog(())

    with pytest.raises(KeyError, match="No static STYLE scenario"):
        catalog.get("case-study-2", "missing")


def _minimal_data() -> StyleModelData:
    return StyleModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_3",
                steam_main="MP",
                temperature=134.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=1.0,
                use_enthalpy_delta=1.0,
            ),
        ),
        power_demand=0.0,
    )
