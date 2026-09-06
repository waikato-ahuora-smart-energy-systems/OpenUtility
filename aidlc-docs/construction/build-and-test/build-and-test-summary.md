# Release readiness results

Validated locally on macOS with Python 3.14.3. Full release gate exited 0.

- 188 tests passed; package coverage 90.24% (required 90%).
- Ruff lint and format, mypy, strict Sphinx HTML, wheel/source builds, wheel inspection, and twine check passed.
- Dependency audit reported no known vulnerabilities. The unpublished local OpenUtility 0.1.2 itself was skipped by the vulnerability database.
- Fresh wheel installation resolved public dependencies and passed isolated imports plus HiGHS binary, heat-pump, and refrigeration solves.
- Source archive includes tools/release_check.py. Wheel contains 15 Python modules, py.typed, and the confirmed RTD documentation URL.
- Git diff whitespace validation passed.

Public service verification:

- PyPI currently serves 0.1.1; 0.1.2 was unused at verification.
- Existing Release workflow 33925200883 succeeded for main commit 22ff10f7, confirming the existing publication path worked.
- RTD build 34413757 succeeded for that same main commit. The live page still identifies itself as 0.1.0 with the old theme; develop already contains dynamic version/theme configuration, which will take effect after merge and rebuild.
- Documentation address: https://openutility.readthedocs.io/en/latest/
- Private publisher/environment settings were not inspected: CLI has no GitHub authentication and the browser is not signed in. Native browser control lacks Computer Use permissions. No permissions were changed.

The readiness changes remain local on develop. No commit, push, merge, upload,
or new hosted build was performed. Publish through the established reviewed
PR into main, successful CI, and pypi environment approval when required.

Extension compliance for this unit:

- Security baseline: disabled; skipped.
- Resiliency baseline: disabled; skipped.
- PBT-01: N/A; no domain design.
- PBT-02: N/A; no serialization or reversible transformation.
- PBT-03: N/A; no pure domain function changes.
- PBT-04: N/A; no idempotent domain operation changes.
- PBT-05: N/A; no algorithm/oracle changes.
- PBT-06: N/A; no stateful domain changes.
- PBT-07: N/A; no property generators needed.
- PBT-08: N/A; deterministic subprocess regression and installation integration.
- PBT-09: N/A; no PBT-applicable code introduced.
- PBT-10: N/A; no business-critical domain path changed.
