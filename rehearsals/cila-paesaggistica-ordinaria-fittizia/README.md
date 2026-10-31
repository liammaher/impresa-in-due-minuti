# CILA with its autorizzazione paesaggistica ordinaria, one pratica

The CILA and the ordinaria selected together in the wizard on Napoli's SUE. The case: the CILA
rehearsal's P6 job (rehearsals/cila-fittizia: a tenant's interior works, already started) with a
45 m² timber pergola on the roof terrace of a building under art. 136 and 142: over the 30 m² of
DPR 31/2017's item B.17, so outside Allegato B and the ordinaria's (art. 146). The client as owner
(the ordinaria's form takes no tenant). Made-up data; the draft is "PROVA NON INVIARE" and stops
before the declarations, payment, signing and sending.

- **Two operations**, their sections in the order of the combination's crawl
  (`catalogue/F839/sections/sue-combo-cila-paesaggistica-ordinaria.json`, crawled 2026-10-31 with
  its attachments screen): every section one already in the dictionary.
- **The recipe** `extends` the CILA's and `parts/paesaggistica-ordinaria.yaml`.
- The rules table sends here every CILA case (works to start, under way or done, interior only)
  whose landscape works need the ordinaria and aren't done yet: 8 cases.

## Runs

| Date | Browser | Result |
|---|---|---|
| 2026-10-31 | pane | P6, from scratch: stopped at Allega documenti on the ordinaria's second relazione slot, which only the SCIA's and the permesso's "Si allega" box opens; dropped (`drop: true`) |
| 2026-10-31 | pane | P6 again, on the slot dropped, `bench/rerun.py` bundle: **filled** in 101 s |
