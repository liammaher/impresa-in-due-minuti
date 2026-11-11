# GEIS Portal and the Portale dei Tributi: what we know

Read on 2026-11-11 in the Claude browser pane, logged out. Nothing was logged into, filled or sent.
Source for "which portals": `docs/napoli-business-portals.md` in the older `personal-vault` checkout,
which lists GEIS (imposta di soggiorno) and the Portale dei Tributi as two of the Comune's five
business portals.

## They are one app

`cizrm.municipia.eng.it/?ente=NAPO` (GEIS) and `portaletributi.comune.napoli.it/?ente=NAPO` both
serve Municipia's `fe-cittadino v5.3.61` with the same tiles (Pagamenti, Domande Online, Documenti,
Accedi all'area personale, "Effettua una domanda online", "Calcola l'imposta IMU", "Calcolatrice
Tari") and the same `assets/env.json`. One login, one mapping effort: the two rows of the portal
list are one platform. GEIS is the imposta di soggiorno part, reached after login from a "Gestione
Imposta di Soggiorno" link in the header (it is not on the logged-out pages).

## No API to use: browser automation, as for impresainungiorno

- An Angular app of micro-frontends (module federation remotes `shared`, `smart`, `tax`, `urban`),
  forms by `ngx-formly`, Cloudflare Turnstile loaded (`ngx-turnstile`).
- Its backends (`cizrm-be-k8s.municipia.eng.it`, `ms-jdomandeonlinenapoli.jentecloud.net`,
  `argo-be-k8s.municipia.eng.it`) serve the front end; the user-data calls sit behind the
  login's token. No published developer API was found. Calling the backend directly would
  skip the person's login and trip the bot check: not an option.
- Public calls seen: CMS pages (`/cms/pagine/chiavi/...`), the payment token
  (`/pargopa/pagamenti/public/getToken`), and the forms catalogue
  (`.../public/api/nuovaPratica/listaModelli`, `dettaglioModello`).

## Login: the person's step

"Accedi all'area personale" goes to the Comune's POTESs sign-in (`login-potess.comune.napoli.it`,
WSO2), brokered by Keycloak (`muniiam.spid.municipia.eng.it`, realm `napoli`), with three tabs:
SPID, TS-CNS, CIE. Same rule as impresainungiorno: the person logs in, we never do.

## What the logged-out pages hold

- Domande Online > "Procedimenti Tributi Comune di Napoli" > one form, **Nuovo gestore struttura**
  (code `GESTORE`, area `NAPO`). Choosing it says the form needs the personal area to be sent.
- `dettaglioModello?codArea=NAPO&codModello=GESTORE` answers `autenticato: true`, `firmato: false`,
  `sezioni: []`. The form's sections are not public, so **its fields can't be crawled without a
  session**.
- A notice says existing gestori were migrated automatically to GEIS, so no new registration is
  needed for them; this form is for new gestori.

## The gate, and what to do next

The north-star's gate is "can the wizard be walked without submitting?" Not answered yet: it needs a
session.

1. The person logs in (SPID/CIE/CNS) in the pane, with a real gestore account if there is one.
2. Open "Gestione Imposta di Soggiorno": is there a draft or save step on the quarterly declaration?
   What does it ask (nights, exempt nights, rates by structure) and how does the payment
   (pagoPA, PartenoPay) start?
3. If yes: crawl it like impresainungiorno (a `crawl.js` equivalent over `formly` fields, then a
   dictionary by section). If no, it waits for reports from users who file.
4. Check whether "Nuovo gestore struttura" has a draft, and what it asks, once logged in.

Not checked: the Documenti and Pagamenti tabs behind login, the IMU and TARI calculators (public,
not a filing), and the CUIT portal.

## Is there anything to automate? (assessment, 2026-11-11)

From the library's procedure `napoli/comune/imposta-di-soggiorno-gestori` (checked against the GEIS
manual and FAQ) and two web searches, **not** from the logged-in portal. Time figures are estimates to
validate with a real gestore.

