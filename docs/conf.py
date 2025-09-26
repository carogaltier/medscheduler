import os
import sys
from datetime import datetime

# Add src to path for autodoc (optional)
sys.path.insert(0, os.path.abspath("../src"))

project = "medscheduler"
author = "medscheduler contributors"
copyright = f"{datetime.now():%Y}, {author}"
release = ""  # set from package version dynamically if you prefer

extensions = [
    "myst_parser",
    "myst_nb",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx.ext.viewcode",
]


# MyST / MyST-NB options
myst_enable_extensions = ["colon_fence", "deflist", "attrs_block", "attrs_inline"]
nb_execution_mode = "off" 

html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "show_prev_next": False,
    "navbar_align": "content",
    "logo": {
        "text": "medscheduler",
    },
    "navigation_depth": 3,
}
html_static_path = []
html_title = "medscheduler documentation"

# Intersphinx (optional examples)
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", {}),
    "numpy": ("https://numpy.org/doc/stable/", {}),
    "pandas": ("https://pandas.pydata.org/docs/", {}),
}

# Autodoc (optional)
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "inherited-members": True,
}


autosectionlabel_prefix_document = True
