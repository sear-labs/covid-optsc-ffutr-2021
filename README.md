# COVID-19 therapeutics supply chain — NSF EAGER #2028612

A minimum-cost network-flow model for distributing COVID-19 therapeutics, with penalties on unmet
demand so the question becomes *who goes short, and where* rather than *is this feasible*.

Built under **NSF EAGER award #2028612**, *"AI-Enabled Optimization of the COVID-19 Therapeutics
Supply Chain to Support Community Public Health"* (Erick C. Jones Jr., PI).

## The model

```
minimise   Σ cost(a)·flow(a)  +  Σ penalty(c)·deficit(c)

s.t.  Σ flow out of producer p        ≤  supply(p)
      Σ flow into customer c + deficit(c)  =  demand(c)
      Σ flow out of depot d           =  Σ flow into depot d
      Σ flow into depot d             ≤  throughput(d)
```

Producers → depots → customers, one commodity. Deficit variables keep it always feasible: if demand
cannot be met the solver pays the penalty rather than returning infeasible.

## Run it

```bash
pip install -e ".[dev]"
python scripts/run_all.py
pytest -q
```

Gurobi is required, but this is a small LP — the free `pip` licence is enough.

## Reproduces

The original notebook recorded an objective of **579000.0**. This port produces the same:

```
instance: 1 producer(s), 5 depots, 10 customers, 55 arcs
total demand 404,000, total supply 500,000

objective            579000.00
arcs carrying flow   17
customers short      0
```

Unlike a MIP, this is an LP with no integer variables — it solves to proven optimality, so the
number is exact and reproducible on any solver, not an incumbent inside a gap.
`tests/test_reproduces_notebook.py` asserts it, along with the domain invariants any correct answer
must satisfy: non-negative flow, no producer over supply, no depot over throughput, conservation at
every depot, and demand balanced against deficit at every customer.

## The data is synthetic

**One producer `P1`, depots `D1`–`D5`, customers `C1`–`C10`, round figures throughout.** There are
no zip codes, no demographics and no case counts anywhere in this repository.

That is not a claim, it was checked. The source notebook opens exactly one file —
`covid_input_example.xlsx`, five sheets — and nothing else. It never touches the wider project's
`Information Tables/`, which does hold real Houston case data by demographic and zip code. Only the
traced path was brought across, converted to CSV so it ships readable.

The spreadsheet's own `instructions` sheet describes what *real* inputs would be ("The Zip Codes
demand by…", "Either Case Info or CHI"). So the **schema anticipates real data while the shipped
instance is synthetic** — the arrangement that makes this publishable. If you want to run it on real
data, the schema is `data/raw/*.csv` and the real data is not ours to hand out.

## Layout

```
data/raw/            5 instance tables + the original instructions sheet. Read-only.
src/covid_sc/        model.py (the model) · paths.py (where things live)
scripts/run_all.py   load, solve, report, write results/
notebooks/           thin walkthrough — imports the package, holds no model logic
draft/               superseded GAMS and MATLAB implementations. Not the model.
tests/               asserts the notebook's number and the domain invariants
```

## Two defects fixed in the port

Both are documented in `src/covid_sc/model.py` rather than silently corrected:

1. **The depot conservation constraint iterated the wrong dictionary.** The notebook built the model
   twice — once from inline values, once from the spreadsheet — and the spreadsheet version's
   conservation constraint looped over the *inline* model's `depots`. It gave the right answer only
   because both instances happened to use the same depot names; on any other spreadsheet it would
   have silently constrained the wrong set.
2. **`DataFrame.append` was removed in pandas 2.0**, so the notebook's reporting cells cannot run on
   any current pandas.

## Deliberately not included

- **The ArcGIS material.** A separate line of work — its published output is *"Analyzing the
  Connectivity of Combined Statistical Areas in Different Census Regions Using ArcGIS"* (ISCTJ 2023).
  The model reads none of it. The project folder also contains Gulf Coast carbon-storage GIS from an
  unrelated project.
- **The `jensen.lib.LP` Excel add-ins** — third-party, from the Jensen ORMM library.
- **Anything from `Information Tables/`**, including `Health Data/`.

## Papers

- Jones, E.C.; Azeem, G.; **Jones, E.C., Jr.**; Jefferson, F.; Henry, M.; Abolmaali, S.; Sparks, J.
  *"Understanding the Last Mile Transportation Concept Impacting Underserved Global Communities to
  Save Lives During COVID-19 Pandemic."* **Frontiers in Future Transportation**, 2021.
  [10.3389/ffutr.2021.732331](https://doi.org/10.3389/ffutr.2021.732331)
- Jones, **Jones Jr.**, Azeem, Jefferson. *"Impacting at Risk Communities using AI to optimize the
  COVID-19 Pandemic Therapeutics Supply Chain."* International Supply Chain Technology Journal, 2020.
