"""No committed file carries an absolute path from the machine that wrote it.

This repository is clean, and this guard exists so it stays that way.

Two of the six DOI'd repositories under this release process shipped an author's
home directory into an immutable Zenodo deposit before anything checked for it -
`lithium-optsc-energies-2024` and `water-energy-coopt-scs-2021`. Four of the six,
this one included, had no guard at all, which is why those two were not caught
until a peer session audited all six.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "check_no_machine_paths.py"


def test_the_guard_script_exists():
    assert GUARD.exists(), f"{GUARD.name} is missing - the sweep is the whole protection"


def test_no_committed_file_carries_a_machine_path():
    result = subprocess.run([sys.executable, str(GUARD)], cwd=ROOT,
                            capture_output=True, text=True)
    assert result.returncode == 0, (
        "a committed file carries an absolute home path:\n"
        f"{result.stdout}{result.stderr}\n"
        "Fix it where the string is produced, not by normalising the artifact - "
        "a normaliser hides it from every reader who is not diffing bytes."
    )
