# Portal defect reports, ready to send

The 11 defects of `docs/portal-defects.md` (`claude/skills/pratica/portal/defects.yaml`) as two
reports in Italian, one per recipient, each defect where its fix most likely belongs. Nothing here
has been sent: sending is the person's. Each report asks the recipient to forward a point that
belongs to the other.

| Report | Recipient | Defects |
|---|---|---|
| [`infocamere.md`](infocamere.md) | InfoCamere, impresainungiorno's operator | `scia-36bis-c1`, `scia-34ter`, `pdc-36bis`, `pdc-36-paesaggio`, `pdc-incentivo-energetico` |
| [`comune-napoli-sue.md`](comune-napoli-sue.md) | Comune di Napoli, Servizio Sportello Unico Edilizia | `cila-impresa-dopo`, `agibilita-art24`, `pdc-aree-fuoco`, `coholder-sesso`, `cambio-uso-regionale`, `paesaggio-altri-tecnici` |

Why each goes where: a defect goes to InfoCamere where InfoCamere's national form
(`schema/sue-choices.json`) has the right structure and the portal renders it otherwise, or where
the national form itself lacks the line; to the Comune where the box isn't in the national forms
(Napoli's own addition, or a form with no national model: the voltura and the cambio
d'intestazione) or the case is Campania's. Unchecked against the national form: the permesso's
energy incentive.

## Channels (checked 2026-11-04)

- **InfoCamere**: in the portal, *Supporto* → *Contattaci* → *Scrivici* (a web form to the
  assistance), or the help desk at 06 64892892, Monday to Friday 8:30-18:30
  ([impresainungiorno HelpDesk](https://www.impresainungiorno.gov.it/web/helpdesk)). The Camera di
  Commercio di Padova also gives `assistenza.pa@impresainungiorno.gov.it` for technical (not legal or
  content) questions ([CCIAA Padova FAQ, 2022-10-05](https://www.pd.camcom.it/it/avvia-impresa/suap/faq-suap/faq-suap-utente-professionista/faq-assistenza-portale-impresainungiorno-gov.it));
  it says content questions go first to the comune's sportello.
- **Comune di Napoli SUE**: PEC `sportello.unico.edilizia@pec.comune.napoli.it`, for communicating
  with the office (pratiche by PEC are irricevibili since 6 July 2026, DD 501/2026), or the info
  email `sportello.unico.edilizia@comune.napoli.it`
  ([the office's page](https://www.comune.napoli.it/amministrazione/unita_organizzativa/servizio-sportello-unico-edilizia/),
  as the pratiche-napoli library's CILA entry records it, retrieved 2026-10-25).

## Once sent

Add `reported: {date: YYYY-MM-DD, to: infocamere | comune, channel: ...}` to each defect in
`defects.yaml`, and an answer when one comes, so pre-flight can tell the person a defect is reported
and what the office said. A defect fixed on the portal is checked on a made-up draft, then removed
from `defects.yaml` (and `docs/portal-defects.md` drawn again, `defects.py --write`), and its
recipe's refusal lifted.
