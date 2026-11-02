# Portal defects

Things Napoli's SUE on impresainungiorno does that a pratica can't work around: each blocks a case
the law allows, so the recipe refuses it with the reason. Each is also a record in
`claude/skills/pratica/portal/defects.yaml`, which the refusal names (`defect:`): pre-flight then
returns it under `defects`, and the person is told what the portal does and chooses what to do. Fixing them is the portal's operator's
(InfoCamere, which runs impresainungiorno) or the Comune's (the SUE configures its forms). Each
entry says what to report and how it was checked, without personal data.

## SCIA in sanatoria, art. 36-bis c. 1: dating, oblazione and works proposal saved as one field

- **Where**: SCIA edilizia with the sanatoria scelta, section "Asseverazione SCIA - Stato legittimo,
  Dichiarazione di tolleranze, Sanatoria e regolarizzazioni per interventi già realizzati e in corso
  di esecuzione", case "un intervento soggetto a SCIA realizzato in assenza della SCIA stessa o in
  difformità da essa, che risulta conforme alla disciplina urbanistica vigente al momento della
  presentazione [...] e ai requisiti prescritti dalla disciplina edilizia vigente al momento della
  realizzazione" (art. 36-bis c. 1 DPR 380/2001, as the Salva Casa decree 69/2024 wrote it).
- **What happens**: the case opens four rows, "dà atto che la data/epoca di realizzazione
  dell'intervento", "attesta che la data/epoca di realizzazione dell'intervento", "determina
  l'oblazione dovuta" and "ai fini della sanatoria, la presente SCIA:". They are one radio field
  with the values 1, 2, 3 and 4: ticking one unticks the others, and the form saves one value.
- **What the law and the national form ask**: the technician states the date or epoch of the works
  (proven by documents, or attested), determines the oblazione (art. 36-bis c. 5), and says whether
  the SCIA proposes works needed for the sanatoria (c. 2). In InfoCamere's national form
  (`intervento_in_assenza_scia_fino_dieci_mila`) only the last is a choice (`no_interventi` or
  `propone_interventi`); the dating and the oblazione are separate items.
- **Effect**: the asseverazione can state one of the three, so a Salva Casa sanatoria of works done
  without a SCIA or in difformity from it can't be filed complete on the portal.
- **Checked**: 2026-10-30 by hand; 2026-11-01 on a made-up draft ("PROVA NON INVIARE"): ticking
  each row in turn left only that one ticked, and the four rows' inputs carry the values 1 to 4 of
  one field. Nothing was saved.
- **Not part of it**: the case's seismic box below the four rows, "Quanto alla rilevanza sismica
  [...] ai sensi dell'art. 36-bis, comma 3-bis", works. Its choices are fields of their own: the
  zone (3 and 4, or 1 and 2), then for zones 1 and 2 whether the works have structural relevance,
  then the art. 94-bis class, and for a relevant one "allega l'autorizzazione sismica" or the
  silenzio assenso. Ticking them kept the dating row ticked (2026-11-01, same draft, not saved). So
  works on structures under c. 1 are blocked by this defect only. The box is offered only in this
  case, as in InfoCamere's SCIA form (`schema/sue-choices.json` 033/034): with double conformity
  and for works under way, structures go in the asseverazione's sismica quadro (the SCIA in
  sanatoria maps them there).

## Permesso in sanatoria, art. 36-bis: the same, on the permesso's asseverazione

- **Where**: permesso di costruire with the sanatoria scelta, the asseverazione's sanatoria quadro,
  case "In parziale difformità [...] o con variazioni essenziali" (art. 36-bis).
- **What happens**: the documents attached, the dating (documents or attestation) and the works
  proposal are one radio group, as on the SCIA (seen 2026-10-30). Art. 36 (works without the
  permesso) fills.
- **Effect**: a permesso in sanatoria under art. 36-bis can't be filed complete on the portal.

## Permesso: the burned-area line is one choice with the soil statement

- **Where**: permesso di costruire, the asseverazione's quadro "qualità terreni, opere di
  urbanizzazione, scarichi": "non interessa aree percorse dal fuoco ai sensi dell'art. 10 della
  legge 353/2000".
- **What happens**: the line is a radio of the same choice as the soil investigations' ("non
  richiede indagini ambientali preventive", "a seguito delle preventive analisi ambientali", "è
  stata oggetto di bonifica"): ticking it unticks the soil statement (seen 2026-11-01, on a
  made-up draft, cancelled without saving).
- **Effect**: a permesso states either its soil or that the area wasn't burned, never both.
  Claude ticks the soil statement and leaves the other (the steps' `yours` says so).
- **To report**: the two lines should be separate choices (the soil under D.Lgs. 152/2006, the
  burned areas under art. 10 c. 1 L. 353/2000).

