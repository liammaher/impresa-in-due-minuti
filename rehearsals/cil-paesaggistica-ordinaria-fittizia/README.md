# CIL for temporary works with its autorizzazione paesaggistica ordinaria, one pratica

The CIL (art. 6 c. 1 e-bis DPR 380/2001) and the ordinaria selected together in the wizard on
Napoli's SUE. The case: the CIL rehearsal's people (rehearsals/cil-fittizia) with a 60 m²
prefabricated site office and store standing for 170 days in the garden of a building under art.
136 and 142, beyond Allegato B's small mobile structures (art. 146). The client as owner (the
ordinaria's form takes no tenant). Made-up data; the draft is "PROVA NON INVIARE" and stops before
the declarations, payment, signing and sending.

- **Two operations**, their sections in the order of the combination's crawl
  (`catalogue/F839/sections/sue-combo-cil-paesaggistica-ordinaria.json`, crawled 2026-10-31 with
  its attachments screen).
- **The recipe** `extends` the CIL's and `parts/paesaggistica-ordinaria.yaml`.
- **The start date** is the earliest: the works start once the SUE says the authorization is in.

## Runs

| Date | Browser | Result |
|---|---|---|
| 2026-10-31 | pane | P6, from scratch: stopped at Allega documenti on the ordinaria's second relazione slot, which only the SCIA's and the permesso's "Si allega" box opens; dropped (`drop: true`) |
| 2026-10-31 | pane | P6 again, on the slot dropped, `bench/rerun.py` bundle: **filled** (723 s: the form in about 2 minutes, then about 10 minutes before the run ended, after the declarations were read) |
