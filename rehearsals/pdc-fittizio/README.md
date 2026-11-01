# Permesso di costruire (art. 10 DPR 380/2001)

The permesso for the CILA rehearsal's job: the architect with a procura designs and presents, for
the tenant client, with the owner company's assent and two firms. The P6 case: a ristrutturazione
edilizia of art. 10 c. 1 c (demolished and rebuilt, more volume, three storeys in reinforced
concrete), the contributo worked out by the SUE and paid when the permesso is collected, under
the energy rules (with an art. 14 c. 6 incentive), the renewables, the passive acoustics and the
barriers rules. Made-up data (rehearsals/cila-fittizia's people and property); the draft is
"PROVA NON INVIARE" and stops before the declarations, payment, signing and sending.

`portal-steps.generated.yaml` is `gen.py`'s, from `recipe.yaml`, the crawl of an empty draft
(`catalogue/F839/sections/sue-permesso-di-costruire-art-10-d-p-r-380-2001.json`: 37 sections)
and `dictionary/fnsuap.yaml`. The wizard's Si/No (sanatoria) is answered No.

## What it maps

- **What it asks for** (quadro a) and the asseverazione's tipologia): a new building, a
  ristrutturazione urbanistica or an art. 10 c. 1 c ristrutturazione edilizia (each changing the
  use or not, as the SCIA's four cases), works a SCIA could file asked as a permesso (art. 22
  c. 7), or an essential variant to a permesso, a SCIA alternativa or a titolo unico (its number
  and date), or a variant changing the shape in the centro storico (Tab. A n. 38). An art. 10
  permesso may be convenzionato (art. 28-bis) or in deroga (art. 14: each limit with its own
  line). Campania's kinds, which Napoli's quadro a) puts under "procedimento ordinario": an attic
  made habitable (L.R. 15/2000), car parks on free land, a change of use under art. 2 L.R.
  19/2001 (which of its three).
- **The contributo** (quadro f): free (the rule why), or due: worked out on the architect's
  prospetto or by the SUE, paid when the permesso is collected, in instalments or during the
  works. No opere a scomputo (its Si/No is No).
- **g1)**: the architect presents it ("colui che presenta la pratica": studio, albo, contacts);
  the structural designer and the direttori dei lavori are named before the works start.
- **The asseverazione's own quadri**: surfaces (s.l.p. and superficie coperta), volume, storeys,
  the town plan; the barriers rules (the requirements met, their drawings attached); systems;
  the energy report and the renewables (both filed with the comunicazione di inizio lavori) and
  the incentive the portal then requires; acoustics (art. 8 L. 447/1995 and the DPCM 5/12/1997
  asked apart); excavated earth; fire prevention without the Vigili del Fuoco's assessment;
  asbestos (its plan sent 30 days before the works); structures (the art. 65 denuncia and the
  seismic deposito with the inizio lavori, or the seismic authorization asked now); soil,
  urbanisation and drains (none, or the sewer connection got or asked); every protection the
  SCIA maps (no box to attach for a bene culturale: the SUE asks the Soprintendenza); the
  Autorità di Bacino's plans.
- **The attachments screen** changes with the answers: the co-holders' assent and IDs, the
  barriers drawings. The stato legittimo documents, the procura, the DSC, the receipt and the
  broadband infrastructure drawing (art. 135-bis) take only signed files or are portal
  documents: the architect's. The permesso has no slot for the contributo's documents: the
  architect attaches them, signed, under Allegati liberi.

Refused at pre-flight (`supports`): a landscape authorization (its own operation, filed with the
permesso: not mapped yet); works not allowed in a cemetery's fascia; an acoustic impact or
clima acustico report; a project for the Vigili del Fuoco; a hygiene derogation; systems
needing a project; soil needing investigations; an area without its urbanisation; with the energy
rules or the renewables, no incentive (the portal's form can't say none); a contributo already
paid before filing; the piano casa (L.R. 19/2009: no new requests since 30 September 2022, art.
28 c. 6 L.R. 31/2021). Not offered: "altro non indicato", a SUAP procedure.

## Cases from the schema table (2026-10-30)

Written from `docs/schema-branches.md`, one answers file per group of options of the national
form no case took. Each passes pre-flight offline; **none has been run on the portal yet**.

- `answers-cambio-stessa.json`: a unit's change of use within its category; parti comuni of a condominio; the contributo by prospetto, in instalments; a site of 200 man-days or more; outside the DPCM 5/12/1997.
- `answers-cambio-tra.json`: a unit's change of use between categories; a building of several owners; fire rules apply; asbestos; seismic authorization; a sewer connection to request; protected landscape, works needing no authorization.
- `answers-intero-vincoli.json`: a whole building's change of use; art. 1102 c.c.; a bene culturale; a protected area (no alteration); idrogeologico without authorization; idraulico, VINCA, a cemetery fascia where it's allowed, a RIR activity with no area di danno.
- `answers-per-scelta.json`: SCIA works asked as a permesso by choice (art. 22 c. 7); free of the contributo; no energy filing; a park's nulla osta; idrogeologico authorization; a seismic variant.
- `answers-variante-essenziale.json`: an essential variant to a permesso.
- `answers-rir-deroga-antincendio.json`: a fire-rules deroga; inside a RIR area di danno.
- `answers-rir-fuori-area.json`: a RIR activity, outside its area di danno.

