# SCIA alternativa with the dichiarazione di utilizzo delle terre e rocce da scavo, one pratica

The SCIA alternativa and the dichiarazione di utilizzo (art. 21 DPR 120/2017) selected together in the wizard on
Napoli's SUE. The case: rehearsals/scia-alternativa-fittizia's, with the SCIA alternativa case with a new basement, 900 m³ dug; the soil leaves the site as a by-product
(a small site). Made-up data; the draft is "PROVA NON INVIARE" and stops before the declarations,
payment, signing and sending.

- **Two operations** (`catalogue/F839/sections/sue-combo-scia-alt-dichiarazione-utilizzo.json`, crawled 2026-11-03 with its
  attachments screen, 37 sections): the SCIA alternativa's own sections, every one already in the dictionary. The
  dichiarazione adds two adempimenti (the SUE's, ARPA Campania's) and no section of its own; the
  location and land register sections are the dichiarazione's lower-case ones, not the title's
  (catalogue/F839/sue-wizard.json `pairs`).
- **The recipe** `extends` scia-alternativa-fittizia's and `parts/dichiarazione-utilizzo-terre.yaml`, restating its
  `yours` (a recipe's `yours` replaces the one it extends).
- **The attachments screen** adds one slot, "Dichiarazione di utilizzo di cui all'art. 21 …": the
  portal's own document, required, signed only, attached in the second run. Read on the filled
  draft 2026-11-03 (`slotsOf`): besides it, the SCIA alternativa's own slots under the case's answers: the signed-only stato legittimo slot (the person's), the contributo's prospetto, the energy report, the seismic authorization's documents (the case's answers).
- The rules table sends here a SCIA alternativa case whose excavated soil leaves the site as a by-product from a
  site up to 6,000 m³ (or larger with no VIA/AIA), with no landscape authorization; the DAU (art. 7)
  is the person's, apart, once the soil is used.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-03 | pane |  | P6, from scratch, `bench/rerun.py` bundle: **filled** in 175 s, every value read back on a fresh load; the portal's usual warnings on made-up data (the PEC, the address, the land register) |
| 2026-11-03 | pane |  | P6 again, `bench/rerun.py` bundle, after the asseverazione's soil answers were made to agree with the terre e rocce filing (`scavo: sottoprodotti`, no piano di utilizzo; `run.py` filters `scavo_proposto`, `piano_proposto` and the dictionary's supports): **filled**, every value read back on a fresh load |
| 2026-11-03 | pane | `answers-p6.json` | **filled** in 175 s |

<!-- /runs -->
