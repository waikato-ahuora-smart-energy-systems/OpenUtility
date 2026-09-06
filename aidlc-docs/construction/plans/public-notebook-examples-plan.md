# Public notebook examples

User approval: `go`, following the proposed six-notebook suite.

## Requirements and workflow

As a new package user, I can download each example, install OpenUtility from
PyPI, restart its kernel, and run all cells without private files or a checkout.
As a maintainer, I receive a failing CI gate when execution or numerical checks
fail. The examples are discoverable from Read the Docs and the README.

Reuse existing architecture and public APIs. This is documentation and execution
tooling within existing component boundaries; no new library API, functional
design, infrastructure design, or separate units are needed. Synthetic models
must explain units and assumptions and include readable tables and plots.

## Execution plan

- [x] Inspect current examples, public APIs, existing workflow, and dependencies.
- [x] Document scope and accepted implementation plan.
- [x] Create six independent notebooks with analytic and balance assertions.
- [x] Execute against published OpenUtility 0.1.2 in a fresh environment.
- [x] Add installed-wheel notebook execution and downloadable output artifacts to CI.
- [x] Link tutorials from RTD and README; declare runner dependencies.
- [x] Validate notebooks, documentation, tooling, and existing regression checks.
- [x] Record final results and limitations.

## Validation and extension applicability

Notebook JSON is validated with nbformat and Python code cells parsed with ast
before writing. Tables accompany plots; no Mermaid or ASCII diagrams are used.
Execute in separate kernels and empty temporary directories with installed-wheel
import assertions. Numerical checks use independently calculated annual costs,
energy balances, and comparison of decomposition with a monolithic solve.
Security and resiliency extensions remain disabled per project state. Partial
property-testing requirements are N/A: no library business logic is introduced;
execution checks exercise real kernels and solver behavior.

## Completed validation

- All six notebooks executed with real HiGHS solves in independent kernels
  against PyPI OpenUtility 0.1.2 and the locally built wheel.
- Every notebook includes one plot and tables; numerical assertions passed.
- Negative checks rejected empty input directories, cell exceptions, editable
  checkout imports, and output directories that would overwrite source files.
- All 188 existing tests passed; library coverage remains 90.24%.
- Ruff lint and format, Sphinx warnings-as-errors, workflow YAML parsing, lockfile
  version check, wheel/sdist builds, Twine, and git whitespace checks passed.
- Distribution inspection confirmed all six notebooks and the execution checker
  are in the sdist, while the wheel contains only the library and metadata.
- The saved notebook outputs were validated and selected plots inspected.

## Delivery and limitations

Sources and saved outputs: docs/notebooks. RTD download guide: docs/examples.rst.
Runner: tools/check_notebooks.py. CI and release validation install the built
wheel with its notebook extra and produce executed notebook/HTML artifacts.
Changes are local; hosted docs and GitHub checks require a subsequent push/build.

Grid-only examples explicitly fix aggregate onsite generation to zero: the
current API leaves it available when no generator candidates are supplied.
The decomposition menu includes disabled hot-oil binaries fixed to zero. HPR
maps and tariffs are synthetic; finite candidate enumeration is distinguished
from bound-based convergence. No library implementation changes were required.
