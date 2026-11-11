# A bakery moving to new premises, generated from the batch crawl

"Trasferire la sede dell'attività" for a bakery (sector Panificio) on Napoli's SUAP, with the Reg.
852/2004 notifica for the new premises, for the bakery rehearsal's made-up ditta individuale
(`rehearsals/panificio-fittizio/fixture.json`), moving from via Duomo 40 to via Foria 120. The draft is
"PROVA NON INVIARE - trasferimento panificio generato".

- **Crawl**: `catalogue/F839/sections/suap-004-trasferire-la-sede-dell-attivita.json` (batch).
- **Its two sections**, written from the crawl's text (no national schema for the bakery's form): the
  old premises with their C.C.N. (and its delibera) and shopping centre or covered market, a second
  dictionary entry for "precedente ubicazione dell'esercizio"; and "dati relativi al trasferimento
  dell'attività" (the title, the new premises' C.C.N., shopping centre, consumo sul posto, season). The
  crawl saw the new C.C.N.'s delibera date as the title's date moving (one label twice): it is
  `on_page`, the second "del" once Si is ticked.
- **Which pratica**: the library's rules table has no bakery yet: no `rules:`, as the opening.
- **Fees**: asked ("check it"); 96 is made up.
- **Not read yet**: the attachments screen (no `after:`).

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-10 |  | `answers.json` | **filled** in 86 s |

<!-- /runs -->

