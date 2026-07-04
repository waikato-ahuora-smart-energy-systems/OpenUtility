"""Generic row formatting helpers for STYLE reports."""

from __future__ import annotations

import csv
from collections.abc import Sequence
from io import StringIO
from typing import Any


def format_rows_csv(
    rows: Sequence[dict[str, Any]],
    fieldnames: Sequence[str],
) -> str:
    """Return CSV text for dictionaries using a stable field order."""

    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
