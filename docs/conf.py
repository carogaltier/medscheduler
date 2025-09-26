import os
import sys
from datetime import datetime

# Make package importable for autodoc (if enabled later)
sys.path.insert(0, os.path.abspath("../src"))

project = "medscheduler"
author = "Carolina Gonzalez Galtier"
copyright = f"{datetime.now():%Y}, {author}"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx.ext.viewcode",
]

# Recognize both .md and .rst files
source_suffix = {
    ".md": "markdown",
    ".rst": "restructuredtext",
}

# MyST options
myst_enable_extensions = ["colon_fence", "deflist", "attrs_block", "attrs_inline"]

# Theme
html_theme = "pydata_sphinx_theme"

# Logo path
html_logo = "_static/logo.png"
html_favicon = "_static/logo.png"
html_static_path = ["_static"]
