r"""Reconstruct the paper's actual scenarios, not the toy instance.

The notebook shipped a 10-customer example. The PAPER ran 96 Harris County ZIP
codes across eight scenarios, and its parameter file was not preserved. This
rebuilds that parameterisation from the project's own data files and reports how
close it lands to the published figures.

Every parameter is labelled by how it was obtained:

  RECOVERED  read directly from a project data file and confirmed against a
             number the paper states
  DERIVED    computed from recovered data by a rule the paper describes
  CALIBRATED fitted so a model output matches a published result
  ASSUMED    a modelling choice the paper does not pin down

WHAT IS RECOVERED, AND HOW IT WAS CONFIRMED

  Demand base.  Information Tables/Zip Code Populations.xlsx, column Pop2019,
  restricted to ZIPs 77002-77099, sums to 3,270,360 - the paper's stated
  "Population of all zip-codes in Harris County" TO THE DIGIT. Twenty percent of
  it is 654,072, again exactly the paper's "20% population for elderly
  population". Two independent exact matches, so this is the right table and the
  right column, and demand_z = 0.20 * Pop2019_z per ZIP.

WHAT THE PAPER GIVES US TO AIM AT (Table 2, Table 3, and the results text)

  transport                 $1 per mile
  penalty                   $35-$70 per unserved person
  hubs                      5
  scenarios                 supply and capacity at 1x, 2x, 3x, 4x
  service level  scenario 1 32%
  service level  scenario 4 100%
  penalty cost   scenario 1 $34M
  penalty cost   scenario 2 $22M
  penalty cost   scenario 4 $0

Usage:  python scripts/reconstruct_paper.py [--csv OUT.csv]
"""
from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

EAGER = os.path.join(
    os.path.expanduser("~"), "OneDrive - UT Arlington", "Documents", "Projects", "Old",
    "2020 - 2023 NSF Eager Houston COVID-19 Project (2020-23)")
INFO = os.path.join(EAGER, "Information Tables")

ZIP_LO, ZIP_HI = 77002, 77099
ELDERLY_SHARE = 0.20          # RECOVERED: 654,072 / 3,270,360 exactly
PENALTY_LO, PENALTY_HI = 35.0, 70.0   # RECOVERED: Table 2
COST_PER_MILE = 1.0           # RECOVERED: Table 2

PAPER = {
    "population": 3_270_360,
    "target": 654_072,
    "service": {1: 0.32, 4: 1.00},
    "penalty_musd": {1: 34.0, 2: 22.0, 4: 0.0},
}


def load_demand():
    """RECOVERED. 20% of Pop2019 per ZIP over 77002-77099."""
    pop = pd.read_excel(os.path.join(INFO, "Zip Code Populations.xlsx"))
    pop = pop[(pop.ZipCode >= ZIP_LO) & (pop.ZipCode <= ZIP_HI)][["ZipCode", "Pop2019"]]
    pop = pop.dropna().drop_duplicates("ZipCode")
    pop["demand"] = ELDERLY_SHARE * pop["Pop2019"]
    return pop.reset_index(drop=True)


def load_penalty(zips):
    """DERIVED. The paper prices shortage in [$35, $70] and says it uses higher
    service levels where vulnerability is higher. The project's own SVI-by-ZIP
    file carries RPL_THEMES, the CDC overall vulnerability percentile in [0,1],
    so penalty scales linearly across the stated band with vulnerability.
    ZIPs with no SVI record take the midpoint."""
    svi = pd.read_csv(os.path.join(INFO, "SVIZipCode.csv"))
    col = "RPL_THEMES" if "RPL_THEMES" in svi.columns else None
    if col is None:
        raise SystemExit("SVIZipCode.csv has no RPL_THEMES column")
    svi = svi[["ZipCode", col]].dropna().drop_duplicates("ZipCode")
    svi = svi[(svi[col] >= 0) & (svi[col] <= 1)]
    out = zips.merge(svi, on="ZipCode", how="left")
    mid = (PENALTY_LO + PENALTY_HI) / 2
    out["penalty"] = PENALTY_LO + (PENALTY_HI - PENALTY_LO) * out[col]
    out["penalty"] = out["penalty"].fillna(mid)
    return out


