"""Extracted datasets from Jimenez-Romero utility-system optimization studies."""

from __future__ import annotations

from .benchmarks import *  # noqa: F403
from .benchmarks import __all__ as _benchmark_all

DATASET_DESCRIPTION = (
    "Jimenez-Romero utility-system optimization replication fixtures extracted "
    "for STYLE and Contribution 2 case studies."
)

__all__ = (*_benchmark_all, "DATASET_DESCRIPTION")
