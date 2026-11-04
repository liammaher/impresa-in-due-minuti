# SCIA alternativa al permesso di costruire with its autorizzazione paesaggistica semplificata, one pratica

The SCIA alternativa and the semplificata selected together in the wizard on Napoli's SUE. The
case: the SCIA alternativa's P6 ristrutturazione (rehearsals/scia-alternativa-fittizia) with a
25 m³ extension, under 10% of the volume and 100 m³ (DPR 31/2017 Allegato B.1), and facade
changes (B.3), on a property under art. 136 and 142. Made-up data (the CILA rehearsal's people
and property); the draft is "PROVA NON INVIARE" and stops before the declarations, payment,
signing and sending.

- **Two operations**, their sections in the order of the combination's crawl
  (`catalogue/F839/sections/sue-combo-scia-alt-paesaggistica-semplificata.json`, crawled
  2026-10-31): every section one already crawled, the same fingerprint as alone.
- **The recipe** `extends` the SCIA alternativa's (`rehearsals/scia-alternativa-fittizia`) and
  `parts/paesaggistica-semplificata.yaml`: only its procedure, crawl, operations and `yours` are
  its own, so a slot or a refusal mapped on the SCIA alternativa reaches it.
- **The asseverazione** (16, tutela storico ambientale) names the semplificata procedure and
  ticks its "Si allega": the relazione paesaggistica semplificata and its drawings take only
  signed files (.p7m), so they are the person's.
- **The works**: the 30 days before they may start run from the authorization's release (art.
  23 c. 3 DPR 380/2001), not from filing.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-10-31 | pane | `answers-p6.json` | P6 (ampliamento, B.1 and B.3), from scratch: **filled** in 159 s, every value read back on a fresh load (26 s), nothing moved or loose, no retry |
| 2026-11-01 | pane | `answers-p6.json` | P6, `bench/rerun.py` bundle, after the semplificata's "Si allega" box got its slot ("Relazione paesaggistica semplificata e documentazione necessaria": required, plain PDF; read on the earlier filled draft, whose run had left it empty: the runner took the portal's "required" under it for the person's signed-only "Relazione Paesaggistica Semplificata", whose title starts it; fixed in inpage.js): **filled** in 171.7 s, the slot holding its file. |

<!-- /runs -->
