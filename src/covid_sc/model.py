r"""COVID-19 therapeutics supply chain: minimum-cost network flow with shortfall penalties.

The model from the NSF EAGER project (award #2028612). A single-commodity
transshipment network - producers ship to depots, depots ship to customers - that
minimises shipping cost plus a penalty on unmet demand.

    minimise   sum_a cost_a * flow_a  +  sum_c penalty_c * deficit_c

    s.t.  sum of flow out of each producer  <=  its supply
          flow into each customer + its deficit  ==  its demand
          flow out of each depot  ==  flow into it          (conservation)
          flow into each depot  <=  its throughput capacity

Deficit variables make the model always feasible: if demand cannot be met the
solver pays the penalty instead of returning infeasible, which is what you want
when the question is "who goes short, and where".

Ported from Model Formulation/Python Model (Erick)/COVID_supply_chain.ipynb.
The notebook built the model twice - once from inline dictionaries and once from
the spreadsheet. This is the spreadsheet version, which is the one that matters.

TWO DEFECTS IN THE NOTEBOOK ARE FIXED HERE, both flagged rather than silently
carried over:

1. The depot conservation constraint iterated `for depot in depots` - the
   dictionary belonging to the OTHER, hardcoded model - instead of `depots1`.
   It happened to give the right answer only because both instances used the
   same depot names. With any other spreadsheet it would silently constrain the
   wrong set. Fixed: the constraint iterates the depots actually loaded.

2. `DataFrame.append` was removed in pandas 2.0, so the notebook's reporting
   cells cannot run on any current pandas. Replaced with concat-free
   list-of-rows construction.

All inputs are synthetic - one producer P1, depots D1-D5, customers C1-C10.
There is no protected information in this model or its data.
"""
from __future__ import annotations

import pandas as pd

from .paths import DATA_DIR, RESULTS_DIR, check_data_dir


def _read(name: str) -> pd.DataFrame:
    """Read one instance table from the immutable data tier."""
    check_data_dir(DATA_DIR)
    path = DATA_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing - the instance is incomplete")
    return pd.read_csv(path)


def load_instance(data_dir=None):
    """Load the five instance tables into plain Python structures.

    Returns a dict with supply, through, demand, penalty (all name -> value)
    and cost ((from, to) -> value). No solver involved, so this is cheap and
    testable on its own.
    """
    global DATA_DIR
    if data_dir is not None:
        DATA_DIR = data_dir

    supply = _read("supply").set_index("Producer")["Supply"].to_dict()
    through = _read("through").set_index("Depot")["Capacity"].to_dict()
    demand = _read("demand").set_index("Customer")["Demand"].to_dict()
    penalty = _read("penalty").set_index("Customer")["Penalty"].to_dict()

    cost_df = _read("cost")
    cost = {(r.From, r.To): r.Cost for r in cost_df.itertuples(index=False)}

    return {"supply": supply, "through": through, "demand": demand,
            "penalty": penalty, "cost": cost}


def build_model(inst, env=None):
    """Build the Gurobi model from a loaded instance. Does not solve."""
    import gurobipy as gp

    model = gp.Model("CovidTherapeuticsSupplyChain", env=env) if env is not None \
        else gp.Model("CovidTherapeuticsSupplyChain")

    arcs, cost = gp.multidict(dict(inst["cost"]))
    customers_idx, penalty = gp.multidict(dict(inst["penalty"]))

    flow = model.addVars(arcs, obj=cost, name="flow")
    deficit = model.addVars(customers_idx, obj=penalty, name="deficit")
    model.update()

    supply, through, demand = inst["supply"], inst["through"], inst["demand"]

    model.addConstrs(
        (gp.quicksum(flow.select(p, "*")) <= supply[p] for p in supply),
        name="producer")

    model.addConstrs(
        (gp.quicksum(flow.select("*", c) + deficit.select(c)) == demand[c]
         for c in demand),
        name="customer")

    # NOTE: iterates `through`, the depots actually loaded. The notebook
    # iterated the other model's `depots` here - see the module docstring.
    model.addConstrs(
        (gp.quicksum(flow.select(d, "*")) == gp.quicksum(flow.select("*", d))
         for d in through),
        name="depot_conservation")

    model.addConstrs(
        (gp.quicksum(flow.select("*", d)) <= through[d] for d in through),
        name="depot_capacity")

    model.update()
    return model, flow, deficit, cost, penalty


def solve(inst=None, env=None, verbose=False):
    """Load, build, solve, and return the model plus tidy result frames."""
    inst = inst or load_instance()
    model, flow, deficit, cost, penalty = build_model(inst, env=env)
    if not verbose:
        model.Params.OutputFlag = 0
    model.optimize()

    flows = pd.DataFrame(
        [{"From": a[0], "To": a[1], "Flow": flow[a].x, "Cost": flow[a].x * cost[a]}
         for a in flow if flow[a].x > 1e-6])
    deficits = pd.DataFrame(
        [{"Customer": c, "Deficit": deficit[c].x, "Penalty": deficit[c].x * penalty[c]}
         for c in deficit if deficit[c].x > 1e-6])

    return {"model": model, "objective": model.ObjVal,
            "flows": flows, "deficits": deficits}


def write_results(res, results_dir=None):
    """Write the result tables to results/. Never touches data/raw."""
    out = results_dir or RESULTS_DIR
    out.mkdir(parents=True, exist_ok=True)
    res["flows"].to_csv(out / "flows.csv", index=False)
    res["deficits"].to_csv(out / "deficits.csv", index=False)
    return out
