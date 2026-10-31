# Segnalazione certificata per l'agibilità: generated, never walked

After the CILA rehearsal's works: the architect is the direttore dei lavori and attests, the
client is the tenant. Made-up data (an invented CILA, fine lavori and DOCFA, made-up
dichiarazione di conformità in `files/`); the draft is "PROVA NON INVIARE" and stops before
the declarations, signing and sending.

`portal-steps.generated.yaml` is `gen.py`'s, from `recipe.yaml`, the crawl of an empty draft
(`catalogue/F839/sections/agibilita.json`: 255 s, 117 choices) and `dictionary/fnsuap.yaml`.
The attestations (impianti, statics, energy, barriers, catasto, house numbers, fire, lifts)
are pre-flight's questions.

## What it covers (2026-10-31)

- **Works on structures** (art. 24 c. 5 b) DPR 380/2001): the collaudo statico certificate of
  art. 67, or for repairs and local works the direttore dei lavori's dichiarazione di regolare
  esecuzione (art. 67 c. 8-bis, 8-ter), each attached or named by where it is kept, protocol and
  date; or minor works with no collaudo (the form's own box). Each "references" choice has its
  own rows with the same labels: they go by the block that starts at that choice.
- **Partial agibilità** (art. 24 c. 4 a) and b)): single buildings or single units, in both the
  presentation and the attestation.
- **SCIA Unica** (art. 19-bis c. 2 L. 241/1990): proposed when the fire SCIA (art. 4 c. 1 DPR
  151/2011) goes with it; the presentation's second row of radios.
- **Energy**: the AQE attached. **Barriers**: art. 77 or art. 82. **House numbers**: the request
  attached, or the one already filed by protocol and date. **Lifts**: this agibilità counts as
  the communication of art. 12 DPR 162/1999, or names the one filed before.
- **Every system** the form lists (ten, "Altro impianto" with what it is), each with its
  dichiarazione di conformità or di rispondenza; or, system by system (art. 24 c. 5 c) DPR
  380/2001), any of the form's certificates: the dichiarazione attached, one already filed with
  the Comune (its P.G.), a collaudo where required, an atto notorio (art. 6 DPR 392/1994; the
  form has none for safety lines and "Altro"). One checklist a certificate. The Dichiarazione di
  conformità slot is asked whenever systems were touched (shared with the other SUE pratiche).
