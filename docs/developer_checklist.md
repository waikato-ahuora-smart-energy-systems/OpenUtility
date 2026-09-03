# Developer Checklist

Install the package with development dependencies:

```bash
python -m pip install -e ".[dev,docs,release]"
```

Run the full release gate:

```bash
python tools/release_check.py
```

The gate checks linting, formatting, type checking, tests with coverage, Sphinx
docs, build artifacts, wheel metadata, dependency audit, and a fresh install
smoke test.

Public tests must use minimal reproducible fixtures under `tests/`; they should
not import private replication workflows or read private generated artifacts.
