"""Sphinx configuration for OpenUtility documentation."""

from __future__ import annotations

project = "OpenUtility"
author = "Tim Walmsley"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

autodoc_typehints = "description"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "alabaster"
