# Changelog

## 0.1.0 - Current Alpha Release

OpenUtility `0.1.0` establishes a tested reusable package for Pyomo-based
utility-system optimization.

### Package Boundaries

- `OpenUtility/` is the public library for model data, Pyomo model builders,
  solver adapters, reporting helpers, bilevel utilities, and thermal intervals.
- Private replication workflows, notebooks, and generated outputs are not part
  of the public package, release tests, or built wheel.

### Solver And Runtime

- Python `>=3.14.2` is required.
- Pyomo is the model structure.
- HiGHS is used through Pyomo `SolverFactory("appsi_highs")` and the required
  `highspy` dependency.
- OpenUtility consumes plain stream-like thermal data and versioned HPR
  performance maps; OpenPinch is not a runtime dependency.

### Public Interfaces

- Reusable public APIs are exposed from `OpenUtility` and
  `OpenUtility.utility_system`.
- Removed compatibility names are not restored, including historical stream
  adapters and the removed SciPy MILP solver path.

### Release Verification

- Added a strict release readiness gate in `tools/release_check.py`.
- Added GitHub Actions CI and tag-based PyPI publishing workflow.
- Added typed-package marker `OpenUtility/py.typed`.
- Added wheel inspection for dependency metadata and private-artifact
  exclusion.
