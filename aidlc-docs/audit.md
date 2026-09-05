# AI-DLC Audit Log

## 2026-09-03 - AI-DLC v1 Installation

**User Request**: "Install aidlc v1 like OpenPinch."

**Action**: Installed the same AI-DLC v1 rule scaffold layout used by the local
OpenPinch checkout, including `AGENTS.md` and `.aidlc-rule-details/`. Created
OpenUtility-specific state tracking instead of copying OpenPinch project
history.

**Verification**: Added packaging tests for the rule scaffold and project state.

---

## Implementation Request
**Timestamp**: 2026-09-04T19:04:44Z
**User Input**: "Please action the follow-up review findings for the implemented Multi-Period HPR Boundary and verify them end-to-end. Preserve OpenUtility’s independence from OpenPinch and TESPy at runtime.

Required corrections:
1. For ordered_part_load_curve, enforce interpolation between adjacent PLR breakpoints using a HiGHS-portable segment-binary formulation or an equivalent exact adjacency formulation. Add a curve with at least three points and prove by test that nonadjacent mixing is impossible.
2. Resolve fixed/reference-capacity semantics. For v1 absolute maps, either require fixed capacity to equal the map reference capacity or apply one explicit constant scale to q_source, q_sink, and power. Validate the useful-capacity basis. Add reference_capacity_basis: q_sink for heat_pump and q_source for refrigeration.
3. Make schema 1.0 strict: reject unknown versions and incompatible unit or COP conventions; validate finite temperatures, unique coordinates, one constant source/sink temperature pair per ordered curve, strictly ordered unique PLRs, load_fraction × reference_capacity consistency, COP consistency, and energy balance.
4. Separate energy-balance tolerance from temperature-matching tolerance.
5. Use mode-aware useful duty—q_source for refrigeration—for minimum-load constraints and variable operating cost, or introduce an explicit q_useful expression.
6. Preserve structured JSON provenance without coercing values to strings.
7. Explicitly document and test whether HPR electricity is still an isolated multi-period overlay. Prefer integration into a single period-indexed electricity balance that includes onsite generation, grid limits, and transmission efficiency if that is in current scope; otherwise state the limitation precisely and do not claim integration.
8. Update the JSON mapping decoder, docs, release smoke checks, and tests. Keep OpenPinch and TESPy absent from OpenUtility dependencies and imports. Treat the schema as alpha until these corrections settle, and report the exact final field names and semantics for the OpenPinch producer.

OpenPinch’s complementary producer design expects external thermal service temperatures in degC, duties and power in kW, an external thermodynamic_backend field, and fixed-capacity single-source/single-sink v1. Do not add OpenPinch imports. Please follow OpenUtility’s repository workflow and pause only where a user decision or explicit approval is genuinely required."
**AI Response**: "Loaded common AI-DLC rules, scanned extension opt-in files, loaded the partially enabled property-based testing rules, and began implementation planning for HPR schema/model corrections."
**Context**: Construction/code generation and verification for existing OpenUtility HPR implementation.

---

## Implementation Verification
**Timestamp**: 2026-09-04T19:13:40Z
**User Input**: "N/A - verification step for the active implementation request."
**AI Response**: "Implemented strict alpha HPR schema validation, structured provenance preservation, fixed-capacity scaling, adjacent-only ordered part-load interpolation, mode-aware useful duty, release smoke updates, and documentation of the current isolated HPR electricity overlay. Verified with `uv run python tools/release_check.py`: 186 tests passed, coverage 90.24%, ruff, ruff format, mypy, Sphinx, build, twine check, pip-audit, and smoke install passed."
**Context**: Construction/build and test completion for Multi-Period HPR follow-up corrections.

---

## Workflow Change Request
**Timestamp**: 2026-09-04T19:37:36Z
**User Input**: "If CI runs on main and passes, the release should run automatically."
**AI Response**: "Inspected CI and release workflows, release validation scripts, and release documentation. Began updating the release workflow so a successful CI workflow_run on main starts the protected PyPI release path automatically."
**Context**: GitHub Actions release automation update.

---

## CI Failure Triage
**Timestamp**: 2026-09-04T19:45:50Z
**User Input**: "CI failed on version bump"
**AI Response**: "Inspected GitHub Actions run 33912538030. The bump-version job failed because the workflow added an AUTHORIZATION extraheader while checkout persisted credentials, causing GitHub to reject the fetch with Duplicate header: Authorization. Removed the redundant fetch extraheader from the bump-version job and added a regression test for that workflow shape."
**Context**: GitHub Actions version bump failure correction.

---

## CI Failure Triage
**Timestamp**: 2026-09-04T19:49:46Z
**User Input**: "CI failed on version bump"
**AI Response**: "Pushed the bump-version fix and observed CI run 33912975799. The original bump-version job passed, but release-version failed during its base-branch fetch because the checkout intentionally did not persist credentials and the custom bearer extraheader was not accepted for Git smart HTTP. Updated release-version to authenticate only the fetch URL with GITHUB_TOKEN, then unset GH_TOKEN before running repository-owned Python code."
**Context**: GitHub Actions release-version fetch authentication correction.

---

## Release Failure Triage
**Timestamp**: 2026-09-04T22:17:45Z
**User Input**: "Failed"
**AI Response**: "Inspected Release run 33917477453. After the pypi environment was updated to allow main and the publish job was approved, the rerun failed because the validate job uploaded openutility-dist-${{ github.run_id }}-${{ github.run_attempt }} on attempt 1 while the rerun publish job looked for attempt 2. Updated the release artifact name to use only github.run_id so rerun-failed-jobs can download the previously verified distributions."
**Context**: GitHub Actions release artifact naming correction.

---

## Repository Protection Setup
**Timestamp**: 2026-09-05T20:33:17Z
**User Input**: "I want to set up the repo to protect main and force PR into main after tests run. Use the same workflow approach as OpenPinch."
**AI Response**: "Compared OpenUtility with OpenPinch's PR workflow model. Added an aggregate pr-gate job to the CI workflow so GitHub branch protection can require one stable check that verifies all applicable tests, release-gate, version-bump, and release-version jobs before merging pull requests to main."
**Context**: GitHub Actions pull-request protection workflow update.