The permesso's other kinds (2026-10-31):

- `answers-sottotetti.json`, `answers-parcheggi.json`, `answers-mutamento-lr.json`: Campania's
  kinds (L.R. 15/2000; L.R. 19/2001, its art. 2 with works adding volume).
- `answers-convenzionato.json`, `answers-deroga.json` (density, height and distance).
- `answers-variante-sagoma.json`, `answers-variante-scia-alt.json`, `answers-variante-titolo-unico.json`.

## Runs

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-10-29 | pane | P6 (plain), first legs on one draft | sections 0-14 filled first time (a), f), g1) included); then stopped six times, each fixed for every pratica and resumed on the same draft: the firm's opening radio worded "saranno eseguiti" (a fourth `if_present` variant), the safety notifica sent before the works (an `on_page` radio), the asseverazione's two opening radios kept as one by the portal, the energy rules requiring an incentive claimed, then two on the attachments screen (the slots the answers add, read and recorded in the crawl; the procura's box named "Scarica il documento") |
| 2026-10-29 | pane | P6 (plain), from scratch, in a batch with the SCIA alternativa | **filled** in 213 s with 7 attachments; fresh load 33 s, every value read back; no retry |
| 2026-10-29 | pane | P6, from scratch after the shared acoustic/fire and ecological quadri changed | **filled** in 141 s; fresh load 23 s, every value read back; no retry |
| 2026-10-30 | pane | P6, from scratch after the sanatoria choice and the project radios went by label (one batch with the SCIA P6 and sanatoria) | **filled** in 156 s; fresh load 26 s, every value read back; no retry |
| 2026-10-30 | pane | asseverazione tolerances (`answers-tolleranze`), `bench/rerun.py` bundle | stopped on "Asseverazione PdC - stato legittimo" as the SCIA's: the sanatoria's si/no left empty ("no" matched "non ha rilevanza strutturale") |
| 2026-10-30 | pane | the same, rerun with a yes or a no read as a whole word | **filled** in 161 s, read back on a fresh load (27 s), nothing moved or loose |
| 2026-10-30 | pane | structural tolerance of no relevance for public safety (`answers-tolleranze-privo`: the regional control term run out), then relevant with the Genio Civile's authorization and its "Autorizzazione sismica" slot (`answers-tolleranze-autorizzazione`) | **filled** both (195 s, 169 s), read back on a fresh load, nothing moved or loose |
| 2026-10-30 | pane | systems needing a project (`answers-impianti`: six systems, each project in its own slot), `bench/rerun.py` bundle | **filled** in 147 s, read back on a fresh load (25 s), nothing moved or loose |
| 2026-10-31 | pane | Campania's kinds and the other permessi (`bench/rerun.py` bundle of nine): `answers-sottotetti`, `-parcheggi`, `-convenzionato`, `-variante-sagoma`, `-variante-scia-alt`, `-variante-titolo-unico` | **filled** all six (151, 141, 144, 168, 150, 142 s), read back on a fresh load (23-27 s), nothing moved or loose |
| 2026-10-31 | pane | `answers-deroga` | stopped on quadro a): the "(specificare)" box beside each limit has no text of its own and reads the limit from the cell before, so it started a block of its own; inpage.js now starts a block where the anchor is a box's best label |
| 2026-10-31 | pane | `answers-mutamento-lr`, built on `answers-cambio-tra` | stopped on the attachments: a required slot empty, from that case's other answers (`answers-cambio-tra` had never run); rebuilt on P6 |
| 2026-10-31 | pane | after the runner's fix: `answers-deroga`; `answers-mutamento-lr` rebuilt on P6; `answers-cambio-tra` alone (with the CILA's direttore and the SCIA's other technician, anchored blocks, as checks) | **filled** the deroga (142 s: each limit's line by its own box) and the change of use (142 s), read back on a fresh load, nothing moved; `answers-cambio-tra` stopped on the attachments: "Documentazione necessaria per la richiesta di autorizzazione all'allaccio in pubblica fognatura", required once the sewer connection is to be requested, was in no recipe: now mapped (plain PDFs) |
| 2026-10-31 | pane | `answers-cambio-tra` with the sewer slot mapped | **filled** in 140 s, read back on a fresh load (22 s), nothing moved or loose |
| 2026-10-31 | pane | two other technicians (`answers-altri-tecnici`: g2 by "+", the second a firm's employee; the permesso's g2 first run) | **filled** in 174 s, read back on a fresh load (24 s), nothing moved or loose |
| 2026-10-31, 11-01 | pane | the never-run cases, `bench/rerun.py` bundles: `cambio-stessa`, `rir-fuori-area`, `variante-essenziale`, P6 **filled**; `intero-vincoli` and `rir-deroga-antincendio` stopped on the Soprintendenza and fire-deroga slots, mapped, then **filled**; `per-scelta` stopped twice on the opere a scomputo's NO, disabled for a free permesso, fixed, then **filled** (164 s) |
| 2026-11-01 | pane | `answers-acustica-vvf-igiene` (acoustics, the Vigili del Fuoco's review, the hygiene deroga) **filled** (154 s); `answers-terreni-urbanizzazione` (soil analysed, no urbanisation works under a convenzione, the cemetery deroga) stopped on the results' slot, mapped, then **filled** (148 s) | |
