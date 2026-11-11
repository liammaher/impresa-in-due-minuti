# A acconciatore's move to new premises, generated from the batch crawl

"Trasferire la sede dell'attività di acconciatore" on Napoli's SUAP, for the shop rehearsal's made-up ditta
individuale (`rehearsals/negozio-fittizio/fixture.json`) as a salon, moving from via Bernini 30 to via
Luca Giordano 50. The draft is "PROVA NON INVIARE - trasferimento acconciatore generato".

- **Crawl**: `catalogue/F839/sections/suap-011-trasferire-la-sede-dell-attivita-di-acconciatore.json` (batch).
- **Its two sections**, written from the crawl's text: "Dati sull'attività" (which activity moves,
  ticked from the operation; the title; the new premises' shopping centre) and "Dichiarazioni", every
  box the person's (`theirs`). The form ticks both activities: moving both is two wizard operations,
  refused for now.
- **Which pratica**: the rules table's `acconciatore-estetista-scia` names one activity for both, so only
  the hairdresser's move has `rules:` (as the opening); the beautician's waits for the table to tell
  them apart.
- **Fees**: asked ("check it"); 50 is made up.
- **Not read yet**: the attachments screen (no `after:`).

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-10 |  | `answers.json` | **filled** in 63 s |

<!-- /runs -->

