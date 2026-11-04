# CIL for temporary works: generated, never walked

The Comunicazione di Inizio Lavori for opere temporanee (art. 6 c. 1 e-bis DPR 380/2001) on
Napoli's SUE, for the CILA rehearsal's people (`rehearsals/cila-fittizia`): the architect with
a procura, the tenant client, one firm. Made-up data; the draft is "PROVA NON INVIARE" and
stops before the declarations, signing and sending.

`portal-steps.generated.yaml` is `gen.py`'s, from `recipe.yaml`, the crawl of an empty draft
(`catalogue/F839/sections/sue-comunicazione-di-inizio-lavori-per-opere-temporanee.json`: 176 s, 79 choices) and `dictionary/fnsuap.yaml`. Its
quadri are the CILA's under other letters (b = b, d = e, f = h, g = i), matched without the
letter. New in the dictionary: quadro c) (the dates and what the works are) and the empty
"altre comunicazioni". The safety quadro shows the "under 200 uomini-giorno" choice as a
checkbox where the CILA has a radio (`kind: tick`), and the D.Lgs. 81 and notifica choices are
now questions.

On a bene culturale (since 2026-11-01) the CIL goes once the Soprintendenza has authorized the
works (art. 21 c. 4 D.Lgs. 42/2004), requested apart and first (the rules table's
`soprintendenza-cil`): the CIL's quadro e lists only filings made with it, not assents, so the
authorization isn't written in the CIL. `answers-bene-culturale.json`.

Quadro e lists the other filings presented with the CIL (since 2026-11-03: `comunicazioni_contestuali`,
two rows and more by "+"). Their documents, the notifica preliminare and, on a bene culturale, the
Soprintendenza's authorization go under Allegati liberi, each in its own box (the slot's "+"),
attached by the run since 2026-11-03: that slot takes plain PDFs, not only signed ones as the
2026-11-01 run below read it. Assents still to obtain are refused: the CIL's form, national and Napoli's,
asks the SUE for none. `answers-comunicazioni.json`: three filings, never run on the portal.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-10-28 | pane |  | First run, no stop: 106 values and 3 attachments kept, every value read back on a fresh load; Login → draft: 112.2 s to the end of the form (wizard 10.4, 15 sections, fresh load 14.9), then 14.5 s for 3 attachments |
| 2026-10-29 | pane |  | **Filled** with the Comune's 100 € diritti: the "sono dovuti oneri" branch, its total and "pagamento on line", walked for the first time; every value read back on a fresh load; Login → draft: 70.9 s, fresh load 11.1 s (`bench/rerun.py` with two SCIAs) |
| 2026-10-31 | pane | `answers-p6.json` | **filled** in 78 s |
| 2026-10-31 | pane | `answers-proprietario.json` | **filled** in 63 s |
| 2026-11-01 | pane | `answers-bene-culturale.json` | **Filled** from a blank draft in 75.6 s, read back on a fresh load, nothing moved; one `loose`, the impresa quadro's "lavori sono/saranno eseguiti dall…" (the CILA's base case has it too); Login → draft: `answers-bene-culturale` (a listed building, the Soprintendenza's authorization obtained first), `bench/rerun.py` bundle |
| 2026-11-01 | pane | `answers-notifica.json` | **filled** in 76.7 s; its draft's Allega documenti read after: no slot for the notifica, only Allegati liberi (signed files only on the CIL), so it is the person's; Login → draft: `answers-notifica` (a notifica preliminare due: "allega alla presente comunicazione la notifica" ticked), `bench/rerun.py` bundle |
| 2026-11-03 | pane | `answers-comunicazioni.json` | **filled** in 82 s |
| 2026-11-03 | pane | `answers-bene-culturale.json` | **filled** in 78 s |
| 2026-11-03 | pane | `answers-notifica.json` | **filled** in 79 s |

<!-- /runs -->

Left to the person: the procura and the "Quadro riepilogativo della documentazione C.I.L."
(portal documents, signed), the declarations, signing and sending. Diritti: 100 € (line SUE 14
of the Comune's 2026 table, in the library's CIL page). The earlier runs filled 0 €; the
"sono dovuti oneri" branch was first walked on 2026-10-29 (Runs).

## Clean reruns (2026-10-29)

In the pane, from run.py's install.js and run.js, nothing touched between runs: first filled in 76.1 s; second, with the runner waiting for a section to open, **filled** in 87.9 s, read back on a fresh load.

## Owner case (2026-10-29)

`answers-proprietario.json`: an usufruttuario holding the title alone, works on parts shared by
co-owners, done in proprio (D.Lgs. 81 doesn't apply), no co-holders' ID slot. In the pane,
after the dictionary mapped every title and firm case: **filled** in 59.7 s, 17 sections, fresh
load 11 s.
