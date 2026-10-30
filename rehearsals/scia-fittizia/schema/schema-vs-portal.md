# The official SCIA schema against the SUE portal

Compared on 2026-10-30: InfoCamere's `mod_scia_v1.0.7.xsd` (repository
`InfoCamereSCpA/Sistema-Informatico-degli-Sportelli-Unici-Moduli-PA`, commit `fc13e08`, 12 March
2026), flattened by `../../cila-fittizia/schema/flatten.py`, against every box the SUE of Napoli
showed on a SCIA draft in `claude/skills/pratica/portal/catalogue/F839/sections/scia.json`: the
boxes of each section, those a choice reveals, and the two sections that only appear after a choice
(the procuratore, the sanatoria). Matching is by meaning, as in the CILA comparison
(`../../cila-fittizia/schema/schema-vs-portal.md`), but done by a subagent, not by hand; a person
checked six of its high-confidence matches (all right), which is not a validation of the rest.

The ids in this file point into the dumps next to it: `scia-schema.txt` (S000-S402, the schema's
leaves minus its attachment lists), `scia-portal.txt` and `scia-portal-extra.txt` (P000 onward, the
portal's boxes; the second is the two sections that only appear after a choice). `A` and `X` ids
are schema leaves outside the 403 (below), read from the flattened form. `scia-match.json` is the
whole result, machine-readable.

## Counts

### Schema leaves (403)

| Outcome | Leaves |
|---|---|
| same | 311 |
| elsewhere | 15 |
| none (no portal box) | 75 |
| declarations (not counted: privacy x2) | 2 |
| **Total** | **403** |

Share of the 401 non-declaration leaves: same 77.6%, elsewhere 3.7%, none 18.7%.

Low-confidence entries: **11** (5 matches, 6 `none`). The `none` ones are where the portal may be hiding a branch rather than lacking the field.

### Portal boxes (661)

| | Boxes |
|---|---|
| declarations (not counted) | 9 |
| matched | 614 |
|   to a leaf of the 403 | 326 |
|   only to leaves outside the 403 file (see below) | 171 |
|   structural gate boxes (stand for a schema group) | 117 |
| portal-only | 38 |
| **Total** | **661** |

Read against the 403-leaf file alone, 326 of the 652 counted portal boxes have no leaf to match; 171 of those belong to leaves the file leaves out (next section), 117 are gates, which leaves the 38 truly portal-only boxes.

## The 403-leaf file leaves out the schema's repeated person blocks

`scia-schema.txt` has `scheda_anagrafica` (titolare, ditta, delegato) and `dichiarazioni` / `relazione_tecnica_asseverazione`, but **not** `allegatiSCIA/allegatoSoggettiCoinvolti` (333 leaves: terzi titolari, the technicians, the imprese esecutrici, DURC) nor the 24 `allega...` checkboxes of the relazione. They sit in `tabella_allegati`, which the file treated as an attachment list. The portal asks all of them inline (quadri a, h1, H2, i and the Asseverazione), so judging the portal against the 403 alone would call 171 ordinary boxes portal-only. I read those leaves from `flat/scia.json` (ids `A000`-`A332` and `X00`-`X23`, in the JSON under `schema_supplement`) and matched the portal to them too; they are **not** in the counts above.

| Supplement | Leaves | same | elsewhere | none |
|---|---|---|---|---|
| allegatoSoggettiCoinvolti (A) | 332 (+1 privacy declaration) | 115 | 34 | 183 |
| relazione `allega` checkboxes (X) | 24 | 22 | 0 | 2 |

How the repeats were treated: titolare, terzo titolare, progettista architettonico, progettista strutturale, altro tecnico and impresa esecutrice each matched role to role, the portal's repeated address triples (born / resident / studio) to the schema's `nato` / `residente` / `studiopro`. The schema keeps the studio and ordine only on the *direttori dei lavori*; the portal asks them of the progettista, so those are *elsewhere* (medium). A schema leaf asked in two portal variants (the progettista as 'tecnico incaricato' and as 'titolare o procuratore') lists both boxes. The portal's 'Via, Piazza, ecc.' is one text box where the schema has a toponimo select plus a street, and its 'telefono / cell.' follow the schema's telefono / cellulare / fax. The `A` entries with no portal box are mostly the direttori dei lavori (79 leaves: the portal sends you to a 'DIRETTORE/I LAVORI' section that is not in the dump), the rest of the altri tecnici's employer (38), the third-party owner's company data (22), the progettisti's remaining personal fields (20).

## Declarations (the person's own, not counted)

Schema: S218 privacy information read (dichiarazione_presa_visione_informativa_privacy); S402 privacy information read, repeated at the end of the Asseverazione; plus A332 in the supplement.

Portal: P054 consapevolezza: no PEC means no certainty of delivery; P100 'PER PRESA VISIONE' acknowledgement in quadro b); P364 consapevolezza: the SCIA cannot limit third parties' rights (quadro m); P607 diritti di segreteria/istruttori (tasse comunali): none due; P608 ... not in the tariff; P609 ... exempt; P610 diritti/spese due; P611 total in euro; P612 pay online on the next page.

