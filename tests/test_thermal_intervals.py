from __future__ import annotations

import pytest

from OpenUtility.thermal import build_temperature_intervals, heat_content_by_interval


class FakeStream:
    def __init__(
        self,
        *,
        name: str,
        stream_type: str,
        t_min_star: float,
        t_max_star: float,
        cp: float,
        active: bool = True,
    ) -> None:
        self.name = name
        self.type = stream_type
        self.t_min_star = t_min_star
        self.t_max_star = t_max_star
        self.CP = cp
        self.active = active


class FakeStreamCollection:
    def __init__(self, streams: list[FakeStream]) -> None:
        self.process_streams = streams

    def __len__(self) -> int:
        return len(self.process_streams)


class FakeZone:
    def __init__(self, streams: list[FakeStream]) -> None:
        self.process_streams = streams


def _hot_stream() -> FakeStream:
    return FakeStream(
        name="hot",
        stream_type="hot",
        t_min_star=95.0,
        t_max_star=195.0,
        cp=10.0,
    )


def _cold_stream() -> FakeStream:
    return FakeStream(
        name="cold",
        stream_type="cold",
        t_min_star=85.0,
        t_max_star=185.0,
        cp=5.0,
    )


def test_build_temperature_intervals_uses_openpinch_shifted_kinks() -> None:
    hot_stream = _hot_stream()
    cold_stream = _cold_stream()

    intervals = build_temperature_intervals([hot_stream, cold_stream])

    assert [(item.upper, item.lower) for item in intervals] == [
        (195.0, 185.0),
        (185.0, 95.0),
        (95.0, 85.0),
    ]


def test_heat_content_by_interval_matches_style_interval_formula() -> None:
    hot_stream = _hot_stream()
    cold_stream = _cold_stream()
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
    collection = FakeStreamCollection([_hot_stream(), _cold_stream()])

    intervals = build_temperature_intervals(collection)

    assert isinstance(collection, FakeStreamCollection)
    assert len(collection) == 2
    assert [(item.upper, item.lower) for item in intervals] == [
        (195.0, 185.0),
        (185.0, 95.0),
        (95.0, 85.0),
    ]


def test_heat_content_by_interval_accepts_openpinch_zone() -> None:
    zone = FakeZone([_hot_stream(), _cold_stream()])
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
