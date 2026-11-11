# A bar or restaurant moving within the historic centre, generated from the batch crawl

"Trasferire la sede dell'attività" for a bar or restaurant in the protected zones (sector "Esercizio di
somministrazione di alimenti e bevande in zone tutelate"): an authorization since the 2026 Piano (rules
table `somministrazione-trasferimento-zone-tutelate`, checked before writing it), with the Reg. 852/2004
notifica and the acoustic nulla osta the table adds there (the wizard's "interventi eventuali" tick, as
the opening). For the centro storico rehearsal's made-up ditta individuale
(`rehearsals/ristorante-centro-storico-fittizio/fixture.json`), moving from via San Biagio dei Librai 20
to via dei Tribunali 150 (zone A, area 3). The draft is "PROVA NON INVIARE - trasferimento centro storico
generato".

- **Crawl**: `catalogue/F839/sections/suap-061-trasferire-la-sede-dell-attivita.json` (batch).
- **Its sections**: the move's "Dati dell'esercizio di somministrazione" here has no shopping-centre
  question and names the comune the title was filed with: the move entry's boxes for those are
  `if_present`. The old premises have the address alone. The Piano's requirements (20 m², accessibility,
  security, the area's score) are asked as at the opening, for the new premises.
- **Fees**: asked ("check it", the VCA column of S74-S76); 420 is made up.
- **Not read yet**: the attachments screen (no `after:`).

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-10 |  | `answers.json` | **stopped** in 1 s |
| 2026-11-10 |  | `answers.json` | **filled** in 109 s |

<!-- /runs -->