## Schema fields with NO portal box (75), by schema section

Each was checked against the whole portal list (both files, 661 lines) for the same meaning under another wording; where one is close, the note says so.

### scheda_anagrafica / schedaTitolare (5)


*region: the portal asks province and comune only* (high)

- `S004` nato / a / regione

*document type (permesso, passaporto, ...): the portal only has the 'cittadino non UE' checkbox and the document's numbers* (medium)

- `S010` documentoSoggiorno / tipo

*region: the portal asks province and comune only* (high)

- `S016` residente / regione

*localita (frazione) of the address: asked only for the intervento's address (P056), not for residence/sede* (high)

- `S020` residente / localita

*fax of the titolare: the portal asks fax only for the ditta (P037)* (high)

- `S029` contatti / fax

### scheda_anagrafica / schedaDitta (6)


*REA number of the ditta: the portal asks only the Camera di commercio (P041), the REA 'n.' only for imprese esecutrici* (medium)

- `S035` CCIAA / numeroREA

*other register (registroDi / estremi) alternative of the CCIAA choice* (medium)

- `S036` CCIAA / registroDi
- `S037` CCIAA / estremi

*region: the portal asks province and comune only* (high)

- `S039` sedeLegale / regione

*localita (frazione) of the address: asked only for the intervento's address (P056), not for residence/sede* (high)

- `S043` sedeLegale / localita

*ditta email: the portal has the PEC only (P038)* (high)

- `S049` contatti / email

### scheda_anagrafica / schedaDelegato (11)


*region: the procuratore form asks province and comune only* (high)

- `S059` nato / a / regione

*documento di soggiorno of the procuratore: not asked in the procuratore section* (medium)

- `S065` documentoSoggiorno / tipo
- `S066` documentoSoggiorno / estremi
- `S067` documentoSoggiorno / rilasciatoDa
- `S068` documentoSoggiorno / dataRilascio
- `S069` documentoSoggiorno / dataScadenza

*country of residence of the procuratore: the portal asks 'Residente in', Provincia, CAP, Indirizzo only* (medium)

- `S070` residente / stato

*region: the procuratore form asks province and comune only* (high)

- `S071` residente / regione

*foreign-place alternative, localita and toponimo of the procuratore's residence: only the 'Residente in' and 'Indirizzo' texts exist* (medium)

- `S074` residente / localitaEstera
- `S075` residente / localita
- `S076` residente / toponimo / specie

### dichiarazioni / presentazione (1)


*scia_condizionata flag: the kind of SCIA is chosen in the wizard, not on a quadro* (medium)

- `S090` scia condizionata

### dichiarazioni / qualificazione_intervento (9)


*restauro sub-options other than 'intero immobile': only P113 was seen under restauro; the 'non comporta / singola unita' boxes (P109-P111 exist under manutenzione straordinaria) may be shared DOM or really absent* (low)

- `S095` manutenzione restauro / no mutamento
- `S096` manutenzione restauro / mutamento categoria singola unita
- `S097` manutenzione restauro / mutamento tra categorie singola unita

*ristrutturazione sub-options other than 'intero immobile': see S095* (low)

- `S099` manutenzione ristrutturazione / no mutamento
- `S100` manutenzione ristrutturazione / mutamento categoria singola unita
- `S101` manutenzione ristrutturazione / mutamento tra categorie singola unita

*change of use without works, same category, single unit: not offered in quadro c) (it is in the Asseverazione, P386)* (medium)

- `S108` mutamento destinazione uso singola unita / senza opere categoria singola unita

