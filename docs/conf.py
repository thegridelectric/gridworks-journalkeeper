"""Sphinx configuration."""

project = "Gridworks Journal Keeper"
author = "GridWorks"
copyright = "2023, GridWorks"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
