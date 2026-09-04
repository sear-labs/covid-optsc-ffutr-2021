"""Where the data lives. Importable without building or solving anything.

Kept separate from model.py on purpose: anything that only needs to know where
files are - tests, scripts, tooling - imports this and pays nothing for it.
"""
import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]

# Derived, not explicit. Override to point at a different instance.
DATA_DIR = Path(os.environ.get("COVID_SC_DATA_DIR", _ROOT / "data" / "raw"))

# Everything a run produces goes here, so data/raw stays immutable.
RESULTS_DIR = Path(os.environ.get("COVID_SC_RESULTS_DIR", _ROOT / "results"))

TABLES = ("supply", "through", "demand", "penalty", "cost")