**The job.** Per structure, every quarter: a "Comunicazione periodica" in GEIS, then the tax by pagoPA,
by 15 Jan / Apr / Jul / Oct, even with nothing to pay. Yearly: the Ministry's declaration on the
Agenzia delle Entrate portal by 30 June. Once: "Nuovo gestore struttura". Disputed: whether the
Modello 21 is still due by 30 January. A commercial guide says Naples is bimonthly; the library cites
the Comune and DCC 12/2020 for quarterly. Confirm on the first logged-in run.

| Step | Manual | With a mapped Claude |
|---|---|---|
| Deadline | memory or calendar | tracked in the vault, reminder |
| Work out the figures (per month: guests, nights, 14-night cap, exempt categories, convenzionate platforms vs direct) | spreadsheet from booking exports; the biggest chunk | Claude proposes the figures from the exports, with sources; one summary to confirm |
| Login (SPID/CIE/CNS) | person | person |
| Enter in GEIS, per structure and month | by hand | filled, read back, left as a draft |
| Send, download the receipt | person | person sends; receipt filed |
| pagoPA notice and payment | person | person pays |
| Annual declaration (AdE portal, other login) | person or accountant | could be prefilled from the four quarters; out of scope for now |

Estimate: about 45–90 min per structure per quarter by hand, mostly the figures; about 10–15 min mapped.