*procedimento automatizzato / ordinario: not shown (same as the CILA)* (medium)

- `S114` procedimento automatizzato
- `S115` procedimento ordinario

### dichiarazioni / localizzazione_intervento (3)


*country of the intervento's address: the portal assumes Italy* (high)

- `S141` immobile / ubicazioneImmobile / stato

*ufficio provinciale catastale (same as the CILA)* (high)

- `S142` immobile / riferimentiCatastali / datiCatastali / ufficio provinciale catastale

*coordinates (same as the CILA)* (high)

- `S150` immobile / coordinate / valori

### relazione_tecnica_asseverazione / dichiarazioni_tolleranze (6)


*structural tolerance in seismic zone 1-2: pubblica incolumita (authorisation number/date, silenzio-assenso), minore rilevanza, priva rilevanza. The portal shows only the stem P415 'ha rilevanza strutturale ...' with no sub-boxes. HIDDEN BRANCH* (medium)

- `S250` tolleranza zona sismica alta / tolleranza strutturale / tolleranza pubblica incolumita / allega autorizzazione sismica / data
- `S251` tolleranza zona sismica alta / tolleranza strutturale / tolleranza pubblica incolumita / allega autorizzazione sismica / numero
- `S252` tolleranza zona sismica alta / tolleranza strutturale / tolleranza pubblica incolumita / silenzio assenso autorizzazione / data
- `S253` tolleranza zona sismica alta / tolleranza strutturale / tolleranza pubblica incolumita / silenzio assenso autorizzazione / numero
- `S254` tolleranza zona sismica alta / tolleranza strutturale / tolleranza minore rilevanza / decorso termine minore rilevanza
- `S255` tolleranza zona sismica alta / tolleranza strutturale / tolleranza priva rilevanza / decorso termine priva rilevanza

### relazione_tecnica_asseverazione / sanatoria (6)


*rilevanza sismica of works done without SCIA (art. 36-bis c.3-bis): zona bassa, zona media/alta (no rilevanza / art. 94 silenzio-assenso number+date / minore / priva rilevanza). The portal shows only the stem P434. HIDDEN BRANCH* (medium)

- `S267` intervento in assenza scia fino dieci mila / rilevanza sismica interventi / zona sismica bassa
- `S268` intervento in assenza scia fino dieci mila / rilevanza sismica interventi / zona sismica media alta / no rilevanza strutturale
- `S269` intervento in assenza scia fino dieci mila / rilevanza sismica interventi / zona sismica media alta / ha rilevanza strutturale / intervento rilevante ai sensi art 94 / silenzio assenso documentato / numero
- `S270` intervento in assenza scia fino dieci mila / rilevanza sismica interventi / zona sismica media alta / ha rilevanza strutturale / intervento rilevante ai sensi art 94 / silenzio assenso documentato / data
- `S271` intervento in assenza scia fino dieci mila / rilevanza sismica interventi / zona sismica media alta / ha rilevanza strutturale / intervento minore rilevanza / decorso termini controllo regionale
- `S272` intervento in assenza scia fino dieci mila / rilevanza sismica interventi / zona sismica media alta / ha rilevanza strutturale / intervento privo rilevanza / decorso termini controllo regionale

### relazione_tecnica_asseverazione / strumentazione_urbanistica (7)


*'specificare' for piano di recupero / PIP / PEEP: the portal has only zona and art.* (high)

- `S286` piano recupero / specificare
- `S289` pip / specificare
- `S292` peep / specificare

*convenzione urbanistica (specificare, zona, art.): the portal has no such instrument* (high)

- `S295` convenzione / specificare
- `S296` convenzione / zona
- `S297` convenzione / art

*'altro' strumento urbanistico: specificare: the portal's ALTRO has zona and art. only* (high)

- `S298` altro / specificare

### relazione_tecnica_asseverazione / sicurezza_impianti (1)


*free text for 'altre tipologie di impianti' (specifica): P483 is the checkbox, no text box showed* (medium)

- `S315` comporta impianti / altro / specifica

### relazione_tecnica_asseverazione / materiali_risulta (3)


*ids of the VIA/AIA provvedimento (codice amministrazione, AOO, registro): the portal asks protocol, date and issuer only* (high)

- `S340` comporta produzione / vol sup 6000 / estremi provvedimento / codice amministrazione
- `S341` comporta produzione / vol sup 6000 / estremi provvedimento / codice aoo
- `S342` comporta produzione / vol sup 6000 / estremi provvedimento / codice registro

