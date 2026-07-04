# Changelog

## 0.1.0 - Current Alpha Release

OpenUtility `0.1.0` establishes a tested Python package for reusable
Pyomo-based utility-system optimization plus Jimenez-Romero replication
workflows.

### Package Boundaries

- `OpenUtility/` is the reusable library for model data, Pyomo model builders,
  solver adapters, reporting helpers, bilevel utilities, and thermal intervals.
- `case_study/jimenez_romero_utility_system_optimization/` owns extracted
  case-study input data, replication builders, notebooks, scripts, and checked
  generated outputs.
- Case-study APIs are not re-exported from `OpenUtility`.

### Solver And Runtime

- Python `>=3.14.2` is required.
- Pyomo is the model structure.
- HiGHS is used through Pyomo `SolverFactory("appsi_highs")` and the required
  `highspy` dependency.
- OpenPinch `Stream`, `StreamCollection`, and `Zone` objects are required for
  case-study stream fixtures and heat-profile construction.

### Included Workflows

- Contribution 2 Table 2-9 reported-equipment and physical-profile replication.
- Stage 1 steam-main and hot-oil target notebook replication.
- Contribution 2 computational-performance, steam-property, and bilevel
  trajectory reporting.
- Candidate-driven STYLE binary-selection decomposition diagnostics.
- Checked CSV outputs generated from packaged input fixtures.
- Three executable case-study notebooks, one per implemented case-study scope.

### Public Interfaces

- Reusable public APIs are exposed from `OpenUtility` and `OpenUtility.style`.
- Case-study public APIs are exposed from the relevant `case_study` packages.
- The CLI command `openutility-style-table2-9` is retained and implemented from
  the `case_study` package.
- Removed compatibility names are not restored, including old notebook workflow
  names, old thesis-named stream adapters, and the removed SciPy MILP solver
  path.

### Release Verification

- Added a strict release readiness gate in `tools/release_check.py`.
- Added GitHub Actions CI and tag-based PyPI publishing workflow.
- Added typed-package marker `OpenUtility/py.typed`.
- Added wheel inspection for dependency metadata and packaged case-study assets.
- Added release metadata, project URLs, classifiers, license file metadata, and
  explicit package-data include patterns.
