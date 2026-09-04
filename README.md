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

## Reconstructing the paper's actual scenarios

The notebook shipped a **10-customer example**. The paper ran **96 Harris County ZIP codes across
eight scenarios**, and its parameter file was not preserved. `scripts/reconstruct_paper.py` and
`scripts/calibrate.py` rebuild that parameterisation from the project's own data and check it
against every number the paper publishes.

### Demand is recovered exactly, and confirmed twice

`Information Tables/Zip Code Populations.xlsx`, column **`Pop2019`**, restricted to ZIPs
**77002–77099**, sums to **3,270,360** — the paper's stated Harris County population *to the digit*.
Twenty percent of it is **654,072**, again exactly the paper's stated elderly target. Two
independent exact matches, so this is the right table, the right column and the right ZIP range.
Demand per ZIP is 20% of its `Pop2019`.

### Two parameters were never recorded, so they were fitted

The paper gives penalty as a **range** ($35–$70), not a value, and never states the scenario-1
supply. Both were grid-searched against the published results. The best fit uses **$70 per unserved
person** — the top of the paper's own band — and **scenario-1 supply at 26% of demand**:

| scenario | service level | penalty rebuilt | penalty in paper | transport |
|---:|---:|---:|---:|---:|
| 1 | 26.0% | **$33.88M** | $34M | $0.16M |
| 2 | 52.0% | **$21.98M** | $22M | $0.33M |
| 3 | 78.0% | $10.07M | *(chart only)* | $0.49M |
| 4 | 100.0% | **$0.00M** | $0 | $0.63M |

**All three published penalty figures reproduce to within 0.4%**, and the qualitative findings hold:
penalty falls monotonically to zero by scenario 4, transport rises as coverage grows, and transport
stays far below penalty throughout — the paper's central point.

### One published number cannot be reproduced, and the reason is arithmetic

The paper also reports a **32% service level at scenario 1**. That is incompatible with its own
penalty figures under equal distribution:

- the **ratio** 34/22 = 1.545 forces supply₁ ≈ 26% of demand, because when supply doubles,
  unmet₂/unmet₁ = (D−2S)/(D−S), which equals 0.647 only at S = 0.261·D
- a 32% service level would instead give unmet₂/unmet₁ = 0.36/0.68 = 0.529, i.e. a penalty pair of
  **34 and 18**, not 34 and 22

So the reported service level and the reported penalty pair imply **different supply levels**. No
choice of penalty rate reconciles them — fitting the service level instead gives $15.6M and $8.2M
against the published $34M and $22M. `calibrate.py` reports both fits side by side rather than
quietly optimising one and presenting it as agreement.

Most likely the 32% is computed on a different base or is a reporting slip; the penalty figures are
mutually consistent and the service level is the odd one out.

### The figures

The paper's eight result figures were made in R and were not preserved.
`scripts/make_figures.py` rebuilds approximate replicas in Python from the
reconstructed parameterisation, into `figures/`:

| | equal distribution | prioritized distribution |
|---|---|---|
| penalty cost | `fig05_penalty_equal.png` | `fig09_penalty_prioritized.png` |
| transport cost | `fig06_transport_equal.png` | `fig10_transport_prioritized.png` |
| cost comparison | `fig07_costcomparison_equal.png` | `fig11_costcomparison_prioritized.png` |
| service levels | `fig08_service_equal.png` | `fig12_service_prioritized.png` |

Figure 5 overlays the paper's published values as open circles on the
reconstructed bars — they sit on top of each other, which is the clearest
statement of how well the reconstruction lands.

**Two things fall out that corroborate the paper.** First, the penalty charts for
equal and prioritized distribution are near-identical, and the paper says
exactly that: *"This figure for penalty cost for prioritized distribution looks
similar to penalty cost chart for equal distribution in this case."* The reason
is visible in the reconstruction — a flat $70 rate makes total penalty depend
only on total unmet demand, not on who goes unserved.

Second, the service-level figures carry a line the originals do not: coverage of
the **most-vulnerable third** of ZIPs. That is where prioritization actually
shows up. At scenario 1 the city overall is at **26%**, while the most
vulnerable third reaches **77%** — the paper's central claim, made measurable.

The policies are implemented as the paper describes them: **equal** serves every
ZIP the same *fraction* of its demand; **prioritized** fills ZIPs in descending
CHI order, with CHI stood in for by the CDC SVI percentile the project's data
carries.

### What ships

- `data/derived_paper_instance.csv` — the recovered 96-ZIP instance: population, demand, SVI-scaled
  penalty, last-mile miles
- `results/reconstructed_scenarios.csv` — the table above

`data/raw/` still holds the original 10-customer example, which is what `run_all.py` and the tests
use, because it is the instance whose answer (579,000) is independently recorded in the notebook.

## What matches the paper, and what does not

**The model structure matches exactly.** The Frontiers paper defines the same problem in the same
terms — *"Given a set of producers, depots, and customers (zip codes)…"* with
`Depots {D1..D5}` and `Customers {C1..C10}`, and parameters `cost`, `supply`, `through`, `demand`.
Those are precisely this repository's five input tables and the sets in `model.py`.

**The parameter values do not, and the objective is therefore not a paper result.** The paper's
Table 2 gives a shortage penalty of **$35–$70** and transport at **$1/mile**; the shipped instance
uses a flat penalty of **100** and costs from **0.2 to 999**. So `579,000` is the *example* instance's
optimum, reproduced exactly from the notebook that produced it — not a number the paper reports.

**The paper reports no headline objective at all.** Its results are presented as Figure 7, a chart,
so there is no published figure to assert against. That is why `tests/` targets the notebook's
recorded `579000.0` rather than a paper value — the honest referent, and stated as such.

The distinction in one line: **this reproduces the model, not the paper's run.** Anyone wanting the
paper's numbers needs the paper's parameters, which were not preserved.

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

## How to cite

Cite **the paper** for the work and **this repository** for the code.

```bibtex
@article{jones2021lastmile,
  author  = {Jones, Erick C. and Azeem, Gohar and Jones, Jr., Erick C. and
             Jefferson, Felicia and Henry, Marcia and Abolmaali, Shannon and
             Sparks, Janice},
  title   = {Understanding the Last Mile Transportation Concept Impacting
             Underserved Global Communities to Save Lives During COVID-19 Pandemic},
  journal = {Frontiers in Future Transportation},
  year    = {2021},
  doi     = {10.3389/ffutr.2021.732331}
}
```

**Code DOI:** not yet minted. Once this repository is connected to Zenodo and a release is tagged,
Zenodo issues two DOIs — a *version* DOI per release, and a **concept DOI that always resolves to
the latest version and never changes**. The concept DOI goes here and in `CITATION.cff`; it stays
correct for the life of the repository, so it is one edit rather than a per-release chore.

`CITATION.cff` in the repo root also gives GitHub's "Cite this repository" button.

## Papers

- Jones, E.C.; Azeem, G.; **Jones, E.C., Jr.**; Jefferson, F.; Henry, M.; Abolmaali, S.; Sparks, J.
  *"Understanding the Last Mile Transportation Concept Impacting Underserved Global Communities to
  Save Lives During COVID-19 Pandemic."* **Frontiers in Future Transportation**, 2021.
  [10.3389/ffutr.2021.732331](https://doi.org/10.3389/ffutr.2021.732331)
- Jones, **Jones Jr.**, Azeem, Jefferson. *"Impacting at Risk Communities using AI to optimize the
  COVID-19 Pandemic Therapeutics Supply Chain."* International Supply Chain Technology Journal, 2020.
