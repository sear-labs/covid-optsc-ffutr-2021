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
