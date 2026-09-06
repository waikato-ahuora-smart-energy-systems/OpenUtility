# Release readiness code generation plan

One unit: existing tools/release_check.py, tests/test_release_tooling.py,
pyproject.toml, README.md, CHANGELOG.md, docs/release_strategy.rst.
Requirements are in ../../inception/requirements/requirements.md.
User "go" authorizes the preceding proposed changes and validation sequence.

- [x] Step 1 (R1): Run wheel smoke code with isolated Python from the temporary environment, assert distribution-owned import, and add behavioral regression coverage.
- [x] Step 2 (R2): Include /tools in the source distribution and verify packaged release tooling.
- [x] Step 3 (R3): Update README installation/version language and record 0.1.2 release notes.
- [x] Step 4 (R4): Check external project status and set an RTD URL only after confirming the actual project address.
- [x] Step 5 (R5): Run full release gate, inspect sdist, and document results and remaining account setup.

PBT compliance: PBT-01 through PBT-10 N/A for subprocess integration and metadata/documentation work; no pure domain transformations or serialization introduced.

RTD project and URL confirmed from user-supplied project page. Build 34413757 succeeded for main commit 22ff10f7; it predates local release readiness changes. PyPI 0.1.1 published; administrative settings remain unverified without login.
