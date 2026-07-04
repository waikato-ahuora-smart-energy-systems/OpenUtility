from __future__ import annotations

import pytest

from case_study.jimenez_romero_utility_system_optimization.benchmarks import (
    STYLE_CASE_STUDY_2_STREAMS,
)
from OpenUtility.thermal import build_temperature_intervals, heat_content_by_interval

from OpenPinch.classes.stream import Stream
from OpenPinch.classes.stream_collection import StreamCollection
from OpenPinch.classes.zone import Zone


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


def test_heat_content_by_interval_matches_style_interval_formula() -> None:
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


def test_build_temperature_intervals_accepts_openpinch_stream_collection() -> None:
    collection = StreamCollection(
        [
            Stream(
                name="hot",
                t_supply=200.0,
                t_target=100.0,
                dt_cont=5.0,
                heat_flow=1000.0,
            ),
            Stream(
                name="cold",
                t_supply=80.0,
                t_target=180.0,
                dt_cont=5.0,
                heat_flow=500.0,
            ),
        ]
    )

    intervals = build_temperature_intervals(collection)

    assert isinstance(collection, StreamCollection)
    assert len(collection) == 2
    assert [(item.upper, item.lower) for item in intervals] == [
        (195.0, 185.0),
        (185.0, 95.0),
        (95.0, 85.0),
    ]


def test_heat_content_by_interval_accepts_openpinch_zone() -> None:
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
    zone = Zone(name="test-zone")
    zone.hot_streams.add(hot_stream)
    zone.cold_streams.add(cold_stream)
    intervals = build_temperature_intervals(zone)

    profile = heat_content_by_interval(zone, intervals)

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


def test_case_study_stream_collection_is_openpinch_native() -> None:
    intervals = build_temperature_intervals(STYLE_CASE_STUDY_2_STREAMS)

    assert isinstance(STYLE_CASE_STUDY_2_STREAMS, StreamCollection)
    assert len(STYLE_CASE_STUDY_2_STREAMS) == 36
    assert STYLE_CASE_STUDY_2_STREAMS.get_stream_names()[:2] == ["A-1", "A-2"]
    assert STYLE_CASE_STUDY_2_STREAMS["A-1"].heat_flow.value == pytest.approx(30.0)
    assert intervals[0].upper == pytest.approx(292.5)
