# Domanda di parere per esonero dall'autorizzazione paesaggistica: mapped, refused in Napoli

The 27th SUE operation: asking that works in a protected area be recognised as excluded from the
landscape authorization (an item of DPR 31/2017's Allegato A). Same architect with procura and
client as the CILA rehearsal, made-up data: a façade's plaster and paint redone in its existing
colours, item A.2.

`portal-steps.generated.yaml` is `gen.py`'s, from `recipe.yaml`, the crawl of an empty draft
(`catalogue/F839/sections/sue-domanda-di-parere-per-esonero-dallobbligo-di-autorizzazione-paesaggistic.json`)
and `dictionary/fnsuap.yaml`. Of its sixteen sections, nine are other pratiche's, three are the
dichiarante's declarations, and four are its own: the client's title, the building's lawful
state, the Allegato A item and the ente asked (with the relazione illustrativa).

## Why every case is refused (2026-10-30)

The Comune's landscape directive (Allegato 1 to D.D. 1072I/2024/154, § 3.2) rules out "an
attestation (atypical, not provided for by law) of the exclusion or exemption": the technician
asseverates the case of exclusion and its Allegato A item, in the building pratica when the works
need one, and the Comune may check it later. The Soprintendenza's FAQ sends such questions to the
Comune. So the SUE rules table (`rules/sue-napoli.yaml`, rule `parere-esonero`) refuses the
request with that reason; the library's page is `napoli/comune/parere-esonero-autorizzazione-paesaggistica`.
Every other SUE recipe fixes `parere_esonero: "false"`, so none asks the question.

The steps are kept: the pratica is mapped whole, for the day a case is one the table gives it (or
a comune whose office does answer it).

## Not confirmed

- The legittimità section's eight radios are read as three choices by row order (the lot; whether
  the place matches its lawful state; what else proves it). The crawl kept none of its text. A
  wrong grouping unticks a radio on Salva and the read-back stops the run. A depth-3 recrawl of
  2026-10-30 (not yet in the catalogue) shows the three conformity radios greyed until "esiste un precedente
  edilizio" is ticked, so they are asked only then; the rest of the grouping is still unconfirmed.
- The Allegato A dropdown is chosen by the item's number ("A.2."): `inpage.js` takes the one option
  that starts with it. Not run on the portal.
- Refused besides: more than one previous building title (the section's "+" rows), works under
  several Allegato A items, the bollo by marche.

## Runs

None: pre-flight refuses every case in Napoli.
