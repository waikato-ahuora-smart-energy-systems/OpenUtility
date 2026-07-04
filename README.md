# OpenUtility

OpenUtility is a Python package for Pyomo-based utility-system optimization,
reporting, and Jimenez-Romero case-study replication.

The package boundary is deliberate:

- `OpenUtility/` contains reusable model data classes, Pyomo model builders,
  solver adapters, reporting helpers, bilevel decomposition utilities, and
  thermal interval utilities.
- `case_study/jimenez_romero_utility_system_optimization/` contains extracted
  Jimenez-Romero input data, case-study builders, notebooks, scripts, and
  checked generated outputs.

OpenUtility targets Python `>=3.14.2` and solves the MILP workflows through
Pyomo `SolverFactory("appsi_highs")` with the required `highspy` package.
OpenPinch is a required dependency for stream, stream-collection, and zone
objects used by the case-study heat-profile inputs.

## Install

From a checkout:

```bash
python -m pip install -e ".[dev,docs,notebook,release]"
```

For normal package use:

```bash
python -m pip install .
```

## Quick Start

Run the main Contribution 2 Table 2-9 replication workflow:

```python
from case_study.jimenez_romero_utility_system_optimization.contribution2_integrated_hot_oil_fsr import (
    run_contribution2_table_2_9_case_study,
)

run = run_contribution2_table_2_9_case_study(
    catalog="physical-profile",
    apply_fuel_targets=True,
    apply_operating_targets=True,
)

summary = run.summary_table()
comparison = run.comparison_table()
axes = run.plot_field_comparison("total_annualized_cost")
```

The checked notebooks are:

- `case_study/jimenez_romero_utility_system_optimization/style_stage1_hot_oil_and_steam_mains/notebooks/replication.ipynb`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_integrated_hot_oil_fsr/notebooks/replication.ipynb`
- `case_study/jimenez_romero_utility_system_optimization/contribution2_computational_performance/notebooks/replication.ipynb`

## CLI

The installed CLI command remains:

```bash
openutility-style-table2-9 --catalog physical-profile --format csv
```

Common reports:

```bash
openutility-style-table2-9 --catalog reported-equipment --format csv
openutility-style-table2-9 --catalog physical-profile --view summary --format csv
openutility-style-table2-9 --report style-decomposition --view candidate-summary --format csv
```

Checked CSV outputs live under the relevant `case_study/.../outputs/`
directories. The test suite verifies that current code regenerates the checked
outputs from packaged input fixtures.

## Verification

Run the full release gate:

```bash
python tools/release_check.py
```

The gate runs:

- `ruff check`
- `ruff format --check`
- `mypy`
- `pytest` with coverage threshold
- Sphinx docs with warnings as errors
- source distribution and wheel build
- wheel metadata and package-asset inspection
- `twine check`
- dependency audit
- fresh wheel-install smoke test

For offline local triage only:

```bash
python tools/release_check.py --skip-audit --skip-smoke-install
```

## Documentation

Start with:

- `docs/index.rst`
- `docs/usage.md`
- `docs/inputs.rst`
- `docs/developer_checklist.md`
- `docs/replication_plan.md`

Build docs locally:

```bash
python -m sphinx -W -b html docs /tmp/openutility-docs-html
```

## Release Status

OpenUtility `0.1.0` is an alpha release. The public reusable API is exposed
through `OpenUtility.__all__` and `OpenUtility.style.__all__`. Case-study data,
helpers, notebooks, scripts, and generated outputs are intentionally exported
from the `case_study` package, not from `OpenUtility`.
