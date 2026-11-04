# Permesso di costruire with its autorizzazione paesaggistica ordinaria, one pratica

The permesso and the ordinaria selected together in the wizard on Napoli's SUE. The case: the
permesso's P6 job (a residential building demolished and rebuilt, more volume, structures,
contributo worked out by the SUE) on a property under art. 136 and 142, with the client as
owner (the ordinaria's form takes no tenant). Made-up data (rehearsals/pdc-fittizio's people and
property); the draft is "PROVA NON INVIARE" and stops before the declarations, payment,
signing and sending.

- **Two operations**, their sections in the order of the combination's crawl
  (`catalogue/F839/sections/sue-combo-pdc-paesaggistica-ordinaria.json`, crawled 2026-10-31):
  every section one already crawled, the same fingerprint as alone.
- **The recipe** `extends` the permesso's (`rehearsals/pdc-fittizio`) and
  `parts/paesaggistica-ordinaria.yaml`.
- **The asseverazione** names the ordinaria procedure and ticks its "Si allega la relazione
  paesaggistica e la documentazione", which adds a required slot for the relazione (plain PDF),
  besides the ordinaria's own.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-10-31 | pane | `answers-p6.json` | P6, from scratch: stopped on Gestione degli allegati, "il valore è obbligatorio": the slot the asseverazione's "Si allega la relazione paesaggistica" adds wasn't mapped (the SCIA's combination had it). Now in `parts/paesaggistica-ordinaria.yaml`, for both |
| 2026-10-31 | pane | `answers-p6.json` | P6, from scratch, with that slot: **filled** in 140 s, every value read back on a fresh load (23 s), nothing moved or loose, no retry |

<!-- /runs -->