**Where the value is.**
- The figures, not the typing. Costly errors: the 14-night cap per guest; platforms convenzionate
  with the Comune (Airbnb, Boundless Housing, Di Morra, Domus Extra, Mister B&B, MyBnB) collect and
  remit themselves and go on their own line, while Booking.com is not on that list (library:
  unverified); the rate rose on 1 May 2026, mid-Q2 (the Comune's form says to ask the office).
- Errors are expensive: after the deadline a correction needs the office's approval ("Riporta in
  Bozza"), and the penalties for an omitted or unfaithful declaration are 100–200% of the tax due
  until 2026, with a new regime from 2027 (library: don't calculate them yourself).
- The library says GEIS has "salvare e inviare" and "Riporta in Bozza", so a draft state probably
  exists, which would pass the north-star gate. Unverified on the live portal.
- Recurring and rote, unlike impresainungiorno's one-off pratiche.

**Who it is worth it for.** A single-structure host: modest, roughly 3–5 hours a year. Operators with
many structures and property managers: large, since the work multiplies per structure and quarter.
The library says GEIS can link a delegate (a collaborator or the commercialista), so a manager could
file for clients with only their own login. A search result citing a Comune document gives 10,361
extra-hotel structures registered at 28 Nov 2025; trade bodies say about 7,000 operate (source not
opened). That is roughly 28,000 or more quarterly declarations a year.

**Caveats.**
- Automating only the GEIS form, with no intake of booking data, would be underwhelming; both halves
  are needed.
- The run never sends or pays: the person does. The riepilogo and one-yes pattern fits.
- "Nuovo gestore struttura" is long with attachments but runs once per structure: map it after the
  quarterly filing.
- The next real run is Q4 2026, due 2027-01-15.

**To verify logged in.** Whether the Comunicazione periodica has a draft state; how the monthly and
per-category rows look; whether the periods are quarterly; how a delegate logs in.

## The two flows, one quarter (2026-11-11)

What goes in is **not revenue or costs**: the tax is per guest per night. The declaration needs
stay-level data: who stayed in which structure, which nights, how they booked (a platform convenzionata
collects itself; Booking and direct stays are collected by the host) and whether the guest was
exempt. Inferred from the library's procedure; no real export or logged-in form has been seen.

### Before: a host with 3 structures, Airbnb, Booking and direct stays

1. All quarter: collect the tax at check-out, give a receipt, gather exemption papers (the Comune's
   modules A–J).
2. After quarter-end: download a reservations export from each platform; add direct stays from a
   notebook, WhatsApp or spreadsheet.
3. Reconcile in a spreadsheet, per structure and month: guests subject to tax and nights (14
   consecutive per guest at most), exempt guests by category, platform-collected versus self-collected
   nights, the rate (it changed on 1 May 2026).
4. Log in (SPID), open Comunicazione periodica, pick structure and quarter.
5. Type the figures per month and category, plus the platform row. Save, send, download the receipt.
6. Repeat for each structure.
7. Generate the pagoPA notice and pay; wait 24–72 h; check for anomaly notices.
8. Keep receipts 5 years. In June, redo the quarters for the Agenzia delle Entrate declaration.

The pain is steps 2–3 and remembering a zero-return quarter.

### After: Claude has mapped GEIS

One-time setup: the vault holds the gestore's identity and each structure (address, category,
CUSR/CIN); the person points Claude at the folder where the exports land; a delegate is linked if one
files.

Each quarter:
1. Claude reminds ahead of the deadline ("Q4 closes 31 Dec, due 15 Jan, drop your exports").
2. The person drops the files: platform exports, plus whatever holds direct stays and exemptions.
   This is the only upload.
3. A script, not the model, reads them and computes per-structure figures. Claude sees only totals
   and flags, never guest names (the pattern of `claude/skills/pratica/intake/`; no such intake for
   booking data exists yet).
4. Claude asks only what the files can't say: guests under 14, whether Booking stays were collected,
   a structure with no stays (zero declaration?).
5. One summary and one "sì": guests, nights, tax due, exempt guests by category, the platform row,
   the change against last quarter, the rule checks (nights at least guests, the 1 May rate split).
6. The person logs in (SPID) in the pane.
7. The runner fills each structure's declaration, reads it back and stops at the draft.
8. The person presses Send. Claude never sends or pays.
9. The receipt is filed. Claude gets the person to the pagoPA notice, the person pays, Claude later
   checks the payment registered.
10. In June, the annual declaration is prefilled from the four stored quarters; the Agenzia delle
    Entrate login is the person's.

| | Before | After |
|---|---|---|
| Gather and reconcile figures | person | script and Claude; person confirms |
| Deadlines and zero returns | person | Claude |
| Login | person | person |
| Typing into GEIS | person, per structure | Claude |
| Send and pay | person | person |
| Receipts, annual declaration | person | Claude files and prefills |

Estimate: about 60 min per structure per quarter by hand, about 10–15 min after.

### What could break this

- Exports may lack what the tax needs. Platform exports typically give guest counts, not ages or
  residence, so some exemptions stay questions to the host.
- Direct and cash stays often live in a notebook or WhatsApp; for those hosts the value shrinks to
  reminders and form-filling. It is largest for hosts on a channel manager or PMS.
- The intake does not exist: today's reads architects' documents.
- A manager filing for clients needs only their own SPID, but how a delegate logs in is unconfirmed.

Cheapest next test: ask one real gestore for an anonymised quarter of exports. It shows whether this
is a data-ingestion product with a form-filler on the end, or only a form-filler.

## Research on the data a host holds (2026-11-11)

Primary sources read: the GEIS manager manual and FAQ (the manual's cover says v0.6, 7 Oct 2025; the
library cites it as V.0.7, 23 Jan 2026, so a newer version may exist), the Comune's guest-record layout
spreadsheet, the Questura's Alloggiati Web manual and file format, the Comune's accordi, modulistica,
modalità and avviso pages, the Regione Campania's Sinfonia Turismo SMART page. Platform and vendor pages
are noted as official or third-party. The PDFs were extracted locally with `pdftotext`; nothing was
logged into.

### What GEIS asks for (official manual and FAQ)

- The quarterly declaration is **aggregate only**: per structure and quarter, per month, the number of
  guests and nights by tariff type (taxable, the "AIRBNB" row, each exemption). GEIS computes the amount
  and checks that nights are at least guests. No per-guest field on that screen.
- **A draft state exists**: saving makes a "Bozza", editable (Modifica, Elimina); sending issues a
  protocol number and a receipt PDF. So the form can be mapped without submitting. The period is a
  quarter ("trimestre di riferimento"); the "bimestrale" in some guides is wrong.
- Corrections: before the deadline "Comun. Sost./Ripresenta"; after it, the online request "Riporta in
  Bozza Dichiarazione", approved by an operator.
- Payment: pagoPA from Elenco Dichiarazioni. The list also shows anomalies (missing payment, unpaid
  notices, missing CUSR or CIN).
- Delegates: added per structure on a "Delegati" page; how a delegate logs in is not described.
- Login: SPID or CIE (manual); the Comune's page adds TS-CNS.

### GEIS has a guest-level import (unexplained)

The manual's menu lists **Tracciato Ospiti > Import Tracciato Ospiti** and never describes it. The
Comune's Modulistica page publishes a "Tracciato record per software house", the spreadsheet
`Tracciati_Record_ImportazioneTBPRES01_Napoli.xlsx`: one **check-out record per guest**, with room,
arrival and departure dates and times, a paid flag, an exemption code, a tax-cap code (14 nights), name,
and optional tax code, birth date, residence, document and email. Its exemption table includes residents
of Napoli and staff. Oddities to verify: it lists minors up to 18 as exempt (the regulation says 14) and
has codes for teaching staff and for guests paying at 60/90/120 days, which are not in the regulation
list we hold. **Unknown: what the import does and whether it feeds the quarterly declaration.** The top
question for a logged-in session.

### What the host holds

| Needed | Where it lives | Can the host get it? |
|---|---|---|
| Guests, nights, dates | PMS or channel manager; Airbnb earnings CSV; Booking.com XLS | Partly. Airbnb's column list is not official and guest counts were not found there; Booking's columns are undocumented. Hospitable's export has adults, children, infants, nights and platform. |
| Birth dates (minors) | Alloggiati Web record | Fields confirmed, but history cannot be pulled back (below) |
| Residents of Napoli | Not in Alloggiati | Only from the host's PMS or knowledge |
| Other exemptions | Host's papers (modules A–J) | Scans, not data |
| Who collected the tax | Airbnb earnings CSV; Booking.com API tax flag; direct stays are the host's | Mostly |

**Alloggiati Web** (official file format and manual): each record has guest type, arrival date, days of
stay (maximum 30), name, sex, birth date and place, state of birth, citizenship, and document details for
singles and group heads. **No residence, no departure date, no exemption data.** Due within 24 hours of
arrival. **No history export**: "Analisi" shows only today's submissions, receipts are PDFs of daily
counts for the last 30 days. A web service exists for software. The host's real register has to live in
their own software.

**Airbnb**: collects and remits tourist tax only in comuni registered with it, for stays up to 30 days;
its Italy page does not name Napoli. The Comune's accordi page lists AIRBNB among six intermediaries
(agreement of one year; it does not say what hosts must still declare). The "All reservations" CSV was
reportedly removed: host forum posts only, nothing official. **Booking.com**: no official statement on
collecting tax in Italy; its API marks city tax as collected by the property or by Booking.

**Regione Campania, Sinfonia Turismo SMART**: hosts report arrivals and nights (and tariffs); software
can upload by web API; login by SPID/CIE/CNS for the titolare or a delegate. Frequency, origin, ages and
export are not stated; whether short lets must report is not stated. A possible cross-check on nights.

### Existing tools

No tool found that fills or submits the GEIS declaration (medium confidence: absence of evidence from
vendor pages). QUICKin has a Napoli-specific page: it calculates the tax, gives a CSV summary and a
reminder; the host still submits. Chekin and NowCheckin calculate and prepare data. Hostaway says it does
not file. Smoobu has a paid collection add-on with no GEIS link.

### What this changes

1. The figures problem is a data problem. Hosts using a check-in tool already hold stay-level data; hosts
   on platform exports or a notebook do not.
2. Build stay-level records first: one record per guest-stay. They give the quarterly totals, and if the
   GEIS import works they could be the upload file.
3. Exemptions and residence stay questions to the host unless their PMS captures them.
4. The draft state is confirmed, so mapping does not depend on filing.

### Still unknown

What "Import Tracciato Ospiti" does and whether ordinary hosts can use it; Airbnb's and Booking's actual
export columns; Booking.com's tax role in Napoli; how a delegate logs in; penalty amounts (sources
conflict); the 10,361-structures figure used earlier in this document's assessment, which was not traced
to a source.

