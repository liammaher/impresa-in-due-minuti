# Voltura del permesso di costruire, with a co-holder: generated from the batch crawl, run to the declarations

On Napoli's SUE: an invented permesso di costruire passes from Immobiliare Fittizia S.r.l. to the
CILA rehearsal's client and a co-owner, Paolo Fittizio (`a:`, added to the P6 fixture for this).
Made-up data; the draft is "PROVA NON INVIARE" and stops before the acknowledgements in the new
holders' names, the bollo, signing and sending.

- **Crawl**: `catalogue/F839/sections/sue-voltura-intestazione-permesso-di-costruire.json`, with
  two scelte: "ci sono cointestatari" (adds *Informazioni su eventuali altri aventi titolo*) and the
  procura. gen.py lost the first scelta's section when a second followed (fixed: by index).
- *dichiarazione relativa alla conoscenza dei soggetti* was never crawled: the batch read the
  prescrizioni section again (crawl.js waited on the title's first 20 characters, which both share;
  fixed). Written into the crawl by hand from the pane (`by_hand`).
- The co-holder's sex is two radio groups, each required: the section saves only with both "M" and
  "F" ticked. Both are ticked, and `yours` says so; the codice fiscale says which.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-10-29 | pane |  | Stopped: the old holder's made-up partita IVA failed the portal's check digit (now the fixture's Immobiliare Fittizia); then the soggetti section (empty entry, wrong crawl); then the co-holder's sex (see above). |
| 2026-10-29 | pane |  | **Filled**, resumed on the same draft: all 16 sections read back on a fresh load (11 s). |
| 2026-10-29 | pane |  | Clean reruns of all 23 SUE recipes from run.py's install.js and run.js, nothing touched between runs: first filled in 76.5 s; second, with the runner waiting for a section to open, **filled** in 65.8 s, read back on a fresh load. |
| 2026-10-30 | pane |  | the bollo with two marche (`answers-marche`), `bench/rerun.py` bundle: stopped on the bollo as the semplificata's ("numero seriale (2)" isn't a label on the page) |
| 2026-10-30 | pane |  | the same, the second marca by label and nth: **filled** in 82 s, read back on a fresh load (12 s), nothing moved or loose |
| 2026-10-31 | pane | `answers-marche.json` | **filled** in 67 s |
| 2026-10-31 | pane | `answers-p6.json` | **filled** in 66 s |
| 2026-11-02 | pane | `answers-senza-cointestatari.json` | **filled** in 56 s |
| 2026-11-02 | pane | `answers-p6.json` | **filled** in 59 s |
| 2026-11-03 | pane | `answers-p6.json` | **filled** in 87 s |

<!-- /runs -->
