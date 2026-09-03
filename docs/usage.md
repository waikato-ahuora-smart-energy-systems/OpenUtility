# Usage

OpenUtility is a library-first package. Build typed input data, assemble a Pyomo
model, solve it with HiGHS through Pyomo, then extract or report results.

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

Thermal interval helpers accept any stream-like object exposing `type`, `CP`,
`t_min_star`, and `t_max_star`. OpenPinch can produce such data, but
OpenUtility does not import OpenPinch.
