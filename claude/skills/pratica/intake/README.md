# Intake: a job's documents to the pratica's values and answers

What an architect hands over for a pratica (the visura, the lease or the deed, their own relazione
tecnica, the drawings, the receipts) holds most of what pre-flight asks. `intake.py scan` reads it,
puts the people's and the property's fields in a private values file, and proposes the router's
facts and the pratica's answers, each with the document and the words it comes from. The person
confirms them in one "ok" (`accept`); pre-flight then asks only what no document says. `accept`
also records each answer's document under the answers file's `fonti`, so pre-flight's summary of
a complete folder (`riepilogo`) can say where every answer comes from.

## What it reads, and from where

| Document | Read for |
|---|---|
| Visura catastale (per immobile) | sezione urbana, foglio, particella, subalterno, categoria, address with scala and piano, comune and provincia, superficie; the owners with their diritto and quota; the planimetria's filing date |
| Lease or comodato | the tenant (name, codice fiscale, birth), the landlord, interno and CAP: the client is the tenant (`titolo` locatario, not exclusive) |
| Deed (atto di provenienza) | the menzioni urbanistiche: the titles the building was built under (`stato_legittimo` titoli, the first as `prec_permesso`), or that it predates 1 September 1967 |
| Relazione tecnica | the art. 3 category, structures, prospetti, cambio d'uso, vincoli (the router's facts); works started or not and when; parti comuni, contributo, uomini-giorno, firms, tolerances, other assents, technicians, direttore dei lavori; OGGETTO and the description as the form's free text |
| Notifica preliminare | D.Lgs. 81 applies; how many firms |
| Receipts | whether the diritti went to Napoli's postal account and a sanzione to its IBAN |
| Programma 100, Modello DP, tipo edilizio attestation, atto d'obbligo | Napoli's annexes: with `--steps` for a building title, a note names those the dossier lacks (the first two always, the attestation when the relazione says zona A, the atto d'obbligo when it describes a frazionamento) |
| Assent, drawings, photos, identity document | their file slots |

With no lease, a visura with one owner makes that owner the client (`proprietario` at 1/1, else
`comproprietario`). `--client SLUG` names the client when the documents don't.

## The SUAP's documents (`--table suap-napoli`, 2026-11-12)

A business's pratica reads other documents. Same contract: the business's and its people's values go to
`OUT/private/values.json`, Claude reads `intake.json`, the person confirms the proposals with `accept`.

| Document | Read for |
|---|---|
| Visura camerale (Registro delle Imprese) | `business.*` (denominazione, forma giuridica, codice fiscale, partita IVA, REA and CCIAA, PEC, the dates, ATECO, the activity, the registered office); each person with a carica as `<first name>:identity.*`, `residenza.*` and `ruolo.*`; the router's `attivita` from the ATECO code (a proposal: the code proves nothing about the premises) and `altri_soggetti` from how many people have cariche |
| Lease or comodato of the premises | `locale.*`: address, CAP, catasto, the use, the term's start, `locale.titolo` |
| Visura catastale of the unit | `locale.catasto_*` and the surface; its identifiers win over the lease's |
| Relazione descrittiva dei locali | the sales area, consumption on the spot, sign, music, dehors, alcohol, fire prevention (a "no" only from an explicit sentence: «non è prevista alcuna insegna»), and `oggetto` |
| Deed of sale or rental of a business | `evento: subingresso`, the one event a document can say |
| Certificato di agibilità, ricevuta pagoPA, identity card | a note with its estremi; the files' slots |

What no document says is asked: the event of a new business (opens, moves, enlarges, closes), the zone of
the Piano (it is on the Comune's map, not in a folder), the declarations, the diritti. The slug of a person is
their first name, as in the vault (the visura writes SURNAME NAME).

**The test dossiers are made up** (`bench/dossier_suap.py`): no real visura camerale, commercial lease or
relazione descrittiva is public. The visura follows the headings of the Camera di Commercio's «visura ordinaria»
as the maintainer remembers them, one `label: value` per line; a real one may lay its text out otherwise, and
the first real visura camerale is the test that counts. Not covered yet: a statuto or atto costitutivo (the
visura carries what the pratica asks), a DIA/SCIA of the previous holder, a planimetria's own dimensions, a
company's other administrators' documents.

## Privacy

People's data goes from the files to `OUT/private/values.json` (0600, its folder 0700), the format
`pvault get` prints, read by `run.py --values` after the vault's own (`--values - --values FILE`: the
vault's value wins). `OUT/intake.json` is what Claude reads: kinds, field ids, notes and proposals,
no person's value (`bench/test_intake.py` checks it for every codice fiscale, birth date and surname
in the dossier). A proposal's words are the relazione's own technical phrases.

The intake writes nothing to the vault: `pvault set` takes one field per approval. Keeping a
client's data for the next pratica would need a batch write with its own Touch ID prompt.

## Reading PDFs

`pdftotext -layout` (poppler) when installed; else its own reader (compressed content streams,
simple fonts), which reads PDFs as office software and the Agenzia's own tools write them, not
every PDF: a font it can't decode is reported as unread, never misread. A .p7m is read for the
document it wraps (openssl). A scan has no text: it is placed by its file name, read for nothing.

## What isn't known yet

No real document of these kinds is public: they carry people's data. The test dossier
(`bench/dossier.py`) is made up in the documents' published layouts: the visura from the Agenzia
delle Entrate's November 2025 guide (whose specimens are images, so the words and their order are
copied), the lease from the DM 16/01/2017 model's headings, the deed's menzioni from art. 46 DPR
380/2001, the receipts from Napoli's SUE Costi page. A real visura's PDF may lay its columns out
otherwise: the patterns read the text whatever the line order, but the first real visura is the
test that counts. The relazione's phrases are those the national models and Napoli's CILA notes
use; a relazione worded otherwise proposes less, never something else.

## Tests

`bench/test_intake.py` (the pratica venv's Python; no network, vault or browser; the SUAP's tests last, on `bench/dossier_suap.py`'s shop and bar: kinds, values against `rehearsals/negozio-fittizio/fixture.json`, no codice fiscale, birth date, surname or address in `intake.json`, the facts with their words, negations, and the path scan, route.py, pre-flight): the P6 dossier's
kinds (Napoli's annexes too), its values against `rehearsals/cila-fittizia/fixture-p6.json`, nothing personal in
`intake.json`, both PDF readers alike, the router's facts, the deed's titles, a receipt paid
elsewhere, a signed .p7m, the owners' cases, and the whole path: scan, accept, route, scan against
the steps file, accept, pre-flight with both values. On P6, pre-flight asks 20 questions and lacks
140 fields with the vault alone, and 0 and 5 (contacts no document carries) with the documents.
