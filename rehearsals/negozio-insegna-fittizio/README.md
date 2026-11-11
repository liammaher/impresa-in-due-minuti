# A shop's opening with an outside sign, generated from the batch crawl

"Aprire l'attività" for a non-food shop (esercizio di vicinato) on Napoli's SUAP, with the wizard's
"in caso di attività che preveda insegna esterna" tick (the sign's SCIA per mezzi pubblicitari inside the
pratica), for the shop rehearsal's made-up ditta individuale (`rehearsals/negozio-fittizio/fixture.json`).
The draft is "PROVA NON INVIARE - negozio insegna generato".

- **Crawl**: `catalogue/F839/sections/suap-016-aprire-l-attivita.json` (batch, shared with the opening),
  the sign's sections from `suap-060-aprire-l-attivita-interventi` (the restaurant's opening with its
  ticks). They were `borrowed` until this run: the filled draft's own section list holds exactly those
  seven and nothing else besides the person's declarations, so the crawl's `scelte_seen` says so.
- **The sign's text** is named by its own words ("Testo del messaggio pubblicitario"): the run found it
  only by its crawled id under the counter's label ("Caratteri restanti", `loose`).
- **Attachments screen** (read on the filled draft 2026-11-10): the opening's two and the sign's 14 slots,
  the recipe's own `slots:` (as the restaurant's with a sign), every one but Allegati liberi signed only:
  the person's.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-10 |  | `answers.json` | **filled** in 137 s |

<!-- /runs -->

