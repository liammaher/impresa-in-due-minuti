# A food shop with consumo sul posto moving within the protected zones, generated from the batch crawl

"Trasferire la sede dell'attività" in the sector "Vicinato - settore alimentare consumo immediato
(zone tutelate)": since the 2026 Piano an authorization, with the Reg. 852/2004 notifica for the new
premises. For the shop rehearsal's made-up ditta individuale (`rehearsals/negozio-fittizio/fixture.json`)
as a grocer's where customers eat on the spot (no table service), moving from via dei Tribunali 30 to the
fixture's premises: the fixture's address (via Luca Giordano, Vomero) isn't in zone A, so the case's `zona: a`
is made up as the rest. The draft is "PROVA NON INVIARE - trasf. alimentari zone tutelate generato".

- **Crawl**: `catalogue/F839/sections/suap-018-trasferire-la-sede-dell-attivita.json` (batch).
- **Which pratica**: the rules table's `vicinato-alimentare-consumo-variazioni-zone-tutelate`
  (autorizzazione) with the notifica; the recipe fixes `consumo_sul_posto: true`, and the table names
  this sector (pratiche-napoli#93), so a zone C case isn't routed here.
- **Its sections**: all in the dictionary already, the old premises' with the address alone. The
  authorization's bollo is asked as the protected-zone restaurant's.
- **Fees**: asked ("check it"); 96 is made up.
- **Not read yet**: the attachments screen (no `after:`).

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-10 |  | `answers.json` | **stopped** in 1 s |
| 2026-11-10 |  | `answers.json` | **filled** in 82 s |

<!-- /runs -->

