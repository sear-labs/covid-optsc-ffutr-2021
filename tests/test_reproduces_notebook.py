r"""Assert the number the original notebook recorded.

There is no second implementation to reconcile against, so the referent is the
notebook's own stored output: cells 18 and 23 of
Model Formulation/Python Model (Erick)/COVID_supply_chain.ipynb both print

    Objective Function Value:
    579000.0

That is an LP with no integer variables, so unlike the lithium model it solves
to proven optimality and the number is exact. A tolerance is here only to absorb
floating-point noise, not solver drift.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

NOTEBOOK_OBJECTIVE = 579000.0


def test_instance_loads():
    from covid_sc.model import load_instance
    inst = load_instance()
    assert len(inst["supply"]) == 1
    assert len(inst["through"]) == 5
    assert len(inst["demand"]) == 10
    assert len(inst["cost"]) == 55


def test_objective_matches_the_notebook():
    from covid_sc.model import solve
    res = solve()
    assert abs(res["objective"] - NOTEBOOK_OBJECTIVE) < 1e-6, (
        "objective %.4f, notebook recorded %.1f" % (res["objective"], NOTEBOOK_OBJECTIVE))


def test_domain_invariants():
    """Whatever must be true of any correct answer."""
    from covid_sc.model import load_instance, solve
    inst = load_instance()
    res = solve(inst)

    assert (res["flows"]["Flow"] >= -1e-9).all(), "negative flow"

    shipped_out = res["flows"].groupby("From")["Flow"].sum()
    for p, cap in inst["supply"].items():
        assert shipped_out.get(p, 0.0) <= cap + 1e-6, "producer %s over supply" % p

    into = res["flows"].groupby("To")["Flow"].sum()
    for d, cap in inst["through"].items():
        assert into.get(d, 0.0) <= cap + 1e-6, "depot %s over throughput" % d
        # conservation: what enters a depot leaves it
        assert abs(into.get(d, 0.0) - shipped_out.get(d, 0.0)) < 1e-6, \
            "depot %s does not conserve flow" % d

    deficit = dict(zip(res["deficits"].get("Customer", []),
                       res["deficits"].get("Deficit", [])))
    for c, dem in inst["demand"].items():
        got = into.get(c, 0.0) + deficit.get(c, 0.0)
        assert abs(got - dem) < 1e-6, "customer %s demand not balanced" % c


def test_data_tier_is_not_written_to():
    from covid_sc.paths import DATA_DIR, RESULTS_DIR
    assert DATA_DIR != RESULTS_DIR
    assert DATA_DIR.exists()
    for t in ("supply", "through", "demand", "penalty", "cost"):
        assert (DATA_DIR / f"{t}.csv").exists(), "%s.csv missing" % t


def test_no_absolute_paths_or_credentials():
    import re
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "src", "covid_sc", "model.py")
    text = open(src, encoding="utf-8").read()
    assert "C:" + chr(92) not in text
    assert not re.search(r"WLSACCESSID|WLSSECRET|LICENSEID", text)
