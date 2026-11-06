# The SUE's five common cases

What a Napoli architect files most often on the SUE, and how far the portal runner fills each one.
Written by hand on 2026-11-05 from the rehearsals' `runs.json`, READMEs and recipes; those are the
record, and this page only points at them. `docs/coverage.md` counts every pratica, and
`docs/portal-defects.md` says why the refused cases are refused.

"Filled" means what `docs/coverage.md` means: every value read back on a fresh load of the
draft, with made-up people, never declared, paid, signed or sent. Slots that take only signed
files (.p7m) stay empty in a rehearsal (`--made-up`), so they aren't counted against a case.

## Why these five

No published figures count the Comune's pratiche by type. These are what the sources agree on:
apartment renovation is the most frequent work, filed as a CILA, or a SCIA once it touches the
structure; merging or splitting units is usually a CILA; the Salva Casa decree (DL 69/2024) made
sanatorie common again; and the agibilità follows most of them, on Campania's 2025 form. The
Comune's DD 603/2025 forms (CILA, SCIA, SCIA alternativa, permesso) are the titles' own.

## How far each one fills (2026-11-05)

| Case | Steps file | Filled on the portal | Not filled (why) |
|---|---|---|---|
| CILA: interior renovation, no structural work | `rehearsals/cila-fittizia` | 24 of 26 answer sets: works to start, under way or done (late CILA), the Salva Casa tolerances, co-owners, condominium, company clients, several cadastral units | The firm named later (`cila-impresa-dopo`: the portal demands the firm's boxes though the form offers the reservation); a company in the Registro Imprese can't be filled with made-up data (the portal checks the codice fiscale against the RI) |
| SCIA: renovation touching the structure | `rehearsals/scia-fittizia` | 42 of 43, structures included (`answers-strutture`) | The deposito or autorizzazione sismica is a separate pratica at the Genio Civile, not on the SUE and not mapped |
| Merging or splitting units | `rehearsals/cila-fittizia` (manutenzione straordinaria) | Merging (`answers-accorpamento`, 2026-11-04) | Nothing. Splitting takes the same boxes but has no answer set of its own; Napoli's transcribed atto d'obbligo (PRG art. 22 c. 2) is a notarial act, in `yours` |
| Sanatoria | `rehearsals/scia-sanatoria-fittizia`, `rehearsals/pdc-sanatoria-fittizio` | SCIA in sanatoria 10 of 10: works under way (art. 37 c. 5), doppia conformità (art. 36-bis c. 5 b), on structures, in a protected area, a change of use, a variant to a SCIA. Permesso in sanatoria (art. 36) 9 of 10: protected area, zona A, whole-building change of use, ristrutturazione urbanistica | Art. 36-bis c. 1, the Salva Casa conformità (`scia-36bis-c1`), and the permesso's art. 36-bis (`pdc-36bis`): the portal saves the dating, the oblazione and the works proposal as one radio group. Art. 34-ter (`scia-34ter`), the same. Art. 36 in a protected area with the accertamento (`pdc-36-paesaggio`). Seismic authorization apart, at the Genio Civile |
| Agibilità (SCA) | `rehearsals/agibilita-fittizia` | 18 of 18 | Nothing. The art. 24 exceptions show a "required" message for an ordinary unit (`agibilita-art24`); the runner ticks only what applies and leaves the message for the direttore dei lavori |

Each item in the last column is a portal defect, a filing outside the SUE or a portal check made-up
data can't pass, not unmapped work: every one has been tried on the portal or read in its form.
Pre-flight refuses the defects and tells the person why and what they can do.

## Sources

- [Comune di Napoli, Edilizia Privata](https://www.comune.napoli.it/articolo_tematico/urbanistica-patrimonio-politiche-per-la-casa-cimiteri-cittadini/edilizia-privata/) (DD 603/2025, the SUE on impresainungiorno)
- [Cose di Casa: pratiche comunali, which works need which](https://www.cosedicasa.com/normativa-legge/normativa-pratiche-edilizie/pratiche-comunali-per-quali-lavori-servono-una-miniguida-13492)
- [Cose di Casa: frazionamento and accorpamento](https://www.cosedicasa.com/normativa-legge/normativa-pratiche-edilizie/dividere-una-casa-in-due-frazionamento-o-accorpamento-immobili-iter-burocratico-e-bonus-fiscali-97651)
- [Ingenio: the Salva Casa CILA and the tolerances](https://www.ingenio-web.it/articoli/come-cambia-la-cila-e-come-attestare-le-tolleranze-edilizie-con-la-modulistica-aggiornata/)
- [Ediltecnico: the works that need a CILA](https://ediltecnico.it/119044/interventi-edilizi-che-richiedono-la-cila/)
