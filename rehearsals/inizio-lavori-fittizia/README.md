# Comunicazione di inizio lavori (after a permesso di costruire): generated, never walked

On Napoli's SUE, for the CILA rehearsal's architect and client, the client holding an
invented permesso di costruire (999/2026). Made-up data; the draft is "PROVA NON INVIARE" and
stops before the declarations, signing and sending.

`portal-steps.generated.yaml` is `gen.py`'s, from `recipe.yaml`, the crawl of an empty draft
(`catalogue/F839/sections/sue-comunicazione-inizio-lavori.json`: 137 s) and `dictionary/fnsuap.yaml`. Its own
four sections (the permit, the date, the permit's holder, where the works are) are plain text
boxes: four dictionary entries.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-10-28 | pane |  | First run, no stop: 52 values and the client's ID kept, every value read back on a fresh load; Login → draft: 87.9 s to the end of the form (wizard 14.1, 10 sections, fresh load 15.8), then 5.3 s for 1 attachment |
| 2026-10-31 | pane | `answers-p6.json` | **filled** in 50 s |
| 2026-11-02 | pane | `answers-p6.json` | **filled** in 53 s |

<!-- /runs -->

## Clean reruns (2026-10-29)

In the pane, from run.py's install.js and run.js, nothing touched between runs: first filled in 52.2 s; second, with the runner waiting for a section to open, **filled** in 50.6 s, read back on a fresh load.
