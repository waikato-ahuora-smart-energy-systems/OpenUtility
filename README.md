# OpenUtility

OpenUtility is a Python package for Pyomo-based utility-system optimization,
reporting, bilevel decomposition utilities, thermal profile handling, and HPR
investment/dispatch optimization. HPR is used as the umbrella term for heat
pump and refrigeration assets.

`OpenUtility/` is the reusable public package. Private replication workflows and
large study-specific artifacts are intentionally outside the package boundary
and are not included in release tests or built wheels.

OpenUtility targets Python `>=3.14.2`. MILP solves use Pyomo
`SolverFactory("appsi_highs")` through the required `highspy` package.
OpenPinch is not a runtime dependency. OpenUtility consumes plain Python data
that can be exported from OpenPinch, TESPy workflows, manufacturer data, or
other upstream tools.

## Academic Basis

OpenUtility began as a Python/Pyomo implementation of utility-system
optimization methods developed by Julia Jimenez Romero, Adisa Azapagic, and
Robin Smith:

- Julia Jimenez Romero, "Reduction of Industrial Energy Demand through
  Sustainable Integration of Distributed Energy Hubs," PhD thesis, The
  University of Manchester, 2022.
- Jimenez Romero, J., Azapagic, A., and Smith, R., "STYLE: A new optimization
  model for Synthesis of uTility sYstems with steam LEvel placement,"
  Computers and Chemical Engineering, 170, Article 108060, 2023.
  https://doi.org/10.1016/j.compchemeng.2022.108060
- Jimenez Romero, J., Azapagic, A., and Smith, R., "BEELINE: BilevEl
  dEcomposition aLgorithm for synthesis of Industrial eNergy systEms,"
  Computers and Chemical Engineering, 180, Article 108406, 2024.
  https://doi.org/10.1016/j.compchemeng.2023.108406

The package has since been generalized beyond the original replication
workflows and extended with HPR optimization. In OpenUtility, HPR means heat
pump and refrigeration: fixed-capacity HPR candidates can be selected and
dispatched against multi-period thermal-node and electricity balances using
versioned plain performance maps.

## Install

From a checkout:

```bash
python -m pip install -e ".[dev,docs,release]"
```

For normal package use:

```bash
python -m pip install .
```

## Quick Start

```python
from OpenUtility import (
    SteamLevelCandidate,
    UtilitySystemModelData,
    build_utility_system_model,
    pyomo_utility_system_solver,
)

data = UtilitySystemModelData(
    steam_mains=("MP",),
    steam_levels=(
        SteamLevelCandidate(
            name="MP_100",
            steam_main="MP",
            temperature=100.0,
            source_heat_available=5.0,
            sink_heat_demand=5.0,
            generation_enthalpy_delta=1.0,
            use_enthalpy_delta=1.0,
            source_heat_upper_bound=5.0,
            sink_heat_upper_bound=5.0,
        ),
    ),
    power_demand=0.0,
    grid_import_limit=0.0,
    grid_export_limit=0.0,
)
model = build_utility_system_model(data)
status = pyomo_utility_system_solver("appsi_highs")(model)
```

## Verification

Run the full release gate:

```bash
python tools/release_check.py
```

The gate runs linting, formatting, type checking, tests with coverage, Sphinx,
source/wheel build, wheel inspection, `twine check`, dependency audit, and a
fresh wheel-install smoke test.

For offline local triage only:

```bash
python tools/release_check.py --skip-audit --skip-smoke-install
```

## Documentation

Build docs locally:

```bash
python -m sphinx -W -b html docs /tmp/openutility-docs-html
```

OpenUtility `0.1.0` is an alpha release. Public reusable APIs are exposed
through `OpenUtility.__all__` and `OpenUtility.utility_system.__all__`.
