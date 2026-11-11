# A beautician's structural change, generated from the batch crawl

"Variazioni strutturali in attività di estetista" on Napoli's SUAP, for the shop rehearsal's made-up ditta
individuale (`rehearsals/negozio-fittizio/fixture.json`) as a salon at via Luca Giordano 50: the premises
enlarged from 40 to 55 m², new equipment, two more workstations. The draft is "PROVA NON INVIARE -
variazione estetista generato".

- **Crawl**: `catalogue/F839/sections/suap-011-variazioni-strutturali-in-attivita-di-estetista.json` (batch).
- **Its own sections** (the same 14 as the hairdresser's form), written from the crawl's text (the
  national schema, mod_acconciatori_estetisti_apertura, is the opening's): the area before and after,
  the equipment, the workstations, the season, the sign, the start date and the title it runs under are
  facts; the premises' compliance, the laws and Comune's rules, the antimafia and the technical manager's
  presence are the person's statements.
- **Which pratica**: the library's rules table (pratiche-napoli, 2026-11-10) since it split
  `acconciatore_estetista`: `{attivita: estetista, evento: ampliamento}`, a comunicazione within 30 days
  (regolamento comunale, artt. 16 and 32), whatever the form's own word "SCIA".
- **Attachments screen** (read on the filled draft 2026-11-10): the new plan with layout and equipment and
  the TARI declaration for the new area (plain or signed: mapped, made-up PDFs in `files/`); the
  preposto's ID, the technical manager's qualification and a technician's art. 19 statement (left: the
  opening's, already filed, and the technicians' asseverazioni with their drawings (left: building works are the SUE's)); the descriptive report and the diritti receipt (signed only, the
  person's); Allegati liberi.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-10 |  | `answers.json` | **filled** in 138 s |

<!-- /runs -->