### relazione_tecnica_asseverazione / prevenzione_incendi (4)


*ids of the VVF parere (codice amministrazione, AOO, registro, comune): portal asks protocol and date only* (high)

- `S352` variante progetto / parere vigili del fuoco / codice amministrazione
- `S353` variante progetto / parere vigili del fuoco / codice aoo
- `S354` variante progetto / parere vigili del fuoco / codice registro
- `S355` variante progetto / parere vigili del fuoco / comune rilascio

### relazione_tecnica_asseverazione / amianto (1)


*amianto: piano di lavoro 'to be presented before the start of works' alternative; the portal shows only 'in allegato' (P532)* (medium)

- `S357` interessano / piano di lavoro prima inizio lavori

### relazione_tecnica_asseverazione / conformita_sanitaria (7)


*art. 24 c.5-bis (reduced heights/areas): requisito di adattabilita and recupero edilizio sub-options; the portal shows only the 'progetto di ristrutturazione' box. HIDDEN BRANCH* (medium)

- `S359` conforme art 24 / altezza minima interna / requisito adattabilita
- `S360` conforme art 24 / altezza minima interna / recupero edilizio
- `S362` conforme art 24 / alloggio mono stanza una persona / requisito adattabilita
- `S363` conforme art 24 / alloggio mono stanza una persona / recupero edilizio

*monostanza for one person: ristrutturazione sub-option (the portal shows it for height and for two persons only)* (medium)

- `S364` conforme art 24 / alloggio mono stanza una persona / ristrutturazione norme igenico sanitarie

*art. 24 c.5-bis (reduced heights/areas): requisito di adattabilita and recupero edilizio sub-options; the portal shows only the 'progetto di ristrutturazione' box. HIDDEN BRANCH* (medium)

- `S365` conforme art 24 / alloggio mono stanza due persona / requisito adattabilita
- `S366` conforme art 24 / alloggio mono stanza due persona / recupero edilizio

### relazione_tecnica_asseverazione / intervento_zona_sismica (4)


*ids of the seismic esecutivo project (codice amministrazione, AOO, registro, comune): portal asks protocol and date only* (high)

- `S373` variante sostanziale / progetto esecutivo / codice amministrazione
- `S374` variante sostanziale / progetto esecutivo / codice aoo
- `S375` variante sostanziale / progetto esecutivo / codice registro
- `S376` variante sostanziale / progetto esecutivo / comune rilascio

### relazione_tecnica_asseverazione / tutela_ecologica (1)


*fascia di rispetto dei pozzi: the portal lists depuratori and 'Altro' only* (high)

- `S392` fascia rispetto pozzi

## Matches worth a second look

### Elsewhere (15)

- `S025` scheda anagrafica / schedaTitolare / contatti / PEC -> P022 (medium). one portal box 'eMail/PEC' for the schema's PEC and email
- `S026` scheda anagrafica / schedaTitolare / contatti / email -> P022 (medium). one portal box 'eMail/PEC' for the schema's PEC and email
- `S027` scheda anagrafica / schedaTitolare / contatti / telefono -> P023 (medium). one box 'Telefono fisso/cellulare' for the schema's telefono and cellulare
- `S028` scheda anagrafica / schedaTitolare / contatti / cellulare -> P023 (medium). one box 'Telefono fisso/cellulare' for the schema's telefono and cellulare
- `S050` scheda anagrafica / schedaDitta / contatti / telefono -> P036 (medium). one box 'Telefono fisso/Cellulare'
- `S051` scheda anagrafica / schedaDitta / contatti / cellulare -> P036 (medium). one box 'Telefono fisso/Cellulare'
- `S053` scheda anagrafica / schedaDitta / domicilioElettronicoComunicazioni -> P053 (medium). schema keeps the domicilio elettronico only for a ditta; the portal asks the PEC for every applicant (same as the CILA)
- `S077` scheda anagrafica / schedaDelegato / residente / toponimo / indirizzo -> P657 (medium). 'Indirizzo' is one text for street + civico, no toponimo select
- `S078` scheda anagrafica / schedaDelegato / residente / civico -> P657 (medium). street and civico in the one 'Indirizzo' box
- `S081` scheda anagrafica / schedaDelegato / contatti / email -> P660 (medium). one box 'eMail PEC' for the schema's PEC and email
- `S083` scheda anagrafica / schedaDelegato / contatti / cellulare -> P658 (medium). one box 'Tel' for telefono and cellulare
- `S085` dichiarazioni / titolo possesso / titolo -> P074, P077, P039, P040 (medium). title (proprietario ... altro + specificare) is asked in quadro a), and again as 'In qualita di' + 'specificare' in the Scheda anagrafica (P039, P040); schema has it once
- `S112` dichiarazioni / qualificazione intervento / mutamento destinazione uso intero immobile / con opere -> P108 (low). portal has one radio for the whole-building change of use (art. 23-ter); schema splits it into with / without works
- `S113` dichiarazioni / qualificazione intervento / mutamento destinazione uso intero immobile / senza opere -> P108 (low). same radio as S112
- `S148` dichiarazioni / localizzazione intervento / immobile / riferimentiCatastali / datiCatastali / info catastali / sezione -> P070, P073 (medium). schema has one 'sezione'; the portal asks sezione amministrativa (P069, portal-only), urbana (P070) and censuaria (P073)

