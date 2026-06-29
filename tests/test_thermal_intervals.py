from __future__ import annotations

import pytest

from case_study.jimenez_romero_utility_system_optimization.benchmarks import STYLE_CASE_STUDY_2_STREAMS
from OpenUtility.thermal import build_temperature_intervals, heat_content_by_interval
from OpenUtility.thermal import (
    openpinch_stream_collection_from_case_study_streams,
    openpinch_streams_from_case_study_streams,
)


Stream = pytest.importorskip("OpenPinch.classes.stream").Stream
StreamCollection = pytest.importorskip("OpenPinch.classes.stream_collection").StreamCollection


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


def test_openpinch_streams_from_case_study_streams_reuses_stream_class() -> None:
    streams = openpinch_streams_from_case_study_streams(
        STYLE_CASE_STUDY_2_STREAMS[:2],
    )
    first_stream = streams[0]

    assert isinstance(first_stream, Stream)
    assert first_stream.name == "A-1"
    assert first_stream.type == "Hot"
    assert first_stream.t_max_star.value == pytest.approx(
        STYLE_CASE_STUDY_2_STREAMS[0].shifted_maximum_temperature,
    )
    assert first_stream.t_min_star.value == pytest.approx(
        STYLE_CASE_STUDY_2_STREAMS[0].shifted_minimum_temperature,
    )
    assert first_stream.CP.value == pytest.approx(
        STYLE_CASE_STUDY_2_STREAMS[0].heat_capacity_flow,
    )


def test_case_study_stream_collection_reuses_openpinch_class() -> None:
    collection = openpinch_stream_collection_from_case_study_streams(
        STYLE_CASE_STUDY_2_STREAMS[:2],
    )

    intervals = build_temperature_intervals(collection)

    assert isinstance(collection, StreamCollection)
    assert len(collection) == 2
    assert collection.get_stream_names() == ["A-1", "A-2"]
    assert intervals[0].upper == pytest.approx(292.5)
