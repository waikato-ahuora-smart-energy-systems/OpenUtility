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

---

## ReadTheDocs Formatting Alignment
**Timestamp**: 2026-09-06T03:02:43Z
**User Input**: "Use the same RTD formatting as OpenPinch"
**AI Response**: "Compared OpenUtility and OpenPinch ReadTheDocs and Sphinx configuration. Updated OpenUtility to use the same docs/requirements.txt RTD install pattern, sphinx-rtd-theme HTML formatting, autosummary/viewcode extensions, dynamic pyproject.toml version loading, and tracked Sphinx asset directories."
**Context**: Documentation build and ReadTheDocs configuration update.

## Publishing Readiness Assessment
**Timestamp**: 2026-09-06T03:11:10Z
**User Input**: "What is needed before publishing this package to Pypi and RTD?"
**AI Response**: "Reviewed package metadata, CI and release workflows, RTD configuration, release tooling, and current official publishing documentation. Local offline release checks passed: 187 tests, 90.24% coverage, Ruff, mypy, Sphinx, source and wheel builds, wheel inspection, and twine check. Dependency audit and fresh dependency installation were not run. Found checkout-shadowed wheel smoke testing, stale 0.1.0 release documentation against package 0.1.2, GitHub docs metadata URL, and omitted tools directory in source distribution. External PyPI, RTD, and GitHub account settings could not be verified; GitHub CLI is unauthenticated and direct network resolution is unavailable. Recommended verifying trusted publisher and environment settings, RTD import and successful build, final version availability, and a full online release gate before publishing."
**Context**: Assessment only; no implementation changes or publication.

---

## Release Readiness Implementation
**Timestamp**: 2026-09-06T03:26:00Z
**User Input**: "go"
**AI Response**: "Proceeding with the five previously proposed readiness steps. Loaded workflow rules and existing extension choices; security/resiliency rules skipped because disabled, Partial PBT not applicable to subprocess and metadata corrections. Created concise requirements and checkbox plans. PyPI confirms 0.1.1 published and 0.1.2 available; RTD public API returns no openutility project. GitHub CLI unauthenticated and Computer Use permissions unavailable."
**Context**: Approved implementation and validation; public API unchanged.

---

## Read the Docs Project Confirmation
**Timestamp**: 2026-09-06T03:28:43Z
**User Input**: "[https://app.readthedocs.org/projects/openutility/](https://app.readthedocs.org/projects/openutility/)"
**AI Response**: "Confirmed RTD project from supplied link. Latest build 34413757 succeeded for main commit 22ff10f7. Updated package metadata and README to the confirmed documentation URL. First full gate encountered scaffold test depending on historical state wording; preserved installation history in state file and continued validation."
**Context**: User supplied project location, superseding earlier API lookup.

---

## Release Readiness Completion
**Timestamp**: 2026-09-06T03:31:47Z
**AI Response**: "Implemented isolated installed-wheel smoke testing with regression coverage, packaged the release tool, refreshed release notes and installation instructions, and linked to the confirmed RTD site. Full online release gate passed: 188 tests, 90.24% coverage, Ruff, mypy, strict Sphinx, source/wheel builds and checks, no known dependency vulnerabilities, and fresh-wheel HiGHS/HPR solves. Public GitHub Release run 33925200883 and RTD build 34413757 succeeded on existing main commit 22ff10f7. Recorded per-rule extension applicability and build/test instructions. Changes remain local on develop; no publishing or permission changes performed."
**Context**: Approved readiness work complete; standard PR/CI/environment release path remains.

---

## Remaining Release Steps
**Timestamp**: 2026-09-06T03:32:40Z
**User Input**: "what else?"
**AI Response**: "Checked local changes and release workflow. No additional code blockers identified by the completed gate. Remaining work is final release-date wording, commit/push and reviewed PR into main, required publishing approval, then verification of the actual PyPI installation and matching RTD build. Private GitHub protection/publisher settings still need authenticated verification. Broader Python/platform coverage is optional follow-up."
**Context**: Readiness follow-up; no publication performed.

---

## Commit Release Readiness Changes
**Timestamp**: 2026-09-06T03:33:12Z
**User Input**: "commit"
**AI Response**: "Preparing a local commit of the verified release-readiness changes on develop. Reviewed changed files and whitespace validation; prior full release gate passed with 188 tests and 90.24% coverage. Commit scope includes release tooling, regression coverage, package metadata, user documentation, and AI-DLC records. No push or publication requested."
**Context**: User-authorized local Git commit.

---

## Main Branch Protection
**Timestamp**: 2026-09-06T03:39:59Z
**User Input**: "Add a protected push to main "
**AI Response**: "Inspected public GitHub branch state: main was unprotected. Signed-in browser revealed active ruleset 22368425 named main had no branch targets. Configured exact refs/heads/main inclusion, GitHub Actions pr-gate requirement, and up-to-date branches, preserving required PRs, deletion and force-push blocking, existing review settings, and empty bypass list. Clicked Save changes; GitHub requires fresh Confirm access authentication. Form remains pending user authentication; protection is not yet verified as saved."
**Context**: External branch protection setup; awaiting GitHub authentication, no merge/push/publication performed.

---

## Main Branch Protection Verified
**Timestamp**: 2026-09-06T03:43:43Z
**User Input**: "done"
**AI Response**: "Verified saved active ruleset 22368425 targets main with an empty bypass list. GitHub API reports protected=true and active deletion, non-fast-forward, pull-request, and required-status-check rules. Existing PR requirements retain one approving review and Code Owner approval where applicable. pr-gate is bound to GitHub Actions integration 15368 with strict up-to-date policy. No push or merge performed."
**Context**: User completed GitHub authentication; requested main protection is active and verified.

---

## Release Handoff Status
**Timestamp**: 2026-09-06T03:45:48Z
**User Input**: "what else?"
**AI Response**: "Branch protection is complete. GitHub has no open PR targeting main. Local changes are limited to protection state/audit records; changelog still marks 0.1.2 Unreleased. Remaining steps: finalize release date, commit/push remaining records, open develop-to-main PR, satisfy pr-gate and required review, merge, complete any pypi environment approval, then verify published package and matching RTD build."
**Context**: Read-only release handoff assessment; no PR, push, or merge performed.

---

## Release 0.1.2 Handoff Authorization
**Timestamp**: 2026-09-06T03:47:07Z
**User Input**: "Go"
**AI Response**: "Proceeding with the approved release sequence: finalize changelog, commit/push develop, open PR into main, follow CI, retain required independent review, merge when protections permit, complete applicable publication approval, and verify PyPI and RTD. Finalized 0.1.2 changelog date to 2026-09-06 and created release execution checkboxes."
**Context**: Release execution authorized; no protection bypass or self-approval.

---

## Publication Discovered and Verified
**Timestamp**: 2026-09-06T03:50:16Z
**AI Response**: "Committed and pushed final release records as d057e13. Fresh origin/main showed PR #2 had already merged the release as 34f1fac; public PyPI serves 0.1.2 and Release run 34009511176 succeeded. Verified a fresh OpenUtility==0.1.2 installation from PyPI with isolated imports and all HiGHS/HPR smoke tests. RTD latest build 34413863 succeeded on the same main commit. Updated release records and synchronized develop with origin/main before preparing a draft documentation PR. A ready documentation PR would trigger the existing automatic patch bump, so the already-published 0.1.2 release must not be repeated."
**Context**: Adapted authorized release sequence to externally completed publication; no additional release or review bypass.

---