### Low confidence (11)

- `S095` dichiarazioni / qualificazione intervento / manutenzione restauro / no mutamento -> none: restauro sub-options other than 'intero immobile': only P113 was seen under restauro; the 'non comporta / singola unita' boxes (P109-P111 exist under manutenzione straordinaria) may be shared DOM or really absent
- `S096` dichiarazioni / qualificazione intervento / manutenzione restauro / mutamento categoria singola unita -> none: restauro sub-options other than 'intero immobile': only P113 was seen under restauro; the 'non comporta / singola unita' boxes (P109-P111 exist under manutenzione straordinaria) may be shared DOM or really absent
- `S097` dichiarazioni / qualificazione intervento / manutenzione restauro / mutamento tra categorie singola unita -> none: restauro sub-options other than 'intero immobile': only P113 was seen under restauro; the 'non comporta / singola unita' boxes (P109-P111 exist under manutenzione straordinaria) may be shared DOM or really absent
- `S099` dichiarazioni / qualificazione intervento / manutenzione ristrutturazione / no mutamento -> none: ristrutturazione sub-options other than 'intero immobile': see S095
- `S100` dichiarazioni / qualificazione intervento / manutenzione ristrutturazione / mutamento categoria singola unita -> none: ristrutturazione sub-options other than 'intero immobile': see S095
- `S101` dichiarazioni / qualificazione intervento / manutenzione ristrutturazione / mutamento tra categorie singola unita -> none: ristrutturazione sub-options other than 'intero immobile': see S095
- `S112` dichiarazioni / qualificazione intervento / mutamento destinazione uso intero immobile / con opere -> P108: portal has one radio for the whole-building change of use (art. 23-ter); schema splits it into with / without works
- `S113` dichiarazioni / qualificazione intervento / mutamento destinazione uso intero immobile / senza opere -> P108: same radio as S112
- `S265` relazione tecnica asseverazione / sanatoria / intervento in assenza scia fino dieci mila / ai fini della sanatoria / no interventi -> P433: portal lists only the stem 'ai fini della sanatoria, la presente SCIA:' as one radio; the two options (no interventi / propone interventi) did not show as separate boxes
- `S266` relazione tecnica asseverazione / sanatoria / intervento in assenza scia fino dieci mila / ai fini della sanatoria / propone interventi -> P433: see S265
- `S343` relazione tecnica asseverazione / materiali risulta / comporta produzione / vol sup 6000 / estremi provvedimento / comune rilascio -> P514: 'rilasciato da' (issuing body) taken for the schema's comune_rilascio

## Portal-only boxes (38), by portal section

A box is portal-only when it matches no leaf of the 403, none of the supplement (A/X) and no schema group.

### Scheda anagrafica (3)

- `P008` Sesso: sesso: the schema leaves it out (the codice fiscale holds it)
- `P014` Se cittadino non UE: 'Se cittadino non UE' checkbox: a gate; the schema just has the optional documentoSoggiorno block
- `P027` Codice Fiscale: codice fiscale of the ditta: schedaDitta has the P.IVA only

### Oggetto della pratica (1)

- `P048` 300 Caratteri restanti: 'Oggetto della pratica': the portal's own 300-character description

### DOMICILIO DIGITALE (4)

