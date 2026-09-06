"""Execute public notebooks against this interpreter's installed OpenUtility wheel.

Run with an isolated wheel environment, for example::

    /tmp/notebook-venv/bin/python -I tools/check_notebooks.py --output-dir /tmp/examples

Each notebook runs in a new kernel and empty working directory. Outputs are saved
as executed notebooks and standalone HTML; source files are never modified.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile


INSTALL_GUARD = """
from importlib.metadata import distribution
from pathlib import Path
import sys
import OpenUtility
actual = Path(OpenUtility.__file__).resolve()
expected = Path(distribution('OpenUtility').locate_file('OpenUtility/__init__.py')).resolve()
assert actual == expected and actual.is_relative_to(Path(sys.prefix).resolve()), (
    f'Expected an installed wheel in the kernel environment; imported {actual}'
)
"""


def main() -> None:
    import nbformat
    from jupyter_client import KernelManager
    from nbclient import NotebookClient
    from nbconvert import HTMLExporter

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--notebooks-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "docs" / "notebooks",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=120, help="Seconds per cell")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.output_dir.resolve() == args.notebooks_dir.resolve():
        parser.error("--output-dir must differ from the notebook source directory")
    notebooks = sorted(args.notebooks_dir.glob("*.ipynb"))
    if not notebooks:
        parser.error(f"No notebooks found in {args.notebooks_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for path in notebooks:
        print(f"Executing {path.name}", flush=True)
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        for cell in notebook.cells:
            if cell.cell_type == "code":
                cell.outputs = []
                cell.execution_count = None
        # This guard executes inside the actual kernel, before any tutorial code.
        notebook.cells.insert(0, nbformat.v4.new_code_cell(INSTALL_GUARD))
        manager = KernelManager(kernel_name="python3")
        manager.kernel_spec.argv = [
            sys.executable,
            "-I",
            "-m",
            "ipykernel_launcher",
            "-f",
            "{connection_file}",
        ]
        with tempfile.TemporaryDirectory(prefix="openutility-example-") as workdir:
            NotebookClient(
                notebook,
                km=manager,
                timeout=args.timeout,
                allow_errors=False,
                resources={"metadata": {"path": workdir}},
                record_timing=False,
            ).execute(cleanup_kc=True)
        notebook.cells.pop(0)
        for cell in notebook.cells:
            if cell.cell_type == "code" and cell.execution_count is not None:
                cell.execution_count -= 1
        nbformat.validate(notebook)
        nbformat.write(notebook, args.output_dir / path.name)
        html, _ = HTMLExporter().from_notebook_node(notebook)
        (args.output_dir / f"{path.stem}.html").write_text(html, encoding="utf-8")
    print(f"Executed {len(notebooks)} notebooks; results: {args.output_dir}")


if __name__ == "__main__":
    main()
