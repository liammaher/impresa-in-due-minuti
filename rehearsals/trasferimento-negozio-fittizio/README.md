# A non-food shop moving to new premises, generated from the batch crawl

"Trasferire la sede dell'attività" for a non-food shop (vicinato, settore NON alimentare) on Napoli's
SUAP, for the shop rehearsal's made-up ditta individuale (`rehearsals/negozio-fittizio/fixture.json`),
moving from via Cimarosa 12 to via Luca Giordano 50. The vault's `locale` is the new premises; the old
ones are asked. The draft is "PROVA NON INVIARE - trasferimento negozio generato" and stops before the
declarations, payment, signing and sending.

- **Crawl**: `catalogue/F839/sections/suap-016-trasferire-la-sede-dell-attivita.json` (batch).
- **Its sections**: the shop's move data ("Dati sull'esercizio di vicinato": the title, the new
  premises) was in the dictionary; the old premises ("precedente ubicazione dell'esercizio") have no
  shopping-centre question here, unlike the restaurant's, so that entry's three boxes are `if_present`.
- **Which pratica**: the rules table's `vicinato-non-alimentare-trasferimento` (SCIA).
- **Fees**: the 2026 table's VCA column isn't in the library for shops: asked ("check it"); 80 is made up.
- **Not read yet**: the attachments screen (no `after:`).

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-10 |  | `answers.json` | **filled** in 67 s |

<!-- /runs -->

