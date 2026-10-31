# Intake: a job's documents to the pratica's values and answers

What an architect hands over for a pratica (the visura, the lease or the deed, their own relazione
tecnica, the drawings, the receipts) holds most of what pre-flight asks. `intake.py scan` reads it,
puts the people's and the property's fields in a private values file, and proposes the router's
facts and the pratica's answers, each with the document and the words it comes from. The person
confirms them in one "ok" (`accept`); pre-flight then asks only what no document says.

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

`bench/test_intake.py` (the pratica venv's Python; no network, vault or browser): the P6 dossier's
kinds (Napoli's annexes too), its values against `rehearsals/cila-fittizia/fixture-p6.json`, nothing personal in
`intake.json`, both PDF readers alike, the router's facts, the deed's titles, a receipt paid
elsewhere, a signed .p7m, the owners' cases, and the whole path: scan, accept, route, scan against
the steps file, accept, pre-flight with both values. On P6, pre-flight asks 20 questions and lacks
140 fields with the vault alone, and 0 and 5 (contacts no document carries) with the documents.
