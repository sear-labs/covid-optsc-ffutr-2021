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


def check_data_dir(path=None):
    """Fail with the real reason when the data directory is not where we think.

    DATA_DIR is derived from this file's location, which is only correct inside
    a source checkout. After a plain `pip install` the package sits in
    site-packages and the derivation lands somewhere meaningless - and the data
    was never in the wheel to begin with, since it lives at the repo root. The
    naive symptom is "some_table.csv missing", which sends people looking for a
    corrupt download. Say what actually happened instead.
    """
    path = DATA_DIR if path is None else path
    if path.exists():
        return path
    raise FileNotFoundError(
        str(path) + " does not exist.\n\n"
        "The data ships with the REPOSITORY, not with the installed package, so\n"
        "`pip install git+https://...` gets you the code without it. Clone instead:\n\n"
        "    git clone https://github.com/sear-labs/covid-optsc-ffutr-2021.git\n"
        "    cd covid-optsc-ffutr-2021 && pip install -e .\n\n"
        "Or point $COVID_SC_DATA_DIR at a directory holding the data files."
    )
