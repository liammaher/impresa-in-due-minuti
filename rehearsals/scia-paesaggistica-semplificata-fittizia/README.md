# SCIA edilizia with its autorizzazione paesaggistica semplificata, one pratica

A SCIA condizionata on Napoli's SUE: the SCIA and the landscape authorization selected
together in the wizard (the SCIA's section b) says that's how an assent is asked with it).
The case: a non-essential variant to a SCIA under way (a new opening and an outdoor air-conditioning unit, Allegato B items B.2 and B.7) on a building under art. 136 and 142, the contributo paid in instalments on the architect's prospetto. Made-up data (rehearsals/cila-fittizia's people and property); the draft is
"PROVA NON INVIARE" and stops before the declarations, payment, signing and sending.

- **Two operations** (`operation:` a list), their sections in the order of the combination's
  crawl (`catalogue/F839/sections/sue-combo-scia-paesaggistica-semplificata.json`: fingerprints read on
  an empty draft on 2026-10-29). Every section is one already crawled: the SCIA's and the
  semplificata's, each the same fingerprint as alone, so the dictionary fills it unchanged.
- **The asseverazione** names the semplificata procedure ("ricade in zona tutelata e le opere comportano
  alterazione", then the procedure and its "Si allega"), and b) gets no start date: the works
  start once the SUE says the authorization is in.
- **Attachments**: the combination's screen was read on the empty draft (`slots`); the SCIA's
  answer-dependent slots are added from its own screen. the relazione paesaggistica semplificata (a portal document) and its drawings take only signed files (.p7m).
- `supports`: the SCIA's, plus the semplificata's own refusals; `paesaggio` is fixed to semplificata (another
  answer is another recipe).

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-10-29 | pane |  | First run, from scratch, in a batch of eight: **filled** in 177 s, every value read back on a fresh load (28 s); variant to a SCIA, contributo in instalments with the prospetto attached, no start date. |
| 2026-10-30 | pane | `answers-impianti.json` | systems needing a project (`answers-impianti`: six systems, each project in its own slot, the energy report's slot too), `bench/rerun.py` bundle: **filled** in 157 s, read back on a fresh load (25 s), nothing moved or loose |
| 2026-10-31 | pane |  | P6 and systems needing a project (`answers-impianti`), `bench/rerun.py` bundle, after the recipe became `extends: [scia-fittizia, parts/paesaggistica-semplificata]` (it gained the SCIA's 12 slots it had missed, and lost 6 refusals the SCIA had closed): **filled** both (146.9 s, 152.8 s), read back on a fresh load (25 s, 25 s), nothing moved or loose |
| 2026-10-31 | pane | `answers-p6.json` | **filled** in 147 s |
| 2026-10-31 | pane | `answers-impianti.json` | **filled** in 153 s |
| 2026-11-01 | pane | `answers-p6.json` | P6, `bench/rerun.py` bundle, after the semplificata's "Si allega" box got its slot ("Relazione paesaggistica semplificata e documentazione necessaria": required, plain PDF; read on the earlier filled draft, whose run had left it empty: the runner took the portal's "required" under it for the person's signed-only "Relazione Paesaggistica Semplificata", whose title starts it; fixed in inpage.js): **filled** in 153.1 s, the slot holding its file. |
| 2026-11-03 | pane | `answers-vincolo-136.json` | The landscape vincolo of art. 136 alone (`answers-vincolo-136`), `bench/rerun.py` bundle: **filled** in 289 s. `answers-vincolo-134` never reached the portal ("the page didn't load" at the domicilio digitale) and the batch dropped it without a word: `loop.js` now lists such runs (`unreached`) |
| 2026-11-04 | pane | `answers-vincolo-134.json` | `answers-vincolo-134` (art. 134 alone), `bench/rerun.py` bundle: **filled** in 238 s |

<!-- /runs -->
