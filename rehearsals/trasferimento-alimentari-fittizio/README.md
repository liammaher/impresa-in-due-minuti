# A food shop moving to new premises, generated from the batch crawl

"Trasferire la sede dell'attività" for a food or mixed shop (vicinato, settore Alimentare o Misto) on
Napoli's SUAP, with the Reg. 852/2004 notifica for the new premises, nothing eaten on the spot, for
the shop rehearsal's made-up ditta individuale (`rehearsals/negozio-fittizio/fixture.json`) as a
grocer's, moving from via Cimarosa 12 to via Luca Giordano 50. The draft is "PROVA NON INVIARE -
trasferimento alimentari generato" and stops before the declarations, payment, signing and sending.

- **Crawl**: `catalogue/F839/sections/suap-017-trasferire-la-sede-dell-attivita.json` (batch).
- **Which pratica**: the rules table's `vicinato-alimentare-variazioni-senza-consumo` (SCIA) with the
  notifica. Its recipe fixes `consumo_sul_posto: false`: eating on the spot is another operation in
  this sector ("Avvio di consumo immediato sul posto"), not mapped with the move. Route tells this move
  from the protected zones' by the sector the table names (pratiche-napoli#93).
- **Fees**: asked ("check it"); 96 is made up.
- **Not read yet**: the attachments screen (no `after:`).

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-10 |  | `answers.json` | **filled** in 71 s |

<!-- /runs -->

