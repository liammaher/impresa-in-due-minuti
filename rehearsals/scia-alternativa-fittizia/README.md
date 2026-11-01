# SCIA alternativa al permesso di costruire (art. 23 DPR 380/2001)

The SCIA alternativa for the CILA rehearsal's job: the architect with a procura designs and
presents, for the tenant client, with the owner company's assent, two firms, and Davide Esempio
as structural designer (`s:`). The P6 case: an art. 10 c. 1 c ristrutturazione edilizia (new
facades and openings, more volume, structural strengthening), the contributo on the architect's
prospetto paid in instalments, under the energy rules (its report attached), with the seismic
authorization asked. Made-up data (rehearsals/cila-fittizia's people and property); the draft is
"PROVA NON INVIARE" and stops before the declarations, payment, signing and sending. The works
start 30 days after filing.

`portal-steps.generated.yaml` is `gen.py`'s, from `recipe.yaml`, the crawl of an empty draft
(`catalogue/F839/sections/sue-segnalazione-certificata-inizio-attivita-alternativa-al-permesso-di-cost.json`:
37 sections) and `dictionary/fnsuap.yaml`.

## What it maps

- **What it files** (quadro c) and the asseverazione's tipologia): an art. 10 c. 1 c
  ristrutturazione edilizia, or a new building (or ristrutturazione urbanistica) under a piano
  attuativo, or directly under the town plan, with precise plano-volumetric rules; each changing
  the use or not (the SCIA's four cases).
- **The contributo** (quadro g): free (the rule why), or due: on the architect's prospetto or by
  the SUE, paid within 30 days of filing, in instalments or during the works. No opere a scomputo.
- **The rest is the SCIA's**: six of its asseverazioni are the same sections (the dictionary's
  SCIA entries, aliased), the structural designer's block, every protection, the fasce. Its own:
  the stato legittimo without the sanatoria question; the systems with the energy report
  attached and the renewables; acoustics, excavated earth and fire prevention asked as on the
  permesso; soil, urbanisation and drains; the other ecological vincoli as checkboxes.
- **The attachments screen**: the co-holders' assent and IDs and the energy report (plain files,
  required once their answers apply) are filled; the stato legittimo documents, the procura, the
  DSC and the receipt are the architect's (signed files only, or portal documents).

A landscape authorization is its own operation, filed with this one in one pratica
(rehearsals/scia-alt-paesaggistica-{semplificata,ordinaria}-fittizia: the rules table sends those
cases there). Refused at pre-flight (`supports`): works not allowed in a cemetery's fascia; an acoustic impact or clima acustico report; a
project for the Vigili del Fuoco; asbestos; a hygiene derogation; the barriers rules; systems
needing a project; soil needing investigations; an area without its urbanisation; a contributo
already paid (its form has no receipt box). Not offered: the 4th tipologia (regional works).

## Cases from the schema table (2026-10-30)

Written from `docs/schema-branches.md`, one answers file per group of options of the national
form no case took. Each passes pre-flight offline; **none has been run on the portal yet**.

- `answers-condominio-strutture.json`: parti comuni of a condominio; the contributo within 30 days; 200 man-days or more; a unit's change of use within its category; renewables; DPCM 5/12/1997; fire rules; concrete structures (art. 65) with a seismic deposito; a sewer connection to request; protected landscape, works needing no authorization.
- `answers-vincoli.json`: a building of several owners; outside D.Lgs. 81/2008; no systems; no energy filing; art. 24 c. 5-bis (heights, recupero); no structures; a bene culturale; a park's nulla osta; idrogeologico authorization; idraulico, VINCA, an allowed cemetery fascia, a RIR activity with no area di danno.
- `answers-variante-sismica.json`: art. 1102 c.c.; no notifica preliminare; a fire-rules deroga; a seismic variant; a protected area (no alteration); idrogeologico without authorization; inside a RIR area di danno.
- `answers-rir-fuori-area.json`: a RIR activity, outside its area di danno.

Planning instruments (quadro 3, 2026-10-31): the PRG is always ticked; any other instrument
in force or in salvaguardia is one checklist behind one yes/no, each found by the block its
box opens. Ready offline, **not yet run on the portal**:

- `answers-strumenti.json`: a P.I.P., a P.E.E.P. and another instrument over the area, each with its name, zone and article, beside the PRG.

## Runs

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-10-29 | pane | P6 (plain), first legs on one draft | sections 0-19 filled first time; stopped on the description box (named by its counter: now by "e che consistono in"), then on "specificare il tipo di intervento" (the 4th tipologia's: left), then every asseverazione filled and read back on a fresh load (32 s); stopped on the attachments screen's required slots (read and recorded in the crawl, the energy report mapped) |
| 2026-10-29 | pane | P6 (plain), from scratch, in a batch after the permesso | **filled** in 194 s with 9 attachments; fresh load 33 s, every value read back; no retry |
| 2026-10-29 | pane | P6, from scratch after the SCIA's technical quadri joined this pratica's dictionary entries | **filled** in 159 s; fresh load 24 s, every value read back; no retry |
| 2026-10-30 | pane | asseverazione tolerances (`answers-tolleranze`: 1-bis at 6% and c. 2, under 60 m², zone 2, not structural), `bench/rerun.py` bundle | **filled** in 172 s, read back on a fresh load (27 s), nothing moved or loose (no sanatoria question on this page) |
| 2026-10-30 | pane | structural tolerance of minor relevance (`answers-tolleranze-minore`), then relevant with the Genio Civile's authorization and its "Autorizzazione sismica" slot (`answers-tolleranze-autorizzazione`) | **filled** both (155 s, 187 s), read back on a fresh load, nothing moved or loose |
| 2026-10-30 | pane | systems needing a project (`answers-impianti`: six systems, each project in its own slot), `bench/rerun.py` bundle | **filled** in 188 s, read back on a fresh load (28 s), nothing moved or loose |
| 2026-10-31 | pane | `answers-condominio-strutture` with the sewer connection's slot ("Documentazione necessaria per la richiesta di autorizzazione all'allaccio in pubblica fognatura", read on the permesso) mapped | **filled** in 148 s, read back on a fresh load (23 s), nothing moved or loose |
| 2026-10-31 | pane | the planning instruments (`answers-strumenti`), `bench/rerun.py` bundle | **filled** in 151 s, nothing moved or loose |
| 2026-10-31, 11-01 | pane | the never-run cases, `bench/rerun.py` bundles: P6, `rir-fuori-area`, `vincoli` **filled**; `variante-sismica` stopped on the fire-deroga slot, mapped, then **filled** (153 s) |