## Under the hood: how GEIS is built (2026-11-11)

Read from the manual's screenshots and from the public JavaScript the browser already loads, logged in as
an ordinary citizen (not a gestore). No backend API was called and the privacy consent was not accepted.

### Two apps, one login

1. **Portale Multiservizi** (`cizrm.municipia.eng.it`, "fe-cittadino v5.3.61"; the same app answers on
   `portaletributi.comune.napoli.it`): Angular, split into modules (shared, smart, tax, urban). The
   "Domande Online" forms, including Nuovo gestore struttura, are generated by Formly with stable field
   codes (for example `ATT_STRUTCLASS`, `SOG_INTESTATARIO-1_CODICEFISCALE`). Behind Cloudflare and
   Turnstile; SSO through the Comune's login and a Keycloak broker. Its config names the second app
   (`urlPortaleGeis`).
2. **GEIS Portal** (`geis-web-portal.municipia.eng.it`): an older Angular app with a JSON backend under
   `/rest/...`, where gestori work. The session carries over from the first app; it stops at a privacy
   consent page.

The GEIS menu entries require the roles `GESTORE_STRUTTURA` or `DELEGATO_STRUTTURA`, granted by the
Comune after it approves "Nuovo gestore struttura". An ordinary account sees only Pagamenti, Domande
Online and Documenti.

