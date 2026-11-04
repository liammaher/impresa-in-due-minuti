# CILA con autorizzazione paesaggistica semplificata e dichiarazione di utilizzo delle terre e rocce da scavo, one pratica

Three operations selected together in the wizard on Napoli's SUE: the building title, the
autorizzazione paesaggistica semplificata and the dichiarazione di utilizzo delle terre e rocce da scavo
(art. 21 DPR 120/2017). The case: rehearsals/cila-paesaggistica-fittizia's, with excavated soil that leaves a small site
as a by-product. The CILA's works are "da iniziare" and start once the SUE says the landscape authorization is in (the P6 CILA is a late one, a sanatoria, which files no dichiarazione). Made-up data; the draft is "PROVA NON INVIARE" and stops before the
declarations, payment, signing and sending.

- **Three operations** (`catalogue/F839/sections/sue-combo-cila-paesaggistica-semplificata-dichiarazione-utilizzo.json`, crawled 2026-11-03 with its
  attachments screen, 27 sections): every section already in the dictionary; four adempimenti (the
  title's, the authorization's, the dichiarazione's to the SUE and to ARPA Campania). Each two of the
  three are a pair the wizard accepts (`catalogue/F839/sue-wizard.json` `pairs`).
- **The recipe** `extends` cila-paesaggistica-fittizia's and `parts/dichiarazione-utilizzo-terre.yaml`, restating its
  `yours` and both `handles` (a recipe's `yours` replaces the one it extends; `rules` merge key by key).
- **The attachments screen**, read on the filled draft 2026-11-03 (`slotsOf`): the landscape
  combination's slots and the dichiarazione's ("Dichiarazione di utilizzo di cui all'art. 21 …", the
  portal's document, required, signed only, second run). Every required slot left empty takes only
  signed files or is a portal document: the person's, as on the combination without the dichiarazione.
- The rules table sends here a case with these works whose landscape works need the semplificata and aren't
  done yet and whose soil leaves a site up to 6,000 m³ (or larger with no VIA/AIA); the DAU (art. 7) is
  the person's, apart, once the soil is used.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-03 | pane | `answers-p6.json` | P6, from scratch, `bench/rerun.py` bundle: **filled** in 132 s, every value read back on a fresh load; the portal's usual warnings on made-up data (the PEC, the address, the land register) |

<!-- /runs -->
