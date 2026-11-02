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

## SCIA in sanatoria, art. 34-ter: a pre-1977 variant's dating and oblazione saved as one field

- **Where**: SCIA edilizia with the sanatoria scelta, section "Asseverazione SCIA - Stato legittimo,
  Dichiarazione di tolleranze, Sanatoria e regolarizzazioni [...]", case "una variante in corso
  d'opera, in parziale difformità dal titolo, rilasciato prima della data di entrata in vigore della
  legge 28 gennaio 1977, n. 10 (articolo 34-ter DPR. n. 380)".
- **What happens**: the case opens three rows, "dà atto che la data/epoca di realizzazione
  dell'intervento" (with its date), "attesta che la data/epoca di realizzazione dell'intervento" (with
  its date) and "determina l'oblazione dovuta [...]" (with the amount). Their inputs carry the values
  1, 2 and 3 of one choice: ticking "dà atto" unticked the oblazione, ticking "attesta" unticked
  "dà atto", so the form saves one of them.
- **What the law asks**: art. 34-ter c. 2 DPR 380/2001 (as the Salva Casa decree 69/2024 wrote it):
  the variant's date is proven by the documents of art. 9-bis c. 1-bis, fourth and fifth periods, and
  where they can't date it the technician attests it; c. 3: the SCIA goes with the payment of an
  oblazione determined under art. 36-bis c. 5. The dating (one of two ways) and the oblazione are both
  due. InfoCamere's national SCIA form (`schema/sue-choices.json`, 12 March 2026) has no pick-one
  rule for this case at all.
- **Effect**: the asseverazione can state the variant's date or its oblazione, never both, so a
  regularization of a variant to a pre-1977 title can't be filed complete on the portal.
- **Checked**: 2026-11-02 on a made-up draft ("PROVA NON INVIARE"), ticked in turn and cancelled
  without saving. The case's quadro "SANATORIA e regolarizzazioni [...]" works: the varied title
  (its number and date, or the art. 9-bis documents) and the payment (its amount and date, or the
  receipt with the amount) are two fields with the values 1 and 2 each, and both stayed ticked.
- **To report**: the dating and the oblazione should be separate choices, as the quadro's title and
  payment are.

## Permesso in sanatoria, art. 36-bis: the same, on the permesso's asseverazione

- **Where**: permesso di costruire with the sanatoria scelta, the asseverazione's sanatoria quadro,
  case "In parziale difformità [...] o con variazioni essenziali" (art. 36-bis).
- **What happens**: the documents attached, the dating (documents or attestation) and the works
  proposal are one radio group, as on the SCIA (seen 2026-10-30). Art. 36 (works without the
  permesso) fills.
- **Effect**: a permesso in sanatoria under art. 36-bis can't be filed complete on the portal.
  What only that case opens goes with it, mapped by no recipe: the landscape compatibility of art.
  36-bis c. 4 in the asseverazione's tutela quadro (works done without the landscape authorization),
  and the sanatoria quadro's acknowledgment that the SUE may ask for structural works, which the
  portal also keeps in one radio group with the oblazione's.

## Permesso in sanatoria, art. 36, in a protected area: no line for the accertamento of art. 167

- **Where**: the pratica that selects the permesso di costruire (sanatoria answered Sì) with the
  "Accertamento di compatibilità paesaggistica (artt. 167-181 D.Lgs. 42/2004 - Comune)"; the
  permesso's asseverazione, quadro 16 "Bene sottoposto ad autorizzazione paesaggistica".
- **What happens**: "ricade in zona tutelata e le opere comportano alterazione" opens three
  procedures (semplificato, ordinario, accertamento "di cui all'articolo 36-bis") and Salva wants one
  ("il valore è obbligatorio" on each, seen 2026-11-02 on a made-up draft). None is the accertamento
  of art. 167 the pratica's other operation asks for.
- **Law**: works done without the permesso or in total difformity (art. 36 DPR 380/2001) in a
  protected area are legalized only with their landscape compatibility found (art. 146 c. 4 D.Lgs.
  42/2004), by the accertamento of art. 167 c. 4-5, which excludes new usable surfaces or volumes;
  art. 36-bis c. 4 is for partial difformity and essential variations only.
