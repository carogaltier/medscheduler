# Installation

`medscheduler` targets **Python 3.9+** and follows PEP 621 packaging standards.  
The core package is lightweight, with minimal dependencies to ensure fast installation.  
Optional visualization helpers can be installed via the `[viz]` extra.

## Quick install with pip

Install the core package from PyPI:

```bash
pip install medscheduler
```

To include optional plotting utilities:

```bash
pip install medscheduler[viz]
```

## Verify your setup

After installation, you can run a quick smoke test:

```python
from medscheduler import AppointmentScheduler

s = AppointmentScheduler(seed=0)
print("appointments/hour:", s.appointments_per_hour)
```

If this executes without errors, your installation is successful.

## Supported environments

- **Python versions:** 3.9, 3.10, 3.11 (and newer when available)  
- **Operating systems:** Linux, macOS, Windows (pure‑Python package, no compilation required)

## Recommended: isolated environments

To avoid conflicts with other packages, install medscheduler in a virtual environment:

### Conda/Mamba

```bash
# Create a new environment
mamba create -n medscheduler -y python=3.11
mamba activate medscheduler

# Install medscheduler from PyPI
pip install medscheduler[viz]
```

### Virtualenv (venv)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install medscheduler[viz]
```

## Development install (from source)

If you plan to modify or contribute to the library:

```bash
git clone https://github.com/carogaltier/medscheduler.git
cd medscheduler
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[viz]
```

## Troubleshooting

- **Missing dependencies (e.g., pandas, numpy):**  
  Upgrade pip and reinstall core libraries:  
  ```bash
  python -m pip install --upgrade pip
  pip install --upgrade numpy pandas
  ```

- **Conflicting environments:**  
  Always prefer a clean environment (`venv` or `conda`). Remove old installs before retrying.

## Next steps

- Continue to **What is Medscheduler?** for an overview of concepts and outputs.  
- Jump to **Quickstart** to generate your first synthetic dataset and export CSV files.  