- `P049` il seguente domicilio digitale inserito in INAD (art.6 -quater, D.lgs lgs. n. 82/2005):: domicilio digitale INAD / INI-PEC (CAD art. 6-bis, 6-quater): newer than the schema (same as the CILA)
- `P050` il seguente domicilio digitale inserito in INI-PEC (art. 6-bis, D.lgs lgs. n. 82/2005) :: domicilio digitale INAD / INI-PEC (CAD art. 6-bis, 6-quater): newer than the schema (same as the CILA)
- `P051` il seguente domicilio digitale inserito in INAD (art.6 -quater, D.lgs lgs. n. 82/2005):: domicilio digitale INAD / INI-PEC (CAD art. 6-bis, 6-quater): newer than the schema (same as the CILA)
- `P052` il seguente domicilio digitale inserito in INI-PEC (art. 6-bis, D.lgs lgs. n. 82/2005) :: domicilio digitale INAD / INI-PEC (CAD art. 6-bis, 6-quater): newer than the schema (same as the CILA)

### Localizzazione dell'intervento (1)

- `P056` Frazione: frazione of the intervento's address: no field in the schema

### Dati catastali (3)

- `P069` sezione Amministrativa (Fabbricati): sezione amministrativa (fabbricati): the schema has one 'sezione'
- `P071` classe: classe / categoria catastale: not in the schema (same as the CILA)
- `P072` categoria: classe / categoria catastale: not in the schema (same as the CILA)

### a) Titolarità dell'intervento (1)

- `P083` Sesso: sesso (terzo titolare / tecnici): not in the schema

### h1) Tecnici incaricati (10)

