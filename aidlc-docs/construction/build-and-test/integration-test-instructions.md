# Integration test instructions

Run `python tools/release_check.py` from the checkout. It builds the source archive
and wheel, installs the wheel and dependencies into a fresh environment, and
executes Python with `-I` from outside the checkout. The test verifies imported
OpenUtility matches the installed distribution and runs HiGHS binary, heat-pump,
and refrigeration solves. Temporary environments are removed automatically.
Inspect the source archive for tools/release_check.py and the wheel metadata for
https://openutility.readthedocs.io/en/latest/.
Build hosted documentation through the repository-connected RTD project after
merging. Existing RTD build 34413757 passed for main commit 22ff10f7.
