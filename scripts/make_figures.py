r"""Approximate replicas of the paper's eight result figures, in Python.

The originals were made in R and were not preserved. These are rebuilt from the
reconstructed parameterisation (see reconstruct_paper.py and calibrate.py), so
they are APPROXIMATIONS, not the published images: the penalty figures land
within 0.4% of the paper's stated values, and everything else follows from the
same fitted parameters.

The paper's eight figures:

  Fig 5  penalty cost      equal distribution
  Fig 6  transport cost    equal distribution
  Fig 7  cost comparison   equal distribution
  Fig 8  service levels    equal distribution
  Fig 9  penalty cost      prioritized distribution
  Fig 10 transport cost    prioritized distribution
  Fig 11 cost comparison   prioritized distribution
  Fig 12 service levels    prioritized distribution

The two distribution policies, as the paper describes them:

  EQUAL        every ZIP is served the same FRACTION of its demand.
  PRIORITIZED  ZIPs are served in descending CHI order, so the most vulnerable
               are filled first. The paper: "using our CHI scores to prioritize
               underserved communities ... this drives our supply chain model to
               give higher service levels to these geographic regions".

Here CHI is stood in for by the CDC SVI percentile (RPL_THEMES), which is the
vulnerability measure the project's own data carries.

    python scripts/make_figures.py
"""
from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reconstruct_paper import (COST_PER_MILE, load_demand, load_miles,  # noqa: E402
                               load_penalty)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures")

# CALIBRATED in calibrate.py against the paper's published penalty figures.
PENALTY_RATE = 70.0
SUPPLY1_FRACTION = 0.26

PAPER_PENALTY = {1: 34.0, 2: 22.0, 4: 0.0}
SCEN_LABELS = ["Current\nsupply", "Supply x2", "Supply x3", "Supply x4"]

INK = "#1f3b57"
ACCENT = "#c1553b"
GREY = "#8a97a3"


