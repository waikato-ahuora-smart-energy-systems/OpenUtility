# Build instructions

From the repository root with Python >=3.14.2, install the environment with
`uv sync --frozen --extra dev --extra docs --extra notebook --extra release`.
Run `uv run --no-sync python tools/release_check.py` for the full gate.
Standalone build: `python -m build --no-isolation`; validate with
`python -m twine check dist/*`. Expected outputs are a wheel and source archive.
Network access is required for package installation and the dependency audit.
The full gate uses checkout-only workflow and scaffold tests; run it from Git.