- `P205` di aver incaricato, in qualità di direttore/i dei lavori, i soggetti indicati nella sezion: direttore dei lavori incaricato / individuato prima dell'inizio dei lavori: the schema has the same choice only for 'altri tecnici' (S206/S207); the direttore's equivalent is not in the 403 leaves
- `P206` che il/i direttore/i dei lavori sarà/saranno individuati prima dell'inizio dei lavori: direttore dei lavori incaricato / individuato prima dell'inizio dei lavori: the schema has the same choice only for 'altri tecnici' (S206/S207); the direttore's equivalent is not in the 403 leaves
- `P211` si: si/no under each Direttore dei lavori (question text lost in the dump; probably 'is also the progettista' or 'studio'); no schema leaf, the schema has the direttore's own person block (A085-A132, A163-A210) in a section that did not show
- `P212` no: si/no under each Direttore dei lavori (question text lost in the dump; probably 'is also the progettista' or 'studio'); no schema leaf, the schema has the direttore's own person block (A085-A132, A163-A210) in a section that did not show
- `P213` si: si/no under each Direttore dei lavori (question text lost in the dump; probably 'is also the progettista' or 'studio'); no schema leaf, the schema has the direttore's own person block (A085-A132, A163-A210) in a section that did not show
- `P214` no: si/no under each Direttore dei lavori (question text lost in the dump; probably 'is also the progettista' or 'studio'); no schema leaf, the schema has the direttore's own person block (A085-A132, A163-A210) in a section that did not show
- `P215` tecnico incaricato: 'tecnico incaricato / titolare dell'intervento o procuratore': who the progettista is; no schema leaf (same idea as the CILA's G1 radios)
- `P216` titolare dell'intervento o procuratore: 'tecnico incaricato / titolare dell'intervento o procuratore': who the progettista is; no schema leaf (same idea as the CILA's G1 radios)
- `P222` Sesso: sesso (terzo titolare / tecnici): not in the schema
- `P263` Sesso: sesso (terzo titolare / tecnici): not in the schema

### H2) Altri tecnici incaricati (5)

- `P292` Sesso: sesso (terzo titolare / tecnici): not in the schema
- `P308` si: two si/no gates in 'altri tecnici' (probably 'iscritto ad ordine' and 'alle dipendenze di ditta'; which is which is not certain); the schema has the optional blocks
- `P309` no: two si/no gates in 'altri tecnici' (probably 'iscritto ad ordine' and 'alle dipendenze di ditta'; which is which is not certain); the schema has the optional blocks
- `P310` si: two si/no gates in 'altri tecnici' (probably 'iscritto ad ordine' and 'alle dipendenze di ditta'; which is which is not certain); the schema has the optional blocks
- `P311` no: two si/no gates in 'altri tecnici' (probably 'iscritto ad ordine' and 'alle dipendenze di ditta'; which is which is not certain); the schema has the optional blocks

### Asseverazione SCIA - Dati immobile, strumentazione urbanistica, barriere architettoniche (6)

- `P440` PUC: PUC / PUA: planning instruments the schema's list does not have (PRG, piano particolareggiato, recupero, PIP, PEEP, convenzione, altro)
- `P441` PUA: PUC / PUA: planning instruments the schema's list does not have (PRG, piano particolareggiato, recupero, PIP, PEEP, convenzione, altro)
- `P456` Zona: PUC / PUA: planning instruments the schema's list does not have (PRG, piano particolareggiato, recupero, PIP, PEEP, convenzione, altro)
- `P457` Art.: PUC / PUA: planning instruments the schema's list does not have (PRG, piano particolareggiato, recupero, PIP, PEEP, convenzione, altro)
- `P458` Zona: PUC / PUA: planning instruments the schema's list does not have (PRG, piano particolareggiato, recupero, PIP, PEEP, convenzione, altro)
- `P459` Art.: PUC / PUA: planning instruments the schema's list does not have (PRG, piano particolareggiato, recupero, PIP, PEEP, convenzione, altro)

### Asseverazione SCIA - Sicurezza impianti, consumi energetici (1)

- `P500` L'intervento non ricade in alcuno dei casi sopra elencati: 'L'intervento non ricade in alcuno dei casi sopra elencati': the schema says it by leaving the elements out

### Asseverazione SCIA - Tutela Funzionale (1)

- `P604` Specificare:: a 'Specificare' text hanging under 'stradale' in the dump: probably the 'Altro' one mis-attributed

### Qualifica e dati del procuratore [only after a choice] (2)

- `P642` Qualifica del procuratore: Qualifica del procuratore (professionista incaricato, notaio, centro elaborazione, ...): the schema has no field for it (same as the CILA)
- `P645` Sesso: sesso of the procuratore: not in the schema

## What is unreliable

- Portal lines are cut at about 150 characters, so several radios and checkboxes (qualificazione, regolarita, relazione) were matched on their opening words; where two schema alternatives differ only in the tail (for example the seismic zone tolerances, S250-S255) the match rests on order.
- The dump lists 'REVEALED by' for the first parent only, and repeated labels (`si`, `no`, `Stato`, `Provincia`, `Cognome`) are ambiguous: the three si/no gates of the Stato legittimo page and the two in 'altri tecnici' could not be told apart.
- Under 'restauro' and 'ristrutturazione' the portal showed only the 'intero immobile' sub-option; the other three schema sub-options (S095-S097, S099-S101) are low-confidence `none`: either shared boxes the dump listed once, or truly absent.
- The portal dump has no DIRETTORE/I LAVORI section, though the portal mentions it: an unvisited branch, not proof of absence. The procuratore and SANATORIA sections (extra file) appear only after a choice and are labelled `[only after a choice]`; the other choice-dependent branches may still be unwalked.
- Option lists (DUG 6 against 194 values, titolo, destinazione d'uso) differ and were not compared value by value.

## Limits and what was corrected

- **The 403-leaf file was too narrow.** It left out the people-and-companies blocks
  (`allegatoSoggettiCoinvolti`, 333 leaves) and 24 `allega` checkboxes, because the filter dropped
  every path with "allegat". The real form is about 760 leaves; the supplement above covers the
  difference, counted apart.
- **A first run missed two portal sections** that only appear after a choice (the procuratore and
  the sanatoria). With them, the schema leaves with no portal box fell from 109 to 75.
- **A schema field with no portal box is a lead, not a gap.** Three kinds are mixed:
  fields the national form has and the portal never asks (region, fax, the issuing body's ids);
  branches the crawl did not go deep enough to open (the seismic sub-options, the direttori dei
  lavori's own section: the working notes already list the SCIA DL fields as not crawled); and
  matches the dump could not make (portal labels cut at about 150 characters, a Si/No pair listed
  once under its first parent, two near-identical SANATORIA blocks assigned by order).
- **Option lists were not compared value by value** (the toponimo list of 6 against 194 values, the
  titolo, the destinazione d'uso).
- **One SCIA, one day.** The portal changes; this is the form as the crawl of 2026-10-28 saw it.