def run(z, policy):
    """Return the four-scenario table for one distribution policy."""
    total = z["demand"].sum()
    rows = []
    for k in (1, 2, 3, 4):
        supply = min(SUPPLY1_FRACTION * total * k, total)
        d = z.copy()
        if policy == "equal":
            d["served"] = d["demand"] * (supply / total)
        else:
            # Fill the most vulnerable first.
            d = d.sort_values("penalty", ascending=False).reset_index(drop=True)
            remaining, served = supply, []
            for r in d.itertuples(index=False):
                take = min(r.demand, remaining)
                served.append(take)
                remaining -= take
            d["served"] = served
        d["unmet"] = d["demand"] - d["served"]
        rows.append({
            "scenario": k,
            "service_level": d["served"].sum() / total,
            "penalty_MUSD": (d["unmet"] * PENALTY_RATE).sum() / 1e6,
            "transport_MUSD": (d["served"] * d["miles"] * COST_PER_MILE).sum() / 1e6,
            # service level in the most-vulnerable third - the paper's actual point
            "top_tertile_service": (
                d.nlargest(len(d) // 3, "penalty")["served"].sum()
                / d.nlargest(len(d) // 3, "penalty")["demand"].sum()),
        })
    return pd.DataFrame(rows)


def _style(ax, title, ylabel):
    ax.set_title(title, fontsize=11, color=INK, pad=10)
    ax.set_ylabel(ylabel, fontsize=9, color=INK)
    ax.set_xticks(range(4))
    ax.set_xticklabels(SCEN_LABELS, fontsize=8)
    ax.tick_params(colors=GREY, labelsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GREY)
    ax.grid(axis="y", color=GREY, alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)


def bar(df, col, title, ylabel, fname, fmt="{:.1f}", overlay_paper=False):
    fig, ax = plt.subplots(figsize=(6.2, 3.9), dpi=150)
    vals = df[col].tolist()
    ax.bar(range(4), vals, color=INK, width=0.58, label="reconstructed")
    for i, v in enumerate(vals):
        ax.annotate(fmt.format(v), (i, v), ha="center", va="bottom",
                    fontsize=8, color=INK,
                    xytext=(0, 2), textcoords="offset points")
    if overlay_paper:
        xs = [k - 1 for k in PAPER_PENALTY]
        ys = list(PAPER_PENALTY.values())
        ax.scatter(xs, ys, s=46, facecolor="none", edgecolor=ACCENT,
                   linewidth=1.6, zorder=5, label="published value")
        ax.legend(frameon=False, fontsize=8, loc="upper right")
    _style(ax, title, ylabel)
    fig.tight_layout()
    p = os.path.join(OUT, fname)
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    return p


def comparison(df, title, fname):
    fig, ax = plt.subplots(figsize=(6.2, 3.9), dpi=150)
    w = 0.38
    xs = range(4)
    ax.bar([x - w / 2 for x in xs], df["penalty_MUSD"], width=w, color=INK, label="penalty")
    ax.bar([x + w / 2 for x in xs], df["transport_MUSD"], width=w, color=ACCENT,
           label="transport")
    _style(ax, title, "cost (million USD)")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    p = os.path.join(OUT, fname)
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    return p


def service(df, title, fname):
    fig, ax = plt.subplots(figsize=(6.2, 3.9), dpi=150)
    xs = range(4)
    ax.bar(xs, 100 * df["service_level"], color=INK, width=0.58, label="all ZIPs")
    ax.plot(xs, 100 * df["top_tertile_service"], marker="o", color=ACCENT,
            linewidth=1.8, markersize=5, label="most-vulnerable third")
    for i, v in enumerate(100 * df["service_level"]):
        ax.annotate("%.0f%%" % v, (i, v), ha="center", va="bottom", fontsize=8,
                    color=INK, xytext=(0, 2), textcoords="offset points")
    ax.set_ylim(0, 112)
    _style(ax, title, "service level (%)")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    p = os.path.join(OUT, fname)
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    return p


def main():
    os.makedirs(OUT, exist_ok=True)
    z = load_miles(load_penalty(load_demand()))
    eq, pr = run(z, "equal"), run(z, "prioritized")

    made = []
    made.append(bar(eq, "penalty_MUSD", "Figure 5 — penalty cost, equal distribution",
                    "penalty cost (million USD)", "fig05_penalty_equal.png",
                    overlay_paper=True))
    made.append(bar(eq, "transport_MUSD", "Figure 6 — transportation cost, equal distribution",
                    "transport cost (million USD)", "fig06_transport_equal.png", "{:.2f}"))
    made.append(comparison(eq, "Figure 7 — cost comparison, equal distribution",
                           "fig07_costcomparison_equal.png"))
    made.append(service(eq, "Figure 8 — service levels, equal distribution",
                        "fig08_service_equal.png"))
    made.append(bar(pr, "penalty_MUSD", "Figure 9 — penalty cost, prioritized distribution",
                    "penalty cost (million USD)", "fig09_penalty_prioritized.png"))
    made.append(bar(pr, "transport_MUSD",
                    "Figure 10 — transportation cost, prioritized distribution",
                    "transport cost (million USD)", "fig10_transport_prioritized.png", "{:.2f}"))
    made.append(comparison(pr, "Figure 11 — cost comparison, prioritized distribution",
                           "fig11_costcomparison_prioritized.png"))
    made.append(service(pr, "Figure 12 — service levels, prioritized distribution",
                        "fig12_service_prioritized.png"))

    print("EQUAL DISTRIBUTION")
    print(eq.round(3).to_string(index=False))
    print("\nPRIORITIZED DISTRIBUTION")
    print(pr.round(3).to_string(index=False))
    print("\nThe paper's point, visible in the tertile line:")
    print("  most-vulnerable third served at scenario 1 — equal %.0f%%, prioritized %.0f%%"
          % (100 * eq.top_tertile_service.iloc[0], 100 * pr.top_tertile_service.iloc[0]))
    print("\nwrote %d figures to %s" % (len(made), os.path.normpath(OUT)))
    for p in made:
        print("   ", os.path.basename(p))
    return 0


if __name__ == "__main__":
    sys.exit(main())
