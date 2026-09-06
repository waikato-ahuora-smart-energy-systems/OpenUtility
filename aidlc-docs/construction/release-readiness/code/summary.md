# Release readiness code summary

Changed tools/release_check.py to execute the fresh-install smoke code using
isolated Python from its temporary environment directory, and assert that the
import belongs to the installed distribution. Added a subprocess regression
covering checkout/PYTHONPATH isolation. Included /tools in the source archive.
Updated README installation instructions, hosted documentation URL, release notes,
and the release strategy description. Public package API and dependencies unchanged.
Validation results are in ../../build-and-test/build-and-test-summary.md.
