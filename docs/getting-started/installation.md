# Installation

`medscheduler` targets **Python 3.9+** and follows PEP 621 packaging. The library has a small set of core
dependencies to keep installs lightweight. Optional visualization helpers require `matplotlib`.

## Quick install (pip)

```bash
pip install medscheduler
```

To enable the optional plotting utilities:

```bash
pip install matplotlib
```

## Verify your setup

```python
from medscheduler import AppointmentScheduler

# Basic smoke test
s = AppointmentScheduler(seed=0)
print("appointments/hour:", s.appointments_per_hour)
```

If this runs without errors, your installation is OK.

## Supported Python versions

- CPython 3.9, 3.10, 3.11 (and newer, as available on PyPI/RTD)
- OS: Linux, macOS, Windows (pure-Python package)

## Alternative installs

### Using Conda/Mamba

```bash
# Create an environment (recommended)
mamba create -n medscheduler -y python=3.11
mamba activate medscheduler

# Install from PyPI inside the environment
pip install medscheduler
# Optional plotting
pip install matplotlib
```

### Editable/development install (from source)

```bash
git clone https://github.com/<your-org-or-user>/medscheduler.git
cd medscheduler
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
# Optional plotting
pip install matplotlib
```

## Troubleshooting

- **Build fails on Read the Docs**: ensure `docs/requirements.txt` includes `sphinx`, `myst-parser`,
  `myst-nb`, `pydata-sphinx-theme`, and any optional extras you import in docs.
- **ImportError for pandas/numpy**: upgrade pip and retry:
  ```bash
  python -m pip install --upgrade pip
  pip install --upgrade numpy pandas
  ```
- **Conflicting environments**: prefer a clean virtual environment (venv/conda) and reinstall.

## Next steps

- Read **What is medscheduler?** for an overview of concepts and outputs.
- Jump to **Quickstart** to generate your first synthetic dataset and export CSV files.