- **Effect**: an art. 36 permesso in sanatoria in a protected area can't be filed on the portal
  without stating a procedure that isn't the case's. The rules table sends the case to the
  permesso with the accertamento (`rehearsals/pdc-sanatoria-accertamento-fittizio`), whose
  recipe refuses it with this defect; every other section of the pratica fills.
- **Ask for**: a line "è assoggettato al procedimento di accertamento della compatibilità
  paesaggistica di cui agli artt. 167 e 181 del D.Lgs. 42/2004" beside the art. 36-bis one.

## CILA and CIL: a firm still to be chosen is offered, then refused

- **Where**: the CILA's quadro "i) Rispetto degli obblighi in materia di salute e sicurezza nei luoghi
  di lavoro" (the CIL's g)), and the firm's quadro (the CILA's h), the CIL's f)).
- **What happens**: the safety quadro offers "ricade nell'ambito di applicazione del d.lgs. 81/2008 ma
  si riserva di presentare le dichiarazioni di cui al presente quadro prima dell'inizio lavori", but
  the firm's quadro has no line for a firm still to be chosen, and the portal requires the firm's
  details (16 required boxes, the DURC ones among them) whatever the safety quadro says.
- **What the law asks**: the firm's documents (DURC, the notifica preliminare, the check of its
  fitness) go to the Comune before the works start (art. 90 c. 9 c D.Lgs. 81/2008). On the same
  portal the permesso's and the SCIA's forms let the firm be named later. InfoCamere's national CILA
  form has no such reservation at all (`schema/sue-choices.json`), so the box looks like the
  Comune's own, without the rest of the form following it.
- **Effect**: a CILA or CIL can't be filed before the firm is chosen.
- **Checked**: 2026-11-01, a made-up CILA run in the pane (`rehearsals/cila-fittizia`,
  `answers-impresa-dopo.json`) stopped on the firm's required boxes. Nothing was sent.
- **To report**: either the reservation should let the firm's quadro wait, or the box should go.

## Permesso: an energy incentive must be claimed, even for a project with none

- **Where**: the permesso's asseverazione, quadro "sicurezza impianti e consumi energetici".
- **What happens**: the quadro requires one of the energy incentives (art. 14 c. 6 or c. 7 D.Lgs.
  102/2014, or the 5% volume bonus of D.Lgs. 28/2011) and offers no line for a project with none.
- **What the law asks**: the incentives are options the designer may take, not a requirement.
- **Effect**: a permesso with no energy incentive can't be filed as it is; the recipe refuses it.
- **Checked**: 2026-10-29, the permesso's first runs in the pane (`rehearsals/pdc-fittizio`).
- **To report**: the quadro should offer "no incentive".

## Voltura and cambio d'intestazione: the co-holder's sex is two required boxes

- **Where**: the co-holders' section ("ci sono cointestatari") of both pratiche.
- **What happens**: "sesso: M" and "sesso: F" are two radio groups, each required, so the section
  saves only with both ticked.
- **Effect**: the pratica states both sexes; Claude ticks both and says so in the person's steps.
- **Checked**: 2026-10-31 (the voltura's runs), 2026-11-02 (the cambio d'intestazione's co-holder).
- **To report**: one group, M or F.

## Agibilità: the art. 24 exceptions are marked required

- **Where**: the agibilità's "Attestazione tecnica - Agibilità".
- **What happens**: the boxes for art. 24 c. 5-bis/5-ter (small or low units) and c. 5-quater (a
  derogation another law allows) show "deve essere selezionata almeno un'opzione" when neither is
  ticked, though an ordinary unit is neither.
- **Effect**: an ordinary unit's draft carries the message; it kept its values on the runs. Whether
  sending accepts it isn't known (nothing is sent).
- **Checked**: 2026-10-31, the four agibilità cases ticking neither (`rehearsals/agibilita-fittizia`).
- **To report**: the exceptions should be optional.

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

