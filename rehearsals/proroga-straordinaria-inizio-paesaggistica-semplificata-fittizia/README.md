# Proroga straordinaria inizio e paesaggistica semplificata, one pratica

`proroga-straordinaria-inizio` + `paesaggistica-semplificata` selected together in the wizard on Napoli's SUE. Why a case files them together (`catalogue/F839/sue-pairs.yaml`, `authorization-keeps-pace`, reading): The landscape authorization lasts five years from the building title's efficacy, plus one to finish works begun (art. 146 c. 4 D.Lgs. 42/2004); a new title or an extension of a title's terms doesn't extend it. When the works' new term passes the authorization's, the filing that sets it carries what keeps the authorization in force: its art. 10-septies extension, before it expires; its renewal (art. 7 DPR 31/2017), expired no more than a year, the works unchanged and not or only partly done; or a new authorization, past that.

- **The crawl**: `catalogue/F839/sections/sue-combo-proroga-straordinaria-inizio-paesaggistica-semplificata.json`.
- **The recipe** `extends` `proroga-straordinaria-inizio-fittizia`, `paesaggistica-semplificata-fittizia`: the first is the main pratica, the others' answers fill what its don't say.
- The rules table sue-napoli-adempimenti routes this combination (2026-11-04).

Made-up data; the draft is "PROVA NON INVIARE" and stops before the declarations, payment, signing and sending.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-05 | pane | `answers-p6.json` | P6, from scratch, `bench/rerun.py` bundle: **filled** in 76 s, every value read back on a fresh load; the portal's usual warnings on made-up data |

<!-- /runs -->

