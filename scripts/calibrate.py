r"""Fit the paper's unrecorded parameters to its published results, and report
honestly where the published numbers disagree with each other.

reconstruct_paper.py recovers demand exactly. Two parameters were never
recorded: the shortage penalty actually used (the paper gives a $35-$70 RANGE,
not a value) and the scenario-1 supply level. This grid-searches both against
everything the paper publishes:

    service level  scenario 1   32%
    service level  scenario 4  100%
    penalty cost   scenario 1  $34M
    penalty cost   scenario 2  $22M
    penalty cost   scenario 4   $0

THE FINDING THIS PRODUCES. Those five numbers are not mutually consistent under
a single-echelon model with proportional (equal) distribution:

  - the RATIO 34/22 = 1.545 pins supply_1 at about 26% of demand, because with
    supply doubling, unmet_2/unmet_1 = (D-2S)/(D-S), and that equals 0.647 only
    when S = 0.261 D
  - but the paper separately reports a 32% service level at scenario 1, which
    would put unmet_2/unmet_1 at (1-0.64)/(1-0.32) = 0.529, i.e. a penalty pair
    of 34 and 18, not 34 and 22

So the reported service level and the reported penalty pair imply different
supply levels. Both cannot be reproduced at once. This script reports the best
fit to each target set separately rather than quietly optimising one and
presenting it as agreement.

Usage:  python scripts/calibrate.py
"""
from __future__ import annotations

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reconstruct_paper import (COST_PER_MILE, load_demand, load_miles,  # noqa: E402
                               load_penalty)

PAPER_PENALTY = {1: 34.0, 2: 22.0, 3: None, 4: 0.0}   # $M
PAPER_SERVICE = {1: 0.32, 4: 1.00}


def scenarios(z, supply1, penalty_rate=None):
    """Equal (proportional) distribution: every ZIP is served the same fraction
    of its demand. That is what the paper's 'Equal Distribution' scenarios mean,
    and it is the allocation the reported numbers have to come from."""
    total = z["demand"].sum()
    pen = (pd.Series(penalty_rate, index=z.index) if penalty_rate is not None
           else z["penalty"])
    rows = []
    for k in (1, 2, 3, 4):
        supply = min(supply1 * k, total)
        frac = supply / total
        served = z["demand"] * frac
        unmet = z["demand"] - served
        rows.append({
            "scenario": k,
            "service_level": frac,
            "penalty_MUSD": float((unmet * pen).sum() / 1e6),
            "transport_MUSD": float((served * z["miles"] * COST_PER_MILE).sum() / 1e6),
        })
    return pd.DataFrame(rows)


def fit(z, targets, use_service):
    """Grid search over (penalty rate, scenario-1 supply fraction)."""
    total = z["demand"].sum()
    best = None
    rate = 35.0
    while rate <= 70.0001:
        frac = 0.15
        while frac <= 0.40001:
            s = scenarios(z, frac * total, rate)
            err = 0.0
            for k, want in targets.items():
                if want is None:
                    continue
                got = s.loc[s.scenario == k, "penalty_MUSD"].iloc[0]
                err += ((got - want) / max(want, 1.0)) ** 2 if want else got ** 2 / 100
            if use_service:
                for k, want in PAPER_SERVICE.items():
                    got = s.loc[s.scenario == k, "service_level"].iloc[0]
                    err += ((got - want) / want) ** 2
            if best is None or err < best[0]:
                best = (err, rate, frac, s)
            frac += 0.002
        rate += 0.5
    return best


def main():
    z = load_miles(load_penalty(load_demand()))
    total = z["demand"].sum()
    print("demand recovered exactly: %s people across %d ZIPs\n" % (f"{total:,.0f}", len(z)))

    print("=" * 74)
    print("FIT A - to the published PENALTY figures only ($34M, $22M, $0)")
    err, rate, frac, s = fit(z, PAPER_PENALTY, use_service=False)
    print("  penalty rate            $%.1f   (paper's stated band: $35-$70)" % rate)
    print("  scenario-1 supply        %.1f%% of demand" % (100 * frac))
    print()
    print(s.assign(service_level=(100 * s.service_level).round(1),
                   penalty_MUSD=s.penalty_MUSD.round(1),
                   transport_MUSD=s.transport_MUSD.round(2)).to_string(index=False))
    print("  vs paper: penalty %s  |  service %s" % (
        ", ".join("S%d %.1f (want %.0f)" % (k, s.loc[s.scenario == k, "penalty_MUSD"].iloc[0], v)
                  for k, v in PAPER_PENALTY.items() if v is not None),
        ", ".join("S%d %.0f%% (want %.0f%%)" % (k, 100 * s.loc[s.scenario == k, "service_level"].iloc[0],
                                                100 * v) for k, v in PAPER_SERVICE.items())))

    print("\n" + "=" * 74)
    print("FIT B - to the published SERVICE LEVELS only (32%, 100%)")
    err2, rate2, frac2, s2 = fit(z, {}, use_service=True)
    print("  penalty rate            $%.1f" % rate2)
    print("  scenario-1 supply        %.1f%% of demand" % (100 * frac2))
    print()
    print(s2.assign(service_level=(100 * s2.service_level).round(1),
                    penalty_MUSD=s2.penalty_MUSD.round(1),
                    transport_MUSD=s2.transport_MUSD.round(2)).to_string(index=False))
    print("  vs paper: penalty %s" % ", ".join(
        "S%d %.1f (want %.0f)" % (k, s2.loc[s2.scenario == k, "penalty_MUSD"].iloc[0], v)
        for k, v in PAPER_PENALTY.items() if v is not None))

    print("\n" + "=" * 74)
    print("CONCLUSION")
    print("  The two fits disagree on supply: %.1f%% vs %.1f%% of demand."
          % (100 * frac, 100 * frac2))
    print("  Fit A reproduces $34M and $22M within a fraction of a million but")
    print("  puts the scenario-1 service level at %.0f%%, not 32%%."
          % (100 * s.loc[s.scenario == 1, "service_level"].iloc[0]))
    print("  Fit B reproduces 32%% exactly but gives $%.0fM and $%.0fM."
          % (s2.loc[s2.scenario == 1, "penalty_MUSD"].iloc[0],
             s2.loc[s2.scenario == 2, "penalty_MUSD"].iloc[0]))
    print("  Under equal distribution these targets are arithmetically")
    print("  incompatible, so no parameter choice satisfies both.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