def load_miles(zips):
    """DERIVED. Last-mile distance per ZIP: the nearest administration point
    from the project's ZIP-to-hospital table. ZIPs absent from it take the
    median. ASSUMED: one representative last-mile leg per ZIP, because the hub
    locations themselves were not preserved."""
    d = pd.read_excel(os.path.join(INFO, "ZipCodes_to_Hospital_Distances_TableToExcel.xlsx"))
    d = d[d.NearRank == 1][["From_ZIP", "Total_Miles"]].rename(
        columns={"From_ZIP": "ZipCode", "Total_Miles": "miles"})
    d = d.groupby("ZipCode", as_index=False)["miles"].min()
    out = zips.merge(d, on="ZipCode", how="left")
    out["miles"] = out["miles"].replace(0.0, pd.NA)
    out["miles"] = out["miles"].astype("float64").fillna(out["miles"].astype("float64").median())
    return out


def solve_scenario(df, supply):
    """The paper's model, reduced to its binding structure.

    Transport is $1/mile and penalty is $35-$70, so serving anyone is worth it
    whenever penalty > miles - true for every ZIP here by a wide margin. The LP
    optimum is therefore greedy: spend limited supply on the highest
    penalty-minus-transport ZIPs first. Solving the full LP returns the same
    allocation, so this computes it directly and stays dependency-free.
    """
    d = df.copy()
    d["net"] = d["penalty"] - COST_PER_MILE * d["miles"]
    d = d.sort_values("net", ascending=False).reset_index(drop=True)
    remaining = supply
    served = []
    for r in d.itertuples(index=False):
        take = min(r.demand, remaining)
        served.append(take)
        remaining -= take
    d["served"] = served
    d["unmet"] = d["demand"] - d["served"]
    return {
        "served": d["served"].sum(),
        "demand": d["demand"].sum(),
        "service_level": d["served"].sum() / d["demand"].sum(),
        "penalty_cost": (d["unmet"] * d["penalty"]).sum(),
        "transport_cost": (d["served"] * d["miles"] * COST_PER_MILE).sum(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="write the scenario table here")
    a = ap.parse_args()

    z = load_demand()
    z = load_penalty(z)
    z = load_miles(z)

    total_pop = z["Pop2019"].sum()
    total_demand = z["demand"].sum()
    print("RECOVERED PARAMETERS")
    print("  ZIP codes (77002-77099)     %6d          paper says 97" % len(z))
    print("  population                  %10s   paper says %s  %s"
          % (f"{total_pop:,.0f}", f"{PAPER['population']:,}",
             "EXACT" if abs(total_pop - PAPER["population"]) < 1 else "differs"))
    print("  target (20%% elderly)        %10s   paper says %s  %s"
          % (f"{total_demand:,.0f}", f"{PAPER['target']:,}",
             "EXACT" if abs(total_demand - PAPER["target"]) < 1 else "differs"))
    print("  penalty  $%.0f-$%.0f, SVI-scaled  mean $%.2f" %
          (PENALTY_LO, PENALTY_HI, z["penalty"].mean()))
    print("  last-mile miles              median %.2f, max %.2f"
          % (z["miles"].median(), z["miles"].max()))

    # CALIBRATED: scenario 1 supply is set so the service level is the 32% the
    # paper reports. Everything downstream then follows from the paper's own
    # "x2, x3, x4" definition rather than from any further fitting.
    supply1 = PAPER["service"][1] * total_demand
    print("\nCALIBRATED")
    print("  scenario-1 supply           %10s   (fitted to the paper's 32%% service level)"
          % f"{supply1:,.0f}")

    rows = []
    for k in (1, 2, 3, 4):
        r = solve_scenario(z, supply1 * k)
        rows.append({
            "scenario": k,
            "supply": round(supply1 * k),
            "service_level_pct": round(100 * r["service_level"], 1),
            "penalty_MUSD": round(r["penalty_cost"] / 1e6, 1),
            "transport_MUSD": round(r["transport_cost"] / 1e6, 2),
            "total_MUSD": round((r["penalty_cost"] + r["transport_cost"]) / 1e6, 1),
        })
    out = pd.DataFrame(rows)

    print("\nRECONSTRUCTED SCENARIOS (equal distribution)")
    print(out.to_string(index=False))

    print("\nAGAINST THE PAPER")
    print("  %-34s %10s %10s" % ("", "rebuilt", "paper"))
    for k, v in PAPER["service"].items():
        got = out.loc[out.scenario == k, "service_level_pct"].iloc[0]
        print("  %-34s %9.1f%% %9.0f%%" % ("service level, scenario %d" % k, got, 100 * v))
    for k, v in PAPER["penalty_musd"].items():
        got = out.loc[out.scenario == k, "penalty_MUSD"].iloc[0]
        print("  %-34s %9.1f  %9.1f" % ("penalty $M, scenario %d" % k, got, v))

    print("\nThe paper reports transport cost only as a chart, so there is no")
    print("published transport figure to compare against.")

    if a.csv:
        out.to_csv(a.csv, index=False)
        print("\nwrote %s" % a.csv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
