from __future__ import annotations

import pytest

from OpenUtility.thermal import build_temperature_intervals, heat_content_by_interval


Stream = pytest.importorskip("OpenPinch.classes.stream").Stream


def test_build_temperature_intervals_uses_openpinch_shifted_kinks() -> None:
    hot_stream = Stream(
        name="hot",
        t_supply=200.0,
        t_target=100.0,
        dt_cont=5.0,
        heat_flow=1000.0,
    )
    cold_stream = Stream(
        name="cold",
        t_supply=80.0,
        t_target=180.0,
        dt_cont=5.0,
        heat_flow=500.0,
    )

    intervals = build_temperature_intervals([hot_stream, cold_stream])

    assert [(item.upper, item.lower) for item in intervals] == [
        (195.0, 185.0),
        (185.0, 95.0),
        (95.0, 85.0),
    ]


def test_heat_content_by_interval_matches_thesis_interval_formula() -> None:
    hot_stream = Stream(
        name="hot",
        t_supply=200.0,
        t_target=100.0,
        dt_cont=5.0,
        heat_flow=1000.0,
    )
    cold_stream = Stream(
        name="cold",
        t_supply=80.0,
        t_target=180.0,
        dt_cont=5.0,
        heat_flow=500.0,
    )
    intervals = build_temperature_intervals([hot_stream, cold_stream])

    profile = heat_content_by_interval([hot_stream, cold_stream], intervals)

    assert profile.source_heat == pytest.approx(
        {
            (195.0, 185.0): 100.0,
            (185.0, 95.0): 900.0,
            (95.0, 85.0): 0.0,
        }
    )
    assert profile.sink_heat == pytest.approx(
        {
            (195.0, 185.0): 0.0,
            (185.0, 95.0): 450.0,
            (95.0, 85.0): 50.0,
        }
    )
