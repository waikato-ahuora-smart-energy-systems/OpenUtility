"""Thermal interval helpers that interoperate with OpenPinch streams."""

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
    streams: Iterable[Any],
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
    streams: Iterable[Any],
    intervals: Iterable[TemperatureInterval],
) -> HeatIntervalProfile:
    """Calculate interval heat content using the STYLE thesis formula."""

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
        heat_capacity_flow = abs(_stream_heat_capacity_flow(stream))
        for interval in interval_tuple:
            overlap = _temperature_overlap(
                stream_min=stream_min,
                stream_max=stream_max,
                interval=interval,
            )
            target[interval.key] += heat_capacity_flow * overlap

    return HeatIntervalProfile(
        intervals=interval_tuple,
        source_heat=source_heat,
        sink_heat=sink_heat,
    )


def openpinch_streams_from_thesis_streams(streams: Iterable[Any]) -> tuple[Any, ...]:
    """Return real OpenPinch streams for thesis stream records.

    The thesis fixtures carry heat-load values in the numeric basis used by the
    OpenUtility model. The OpenPinch ``Stream`` class is reused here for stream
    classification and shifted-temperature handling while preserving those
    numeric heat-load values for the downstream STYLE heat-profile calculation.
    """

    try:
        from OpenPinch.classes.stream import Stream
    except ImportError as exc:  # pragma: no cover - depends on optional package.
        raise ImportError(
            "OpenPinch is required to create OpenPinch Stream objects. "
            "Install OpenUtility with the 'openpinch' extra.",
        ) from exc

    openpinch_streams = []
    for stream in streams:
        temperature_change = abs(
            float(getattr(stream, "supply_temperature"))
            - float(getattr(stream, "target_temperature")),
        )
        heat_flow = float(getattr(stream, "heat_capacity_flow")) * temperature_change
        openpinch_stream = Stream(
            name=str(getattr(stream, "name")),
            t_supply=float(getattr(stream, "supply_temperature")),
            t_target=float(getattr(stream, "target_temperature")),
            dt_cont=float(getattr(stream, "minimum_temperature_difference")) / 2.0,
            heat_flow=heat_flow,
            is_process_stream=True,
        )
        openpinch_stream.active = bool(getattr(stream, "active", True))
        openpinch_streams.append(openpinch_stream)
    return tuple(openpinch_streams)


def openpinch_stream_collection_from_thesis_streams(streams: Iterable[Any]) -> Any:
    """Return an OpenPinch StreamCollection for thesis stream records."""

    try:
        from OpenPinch.classes.stream_collection import StreamCollection
    except ImportError as exc:  # pragma: no cover - depends on optional package.
        raise ImportError(
            "OpenPinch is required to create an OpenPinch StreamCollection. "
            "Install OpenUtility with the 'openpinch' extra.",
        ) from exc
    return StreamCollection(list(openpinch_streams_from_thesis_streams(streams)))


def _active_streams(streams: Iterable[Any]) -> tuple[Any, ...]:
    return tuple(stream for stream in streams if bool(getattr(stream, "active", True)))


def _stream_type(stream: Any) -> str:
    stream_type = getattr(stream, "type", None) or getattr(stream, "stream_type", None)
    if stream_type is None:
        raise TypeError("stream must expose an OpenPinch-style type or stream_type")
    return str(stream_type).strip().lower()


def _stream_shifted_min_temperature(stream: Any) -> float:
    return _value_as_float(
        getattr(stream, "t_min_star", None)
        or getattr(stream, "shifted_minimum_temperature", None),
        unit="degC",
    )


def _stream_shifted_max_temperature(stream: Any) -> float:
    return _value_as_float(
        getattr(stream, "t_max_star", None)
        or getattr(stream, "shifted_maximum_temperature", None),
        unit="degC",
    )


def _stream_heat_capacity_flow(stream: Any) -> float:
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
