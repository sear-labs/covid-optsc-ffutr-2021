# Superseded implementations

**These are kept for provenance. Neither is the model.** The model is
`src/covid_sc/`, ported from the project's Python notebook.

| File | What it is |
|---|---|
| `COVID_Supply_Chain.gms` | An earlier GAMS formulation of the same problem. Superseded. |
| `gohar_travel_plan.m` | A MATLAB travel-planning script by **Gohar Azeem**, second author on the Frontiers paper. Superseded, and not by the same author as the Python model. |

Erick's instruction, 2026-09-03: *"that matlab code can be put in a folder for
like draft code or something the actual model is the python"*, and GAMS the same.

**Do not treat these as baselines to verify the Python against.** They are not
known to produce the same numbers, nobody has checked, and two of the three were
written by different people at different times. Verification here is against the
notebook's own recorded output — see `tests/`.

Excluded from this repository entirely: the `jensen.lib.LP` Excel solver add-ins
(third-party, from the Jensen ORMM library, not ours to redistribute) and the
project's ArcGIS material (a separate line of work — see the repository README).


## The GAMS draft now runs

It did not before. `COVID_Supply_Chain.gms` called `gamsinputcovid.xlsx`, which was never in this
repository, so the committed draft could not be executed by anyone — the only reference to that file
anywhere in the repo was the call itself.

`covid_input.xlsx` is that workbook with the four sheets the model never reads removed:

    kept     TransportDistanceAB · TransportDistanceBJ · Demand · index
    dropped  Technologies · Rainfall · CapacityFactor · indexold

The dropped four were residue from the water-energy workbook this file was copied from — its header
comment still says `* Water_Energy run file` — and carried sheets of the same shape as the Pecan
Street derived series. They were unused by this model, so removing them costs nothing and takes the
file from 695 KB to 226 KB.

What remains is a **32-customer instance labelled with bare integers** — no ZIP codes, no
demographics, no case counts, consistent with this repository's synthetic-data position. It is
neither the 10-customer example in `data/raw/` nor the paper's 96-ZIP run.

Verified: `gams COVID_Supply_Chain.gms` returns `MODEL STATUS 1 Optimal`, objective **192.0000**.
