# A bar or restaurant moving to new premises, generated from the batch crawl

"Trasferire la sede dell'attività" for a bar or restaurant outside the protected zones on Napoli's
SUAP (the SCIA di trasferimento, with the Reg. 852/2004 notifica for the new premises), for the
pizzeria rehearsal's made-up ditta individuale (`rehearsals/pizzeria-fittizia/fixture.json`), moving
from via Giulio Cesare 30 to viale Augusto 74 (both zona C). The vault's `locale` is the new
premises; the old ones are asked. The draft is "PROVA NON INVIARE - trasferimento ristorante
generato" and stops before the declarations, payment, signing and sending.

- **Crawl**: `catalogue/F839/sections/suap-060-trasferire-la-sede-dell-attivita.json` (batch).
- **Its own section**, the move's "Dati dell'esercizio di somministrazione" (the title it runs
  under, the new premises' shopping centre, the area where customers eat and drink): drafted by
  `draft.py` from `mod_somministrazione_zone_non_tutelate_trasferimento`, all six boxes exact, and
  put in the dictionary with the asks the other restaurant pratiche use. The old premises
  ("precedente ubicazione dell'esercizio") were already in the dictionary.
- **Questions**: alcohol, music and an outside sign are refused at pre-flight, as in the opening.
  The title's protocol box takes 10 characters. The fees: €96, the 2026 table's VCA column for
  S72 (as the subingresso).
- **Not read yet**: the attachments screen (the batch crawl didn't reach it), so the steps stop at
  the form; the first run reads its slots.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-10 |  | `answers.json` | **filled** |

<!-- /runs -->

