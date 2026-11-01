# Permesso di costruire with its autorizzazione paesaggistica semplificata, one pratica

The permesso and the semplificata selected together in the wizard on Napoli's SUE. The case: an
extension outside the building's shape, 60 m³ and under 10% of its volume (DPR 31/2017
Allegato B.1, so the semplificata), with structures and new electrical and water systems, on a
property under art. 136 and 142. Made-up data (rehearsals/pdc-fittizio's people and property);
the draft is "PROVA NON INVIARE" and stops before the declarations, payment, signing and sending.

- **Two operations** (`operation:` a list), their sections in the order of the combination's
  crawl (`catalogue/F839/sections/sue-combo-pdc-paesaggistica-semplificata.json`, crawled
  2026-10-31): every section one already crawled, the same fingerprint as alone.
- **The recipe** `extends` the permesso's (`rehearsals/pdc-fittizio`) and
  `parts/paesaggistica-semplificata.yaml`: only its procedure, crawl, operations and `yours` are
  its own, so a slot or a refusal mapped on the permesso reaches it.
- **The asseverazione** (16, tutela storico ambientale) names the semplificata procedure and
  ticks its "Si allega": the relazione paesaggistica semplificata and its drawings take only
  signed files (.p7m), so they are the person's.
- **Attachments**: the combination's screen read on the empty draft, plus the permesso's slots
  its answers add.

## Runs

| Date | Browser | Result |
|---|---|---|
| 2026-10-31 | pane | P6 (ampliamento, B.1), from scratch: **filled** in 145 s, every value read back on a fresh load (24 s), nothing moved or loose, no retry |
| 2026-11-01 | pane | P6, `bench/rerun.py` bundle, after the semplificata's "Si allega" box got its slot ("Relazione paesaggistica semplificata e documentazione necessaria": required, plain PDF; read on the earlier filled draft, whose run had left it empty: the runner took the portal's "required" under it for the person's signed-only "Relazione Paesaggistica Semplificata", whose title starts it; fixed in inpage.js): **filled** in 158.6 s, the slot holding its file. |
