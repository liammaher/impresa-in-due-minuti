# Autorizzazione paesaggistica ordinaria: generated from the batch crawl, run to the declarations

On Napoli's SUE (art. 146 D.Lgs. 42/2004), for the CILA rehearsal's architect (with procura) and
client: a wooden pergola on the roof terrace and new outdoor paving, on a property under art. 136
and 142. Made-up data; the draft is "PROVA NON INVIARE" and stops before the declarations, the
attachments (the relazione paesaggistica, DPCM 12/12/2005), the bollo, signing and sending.

- **Crawl**: `catalogue/F839/sections/sue-autorizzazione-paesaggistica-ordinaria.json`; one section
  of its own, the rest shared with the semplificata.
- **Its own section** (*dichiarazione relativa ai contenuti dell'intervento*, a dictionary entry
  after the voltura's, which shares its name): the client's title and the deed that proves it
  (rogito, Agenzia delle Entrate or Conservatoria), building or area, use and PRG zone, deeds
  weighing on it, and the vincolo (yes, then art. 136 and/or 142). The vincolo's "sì" goes by the
  question beside it: "sì" alone also names the "no" above it.
- `supports` refuses art. 134 alone (the form names only 136 and 142), a tenant (the form offers
  no such title) and the marche da bollo route.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-10-29 | pane |  | Stopped twice in its own section: the vincolo's "sì" by label found the "no" above it; then "in zona di PRG" named the "ad uso" box too (the page's nearest label before each box in a row is the last column's). Fixed in the dictionary and in inpage.js (a box whose own text is the label comes first). |
| 2026-10-29 | pane |  | **Filled**, resumed on the same draft: all 11 sections read back on a fresh load (8 s). Run as owner, rogito, building, no deeds, art. 136 and 142. |
| 2026-10-29 | pane |  | Clean reruns of all 23 SUE recipes from run.py's install.js and run.js, nothing touched between runs: first filled in 53.4 s; second, with the runner waiting for a section to open, **filled** in 58.2 s, read back on a fresh load. |
| 2026-10-29 | pane | `answers-p6.json` | **filled** |
| 2026-11-02 | pane | `answers-p6.json` | **filled** in 49 s |
| 2026-11-03 | pane | `answers-p6.json` | **stopped** in 61 s |
| 2026-11-03 | pane | `answers-p6.json` | **filled** in 65 s |
| 2026-11-05 | pane | `answers-tecnici-tre.json` | **filled** in 89 s |
| 2026-11-05 | pane |  | Three technicians, none the architect presenting (`answers-tecnici-tre`: valerio, elena, davide), the tecnico section's "+" twice, `bench/rerun.py` bundle: **filled** in 89 s, nothing moved or loose. A second technician beside the presenter is refused (defects.yaml `paesaggio-altri-tecnici`: under "è colui" the "+" shows only an albo row, read on a draft the same day) |

<!-- /runs -->
