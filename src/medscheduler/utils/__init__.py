"""Utility namespace for medscheduler.

Submodules
----------
- reference_data_utils : Small, testable helpers to parse/download NHS reference data.
- plotting             : Optional visualization helpers (requires `matplotlib`; install extra `viz`).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any, Final, Tuple

__all__: Final[Tuple[str, ...]] = ("reference_data_utils", "plotting")


def __getattr__(name: str) -> Any:
    if name in __all__:
        return import_module(f"{__name__}.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + list(__all__))
