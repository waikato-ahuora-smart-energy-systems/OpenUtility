# Repository cleanup

## Requirements and scope

User request: "Clean up obsolete and old files. "

Small brownfield maintenance task. Remove files only when they are superseded
or reproducible generated artifacts. Preserve application behavior, case-study
sources and results, notebooks, the installed environment, and workflow history.
Git was clean at inspection. Existing state and release assessment supply the
repository context; a new reverse-engineering stage is unnecessary.

## Evidence

- `docs/developer_checklist.md` duplicates the maintained Sphinx page
  `docs/developer_checklist.rst`.
- `docs/usage.md` duplicates the minimal example in `docs/notebook_workflow.rst`;
  thermal input guidance is in `docs/inputs.rst`.
- `docs/replication_plan.md` is a short boundary note already covered by
  `README.md`, `docs/index.rst`, and `docs/developer_checklist.rst`.
- None of those three Markdown pages has a tracked reference. Sphinx is
  configured for reStructuredText without a Markdown parser.
- `dist/` contains only generated 0.1.2 wheel/source archives; the project is 0.1.4.
- `tmp/` contains only an empty `pdfs/` directory.
- Tool caches, coverage output, and Python bytecode are reproducible.

## Execution

Text workflow: workspace assessment, minimal requirements, plan, cleanup,
documentation and packaging verification. One sequential maintenance unit.
Stories, application design, unit decomposition, functional/NFR/infrastructure
design, and operations are skipped because no behavior or architecture changes.
The user's cleanup request authorizes these local maintenance edits.

- [x] 1. Inspect workspace, prior workflow context, file contents, and references.
- [x] 2. Define conservative requirements and record the cleanup plan.
- [x] 3. Remove the three superseded Markdown pages and add explicit ignore rules
  for `.venv/` and `.mypy_cache/`.
- [x] 4. Run existing documentation/metadata tests, strict Sphinx build, package
  build and archive checks, and Git whitespace validation. Use temporary output
  paths so verification does not leave new build products in the repository.
- [x] 5. Remove generated caches, stale distributions, bytecode outside `.venv/`,
  and empty `tmp/`; verify retained source files and update workflow records.

## Extension compliance

Security and resiliency baselines remain disabled and are skipped. PBT remains
Partial. PBT-01 through PBT-10 are N/A for this task: no domain logic, serializers,
algorithms, generators, or testing framework changes. Existing deterministic
documentation and metadata checks cover the affected boundary.

## Validation instructions

Use `.venv/bin/python -B -m pytest -p no:cacheprovider tests/test_docs.py
tests/test_package_metadata.py -q`, `.venv/bin/python -B -m sphinx -W -b html
docs <temporary-directory>/html`, and `.venv/bin/python -B -m build
--no-isolation --outdir <temporary-directory>/dist`. Inspect the wheel/source
archive to confirm required package/docs content and absence of removed pages.
Run `git diff --check`. Performance testing is N/A for non-runtime cleanup.

## Results

11 existing documentation/metadata tests passed. Strict Sphinx HTML and the
0.1.4 wheel/source build passed; archive contents verified. Git whitespace
validation passed. Removed 141 generated files (28,316,496 bytes),
plus empty temporary directories. Exactly the three documented tracked pages
were removed; all other tracked files remain present. No runtime code changed.
