# Taking over a bakery, generated from the batch crawl

"Subentrare nell'esercizio dell'attività" for a bakery (sector Panificio) on Napoli's SUAP, for the bakery
rehearsal's made-up ditta individuale (`rehearsals/panificio-fittizio/fixture.json`) taking over the bakery
at via Foria 120 by a notary's sale. The draft is "PROVA NON INVIARE - subingresso panificio generato".

- **Crawl**: `catalogue/F839/sections/suap-004-subentrare-nell-esercizio-dell-attivita.json` (batch).
- **Its own sections** (11), written from the crawl's text: the title to the premises, how the business
  changes hands (the deed's date, notary, repertorio; the return of a leased business is refused), the new
  holder's start, the previous holder, the TARI declaration (its crawl kept the SUE's "inizio lavori" text
  for the same one date box: its own ask, not an alias), the ovens, its own shop and consumption on the
  spot, the production manager (the titolare), fire prevention (outside DPR 151/2011).
- **Which pratica**: no bakery in the library's rules table yet: no `rules:`.
- **Left to the person**: the Reg. 852/2004 update for the new holder, filed apart (the wizard's
  interventi tick for the notifica isn't crawled).
- **Attachments screen** (read on the filled draft 2026-11-10): the takeover's deed (plain or signed:
  mapped, `subingresso_atto_doc`, a made-up PDF in `files/`), a technician's art. 19 statement (left: no
  works), Allegati liberi, the diritti receipt.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-10 |  | `answers.json` | **filled** in 101 s |

<!-- /runs -->

