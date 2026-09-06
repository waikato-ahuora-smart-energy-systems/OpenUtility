# Unit test instructions

Run `python -m pytest --cov=OpenUtility --cov-report=term-missing --cov-fail-under=90`
from the checkout. The current result is 188 tests passing and 90.24% coverage.
Run `python -m pytest tests/test_release_tooling.py -q` for release regressions.
The new regression checks subprocess isolation from the checkout and PYTHONPATH.
PBT-08 is N/A: this scope adds deterministic subprocess integration testing only.
