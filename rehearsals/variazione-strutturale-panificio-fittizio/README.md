# A bakery's structural change, generated from the batch crawl

"Variazioni strutturali" for a bakery (sector Panificio) on Napoli's SUAP, with the Reg. 852/2004 update,
for the bakery rehearsal's made-up ditta individuale (`rehearsals/panificio-fittizio/fixture.json`): it
adds selling its bread to eat on the spot (no table service). The draft is "PROVA NON INVIARE - variazione
panificio generato".

- **Crawl**: `catalogue/F839/sections/suap-004-variazioni-strutturali.json` (batch).
- **Its own section**, written from the crawl's text: a second dictionary entry for "dati sull'entità delle
  variazioni" (the production cycle, consumption on the spot added or dropped, the season); "Altro" is
  refused.
- **Which pratica**: no bakery in the library's rules table yet: no `rules:`.
- **Attachments screen** (read on the filled draft 2026-11-10): the diritti receipt and the ASL tariffa's
  (signed only), Allegati liberi; nothing required before the declarations.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-10 |  | `answers.json` | **filled** in 123 s |

<!-- /runs -->

