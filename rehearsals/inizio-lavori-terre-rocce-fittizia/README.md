# Inizio lavori e terre e rocce, one pratica

`inizio-lavori` + `dichiarazione-utilizzo` selected together in the wizard on Napoli's SUE. Why a case files them together (`catalogue/F839/sue-pairs.yaml`, `dichiarazione-with-start`, reading): The dichiarazione goes at least 15 days before the excavation (art. 21 c. 1 DPR 120/2017), and a permesso's works start with the comunicazione di inizio lavori (art. 15 DPR 380/2001): a dichiarazione not filed with the permesso goes with the start of works.

- **The crawl**: `catalogue/F839/sections/sue-combo-inizio-lavori-dichiarazione-utilizzo.json`.
- **The recipe** `extends` `inizio-lavori-fittizia`, `scavo-fuori-sito-fittizio`: the first is the main pratica, the others' answers fill what its don't say.
- The rules table sue-napoli-adempimenti routes this combination (2026-11-04).

Made-up data; the draft is "PROVA NON INVIARE" and stops before the declarations, payment, signing and sending.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-05 | pane | `answers-p6.json` | **filled** in 50 s |

<!-- /runs -->

