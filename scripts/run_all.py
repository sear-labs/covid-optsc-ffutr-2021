r"""Build and solve the COVID therapeutics supply-chain model.

    python scripts/run_all.py            # solve, print the summary
    python scripts/run_all.py --verbose  # with Gurobi's log

Writes results/flows.csv and results/deficits.csv. data/raw is never written to.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from covid_sc.model import load_instance, solve, write_results  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    inst = load_instance()
    print("instance: %d producer(s), %d depots, %d customers, %d arcs"
          % (len(inst["supply"]), len(inst["through"]),
             len(inst["demand"]), len(inst["cost"])))
    print("total demand %s, total supply %s"
          % (f'{sum(inst["demand"].values()):,}', f'{sum(inst["supply"].values()):,}'))

    res = solve(inst, verbose=a.verbose)
    print("\nobjective            %,.2f".replace(",.2f", ".2f") % res["objective"])
    print("arcs carrying flow   %d" % len(res["flows"]))
    print("customers short      %d" % len(res["deficits"]))
    if len(res["deficits"]):
        print("  unmet demand       %.0f" % res["deficits"]["Deficit"].sum())
        print("  penalty cost       %.2f" % res["deficits"]["Penalty"].sum())
    print("  shipping cost      %.2f" % res["flows"]["Cost"].sum())

    out = write_results(res)
    print("\nwrote %s" % out)


if __name__ == "__main__":
    main()
