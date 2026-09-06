# Maintainer merge review configuration

The user clarified that the exception concerns merge reviews only.

- [x] Inspect the active main ruleset and confirm the authenticated maintainer is Tim-Walmsley.
- [x] Select a narrow native configuration: separate required reviews from non-bypassable CI and PR requirements.
- [x] Prepare .github/CODEOWNERS with Tim-Walmsley owning all paths.
- [x] Prepare both GitHub forms without saving live changes.
- [x] Obtain action-time confirmation for the review bypass and ruleset migration (user: Save).
- [x] Save the review-only rule first, then remove review requirements from the core rule.
- [ ] Commit and push CODEOWNERS through the existing PR path; code-owner enforcement starts when it reaches main.
- [x] Verify effective rules and report the remaining CODEOWNERS merge dependency.

Core main rule: no bypass actors; PR required, zero approvals, code-owner review disabled; existing pr-gate with strict up-to-date checks, force-push and deletion protections retained.
Review-only rule: main branch, active, one approval and code-owner review required; only Tim-Walmsley may bypass, for pull requests only.

GitHub applies bypasses to the merging actor, not the PR author. Tim can also bypass review when merging others' PRs. No workflow-run approval settings change.

Validation: native settings review and read-only API verification. No executable code changes; property-based testing is not applicable. Security and resiliency extensions remain disabled per existing state.

GitHub authentication completed. Active review-only rule 22378749 saved first, then core rule 22368425 updated. Public API and authenticated settings confirm the intended split. CODEOWNERS remains local pending delivery through a PR to main.
