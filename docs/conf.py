import os
import sys
from datetime import datetime

# Make package importable for autodoc (if enabled later)
sys.path.insert(0, os.path.abspath("../src"))

project = "medscheduler"
author = "medscheduler contributors"
copyright = f"{datetime.now():%Y}, {author}"

# Use MyST Markdown only (no myst-nb) to avoid extension conflicts
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx.ext.viewcode",
]

# Root document is index.md (not index.rst)
root_doc = "index"

# Recognize both .md and .rst files
source_suffix = {
    ".md": "markdown",
    ".rst": "restructuredtext",
}

# MyST options
myst_enable_extensions = ["colon_fence", "deflist", "attrs_block", "attrs_inline"]

# Theme
html_theme = "pydata_sphinx_theme"
html_title = "Medscheduler"

# Don't try to build API folder for now (until we wire autodoc)
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "api/**"]

# Logo path (relative to docs/)
html_logo = "_static/logo.png"

# Opcional: favicon
html_favicon = "_static/logo.png"

# Theme options
html_theme_options = {
    "logo": {
        "text": "Medscheduler",
    },
    "show_toc_level": 2,
}

html_static_path = ["_static"]
