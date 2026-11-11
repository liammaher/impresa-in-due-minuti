# A bar or restaurant's opening in the protected zones, generated from the batch crawl

"Aprire l'attività" for a bar or restaurant in the historic centre (sector "Esercizio di somministrazione
di alimenti e bevande in zone tutelate") on Napoli's SUAP: since the 2026 Piano an authorization, with
the Reg. 852/2004 notifica and the acoustic nulla osta (the wizard's tick), for the pizzeria's made-up ditta
individuale at via dei Tribunali 150, zone A (`fixture.json`). The draft is "PROVA NON INVIARE - centro
storico generato".

- **Crawl**: `catalogue/F839/sections/suap-061-aprire-l-attivita.json` (batch). The nulla osta tick's
  `scelte_none` was inferred from the move's draft; this run's draft confirms it: its one bollo section
  is the authorization's own.
- **The street**: the stradario's VIA DEI TRIBUNALI is VIA TRIBUNALI on the portal; the lookup's match
  without particles found it (portal/README.md, "Street names without their particles").
- **Attachments screen** (read on the filled draft 2026-11-10): the acoustic report (plain or signed:
  attached, a made-up PDF in `files/`), the portal's Allegati 1 CS 1 and 3 CG 1 (made from the pratica:
  the second run), the planimetria, the ASL tariffa's and the diritti receipts (signed only: the
  person's), Allegati liberi.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-10 |  | `answers.json` | **filled** in 90 s |

<!-- /runs -->

