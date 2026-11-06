# Rinnovo paesaggistica e terre e rocce, one pratica

`rinnovo-paesaggistica` + `dichiarazione-utilizzo` selected together in the wizard on Napoli's SUE. Why a case files them together (`catalogue/F839/sue-pairs.yaml`, `dichiarazione-no-title`, reading): Works that need no building title in a protected area take the landscape procedure alone (artt. 146, 149 D.Lgs. 42/2004); if they dig and the soil leaves the site, the dichiarazione is due before the excavation too (art. 21 c. 1 DPR 120/2017): one pratica carries both.

- **The crawl**: `catalogue/F839/sections/sue-combo-rinnovo-paesaggistica-dichiarazione-utilizzo.json`.
- **The recipe** `extends` `rinnovo-paesaggistica-fittizia`, `scavo-fuori-sito-fittizio`: the first is the main pratica, the others' answers fill what its don't say.
- The rules table sue-napoli routes this combination (2026-11-04).

Made-up data; the draft is "PROVA NON INVIARE" and stops before the declarations, payment, signing and sending.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-05 | pane | `answers-p6.json` | P6, from scratch, `bench/rerun.py` bundle: **filled** in 68 s, every value read back on a fresh load; the portal's usual warnings on made-up data |

<!-- /runs -->