### What the code shows without a gestore login

- Screens: Gestore, Delegato, Comunicazione periodica, Versamento, Elenco Dichiarazioni, Riepilogo
  PagoPA, Conto Gestione, Strutture, **Tracciato Ospiti**, Elenco News.
- The declaration form (manual Figs. 8–9 and the code's labels): a structure picker and a quarter picker;
  a declaration date, notes and a "Locazione breve art.4 d.l. 50/2017" flag; one block per month with
  rows of tariff type, guests, nights, per-night amount and total (the example shows two "Soggetti ad
  imposta" rows and an "AIRBNB" row at 0.00). Buttons: Salva, Nuova, Invia, Caricamento automatico.
- Payment and corrections: Ravvedimento calculation, "Crea nuovo avviso di pagamento", the notice list,
  print and pay, "Comun. Sost./Ripresenta", Mail notifica.
- Backend calls, by name only (authenticated, not a public API; not called): `/rest/dichPeriodiche/`
  (`insertDich`, `inviaDich`, `dettaglioDich`, `annullaDich`, `eliminaDich`), `/rest/cruscotto/`
  (`generaPagoPa`, `stampaDich`, `sostitutiva`), `/rest/versamenti/`, `/rest/contoGestione/`,
  `/rest/struttPortal/`, `/rest/gestori/`, `/rest/delegati/`.

### The guest-file import creates the declaration

The **Tracciato Ospiti** page is real. The user picks a text file in the Comune's TBPRES01 layout; GEIS
parses it in the browser; a confirm box says that pressing the button creates a new declaration from the
imported document. The rules in the code, for taxable guests (exemption code 01, tax-cap code 01):

- each guest counts once, in the month of their **arrival date**;
- nights are departure minus first night, **capped at 14**;
- the file's period must match the declaration's, or it stops with "periodo selezionato non conforme";
- other counters exist, assumed to cover the exemption codes (not read in full).

Unknown: whether the result is an editable draft before sending; how a stay across two months is meant to
count (the code attributes it all to the arrival month).

### Two ways in

| Path | What Claude does | Needs |
|---|---|---|
| A. Type the totals | Fills the monthly rows | Only totals, no guest names |
| B. Upload the guest file | Builds the file; GEIS counts and applies the 14-night cap | Guest-level data with names, and a file picker in the pane |

B makes GEIS do the arithmetic but puts guest names in a file for the Comune, and it is untested. A
logged-in gestore session would settle: the draft state in practice, path B's behaviour, the exact rows
for a structure, and delegate login. The new-registration form is separately mappable from its Formly
field codes.

## The catalogue and how to keep it current (2026-11-11)

`claude/skills/pratica/portal/municipia/` holds a program that reads both apps' public files (no login, no
backend call) into `catalogue/napoli/`: the citizen portal (57 routes, 11 roles, 98 files; one build under
`cizrm.municipia.eng.it` and `portaletributi.comune.napoli.it`) and the GEIS app (26 routes, 7 files, 41
backend paths named in its code, 11 screens including Tracciato Ospiti), plus the Domande Online model list
and the registration form's 56 fields. `extract.py check` compares the files served now with the catalogue's
and exits 1 when a build changed. Its README lists what is not mapped yet: the gestore screens' live
behaviour (needs a gestore session), the three NAPG forms, the Persona giuridica set, and each portal's
terms on automation.