- **Art. 24 c. 5-bis/5-ter** (low rooms 2.40-2.70 m; one-room flats of 20-28 m² for one, 28-38 m²
  for two, with c. 5-ter's condition: recupero, or a renovation with alternative solutions)
  and **c. 5-quater** (a derogation another law allows, the act named: L.R. Campania 15/2000
  for attics). The adattabilità of c. 5-ter is asked and refused when unmet; more than one case
  is refused. The portal requires one of these boxes; when neither applies it is left to the
  direttore dei lavori (`yours`).

Each "si allega" adds its own required slot on Allega documenti (read on the portal
2026-10-30): Certificato di collaudo statico, Dichiarazione di regolare esecuzione, Attestato
di qualificazione energetica (AQE), Documentazione necessaria per l'assegnazione o
aggiornamento di numerazione civica, SCIA ai sensi dell'art. 4 comma 1 del d.P.R. n. 151/2011,
and for a partial agibilità the Copia di elaborato planimetrico (the plan marking the works
completed). The recipe fills them (`on_page`).

## Cases from the schema table (2026-10-30)

Written from `docs/schema-branches.md`, one answers file per group of options of the national
form no case took. Each passes pre-flight offline; **none has been run on the portal yet**.

- `answers-vale-fine-lavori.json`: no fine lavori filed: the segnalazione counts as it, works finished completely.
- `answers-parziale-vale-fine.json`: the same for a partial agibilità, works finished in part.
- `answers-regolare-esecuzione.json`: no systems; the DL's dichiarazione di regolare esecuzione attached instead of the collaudo.
- `answers-non-soggetto-collaudo.json`: works on structures not subject to the collaudo statico.

Cases for the systems' certificates and art. 24 (2026-10-31), each ready at pre-flight
offline; **not yet run on the portal**:

- `answers-impianti-depositati.json`: all ten systems, each certificate already filed with the Comune (its P.G.); rooms under 2.70 m (art. 24 c. 5-bis a).
- `answers-impianti-collaudo.json`: all ten with a collaudo, an atto notorio where the form has one, the dichiarazione for the other two; a one-room flat for one in a recovered building.
- `answers-monostanza-due.json`: a one-room flat for two, with a renovation of alternative solutions.
- `answers-5quater.json`: an attic under L.R. Campania 15/2000 (art. 24 c. 5-quater).

## Runs

| Date | Browser | Login → draft | Result |
|---|---|---|---|
| 2026-10-28 | pane | 218 s of runs in six legs on one draft; attachments 9.5 s | 121 values and 4 attachments kept, every value read back on a fresh load (23.1 s) |
| 2026-10-29 | pane | 89.2 s from a blank draft (`bench/rerun.py` batch, after the SCIA's dictionary change; fresh load 14.3 s) | **Filled**, every value read back on a fresh load |
| 2026-10-30 | pane | `answers-collaudo.json`: 96.4 s from a blank draft (fresh load 16.1 s) | **Filled**: collaudo attached, AQE, house-number request, fire SCIA (SCIA Unica), all ten systems, the lift's communication; 8 files kept |
| 2026-10-30 | pane | `answers-estremi.json`: first try stopped on a required slot the partial agibilità adds (the elaborato planimetrico), mapped; rerun 87.7 s (fresh load 13.6 s) | **Filled**: regolare esecuzione, house-number request and lift communication by their references, one unit's partial agibilità, art. 77; 5 files kept |
| 2026-10-30 | pane | `answers-parziale.json`: 89.9 s (fresh load 14.3 s) | **Filled**: the collaudo certificate by its references, a building's partial agibilità, art. 82 |
| 2026-10-30 | pane | `answers-p6.json` on the final steps: 87.6 s (fresh load 13.4 s) | **Filled**, unchanged |
| 2026-10-31 | pane | `bench/rerun.py` bundle | `answers-monostanza-due` and `answers-5quater` **filled** (87 s, 86 s), nothing moved or loose. `answers-impianti-depositati` stopped at Allega documenti: with every system's certificate deposited the portal drops the dichiarazione di conformità's slot. `answers-impianti-collaudo` stopped there too: a system's collaudo and atto notorio each add a required slot ("Certificato di collaudo ove previsto, degli impianti installati", "Atto notorio relativo alla conformità degli impianti"). Both mapped after the run |
| 2026-10-31 | pane | the two systems cases again, on the slots mapped from their stops | **filled** both (96 s, 98 s), read back on a fresh load (14 s each), nothing moved or loose |

Each stop was general, fixed where it belongs, and the run resumed on the same draft:

1. A street's suggestion list open over "scala" (also once in the CILA): the runner now closes
   any open list before typing in a box.
2. "Attestazione tecnica - Agibilità": the portal marks the art. 24 c. 5-bis/5-ter and
   5-quater boxes as required, though they are exceptions (small or low units). Whether one
   applies is the direttore dei lavori's attestation: left to them (`theirs`, and a line in
   the person's steps).
3. "Sicurezza degli impianti": each system ticked opens its rows ("Subalt. n." and which
   certificate). The crawl tries no two choices together, so it never saw them: the
   dictionary names them by label inside the block that starts at the system's box, and the
   runner finds a moved id again by its label.
4. The label reader took "Il valore è obbligatorio" (the box's title and cell) for the label:
   it now skips validation messages in front.

Left to the person: the procura and the "Quadro riepilogativo - Agibilità" (portal documents,
signed), the art. 24 box above, the declarations, signing and sending.

## Clean reruns (2026-10-29)

In the pane, from run.py's install.js and run.js, nothing touched between runs: first filled in 89.3 s; second, with the runner waiting for a section to open, **filled** in 101.3 s, read back on a fresh load.
