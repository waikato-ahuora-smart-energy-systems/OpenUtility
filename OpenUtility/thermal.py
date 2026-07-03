"""Thermal interval helpers for OpenPinch streams and zones."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True, order=True)
class TemperatureInterval:
    """One descending shifted-temperature interval."""

    upper: float
    lower: float

    def __post_init__(self) -> None:
        if self.upper <= self.lower:
            raise ValueError("temperature interval upper bound must exceed lower bound")

    @property
    def key(self) -> tuple[float, float]:
        """Return a stable dictionary key for this interval."""

        return (self.upper, self.lower)


@dataclass(frozen=True)
class HeatIntervalProfile:
    """Source and sink heat content over shifted-temperature intervals."""

    intervals: tuple[TemperatureInterval, ...]
    source_heat: dict[tuple[float, float], float]
    sink_heat: dict[tuple[float, float], float]


def build_temperature_intervals(
    streams: Any | Iterable[Any],
    *,
    precision: int = 10,
) -> tuple[TemperatureInterval, ...]:
    """Build descending intervals from OpenPinch shifted stream kinks."""

    kinks: set[float] = set()
    for stream in _active_streams(streams):
        kinks.add(round(_stream_shifted_max_temperature(stream), precision))
        kinks.add(round(_stream_shifted_min_temperature(stream), precision))

    levels = sorted(kinks, reverse=True)
    return tuple(
        TemperatureInterval(upper=upper, lower=lower)
        for upper, lower in zip(levels, levels[1:])
        if upper > lower
    )


def heat_content_by_interval(
    streams: Any | Iterable[Any],
    intervals: Iterable[TemperatureInterval],
) -> HeatIntervalProfile:
    """Calculate interval heat content using the STYLE heat-profile formula."""

    interval_tuple = tuple(intervals)
    source_heat = {interval.key: 0.0 for interval in interval_tuple}
    sink_heat = {interval.key: 0.0 for interval in interval_tuple}

    for stream in _active_streams(streams):
        stream_type = _stream_type(stream)
        if stream_type not in {"hot", "cold"}:
            continue
        target = source_heat if stream_type == "hot" else sink_heat
        stream_min = _stream_shifted_min_temperature(stream)
        stream_max = _stream_shifted_max_temperature(stream)
        cp = abs(_stream_cp(stream))
        for interval in interval_tuple:
            overlap = _temperature_overlap(
                stream_min=stream_min,
                stream_max=stream_max,
                interval=interval,
            )
            target[interval.key] += cp * overlap

    return HeatIntervalProfile(
        intervals=interval_tuple,
        source_heat=source_heat,
        sink_heat=sink_heat,
    )


def _active_streams(streams: Any | Iterable[Any]) -> tuple[Any, ...]:
    return tuple(
        stream
        for stream in _stream_iterable(streams)
        if bool(getattr(stream, "active", True))
    )


def _stream_iterable(streams: Any | Iterable[Any]) -> Iterable[Any]:
    if _is_openpinch_stream(streams):
        return (streams,)
    if hasattr(streams, "process_streams"):
        return getattr(streams, "process_streams")
    return streams


def _is_openpinch_stream(value: Any) -> bool:
    return all(
        hasattr(value, attribute)
        for attribute in ("type", "t_min_star", "t_max_star", "CP")
    )


def _stream_type(stream: Any) -> str:
    stream_type = getattr(stream, "type", None)
    if stream_type is None:
        raise TypeError("stream must expose an OpenPinch type")
    return str(stream_type).strip().lower()


def _stream_shifted_min_temperature(stream: Any) -> float:
    return _value_as_float(getattr(stream, "t_min_star", None), unit="degC")


def _stream_shifted_max_temperature(stream: Any) -> float:
    return _value_as_float(getattr(stream, "t_max_star", None), unit="degC")


def _stream_cp(stream: Any) -> float:
    return _value_as_float(getattr(stream, "CP", None), unit="kW/delta_degC")


def _value_as_float(value: Any, *, unit: str | None = None) -> float:
    if value is None:
        raise TypeError("stream value is required")
    if unit is not None and hasattr(value, "to"):
        value = value.to(unit)
    if hasattr(value, "value"):
        value = value.value
    return float(value)


def _temperature_overlap(
    *,
    stream_min: float,
    stream_max: float,
    interval: TemperatureInterval,
) -> float:
    lower = max(stream_min, interval.lower)
    upper = min(stream_max, interval.upper)
    return max(0.0, upper - lower)
