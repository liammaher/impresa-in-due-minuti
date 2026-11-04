#!/usr/bin/env python3
"""Fill a portal pratica from the vault in a real browser, then hand it to the person.

  run.py preflight --steps STEPS.yaml [--answers A.json] VAULT [--made-up]
      Before anything opens: prints JSON with why this case isn't supported (the steps
      file's `supports:`, and its `rules:` table, which says whether the case is this pratica
      at all; a refusal behind a known portal defect also under `defects`, with the person's
      choices, defects.yaml), the answers it proposes for the person to confirm (an ask's
      `propose:`; one reading another answer of the same message comes with it, `assumes` or per
      answer `cases` and `otherwise`, so one message is enough; what a proposal holds back, asked
      only if it is changed, under `if_changed`), the questions still to ask (its `asks:`, branch questions first), the
      vault fields missing or expired, the files to attach (each within the portal's 9.77 MB,
      of a type its slot takes, and as its sportello takes them: Napoli's SUE refuses a file
      not in PDF/A, unsigned or oddly named, FILING) and whether they fit the pane, and the
      person's own steps; `message` is the questions, proposals and missing details as the one
      Italian message to send. Exits 0 when `ready`, 3 when not. --made-up (a rehearsal's made-up
      files, never sent) reports the sportello's refusals as warnings instead.

  run.py scope --steps STEPS.yaml
      Prints the `pvault get` patterns for every vault field the steps read (a role's as
      everyone's category, and every person's ruolo): one approval, nothing else read.

  run.py plan --steps STEPS.yaml --answers A.json
              (--values - [--values FILE] | --server S.json --token NAME | --vault-dir DIR [--keychain SERVICE])
      Resolves every value the steps need and prints what goes where. No browser.

  run.py page --steps STEPS.yaml --answers A.json VAULT --out DIR [--plain]
      Writes the scripts for the Claude browser pane, each run with one call on the
      portal's page: check.js says which of runner.js (inpage.js) and steps.js (the steps,
      no personal data) the pane's storage doesn't already hold byte for byte; run.js starts
      a run with the person's values; install.js is runner.js and steps.js together.
      Claude writes every byte of a call, so run.js would put the values through the
      conversation. It doesn't: run.js carries them sealed under a code that a window on
      the person's screen shows (not printed, not in a file) and that they type into a box
      the runner opens on the portal's page. --plain carries them in the clear instead (made-up
      data, or a person who accepts that), and is the only choice where no window can open.
      bench/rerun.py does it for many rehearsals at once. inpage.js says more.

  run.py run  --steps STEPS.yaml --answers A.json VAULT --out DIR
              [--cdp URL | --profile DIR] [--close]
      Opens the portal in a Playwright window (its own Chromium) and waits for the person
      to log in, then runs inpage.js there, as in the pane: the wizard, each section filled,
      saved and read back, then the draft loaded again and every value read once more. It
      stops before what is the person's: the declarations, the attachments the steps file
      doesn't name, the payment, signing and sending, and shows the draft, left open for
      them unless --close. Writes DIR/report.json (timings, what each section kept, and when
      it stops a `snapshot` of the page with no value in it): no value is in it, so Claude
      may read it. DIR/private/ (kept.json, held.json, shown.json, declarations.json,
      anteprima.pdf) and DIR/review.html (the page the person reviews: what's left for them,
      the steps file's `yours`, the declarations' own text, the portal's PDF preview, every
      value, and what a failed read-back wanted and found) are the person's, for Claude to
      send and never to read. There is no screenshot: a failed page holds the person's data.
      Reading the declarations opens their sections and copies their text, ticking nothing;
      the preview is the PDF the portal's "Visualizza anteprima" shows, fetched with the person's session. Neither can stop a saved draft:
      a failure is a note (`declarations_note`, `preview_note`) in the report and the page.

A run that stops says where (report.json `at`: the wizard screen, or the section and
field). `page` or `run` with --resume REPORT picks it up on the same draft, from that
section, with --fix FIX for what the page really has there; DIR/drift.json records the
fixes, and the fresh load at the end still checks every section.

What the portal makes from the pratica only once the declarations are ticked (the procura, which
the client signs: a steps field's `after_declarations`) waits for a second run: preflight, page or
run with --after-declarations reopens the draft by its name from Pratiche in bozza and attaches
those files alone; the first run's `yours` says so. It carries no other value, its files are
always picked in the page, and so `page` seals nothing and shows no code: one code a pratica. A slot that takes only signed files is filled
with the person's signed file (the portal checks each signature on upload, and the runner stops
on its refusal); with --made-up (a rehearsal) such slots are left empty.

STEPS.yaml is a portal's steps file (rehearsals/*/portal-steps.yaml). Values come from
the vault, VAULT as for plan. --values - takes what `pvault get` printed for the steps'
categories (`pvault get 'business.*' 'locale.*' '*:identity.*' ...`, piped in: one Touch ID
approval, nothing on disk); a second --values FILE (intake.py's private values.json, read off
the job's documents) fills what the vault doesn't hold. --server is the pilot vault's JSON ("url" and "tokens") and a
token's name in it; --vault-dir is a real vault, read over its socket with the token in
$VAULT_TOKEN or the Keychain (--keychain, default fill.py's), as fill.py reads it. The
token reads the categories the steps name. Asks come from A.json. --cdp attaches
to a Chrome the person started with --remote-debugging-port, for a site that refuses a
browser Playwright launched; otherwise Chromium starts with its own profile (--profile,
default ~/.cache/pratica-portal/profile), never the person's own, so a login there
lasts as long as the portal keeps it.

A `kind: file` field attaches a file: its value is a path (usually an {{ask.x}}), and
its bytes travel in run.js. With `page` they pass through the conversation, so all of a
run's files together may be at most 256 KB (PAGE_FILES_LIMIT); `run` evaluates run.js
itself and takes any size. Over that, `page` carries each file's name, size and sha256
instead (`picked`): before the run starts the runner shows a box on the portal's page where
the person chooses them, and keeps only those whose bytes are the ones pre-flight read, so
they go from the person's disk to the portal and nowhere else.

No model is called during a run. A step that doesn't match what the steps file expects
(a label, a lookup with no single answer, a value the portal didn't keep) stops the run:
that is the point where Claude looks at the page and fixes the steps file.
"""

import argparse
import base64
import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import shlex
import unicodedata
import shutil
import subprocess
import sys
import time
from datetime import date
from pathlib import Path


sys.path[:0] = [str(Path(__file__).resolve().parent.parent / "fill"), str(Path(__file__).resolve().parent.parent),
                str(Path(__file__).resolve().parent)]
sys.dont_write_bytecode = True  # no __pycache__ in the skill's folder
import fill  # noqa: E402  (its vault client: the pilot over TCP, a real vault over its socket)
import rules  # noqa: E402  (the library's rules tables: which pratica a case needs)
import review  # noqa: E402  (the page the person reviews)

# Never clicked, whatever a steps file says: these are the person's taps.
FORBIDDEN = re.compile(r"pago\s*pa|\binvia\b|\bpaga\b|procedi con il pagamento|firma", re.I)
# Never opened: the dichiarante's own statements.
DECLARATIONS = re.compile(
    r"consapevolezza|informativa sulla privacy|requisiti di o|altre dichiarazioni|"
    r"dichiarazioni ai sensi dell'art\. 6|rispetto sulle tasse|art\. ?75", re.I)

# A codice fiscale as it sits in a firma digitale certificate's subject ("TINIT-RSSMRA80A01H501U").
CF = re.compile(r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b")
# Choices the form takes in the person's name and the review page lists apart from the long table:
# how the imposta di bollo is settled (pagoPA, or marche whose serial numbers go in the form).
DECIDED = re.compile(r"imposta di bollo", re.I)

# The Scheda anagrafica's "Toponimo (DUG)" list (crawled: these and ALTRO). Any other street type
# is ALTRO, and the portal then requires it in "Dettaglio DUG": a list of 190 that is the national
# toponimo list (InfoCamere's `specie`, 194 in schema/mod_acconciatori_estetisti_apertura_v1.0.7-fields.json:
# one the portal lacks stops the run on that box). Naples' own CUPA, GRADINI, FONDACO, RAMPE and
# SUPPORTICO are in neither: pre-flight names them instead of guessing a type.
DUG = {"VIA", "VIALE", "PIAZZA", "CORSO", "LARGO"}
DUG_DETTAGLIO = frozenset((
    "ACCESSO|ACCORCIATOIA|AIA|ANDRONE|ARCO|ARZERE|ATRIO|AUTOSTRADA|BAGLIO|BANCHINA|BASTIONE|"
    "BASTIONI|BELVEDERE|BROLO|CALATA|CALLE|CAPO DI PIAZZA|CARRAIA|CARRARA|CARRARETTO|CARRARO|"
    "CARRARONE|CASA SPARSA|CAVALCAFERROVIA|CAVALCAVIA|CHIASSO|CHIOSTRA|CHIOSTRO|CIRCONVALLAZIONE|"
    "CLAUSTRO|CLIVO|CONTRADELLA|CORSO|CORTE|CORTILE|CROSA|CROSINO|DIGA|DISCESA|DISTACCO|ERTA|"
    "FORESE|GALLERIA|GRADINATA|GRADINATE|GRANVIALE|INTERRATO|ISOLA|ISOLATO|LARGHETTO|LARGO|"
    "LITORANEA|LOGGIA|LUNGARGINE|LUNGO|LUNGOCANALE|LUNGOFIUME|LUNGOLAGO|LUNGOMARE|LUNGOMOLO|"
    "LUNGOPARCO|LUNGOPORTO|LUNGOTORRENTE|MOLO|OTTAGONO|PARCHEGGIO|PASSAGGIO|PASSEGGIATA|"
    "PASSERELLA|PASSETTO|PASSO|PASSO DI PIAZZA|PENDICE|PENDINO|PERCORSO|PERCORSO CICLABILE|"
    "PERCORSO CICLOPEDONALE|PERCORSO PEDONALE|PIAGGIA|PIAZZA|PIAZZA INFERIORE|PIAZZA SUPERIORE|"
    "PIAZZALE|PIAZZETTA|PISTA CICLABILE|POGGIO|PONTE|PONTE LONGO|PONTILE|PRATO|PROLUNGAMENTO|"
    "PUNTA|QUADRATO|RACCORDO|RAMPA|RATTO|RIO TERA'|RIVALE|RIVETTA|RONCO|RONDO'|ROTATORIA|ROTONDA|"
    "ROTTA|SACCA|SAIA|SALITA|SALITA INFERIORE|SALITA SUPERIORE|SCALEA|SCALETTO|SCALINATA|SCALO|"
    "SCESA|SCIVOLA|SENTIERO|SESTIERE|SLARGO|SORTITA|SOTOPORTEGO|SOTTOPASSO|SOVRAPPASSO|SPIANATA|"
    "SPIAZZO|STRADA|STRADA ANTICA|STRADA COMUNALE|STRADA CONSORTILE|STRADA ESTERNA|STRADA NUOVA|"
    "STRADA PANORAMICA|STRADA PODERALE|STRADA PRIVATA|STRADA PROVINCIALE|STRADA REGIONALE|"
    "STRADA STATALE|STRADA VECCHIA|STRADA VICINALE|STRADALE|STRADELLA|STRADELLO|STRADONE|"
    "SVINCOLO|TANGENZIALE|TERRAZZA|TRAVERSA|TRAVERSA A MARE|TRAVERSALE|TRONCO|TROZO|VALLONE|"
    "VARCO|VENULA|VIA|VIA ANTICA|VIA CARRARA|VIA COMUNALE|VIA ESTERNA|VIA INFERIORE|"
    "VIA NAZIONALE|VIA NUOVA|VIA PANORAMICA|VIA PRIVATA|VIA PROVINCIALE|VIA SUPERIORE|"
    "VIA VECCHIA|VIA VICINALE|VIALE|VIALETTO|VIAZZA|VIAZZOLA|VIAZZOLO|VICO|VICO CHIUSO|"
    "VICO CIECO|VICO DRITTO|VICO INFERIORE|VICO PRIVATO|VICO STRETTO|VICO SUPERIORE|VICOLETTO|"
    "VICOLO|VICOLO CHIUSO|VICOLO CIECO|VICOLO PRIVATO|VICOLOZZO|VIELLA|VIETTA|VIONE|VIOTTOLA|"
    "VIOTTOLO|VIOTTOLONE|VIUCCIOLO|VIUZZO"
).split("|"))
# run.js for the pane is one tool call's text: a receipt or a small scan, not a planimetria.
# Larger files need another route into the page (docs/north-star.md, open question 7).
REHEARSAL_DRAFT = "PROVA NON INVIARE"
PAGE_FILES_LIMIT = 256 * 1024
# What impresainungiorno takes in one slot: "Max: 9,77 MB" beside each, 10,000 KB.
SLOT_MAX_BYTES = 10_000 * 1024
FILE_TYPES = {".p7m": "application/pkcs7-mime", ".pdf": "application/pdf"}
CARICA = {"titolare": "TITOLARE", "legale_rappresentante": "LEGALE RAPPRESENTANTE"}
FORMA = {
    "ditta_individuale": "IMPRESA INDIVIDUALE",
    "srl": "SOCIETA' A RESPONSABILITA' LIMITATA",
    "srls": "SOCIETA' A RESPONSABILITA' LIMITATA SEMPLIFICATA",
    "snc": "SOCIETA' IN NOME COLLETTIVO",
    "sas": "SOCIETA' IN ACCOMANDITA SEMPLICE",
    "spa": "SOCIETA' PER AZIONI",
    "sapa": "SOCIETA' IN ACCOMANDITA PER AZIONI",
    "cooperativa": "SOCIETA' COOPERATIVA",
}
# A client company's dichiarante (asks.cliente_carica) as the Scheda anagrafica's Carica list (the
# Registro Imprese's) names it. That list and the Forma giuridica one have no condominium: its
# administrator is AMMINISTRATORE of ALTRE FORME, NON NECESSITA DI ISCRIZIONE (read 2026-11-02).
CARICA_CLIENTE = {"legale rappresentante": "LEGALE RAPPRESENTANTE", "amministratore unico": "AMMINISTRATORE UNICO",
                  "amministratore delegato": "AMMINISTRATORE DELEGATO",
                  "presidente cda": "PRESIDENTE CONSIGLIO AMMINISTRAZIONE",
                  "amministratore di condominio": "AMMINISTRATORE"}
# identity.citizenship (an adjective, "italiana") as the Scheda anagrafica's Cittadinanza list names
# the country: first the ones cases have needed, then the rest of the EU and the countries many
# people in Naples come from, in Italian as the list writes the first ones, but never read on it:
# one it words otherwise stops the run on that box. A country's own name is taken too. Anything
# else is named by pre-flight, not guessed.
CITTADINANZA = {"italiana": "ITALIA", "francese": "FRANCIA", "tedesca": "GERMANIA",
                "spagnola": "SPAGNA", "rumena": "ROMANIA", "romena": "ROMANIA",
                "polacca": "POLONIA", "britannica": "REGNO UNITO",
                "statunitense": "STATI UNITI D'AMERICA", "albanese": "ALBANIA",
                "ucraina": "UCRAINA", "marocchina": "MAROCCO", "cinese": "CINA",
                "srilankese": "SRI LANKA", "bangladese": "BANGLADESH", "filippina": "FILIPPINE",
                "senegalese": "SENEGAL", "nigeriana": "NIGERIA", "egiziana": "EGITTO",
                "tunisina": "TUNISIA", "russa": "RUSSIA", "indiana": "INDIA",
                "pakistana": "PAKISTAN", "brasiliana": "BRASILE", "peruviana": "PERÙ",
                "austriaca": "AUSTRIA", "belga": "BELGIO", "bulgara": "BULGARIA",
                "croata": "CROAZIA", "cipriota": "CIPRO", "ceca": "REPUBBLICA CECA",
                "danese": "DANIMARCA", "estone": "ESTONIA", "finlandese": "FINLANDIA",
                "greca": "GRECIA", "ungherese": "UNGHERIA", "irlandese": "IRLANDA",
                "lettone": "LETTONIA", "lituana": "LITUANIA", "lussemburghese": "LUSSEMBURGO",
                "maltese": "MALTA", "olandese": "PAESI BASSI", "portoghese": "PORTOGALLO",
                "slovacca": "SLOVACCHIA", "slovena": "SLOVENIA", "svedese": "SVEZIA",
                "norvegese": "NORVEGIA", "islandese": "ISLANDA", "svizzera": "SVIZZERA",
                "moldava": "MOLDAVIA", "georgiana": "GEORGIA", "serba": "SERBIA",
                "kosovara": "KOSOVO", "macedone": "MACEDONIA DEL NORD",
                "bosniaca": "BOSNIA-ERZEGOVINA", "montenegrina": "MONTENEGRO",
                "bielorussa": "BIELORUSSIA", "turca": "TURCHIA", "algerina": "ALGERIA",
                "libica": "LIBIA", "ghanese": "GHANA", "ivoriana": "COSTA D'AVORIO",
                "camerunese": "CAMERUN", "eritrea": "ERITREA", "etiope": "ETIOPIA",
                "somala": "SOMALIA", "maliana": "MALI", "gambiana": "GAMBIA",
                "guineana": "GUINEA", "burkinabe": "BURKINA FASO", "capoverdiana": "CAPO VERDE",
                "sudanese": "SUDAN", "nepalese": "NEPAL", "afghana": "AFGHANISTAN",
                "iraniana": "IRAN", "irachena": "IRAQ", "siriana": "SIRIA", "libanese": "LIBANO",
                "israeliana": "ISRAELE", "giapponese": "GIAPPONE", "sudcoreana": "COREA DEL SUD",
                "vietnamita": "VIETNAM", "thailandese": "THAILANDIA", "indonesiana": "INDONESIA",
                "canadese": "CANADA", "messicana": "MESSICO", "argentina": "ARGENTINA",
                "colombiana": "COLOMBIA", "venezuelana": "VENEZUELA", "ecuadoriana": "ECUADOR",
                "cubana": "CUBA", "dominicana": "REPUBBLICA DOMINICANA", "cilena": "CILE",
                "boliviana": "BOLIVIA", "uruguaiana": "URUGUAY", "paraguaiana": "PARAGUAY",
                "australiana": "AUSTRALIA", "neozelandese": "NUOVA ZELANDA"}


def _cittadinanza(v):
    v = " ".join(v.strip().lower().split())
    # A masculine adjective ("rumeno") as the feminine the list holds ("rumena").
    for k in (v, v[:-1] + "a" if v.endswith("o") else v):
        if k in CITTADINANZA:
            return CITTADINANZA[k]
    if v.upper() in CITTADINANZA.values():
        return v.upper()
    raise ValueError(f"no Cittadinanza for {v!r}: the portal's list names the country, and this one isn't mapped yet")


# A client exempt from the imposta di bollo (ask bollo_esenzione), as the SUE form's "per la
# seguente motivazione" words it. Its two art. 82 c. 5 lines are one law: an ETS in the RUNTS,
# and the article's own words, which name the cooperative sociali.
BOLLO_ESENZIONE = {
    "ets": "ai sensi dell'art.82, c.5, d.Lgs. n.117/2017 (Enti del Terzo settore iscritti nel registro unico "
           "nazionale del Terzo settore ai sensi dell'art. 4, legge 117/2017)",
    "cooperativa sociale": "ai sensi del Decreto Legislativo 03/07/2017, n. 117, art. 82 comma 5 (enti del Terzo "
                           "settore comprese le cooperative sociali ed escluse le imprese sociali costituite in forma di società)",
    "pubblica": "ai sensi del D.P.R. 26/10/1972, n. 642, allegato B, art. 16 (amministrazioni dello Stato, Regioni, "
                "Province, Comuni, loro consorzi ed associazioni, nonchè Comunità montane)",
    "contadina": "ai sensi del D.P.R. 26/10/1972, n. 642, allegato B, art. 21 (piccola proprietà contadina)",
    "sportiva": "ai sensi del D.P.R. 26/10/1972, n. 642, allegato B, art. 27-bis (federazioni sportive, enti di "
                "promozione sportiva ed associazioni e società sportive dilettantistiche senza fine di lucro riconosciuti dal CONI)",
    "onlus": "ai sensi del D.P.R. 26/10/1972, n. 642, allegato B, art. 27-bis (organizzazioni non lucrative di utilità sociale - ONLUS)",
    "partito": "ai sensi del D.P.R. 26/10/1972, n. 642, allegato B, art. 27-ter (movimenti o partiti politici "
               "limitatamente all'adempimento di obblighi derivanti da disposizioni legislative o regolamentari)",
}


def _bollo(v):
    """An answer to bollo_esenzione as check_answer and `is_` read it: case and spaces aside."""
    return " ".join(str(v).lower().split())


def _bollo_non_dovuto(v):
    """bollo_marche's default: no marche or pagoPA question for a client exempt or paying
    virtually ("false", unasked); for one who pays, render's None, so it is proposed."""
    if _bollo(v) in BOLLO_ESENZIONE or _bollo(v) == "virtuale":
        return "false"
    raise KeyError("a client who pays the bollo")


def _bollo_yours(v):
    """The person's bollo step, from {{ask.bollo_marche,ask.bollo_esenzione|bollo_yours}}."""
    marche, esenzione = _facts(v, 2)
    if _bollo(esenzione) in BOLLO_ESENZIONE:
        return "Nessuna imposta di bollo da pagare: il committente è esente, e il modulo ne indica il motivo"
    if _bollo(esenzione) == "virtuale":
        return "Nessuna marca né pagoPA per l'imposta di bollo: il committente la assolve in modo virtuale (il modulo ne riporta la dichiarazione)"
    if truthy(marche):
        return "Annulli le marche da bollo i cui numeri di serie sono nel modulo, e ne conservi gli originali"
    return "Paghi l'imposta di bollo con pagoPA, come chiede il portale"


def _carica(v):
    for role in [r.strip() for r in v.split(",")]:
        if role in CARICA:
            return CARICA[role]
    raise ValueError(f"no portal carica for ruolo {v!r}")


def _categorie(s):
    """Several units' categorie joined by "/" (a/b/c, "" for a unit with none), where a categoria
    itself may hold one (A/2): each read whole, in order."""
    out = []
    while s:
        m = re.match(r"([A-Fa-f]\s*/?\s*\d{1,2}|[^/]*)(/|$)", s)
        out.append(m[1])
        s = s[m.end():]
        if m[2] == "/" and not s:
            out.append("")
    return out


def _split_street(v):
    """A street as the Scheda anagrafica takes it: its DUG, its "Dettaglio DUG" (the street type when
    the DUG is ALTRO, "" when it isn't, None for a type neither list has) and the name after it."""
    words = v.split()
    if len(words) > 1 and words[0].upper() in DUG:
        return words[0].upper(), "", " ".join(words[1:])
    # The shortest type the street starts with ("VICO CHIUSO SAN ..." is a VICO), up to the
    # list's three words ("CAPO DI PIAZZA").
    for n in range(1, min(3, len(words) - 1) + 1):
        if " ".join(words[:n]).upper() in DUG_DETTAGLIO:
            return "ALTRO", " ".join(words[:n]).upper(), " ".join(words[n:])
    return "ALTRO", None, v


def _dug_dettaglio(v):
    d = _split_street(v)[1]
    if d is None:
        raise ValueError(f"the street {v!r} starts with no street type the portal lists (Toponimo or Dettaglio DUG)")
    return d


# The province names the portal wants for a sigla: the free-text "Iscritto all'ordine di ..." and
# a client company's "Camera di commercio di:" dropdown. All 107, in ISTAT's words in capitals; the
# dropdown has been read only at NAPOLI, so a province it words otherwise stops the run on that box.
PROVINCE = {"AG": "AGRIGENTO", "AL": "ALESSANDRIA", "AN": "ANCONA", "AO": "AOSTA", "AP": "ASCOLI PICENO",
            "AQ": "L'AQUILA", "AR": "AREZZO", "AT": "ASTI", "AV": "AVELLINO", "BA": "BARI",
            "BG": "BERGAMO", "BI": "BIELLA", "BL": "BELLUNO", "BN": "BENEVENTO", "BO": "BOLOGNA",
            "BR": "BRINDISI", "BS": "BRESCIA", "BT": "BARLETTA-ANDRIA-TRANI", "BZ": "BOLZANO",
            "CA": "CAGLIARI", "CB": "CAMPOBASSO", "CE": "CASERTA", "CH": "CHIETI", "CL": "CALTANISSETTA",
            "CN": "CUNEO", "CO": "COMO", "CR": "CREMONA", "CS": "COSENZA", "CT": "CATANIA",
            "CZ": "CATANZARO", "EN": "ENNA", "FC": "FORLI'-CESENA", "FE": "FERRARA", "FG": "FOGGIA",
            "FI": "FIRENZE", "FM": "FERMO", "FR": "FROSINONE", "GE": "GENOVA", "GO": "GORIZIA",
            "GR": "GROSSETO", "IM": "IMPERIA", "IS": "ISERNIA", "KR": "CROTONE", "LC": "LECCO",
            "LE": "LECCE", "LI": "LIVORNO", "LO": "LODI", "LT": "LATINA", "LU": "LUCCA",
            "MB": "MONZA E DELLA BRIANZA", "MC": "MACERATA", "ME": "MESSINA", "MI": "MILANO",
            "MN": "MANTOVA", "MO": "MODENA", "MS": "MASSA-CARRARA", "MT": "MATERA", "NA": "NAPOLI",
            "NO": "NOVARA", "NU": "NUORO", "OR": "ORISTANO", "PA": "PALERMO", "PC": "PIACENZA",
            "PD": "PADOVA", "PE": "PESCARA", "PG": "PERUGIA", "PI": "PISA", "PN": "PORDENONE",
            "PO": "PRATO", "PR": "PARMA", "PT": "PISTOIA", "PU": "PESARO E URBINO", "PV": "PAVIA",
            "PZ": "POTENZA", "RA": "RAVENNA", "RC": "REGGIO CALABRIA", "RE": "REGGIO EMILIA",
            "RG": "RAGUSA", "RI": "RIETI", "RM": "ROMA", "RN": "RIMINI", "RO": "ROVIGO", "SA": "SALERNO",
            "SI": "SIENA", "SO": "SONDRIO", "SP": "LA SPEZIA", "SR": "SIRACUSA", "SS": "SASSARI",
            "SU": "SUD SARDEGNA", "SV": "SAVONA", "TA": "TARANTO", "TE": "TERAMO", "TN": "TRENTO",
            "TO": "TORINO", "TP": "TRAPANI", "TR": "TERNI", "TS": "TRIESTE", "TV": "TREVISO",
            "UD": "UDINE", "VA": "VARESE", "VB": "VERBANO-CUSIO-OSSOLA", "VC": "VERCELLI", "VE": "VENEZIA",
            "VI": "VICENZA", "VR": "VERONA", "VT": "VITERBO", "VV": "VIBO VALENTIA"}
# The Scheda anagrafica's "In qualità di" for the title the person holds (a tenant is
# "Altro" + "Locatario").
QUALITA = {"proprietario": "Proprietario", "comproprietario": "Comproprietario", "usufruttuario": "Usufruttuario",
           "amministratore di condominio": "Amministratore di condominio"}


def _albo_tipo(v):
    """An ordine's name ("Ordine degli Architetti P.P.C.") as the SUE's list has it."""
    v = v.lower()
    for word, option in (("architett", "Architetto"), ("ingegner", "Ingegnere"), ("geometr", "Geometra"), ("perit", "Perito")):
        if word in v:
            return option
    return "Altro"


def _qualita(v):
    return QUALITA.get(v.strip().lower(), "Altro")


def _titolo_pratica(v):
    """A SUE quadro a)'s dropdown option for the title: its own name, else "altro" (a
    tenant, a comodatario: then + specificare)."""
    return v.strip().lower() if v.strip().lower() in QUALITA else "altro"


# The SUE's destinazione d'uso dropdown: these three, anything else "altro" + its name.
DESTINAZIONI = {"residenziale", "industriale", "commerciale"}


def _destinazione(v):
    return v.strip().lower() if v.strip().lower() in DESTINAZIONI else "altro"


class Filters(dict):
    """`is_<answer>` is true when the value is that answer, spaces as underscores
    ({{ask.titolo_tipo|is_permesso_di_costruire}}): a choice's branch in a `when`. `in_<a>__<b>`
    is true when it is any of them (a `when` has no "or"). `atleast_<n>` is true when the number
    is n or more (the 20 m² the historic centre's Piano requires)."""
    def __missing__(self, name):
        if name.startswith("atleast_") and name[8:].isdigit():
            def atleast(v):
                try:
                    return "true" if float(str(v or 0).replace(",", ".")) >= int(name[8:]) else "false"
                except ValueError:
                    return "false"  # not a number: pre-flight says so (check_answer)
            return atleast
        answer = lambda v: re.sub(r"[^a-z0-9]+", "_", str(v).strip().lower()).strip("_")
        if name.startswith("in_"):
            return lambda v: "true" if answer(v) in name[3:].split("__") else "false"
        if not name.startswith("is_"):
            raise KeyError(name)
        return lambda v: "true" if answer(v) == name[3:] else "false"


def _facts(v, n):
    return (str(v).split("/") + [""] * n)[:n]


SUE_CAMBIO = {"stessa_categoria": "stessa categoria", "tra_categorie": "tra categorie"}


def _sue_scia_tipo(v):
    """What the SCIA files (asks.scia_tipo), from the SUE table's intervento, strutture,
    prospetti and cambio_uso; "" where they don't settle it (a variant to a SCIA: essential
    or not), so the question is asked."""
    i, strutture, prospetti, cambio = _facts(v, 4)
    if i in ("variante_pdc", "ristrutturazione"):
        return {"variante_pdc": "variante pdc", "ristrutturazione": "ristrutturazione"}[i]
    if i == "restauro" and strutture == "true":
        return "restauro"
    if i == "manutenzione_straordinaria" and "true" in (strutture, prospetti):
        return "manutenzione straordinaria"
    if i in ("nessuna_opera", "edilizia_libera", "manutenzione_straordinaria", "restauro") and cambio in SUE_CAMBIO:
        return "cambio uso"
    return ""


def _sue_cambio_uso_tipo(v):
    """A change of use alone (asks.cambio_uso_tipo), from intervento and cambio_uso."""
    i, cambio = _facts(v, 2)
    works = {"nessuna_opera": "senza opere", "edilizia_libera": "senza opere",
             "manutenzione_straordinaria": "opere 6bis", "restauro": "opere 6bis"}.get(i)
    return f"unita {works} {SUE_CAMBIO[cambio]}" if works and cambio in SUE_CAMBIO else ""


def _sue_pdc_tipo(v):
    """What the permesso asks for (asks.pdc_tipo), from intervento, cambio_uso and
    demolizione_zona_a: SCIA works are asked as a permesso by choice (art. 22 c. 7) only when
    no Campania or Naples rule makes it a permesso anyway."""
    i, cambio, demolizione = _facts(v, 3)
    own = {"nuova_costruzione": "nuova costruzione", "ristrutturazione_urbanistica": "ristrutturazione urbanistica",
           "ristrutturazione_pesante": "ristrutturazione edilizia", "variante_essenziale_pdc": "variante essenziale"}
    if i in own:
        return own[i]
    scia_works = ("nessuna_opera", "edilizia_libera", "manutenzione_straordinaria", "restauro", "ristrutturazione", "variante_pdc")
    if i in scia_works and cambio not in ("zona_agricola", "intero_immobile", "intero_tra_categorie") and demolizione != "true":
        return "facolta scia"
    return ""


FILTERS = Filters({
    "upper": str.upper,
    "albo_tipo": _albo_tipo,
    "sigla": lambda v: ".".join(v.strip().upper()) + "." if v.strip().isalpha() and len(v.strip()) <= 5 else v,
    "sesso": lambda v: {"F": "Femmina", "M": "Maschio"}[v.strip().upper()],
    "provincia_nome": lambda v: PROVINCE[v.strip().upper()],
    "qualita": _qualita,
    "qualita_is_altro": lambda v: "true" if _qualita(v) == "Altro" else "false",
    "qualita_altro": lambda v: v.strip().capitalize(),
    "titolo_pratica": _titolo_pratica,
    "titolo_is_altro": lambda v: "true" if _titolo_pratica(v) == "altro" else "false",
    # The asseverazione's materiali di risulta from the rules table's terre_rocce: soil leaving the
    # site is a by-product, filed with the dichiarazione or the piano; otherwise nothing to declare
    # (on-site reuse or waste are the person's to say). 2026-11-03: the terre e rocce combinations
    # declared "nessuno" while filing a dichiarazione.
    "scavo_proposto": lambda v: "sottoprodotti" if v.strip() in ("dichiarazione", "piano") else "nessuno",
    "piano_proposto": lambda v: "true" if v.strip() == "piano" else "false",
    # A title usually held alone (a.1): the proposal pre-flight asks to confirm.
    "titolo_solo": lambda v: "true" if v.strip().lower() in ("proprietario", "usufruttuario", "amministratore di condominio") else "false",
    "destinazione": _destinazione,
    "destinazione_is_altro": lambda v: "true" if _destinazione(v) == "altro" else "false",
    "filled": lambda v: "true" if v else "false",
    "rea_num": lambda v: v.split("-")[-1].strip(),
    "date_it": lambda v: "/".join(reversed(v.split("-"))),
    "phone_it": lambda v: re.sub(r"^\+39|\s", "", v),
    "dug": lambda v: _split_street(v)[0],
    "dug_altro": lambda v: "true" if _split_street(v)[0] == "ALTRO" else "false",
    "dug_dettaglio": _dug_dettaglio,
    "street": lambda v: _split_street(v)[2],
    "carica": _carica,
    "forma": lambda v: FORMA[v],
    # A client that is a company or a condominium (c:business.*), from {{c:business.denominazione,
    # c:business.rea|...}}: in the Registro delle imprese (a REA), or not (yet).
    "impresa_iscritta": lambda v: "true" if all(_facts(v, 2)) else "false",
    "impresa_non_iscritta": lambda v: "true" if _facts(v, 2)[0] and not _facts(v, 2)[1] else "false",
    "carica_cliente": lambda v: CARICA_CLIENTE[v.strip().lower()],
    # From c:business.forma_giuridica: a condominium is ALTRE FORME, its administrator declares,
    # and it is never in the Registro delle imprese.
    "forma_cliente": lambda v: "ALTRE FORME" if v == "condominio" else FORMA[v],
    "carica_proposta": lambda v: "amministratore di condominio" if v == "condominio" else "legale rappresentante",
    "registro_proposto": lambda v: "non necessita" if v == "condominio" else "",
    # The first of several fields that is set (a company's codice fiscale, else its partita IVA).
    "first": lambda v: next((x for x in v.split("/") if x), ""),
    # The holder a title is in the name of: a company's name, else the person's (first/last/company).
    "intestatario": lambda v: (_facts(v, 3)[2] or f"{_facts(v, 3)[0]} {_facts(v, 3)[1]}").upper(),
    "cittadinanza": _cittadinanza,
    "straniera": lambda v: "false" if v.strip().lower() in ("italiana", "italiano", "italia") else "true",
    # Born abroad: identity.birth_province is EE.
    "estero": lambda v: "true" if v.strip().upper() == "EE" else "false",
    "bollo_esente": lambda v: "true" if _bollo(v) in BOLLO_ESENZIONE else "false",
    "bollo_motivo": lambda v: BOLLO_ESENZIONE[_bollo(v)],
    "bollo_yours": _bollo_yours,
    "bollo_non_dovuto": _bollo_non_dovuto,
    "categoria": lambda v: re.sub(r"^([A-F])/?(\d)$", r"\g<1>0\2", v.replace(" ", "").upper()),
    "empty": lambda v: "true" if not v else "false",
    # Several yes/no answers at once ({{ask.a,ask.b|any}}): true when one is (a `when` has no "or").
    "any": lambda v: "true" if any(truthy(x) for x in str(v).split("/")) else "false",
    # The cadastral units of a job: the client's immobile, immobile2 ... One unit when the vault
    # holds no second ({{c:immobile2.x|empty|single_unit}}); with one, no value (None): the count
    # is asked, proposed from how many are filled (`filled_count`). `two_groups` takes the count, then
    # each unit's categoria (filled: Fabbricati, empty: Terreni), and is true when the
    # first n change catasto at most once (Dati catastali's two groups, one per catasto).
    # `differ`: two yes/no answers apart ({{ask.a#N,ask.a#P|differ}}: this unit starts a group).
    "single_unit": lambda v: "1" if truthy(v) else None,
    "filled_count": lambda v: str(sum(1 for x in str(v).split("/") if x.strip())),
    "two_groups": lambda v: (lambda n, cats: "true" if sum(
        bool(a.strip()) != bool(b.strip()) for a, b in zip(cats[:n], cats[1:n])) <= 1 else "false")(
        int(float(v.split("/")[0] or 1)), _categorie(v.split("/", 1)[1] if "/" in v else "")),
    "differ": lambda v: "true" if len({truthy(x) for x in str(v).split("/")}) > 1 else "false",
    # Steps written before the second group (2026-11-04) still name it: all one catasto.
    "one_catasto": lambda v: (lambda n, cats: "true" if len({bool(c.strip()) for c in cats[:n]}) <= 1 else "false")(
        int(float(v.split("/")[0] or 1)), _categorie(v.split("/", 1)[1] if "/" in v else "")),
    "not": lambda v: "false" if truthy(v) else "true",
    "positive": lambda v: "true" if float(str(v or 0).replace(",", ".")) > 0 else "false",
    # The SUE rules table's facts as the forms' own boxes (an ask's `propose`).
    "sue_scia_tipo": _sue_scia_tipo,
    "sue_cambio_uso_tipo": _sue_cambio_uso_tipo,
    "sue_pdc_tipo": _sue_pdc_tipo,
    # A ground-floor unit in zone A, B or C is what the forms' A/B/C line says; the regional
    # changes the forms have no line for are "altro" (defect cambio-uso-regionale).
    "sue_scia_cambio_uso": lambda v: {"no": "no", "intero_immobile": "intero immobile", "piano_terra": "tra categorie",
                                      "intero_tra_categorie": "altro", "altro": "altro", **SUE_CAMBIO}.get(str(v), ""),
    # Napoli SUE's diritti (tabella G.C. 239/2026) where its line depends on the case: the amount to
    # propose, or "" where the table needs what no ask holds (an onerous title's contributo bracket,
    # a car park's floor area), so the question stays.
    "diritti_cila": lambda v: {"da iniziare": "151", "in corso": "166", "realizzato": "166"}.get(str(v).strip(), ""),
    "diritti_gratuito": lambda v: "401" if v is not None and not truthy(v) else "",
    "diritti_pdc": lambda v: ("501" if _facts(v, 2)[0] in ("variante essenziale", "variante sagoma") else ""
                              if _facts(v, 2)[0] == "parcheggi" or truthy(_facts(v, 2)[1]) else "401"),
    # A SCIA in sanatoria: line SUE 16 names the accertamenti (art. 36-bis) and the regularizations
    # (art. 34-ter), not the works still under way (art. 37 c. 5).
    "diritti_sanatoria_scia": lambda v: "" if str(v).strip() in ("", "in corso") else "441",
    "diritti_proroga_pdc": lambda v: "501" if str(v).strip() == "permesso di costruire" else "",
    "sue_scia_alt_tipo": lambda v: {"ristrutturazione_pesante": "ristrutturazione edilizia",
                                    "ristrutturazione_urbanistica": "nuova costruzione piano attuativo"}.get(str(v), ""),
})


def truthy(v):
    """True for a yes; a `when` of several words ("{{ask.a|not}} {{ask.b}}") wants every one."""
    words = str(v).strip().lower().split()
    return bool(words) and all(w in ("true", "1", "yes", "si", "sì") for w in words)


def fields_of(text):
    """--values: `pvault get`'s JSON object, or a rehearsal's fixture (its "fields", a list of
    [id, value] pairs), as one dict."""
    given = json.loads(text)
    if isinstance(given, dict) and isinstance(given.get("fields"), list):
        given = given["fields"]
    return dict(given) if isinstance(given, list) else given


class StepError(Exception):
    pass


# --- values -----------------------------------------------------------------------

class Values:
    """The vault fields and answers a steps file refers to."""

    def __init__(self, answers, vault=None, fields=None, asks=None):
        """From the vault with a token, or from fields already read (pvault get's JSON).
        asks is the steps file's `asks:`, for the defaults of what answers leave out."""
        self.vault, self.fields = vault, fields
        self.answers, self.asks = answers, asks or {}
        self.cache = {}
        self._titolare_slug = None

    @property
    def titolare(self):
        # Found when a template first names t:, so pre-flight can report a missing one.
        if self._titolare_slug is None:
            self._titolare_slug = self._titolare()
        return self._titolare_slug

    def _get(self, path):
        status, body = self.vault.call("GET", path)
        if status == 404:
            return []
        if status != 200:
            raise StepError(f"reading the vault: {status} {body}")
        return body

    def category(self, cat):
        if cat not in self.cache:
            if self.fields is not None:
                self.cache[cat] = {k: v for k, v in self.fields.items() if k.startswith(cat + ".") and v is not None}
            else:
                self.cache[cat] = {r["id"]: r["value"] for r in self._get("/vault/fields/category/" + cat)}
        return self.cache[cat]

    def _titolare(self):
        # A studio's other architect presents the pratica when the job names them ("people" t).
        named = (self.answers.get("people") or {}).get("t")
        ids = list(self.fields) if self.fields is not None else [f["id"] for f in self._get("/vault/fields")]
        if named:
            if not any(i.startswith(named + ":") for i in ids):
                raise StepError(f"the architect named in people (t: {named}) has nothing in the vault")
            return named
        slugs = sorted({i.split(":")[0] for i in ids if i.endswith(":ruolo.tipo")})
        found = [s for s in slugs if "titolare" in self.category(s + ":ruolo").get(s + ":ruolo.tipo", "")
                 or "legale_rappresentante" in self.category(s + ":ruolo").get(s + ":ruolo.tipo", "")]
        if len(found) != 1:
            raise StepError(f"want one titolare or legale rappresentante, found {found or 'none'}")
        return found[0]

    def raw(self, key):
        """An ask's answer as given; a checklist's answer (the items ticked, as a list
        under the group's key) answers each of its items, ticked or not."""
        v = self.answers.get(key)
        group = self.asks.get(key, {}).get("group")
        if v is None and group and isinstance(self.answers.get(group), list):
            v = key in self.answers[group]
        return v

    def field(self, ref):
        if ref.startswith("ask."):
            v = self.raw(ref[4:])
            if v is None and "default" in self.asks.get(ref[4:], {}):
                v = self.render(self.asks[ref[4:]]["default"])
            return None if v is None else str(v).lower() if isinstance(v, bool) else str(v)
        if ref.startswith("t:"):
            ref = self.titolare + ":" + ref[2:]
        # A role of this pratica (answers.json "people": {"c": "luca", ...}) names a person.
        role, sep, rest = ref.partition(":")
        if sep and role in (self.answers.get("people") or {}):
            ref = self.answers["people"][role] + ":" + rest
        cat = ref.rsplit(".", 1)[0]
        return self.category(cat).get(ref)

    def sum(self, ref):
        """`ask.a+2*ask.b`: a box the portal wants as a total of what was asked (rooms, beds)."""
        total = 0
        for term in ref.split("+"):
            n, _, r = term.strip().rpartition("*")
            v = self.field(r.strip())
            if v is None:
                return None
            total += int(n or 1) * float(str(v or 0).replace(",", "."))
        return f"{total:g}"

    def render(self, template):
        """A template's value, or None when a field it names is missing."""
        def one(m):
            ref, *filters = [p.strip() for p in m.group(1).split("|")]
            if "," in ref:  # several fields for one filter (a proposal from facts of the case): a/b/c, "" for one unknown
                v = "/".join(self.field(r.strip()) or "" for r in ref.split(","))
            else:
                v = self.sum(ref) if "+" in ref or "*" in ref else self.field(ref)
            if v is None:
                if "empty" in filters:
                    v = ""
                else:
                    raise KeyError(ref)
            for f in filters:
                v = FILTERS[f](v)
                if v is None:  # a filter that can't tell (single_unit): no value, as a missing field
                    raise KeyError(ref)
            return v
        try:
            return re.sub(r"\{\{(.+?)\}\}", one, str(template))
        except KeyError:
            return None


# --- "+" blocks, as many as the case has --------------------------------------------

def nth_block(obj, n):
    """A template block's field or ask for its n-th repeat: #N is "" in the first and n after
    (role a, a2; ask altro_tecnico_..., altro_tecnico2_...), #K is n always (comunicazione_3), #P the
    block before's #N (immobile#P: the unit before, to tell where a new catasto group starts)."""
    prev = str(n - 1) if n > 2 else ""
    return json.loads(json.dumps(obj, ensure_ascii=False).replace("#N", str(n) if n > 1 else "")
                      .replace("#K", str(n)).replace("#P", prev))


def leaves(w):
    """A wizard screen's tree as a list: each a label, a {leaf, nth}, or a {leaf, when}."""
    t = w.get("tree", [])
    return t if isinstance(t, list) else [t]


def chosen(steps, values):
    """The steps for this case's "Scelte eventuali": a tick a recipe takes only for some cases
    ({leaf, when}: there are co-holders) is ticked when its `when` holds for this case, and the
    sections it adds (each with the same `when`) are gone when it doesn't. An unanswered `when`
    counts as not taken; pre-flight asks it first: the steps keep each such `when` (`chosen`)."""
    conditional = any(isinstance(x, dict) and "when" in x for w in steps.get("wizard", []) for x in leaves(w)) \
        or any("when" in s for s in steps["sections"])
    if not conditional:
        return steps
    taken = lambda x: truthy(values.render(x["when"]) or "")

    def bare(x):
        rest = {k: v for k, v in x.items() if k != "when"}
        return rest["leaf"] if set(rest) == {"leaf"} else rest
    wizard = []
    for w in steps.get("wizard", []):
        if "tree" not in w:
            wizard.append(w)
            continue
        tree = [bare(x) if isinstance(x, dict) and "when" in x else x
                for x in leaves(w) if not (isinstance(x, dict) and "when" in x) or taken(x)]
        wizard.append({k: (tree[0] if len(tree) == 1 else tree) if k == "tree" else v for k, v in w.items() if k != "tree" or tree})
    sections = [{k: v for k, v in s.items() if k != "when"} for s in steps["sections"] if "when" not in s or taken(s)]
    whens = [x["when"] for w in steps.get("wizard", []) for x in leaves(w) if isinstance(x, dict) and "when" in x]
    return {**steps, "wizard": wizard, "sections": sections, "chosen": list(dict.fromkeys(whens))}


def expand(steps, values):
    """The steps for this case's count of each "+" block. gen.py writes a block the national
    form lets repeat without limit (other technicians, "altro" titles, filings) once, as a
    template: an `add` with `each` (the count, the first block it adds), then its fields with
    `block: "#N"`. Each block also waits for its count (`atleast_n`), so before the count is
    answered one block shows what will be asked. An ask named with #N or #K becomes one per
    block (values.asks too). Steps with no template come back as they are, after `chosen`."""
    steps = chosen(steps, values)
    if not any(f.get("block") == "#N" for s in steps["sections"] for f in s["fields"]):
        return steps
    out = {**steps, "sections": []}
    for sec in steps["sections"]:
        fields, fs, i = [], sec["fields"], 0
        while i < len(fs):
            f, i = fs[i], i + 1
            if not (f["kind"] == "add" and "each" in f):
                fields.append(f)
                continue
            body = []
            while i < len(fs) and fs[i].get("block") == "#N":
                body.append(fs[i])
                i += 1
            each = f["each"]
            v = values.render(each["count"])
            try:
                count = int(float(v.replace(",", "."))) if v is not None else None
            except ValueError:
                count = None  # pre-flight says it isn't a number
            gate = lambda n: each["count"][:-2] + f"|atleast_{n}}}}}"
            base = f.get("when", "")

            def when(g, n):
                # The count right after the block's own condition: a field's own words (is the
                # second technician an employee?) are asked only for a block there is.
                w = g.get("when", "")
                rest = w[len(base):] if base and w.startswith(base) else w
                return " ".join(x for x in (base, gate(n), rest.strip()) if x)
            # The first block it adds is there even when the count says none: it holds the
            # count's question (asked first), and its own `when` keeps it off the page.
            for n in range(each["from"], max(each["from"], count or 0) + 1):
                # The "+" itself may have a condition per block (`each.when`: the unit's "+" only
                # within a group; the group's "+", a block field, where a new catasto starts).
                own = nth_block(each["when"], n) if each.get("when") else ""
                fields.append({**{k: x for k, x in f.items() if k != "each"}, "block": n,
                               "when": " ".join(x for x in (when(f, n), own) if x)})
                fields += [{**g, "block": n, "when": when(g, n)} for g in map(lambda b: nth_block(b, n), body)]
        out["sections"].append({**sec, "fields": fields})
    used = {r[4:] for _, t, _ in templates(out) for r, _ in refs_in(t) if r.startswith("ask.")}
    asks = {}
    for k, a in steps.get("asks", {}).items():
        if "#N" not in k and "#K" not in k:
            asks[k] = a
        for n, u in block_asks(k, used):
            asks.setdefault(u, nth_block(a, n))
    out["asks"] = values.asks = asks
    return out


def block_asks(key, used):
    """The asks in `used` that are blocks of the template ask `key` (named with #N or #K), with
    each one's block number, in order; none for an ask that isn't a template."""
    if "#N" not in key and "#K" not in key:
        return []
    pattern = re.compile("^" + "".join(r"(\d*)" if p == "#N" else r"(\d+)" if p == "#K" else re.escape(p)
                                       for p in re.split("(#N|#K)", key)) + "$")
    return sorted((int(next((g for g in m.groups() if g), "1")), u) for u in used if (m := pattern.match(u)))


def plan(steps, values):
    """Each field with its value; raises on a missing required value."""
    steps = expand(steps, values)
    out, missing = [], []
    for w in steps.get("wizard", []):
        v = values.render(w["fill"]["value"]) if "fill" in w else None
        if v and w["fill"].get("max") and len(v) > w["fill"]["max"]:
            missing.append(f"{w['screen']}: {v!r} is longer than the portal takes ({w['fill']['max']})")
    for sec in steps["sections"]:
        for f in sec["fields"]:
            if "when" in f and not truthy(values.render(f["when"]) or ""):
                continue
            name = f.get("label") or f.get("id") or f.get("css")
            try:
                v = values.render(f["value"]) if "value" in f else None
            except ValueError as e:
                # A vault value the form can't take (a street type the portal lists nowhere): what
                # pre-flight names, said here too when `page` or `run` comes without it.
                missing.append(f"{sec['section']}: {name}: {e}")
                continue
            if "value" in f and v is None and not f.get("optional"):
                missing.append(f"{sec['section']}: {name} ({f['value']})")
            if f["kind"] == "file" and v and not Path(v).expanduser().is_file():
                missing.append(f"{sec['section']}: {name}: no file {v}")
            if f.get("max") and v and len(v) > f["max"]:
                missing.append(f"{sec['section']}: {name}: {v!r} is longer than the portal takes ({f['max']})")
            out.append({"section": sec["section"], "id": f.get("id") or f.get("css"), "kind": f["kind"],
                        "label": f.get("label"), "value": v})
    if missing:
        raise StepError("missing values:\n  " + "\n  ".join(missing))
    return out


# --- pre-flight and branch coverage --------------------------------------------------

ASK_TYPES = {"text", "number", "yes_no", "date", "choice", "file"}


def refs_in(template):
    """The fields a template reads, each with its filters (each term of a sum on its own)."""
    return [(t.strip().rpartition("*")[2].strip(), parts[1:]) for parts in
            ([p.strip() for p in m.split("|")] for m in re.findall(r"\{\{(.+?)\}\}", str(template)))
            for t in re.split(r"[+,]", parts[0])]


def templates(steps):
    """Every template in a steps file, with where it is."""
    for w in steps.get("wizard", []):
        if "fill" in w:
            yield f"wizard: {w['screen']}", w["fill"]["value"], {}
        for x in leaves(w):
            if isinstance(x, dict) and "when" in x:
                yield f"wizard: {w['screen']}: {x['leaf']}", x["when"], {}
    for w in steps.get("chosen", []):
        yield "wizard: Scelte eventuali", w, {}
    for sec in steps["sections"]:
        for f in sec["fields"]:
            for k in ("when", "value"):
                if k in f:
                    yield f"{sec['section']}: {f.get('label') or f.get('id') or f.get('css')}", f[k], f
    for y in steps.get("yours", []):
        yield "yours", y, {}
    for c in steps.get("supports", []):
        for k in ("if", "when", "value", "else"):
            if k in c:
                yield "supports", c[k], {}
    for v in steps.get("rules", {}).get("facts", {}).values():
        yield "rules", v, {}


def scope(steps):
    """The `pvault get` patterns for every vault field the steps read: a role's (`c:identity.x`)
    as everyone's category (`*:identity.*`), the vault owner's own as its category, and every
    person's ruolo, by which the roles are found. One approval reads them all; nothing else."""
    cats, own = {"ruolo"}, set()
    for _, t, _ in templates(steps):
        for r, _ in refs_in(t):
            head, dot, _ = r.partition(".")
            if not dot or head == "ask":
                continue
            (cats if ":" in head else own).add(head.rpartition(":")[2])
    return sorted(f"{c}.*" for c in own) + sorted(f"*:{c}.*" for c in cats)


def check_asks(steps):
    """The asks block itself, and the order to ask in. Every ask a field reads has its
    question, and every question is read by a field, a wizard screen or `supports`: one
    only the person's own steps mention is not worth asking. A yes/no in a `group` is an
    item of that group's checklist, asked as one question."""
    asks, groups = steps.get("asks", {}), steps.get("groups", {})
    reads = lambda wheres: {r[4:] for where, t, _ in templates(steps) if wheres(where)
                            for r, _ in refs_in(t) if r.startswith("ask.")}
    used = reads(lambda w: w != "yours")
    lacking = sorted((used | reads(lambda w: w == "yours")) - set(asks))
    if lacking:
        raise StepError(f"steps file: no question in asks: for {', '.join(lacking)}")
    unused = sorted(set(asks) - used)
    if unused:
        raise StepError(f"steps file: no field reads asks.{', asks.'.join(unused)}: drop it")
    for k, a in asks.items():
        if "group" in a:
            if a["group"] not in groups or a.get("type") != "yes_no" or not a.get("item") or "propose" in a:
                raise StepError(f"steps file: asks.{k} is in a group, so it needs type yes_no, an item, "
                                "its group in groups:, and no propose (the checklist's \"none\" is the proposal)")
        elif a.get("type") not in ASK_TYPES or not a.get("question") or (a["type"] == "choice" and not a.get("options")):
            raise StepError(f"steps file: asks.{k} needs a question and a type ({', '.join(sorted(ASK_TYPES))}), "
                            "and options for a choice")
    for g, d in groups.items():
        if not d.get("question") or not any(a.get("group") == g for a in asks.values()):
            raise StepError(f"steps file: groups.{g} needs a question and at least one ask in it")
    # The asks that decide the branch come first: their answers can end the pratica here.
    branch = {r[4:] for c in steps.get("supports", []) for k in ("if", "when", "value")
              for r, _ in refs_in(c.get(k, "")) if r.startswith("ask.")}
    branch |= {r[4:] for where, t, _ in templates(steps) if where == "rules" for r, _ in refs_in(t) if r.startswith("ask.")}
    return sorted(asks, key=lambda k: k not in branch)


def needed(steps, values):
    """The asks this case needs answered, each with the unanswered asks its need hangs on
    (empty: needed whatever they say). A field whose `when` is false for this case needs
    nothing, so its questions aren't asked."""
    need = {}

    def add(keys, deps=()):
        for k in keys:
            need[k] = set() if (k in need and not need[k]) or not deps else need.get(k, set()) | set(deps)

    asked = lambda tmpl: [r[4:] for r, _ in refs_in(tmpl) if r.startswith("ask.")]

    def gate(when):
        """A `when`'s words in order, each a gate for the next ("onerosa, and then paid?"):
        a later word's asks hang on the earlier ones; a false word ends it. False when this
        case's answers already make it false."""
        deps = []
        for word in re.findall(r"\{\{.+?\}\}", when):
            add(asked(word), deps)
            v = values.render(word)
            if v is None:
                deps = deps + [k for k in asked(word) if values.field("ask." + k) is None]
            elif not truthy(v):
                return False
        return True

    for c in steps.get("supports", []):
        # `if`: a check that only applies once its gate holds (how a contributo is paid,
        # once one is due), asked only then.
        deps = ()
        if "if" in c:
            if not gate(c["if"]):
                continue
            if values.render(c["if"]) is None:
                deps = [k for k in asked(c["if"]) if values.field("ask." + k) is None]
        add(asked(c.get("when", c.get("value", ""))), deps)
    for fact in ruled(steps, values)[1]:
        add(asked(steps["rules"]["facts"][fact]))
    for w in steps.get("wizard", []):
        if "fill" in w:
            add(asked(w["fill"]["value"]))
        for x in leaves(w):
            if isinstance(x, dict) and "when" in x:
                gate(x["when"])  # a scelta ticked only for some cases: its question
    for w in steps.get("chosen", []):
        gate(w)
    for sec in steps["sections"]:
        for f in sec["fields"]:
            deps = ()
            if "when" in f:
                if not gate(f["when"]):
                    continue
                w = values.render(f["when"])
                if w is None:
                    deps = [k for k in asked(f["when"]) if values.field("ask." + k) is None]
            add(asked(f.get("value", "")), deps)
    return need


def _decision(steps, values):
    """The rules table's decision of this case (steps `rules:`), or None without one. Each
    fact is the recipe's value or an ask's answer."""
    r = steps.get("rules")
    if not r or not r.get("table"):
        # A combination no table routes yet (a proroga with the landscape one): `main` and
        # `handles` only, filed when the person names it.
        return None
    t = rules.table(r["table"])
    facts = {}
    for name, fact in t["facts"].items():
        v = r["facts"][name]
        v = values.render(v) if isinstance(v, str) and "{{" in v else v
        if v is not None and rules.fact_value(fact, v) is not None:
            facts[name] = rules.fact_value(fact, v)
    d = rules.decide(t, facts)
    if d["conflict"]:
        raise StepError(f"rules table {r['table']}: rules {', '.join(d['conflict'])} disagree (validate the library)")
    return d


def ruled(steps, values):
    """What the rules table says of this case: why it isn't this pratica, and the facts it
    still waits on. The table's main pratica must be the one this steps file files (`main`,
    else its procedure: a CILA with its landscape authorization files the CILA), at its
    wizard's sector and operation; every other pratica it adds with it must be one this
    pratica files (`handles`), and every one this pratica files one the case needs. Those it
    files apart, with another office, are the person's (`apart`)."""
    d = _decision(steps, values)
    if d is None:
        return [], []
    r = steps["rules"]
    out = [x["reason"] for x in d["refused"]]
    if d["ask"]:
        # While the table's first fact (what the case is: the activity, the works) is unknown
        # it is asked alone: which of the others matter depends on it.
        first = next(iter(rules.table(r["table"])["facts"]))
        return out, d["ask"][:1] if d["ask"][0] == first else d["ask"]
    if d["none"]:
        return out + [f"Per questo caso non serve alcuna pratica: {d['none']['reason']}"], []
    m = d["main"]
    where = lambda o: " (sul portale: " + " › ".join(o["portal"][k] for k in ("settore", "operazione") if k in o["portal"]) \
        + ")" if "portal" in o else ""
    if not m:
        return out or ["Le regole del SUE non indicano alcuna pratica per questo caso."], []
    # A wizard screen's tree is one label, or a list of them (several operations: the SUE's
    # CILA with its landscape authorization), each a label or a {leaf: ...}.
    trees = [w["tree"] for w in steps.get("wizard", []) if "tree" in w]
    labels = {x if isinstance(x, str) else x.get("leaf") for t in trees for x in (t if isinstance(t, list) else [t])}
    seen = m.get("portal", {})
    if m["procedure"] != r.get("main", steps["procedure"]) or any(seen[k] not in labels for k in ("settore", "operazione") if k in seen):
        out.append(f"Questo caso è un'altra pratica: {procedure_name(m['procedure'])}{where(m)}.")
    handles = r.get("handles", [])
    for a in d["also"]:
        if a["procedure"] not in handles:
            out.append(f"Questo caso chiede anche {procedure_name(a['procedure'])}, che questa pratica non presenta.")
    for h in handles:
        if h not in [a["procedure"] for a in d["also"]]:
            out.append(f"Questa pratica presenta anche {procedure_name(h)}, che a questo caso non serve.")
    return out, []


def procedure_name(pid):
    """A library procedure as the tecnico reads it: its title up to " – " (no "Comune di Napoli,
    sul SUE"), from the plugin's library/ or $PRATICHE_NAPOLI_DIR (plugin/build.py sets it, so
    both runners name it alike), else its id's last part in words. Never the id itself."""
    roots = [Path(__file__).resolve().parent.parent / "library"]
    if os.environ.get("PRATICHE_NAPOLI_DIR"):
        roots.append(Path(os.environ["PRATICHE_NAPOLI_DIR"]))
    for root in roots:
        p = root / "procedures" / f"{pid}.yaml"
        if p.is_file():
            m = re.search(r"^title: *[\"']?(.+?)[\"']? *$", p.read_text(), re.M)
            if m:
                return m[1].split(" – ")[0]
    return pid.rsplit("/", 1)[-1].replace("-", " ")


def apart(steps, values):
    """The pratiche the rules table says this case also needs, filed on their own with
    another office (the Genio Civile's seismic filing for works on structures): the
    person's to file, said in their steps, never a reason to refuse this one."""
    d = _decision(steps, values)
    if d is None or d["ask"] or not d["main"]:
        return []
    return [f"Da presentare a parte, al suo ufficio: {procedure_name(a['procedure'])}" for a in d["apart"]]


def asked_yours(steps, values):
    """The person's steps an answer brings (an ask's `yours`, said when it's answered yes: the
    other designer's signature)."""
    return [a["yours"] for k, a in steps.get("asks", {}).items()
            if a.get("yours") and truthy(values.field("ask." + k) or "")]


def supported(steps, values):
    """Why this case isn't mapped, and the asks still needed to tell."""
    out, need, _ = refusals(steps, values)
    return out, need


def refusals(steps, values):
    """supported(), and the known portal defects behind its refusals (a `supports` entry's
    `defect`, from defects.yaml through gen.py): the person is told what the portal does and
    chooses what to do."""
    out, waiting = ruled(steps, values)
    defects = []
    need = []
    for f in waiting:
        tmpl = steps["rules"]["facts"][f]
        asked = [r for r, _ in refs_in(tmpl) if r.startswith("ask.")]
        need += asked
        if not asked:  # read from the vault, and empty there
            out.append(f"The rules need {f}, read from {tmpl}: empty in the vault.")
    for c in steps.get("supports", []):
        if "if" in c:
            # Its words in order, as a field's `when`: a false one ends it, so a later word's
            # asks aren't needed ("altro" ticked, and then a second altro line?).
            holds = True
            for word in re.findall(r"\{\{.+?\}\}", c["if"]):
                unknown = [r for r, f in refs_in(word) if r.startswith("ask.") and values.field(r) is None]
                if unknown:
                    need += unknown
                    holds = False
                    break
                if not truthy(values.render(word)):
                    holds = False
                    break
            if not holds:
                continue
        tmpl = c.get("when", c.get("value"))
        unknown = [r for r, f in refs_in(tmpl) if r.startswith("ask.") and values.field(r) is None]
        if unknown:
            need += unknown
            continue
        v = values.render(tmpl)
        ok = v is not None and (truthy(v) if "when" in c else v in [str(x) for x in c["in"]])
        if not ok:
            out.append(values.render(c["else"]) or c["else"])
            if isinstance(c.get("defect"), dict) and c["defect"]["id"] not in [d["id"] for d in defects]:
                defects.append({**c["defect"], "else": out[-1]})
    return out, need, defects


def require_supported(steps, values):
    out, need = supported(steps, values)
    if out:
        raise StepError("not supported: " + "; ".join(out))
    if need:
        raise StepError("unanswered: " + ", ".join(sorted(set(need))) + " (run preflight)")


def check_answer(ask, v):
    """Why an answer doesn't fit its ask, or None."""
    s = str(v).strip()
    kind = ask["type"]
    if kind == "yes_no" and not (isinstance(v, bool) or s.lower() in ("true", "false", "si", "sì", "no", "yes")):
        return "answer yes or no"
    if kind == "number":
        try:
            float(s.replace(",", "."))
        except ValueError:
            return "answer with a number"
    if kind == "date":
        try:
            date.fromisoformat(s)
        except ValueError:
            return "answer with a date (YYYY-MM-DD)"
    if kind == "choice" and s not in [str(o) for o in ask["options"]]:
        return "answer with one of: " + ", ".join(map(str, ask["options"]))
    if kind == "file" and not Path(s).expanduser().is_file():
        return f"no file {s}"
    if kind == "text" and not s:
        return "the answer is empty"
    return None


def portal_changed(steps):
    """A generated steps file whose pratica the last drift check (catalogue.py drift) found
    changed on the portal: refused until it's crawled and generated again."""
    m = re.match(r"gen\.py from (\S+) ", steps.get("generated", ""))
    if not m:
        return []
    diff = rules.drifted(m.group(1))
    # The person reads it: the portal's own section names (catalogue.py's "gone: ", "new: ",
    # "changed: " in Italian), and that it waits for a new check.
    said = {"gone": "tolta", "new": "nuova", "changed": "cambiata"}
    where = "; ".join(f"{n} ({said.get(k, k)})" for k, _, n in (d.partition(": ") for d in diff))
    return [f"Il portale ha cambiato questa pratica da quando l'ho provata: {where}. Per ora non la "
            "preparo, finché non è verificata di nuovo."] if diff else []


def signed_only(f):
    """A file field whose slot takes only signed files (.p7m)."""
    takes = [t for t in f.get("accepts", "").split(";") if t]
    return f["kind"] == "file" and bool(takes) and all(t.endswith(".p7m") for t in takes)


def applies(f, values):
    """Whether a field is filled in this case: no word of its `when` false (an unknown one isn't)."""
    return "when" not in f or not any(v is not None and not truthy(v) for v in
                                      map(values.render, re.findall(r"\{\{.+?\}\}", f["when"])))


def phase(steps, after=False, made_up=False):
    """The steps of one run. A document the portal makes from the pratica only once the
    declarations are ticked (the procura, for the client to sign: `after_declarations`) can't go
    with the first run, so a second one (after=True, --after-declarations) attaches those alone, on
    the same draft. With made_up (a rehearsal's files) no slot that takes only signed files is
    filled: the portal checks each signature on upload and refuses a made-up one (2026-11-03)."""
    def keep(s, f):
        if made_up and signed_only(f):
            return False
        return not s.get("go") or bool(f.get("after_declarations")) == after
    asked = lambda fs: {r[4:] for f in fs for k in ("when", "value") for r, _ in refs_in(f.get(k, "")) if r.startswith("ask.")}
    out = steps | {"sections": [s | {"fields": [f for f in s["fields"] if keep(s, f)]} for s in steps["sections"]]}
    # A question only the left-out fields read isn't this run's.
    left = asked(f for s in steps["sections"] for f in s["fields"] if not keep(s, f))
    still = {r[4:] for where, t, _ in templates(out) if where != "yours" for r, _ in refs_in(t) if r.startswith("ask.")}
    if "asks" in steps:
        out["asks"] = {k: v for k, v in steps["asks"].items() if k not in left - still}
    return out


def rehearsal(steps, values):
    """The steps a rehearsal's run fills, its files made up: the first run's (phase)."""
    return phase(expand(steps, values), made_up=True)


def after_declarations(steps, values):
    """The labels of what this case's second run attaches (phase's `after_declarations`)."""
    return [f.get("label") or f.get("id") for s in steps["sections"] for f in s["fields"]
            if f.get("after_declarations") and applies(f, values)]


def reopening(steps):
    """How the second run starts: the draft opened from Pratiche in bozza by its name (the
    person's clicks since have moved its address on), then the attachments screen alone."""
    at = next((i for i, s in enumerate(steps["sections"]) if s.get("go") and s["fields"]), None)
    if at is None:
        raise StepError("nothing in this pratica waits for the declarations: no second run")
    return {"reopen": True, "from": {"section": at}, "kept": [], "fixes": []}


# A proposal that reads a question asked in the same message is shown for each of its answers
# when they are few (a yes/no, a short choice): at most this many cases.
MAX_CASES = 6


def conditional_proposals(later, report, values, need):
    """The proposals that read another ask still open in this same message, so the person
    confirms them all at once instead of in a second round. One that reads another proposal is
    worded from it (`assumes`: it holds once that one is confirmed); one that reads an open
    yes/no or choice is worded for each answer (`cases`: if this answer, this proposal), and for
    an answer with no proposal the question itself is asked (`otherwise`: those answers). One that
    reads an open text answer still waits for it. Chains resolve in order, a pass each."""
    provisional = {p["key"]: p["proposal"] for p in report["proposals"] if "proposal" in p}
    out = []
    for _ in range(3):
        waiting = []
        for k, hangs in later:
            a = values.asks[k]
            reads = [r[4:] for r, _ in refs_in(a["propose"]) if r.startswith("ask.")]
            open_ = [r for r in reads if r in need and values.field("ask." + r) is None]
            assumed = [r for r in open_ if r in provisional]
            choose = [r for r in open_ if r not in provisional]
            options = {}
            for r in choose:
                q = values.asks.get(r, {})
                options[r] = (["true", "false"] if q.get("type") == "yes_no" or "group" in q
                              else list(q.get("options", [])) if q.get("type") == "choice" else None)
            if any(not o for o in options.values()):
                waiting.append((k, hangs))
                continue
            combos = [{}]
            for r, opts in options.items():
                combos = [c | {r: o} for c in combos for o in opts]
            if len(combos) > MAX_CASES:
                waiting.append((k, hangs))
                continue
            cases = []
            for combo in combos:
                given = Values(values.answers | {r: provisional[r] for r in assumed} | combo,
                               vault=values.vault, fields=values.fields, asks=values.asks)
                given.cache, given._titolare_slug = values.cache, values._titolare_slug
                proposal = given.render(a["propose"])
                if proposal is not None and not check_answer(a, proposal):
                    cases.append((combo, proposal))
            if not cases:
                waiting.append((k, hangs))
                continue
            entry = {"key": k, "question": a["question"]} | ({"assumes": sorted(assumed)} if assumed else {})
            covered = [c for c, _ in cases]
            if choose and (len(cases) < len(combos) or len({str(p) for _, p in cases}) > 1):
                # A proposal for each answer that has one; the question itself for the others.
                entry["cases"] = [{"if": c, "proposal": p} for c, p in cases]
                rest = [c for c in combos if c not in covered]
                if rest:
                    entry["otherwise"] = rest
                    entry |= {x: a[x] for x in ("type", "options", "labels", "how") if x in a}
            else:
                entry["proposal"] = provisional[k] = cases[0][1]
            out.append(entry | {x: a[x] for x in ("why",) if x in a} | hangs)
        if len(waiting) == len(later):
            break
        later = waiting
    return out


def assumed_proposals(steps, values, report):
    """The message as the proposals make the case: a follow-up that hangs only on proposals and that
    the case doesn't need once they hold (the details of other planning instruments, proposed
    "no") leaves the message for `if_changed`, under the proposal that would open it, and is asked
    only if the person changes that proposal. A follow-up that also hangs on an open question stays.
    Returns what the case needs once the proposals hold (None with none), for message()."""
    held = {p["key"]: p["proposal"] for p in report["proposals"] if "proposal" in p}
    if not held:
        return None
    given = Values(values.answers | held, vault=values.vault, fields=values.fields, asks=values.asks)
    given.cache, given._titolare_slug = values.cache, values._titolare_slug
    need = needed(steps, given)
    later = {}

    def stays(x):
        hangs = x.get("only_if") or []
        if not hangs or not set(hangs) <= set(held) or x["key"] in need:
            return True
        for h in hangs:
            later.setdefault(h, []).append(x["key"])
        return False
    for q in report["questions"]:
        if "items" in q:
            q["items"] = [i for i in q["items"] if stays(i)]
    report["questions"] = [q for q in report["questions"] if ("items" in q and q["items"]) or ("items" not in q and stays(q))]
    report["proposals"] = [p for p in report["proposals"] if stays(p)]
    if later:
        report["if_changed"] = later
    return need


def head(question):
    """A proposal's question as the message shows it: up to its "?", without the asides that cite
    no law (a parenthesis with no number): the answer is already proposed, so they only explain it.
    The whole question stays in the report, for a tecnico who asks."""
    i = question.find("?")
    q = question[:i + 1] if 0 < i < len(question) - 1 else question
    return re.sub(r" \([^()\d]*\)", "", q)


def refusal_text(report):
    """Pre-flight's message when it refuses, for Claude to send as it is: each known portal defect
    first (the exact sub-case, that it is the portal's flaw and not missing work, what still
    fills, the choices), then any other reason in the steps file's own words."""
    blocks = []
    for d in report.get("defects", []):
        blocks.append([f"Non posso preparare: {d['title']}.",
                       f"È un difetto del portale, non manca nulla da parte sua. {d['what']}"]
                      + ([d["works"]] if d.get("works") else [])
                      + ["Può:"] + [f"{i}. {c}" for i, c in enumerate(d.get("choices", []), 1)])
    told = {d.get("else") for d in report.get("defects", [])}
    rest = [u for u in report["unsupported"] if u not in told]
    if rest:
        blocks.append(["Non posso preparare questa pratica:" if len(rest) > 1 else "Non posso preparare questa pratica."]
                      + [f"– {u}" if len(rest) > 1 else u for u in rest])
    return "\n\n".join("\n".join(b) for b in blocks)


# What the person reads again when an answer didn't fit (check_answer's reasons are for Claude).
RETRY = {"yes_no": "risponda sì o no", "number": "serve un numero", "date": "serve una data",
         "choice": "scelga una delle voci", "file": "il file indicato non c'è", "text": "la risposta è vuota"}


def said(ask, v):
    """An answer as the person reads it: sì or no, a choice's own words, a list's items."""
    if isinstance(v, list):
        return ", ".join(said(ask, x) for x in v) or "nessuna"
    s = str(v).lower() if isinstance(v, bool) else str(v)
    if s in ("true", "false") and ask.get("type") != "choice":
        return "sì" if s == "true" else "no"
    label = (ask.get("labels") or {}).get(s)
    # A label's head, before its explanation: "Manutenzione straordinaria (art. 3 c. 1 b): ..."
    return re.split(r" \(|: ", label)[0] if label else s.replace("_", " ")


# Whose a missing detail is, by its role (answers.json "people"; dictionary/fnsuap.yaml's Roles):
# no role, or a slug that isn't one, is the tecnico's or the studio's own, asked once and kept.
WHOSE = [(r"(c|cr|o|r|f\d*|ad\d*|a\d*|s|d|p)(#\d+)?:(immobile|locale\d*)\.", "dell'immobile"),
         (r"c(#\d+)?:", "del committente"), (r"cr(#\d+)?:", "di chi firma per il committente"),
         (r"o(#\d+)?:", "della società proprietaria"), (r"r(#\d+)?:", "del legale rappresentante della proprietà"),
         (r"f\d*(#\d+)?:", "delle imprese"), (r"ad\d*(#\d+)?:", "delle imprese degli altri tecnici"),
         (r"a\d*(#\d+)?:", "degli altri tecnici"), (r"s(#\d+)?:", "del progettista delle strutture"),
         (r"d(#\d+)?:", "del direttore dei lavori"), (r"p(#\d+)?:", "del progettista architettonico")]
OWN = "Suoi e dello studio (una volta sola: valgono per le prossime pratiche)"
WHOSE_ORDER = [OWN] + [w[:1].upper() + w[1:] for w in dict.fromkeys(w for _, w in WHOSE)]


def missing_label(where):
    """A missing detail as the message names it: the portal's label, without the section name
    every person's or the property's shares."""
    return re.sub(r"^(Scheda anagrafica|Localizzazione dell'intervento|Dati catastali): ", "", where)


def whose_of(field):
    for pattern, w in WHOSE:
        if re.match(pattern, field):
            return w[:1].upper() + w[1:]
    return OWN


def message(report, asks, held_need=None):
    """The one message pre-flight's questions, proposals and missing details make, in Italian,
    for Claude to send as it is: the questions numbered, each follow-up (`only_if`) under the
    question it hangs on (3.a, 3.a.1) so the tecnico can answer it in the same reply; the proposals
    as "Risposte che propongo" lines (each question as head() shortens it), a proposal per answer
    (`cases`) as "X se alla 3 risponde sì", with how many questions a change would add; a long
    choice's options one a line; then the details no document holds, by the portal's own section
    and box, and the files the sportello would refuse. Nothing from `if_changed`. A question the
    case needs with the proposals as they are (held_need) is asked as one, never only "if a
    proposal changes"."""
    questions, proposals = report["questions"], report["proposals"]
    order = [x["key"] for x in questions + proposals]
    items = {i["key"]: q["key"] for q in questions for i in q.get("items", [])}
    depth = {x["key"]: len(x.get("only_if", [])) for x in questions + proposals}
    asked = {q["key"] for q in questions}

    def parent(q):
        # The deepest question, checklist item or proposal this one hangs on that the message holds.
        up = [k for k in q.get("only_if", []) if k in items or k in depth and (k in asked or q["key"] not in (held_need or {}))]
        return max(up, key=lambda k: (depth.get(k, depth.get(items.get(k), 0) + 1), order.index(items.get(k, k))),
                   default=None)
    under = {}
    for q in questions:
        under.setdefault(parent(q), []).append(q)
    number, lines = {}, []

    listed = {}

    def text(q):
        a, out = asks.get(q["key"], {}), q["question"]
        if q.get("type") == "yes_no":
            out += " (sì/no)"
        elif q.get("type") == "choice" and not all(str(o).lower() in out.lower() for o in q.get("options", [])):
            heads = [said(a, o) for o in q.get("options", [])]
            if len(heads) <= 4 and len(" / ".join(heads)) <= 100:
                out += " (" + " / ".join(heads) + ")"
            else:  # one a line, under the question: a long list inline reads as a paragraph
                listed[q["key"]] = heads
        if q.get("how") and not q["how"].startswith("Lo stabilisce"):  # who decides: the tecnico reading it
            out += f" ({q['how']})"
        if q.get("error"):
            m = re.search(r"at most (\d+) characters", q["error"])
            out += f" (di nuovo: {'al massimo ' + m[1] + ' caratteri' if m else RETRY.get(q.get('type'), 'la risposta di prima non va')})"
        return out

    def tag(n, j, level):
        return f"{n}.{chr(97 + j) if level % 2 else j + 1}"

    def line(q, n, level):
        indent = "   " * level
        lines.append(f"{indent}{n}. {text(q)}")
        lines.extend(f"{indent}   – {h}" for h in listed.get(q["key"], []))
        number[q["key"]] = n
        for i in q.get("items", []):
            lines.append(f"{indent}   – {i['item']}" + (f" ({i['how']})" if i.get("how") else ""))
            number[i["key"]] = n
            for j, f in enumerate(under.get(i["key"], [])):
                line(f, tag(n, j, level + 1), level + 2)
        for j, f in enumerate(under.get(q["key"], [])):
            line(f, tag(n, j, level + 1), level + 1)
    for n, q in enumerate(under.get(None, []), 1):
        line(q, str(n), 0)
    blocks = [["Domande (risponda con il numero; alle lettere solo se servono):"] + lines] if lines else []

    def cond(combos):
        # One question's answers together ("alla 1 risponde a, b o c"), else each combination.
        ks = {k for c in combos for k in c}
        if len(ks) == 1:
            k = ks.pop()
            vs = [said(asks.get(k, {}), c[k]) for c in combos]
            return f"alla {number.get(k, '?')} risponde " + (", ".join(vs[:-1]) + " o " + vs[-1] if len(vs) > 1 else vs[0])
        return " o ".join(" e ".join(f"alla {number.get(k, '?')} risponde {said(asks.get(k, {}), v)}"
                                     for k, v in c.items()) for c in combos)

    def later(key):
        # What a changed proposal would add: the questions under it, and theirs, counted (asked
        # once it is changed, so the message stays short).
        return sum(1 + later(q["key"]) for q in under.get(key, []))
    use = []
    for p in proposals:
        a = asks.get(p["key"], {})
        if "cases" in p:
            by = {}
            for c in p["cases"]:
                by.setdefault(json.dumps(c["proposal"]), []).append(c["if"])
            what = "; ".join(f"{said(a, json.loads(v))} se {cond(cs)}" for v, cs in by.items())
            if p.get("otherwise"):
                what += f"; se {cond(p['otherwise'])}: me lo dica"
        else:
            what = said(a, p["proposal"])
        use.append(f"– {head(p['question'])} → {what}")
        n = later(p["key"])
        if n:
            more = "un'altra domanda" if n == 1 else f"altre {n} domande"
            use.append(f"   (se la cambia, le farò {more})")
    if use:
        blocks.append(["Risposte che propongo (scriva «ok», o mi dica cosa cambiare):"] + use)
    # The missing details on one line per person they belong to (WHOSE), the portal's labels
    # without the anagrafica's section name, which every person's shares.
    whose = {}
    for m in report["missing"]:
        if m["field"].startswith("*:"):
            continue  # nobody is the titolare yet: the skill seeds studio.json, never the tecnico
        expired = re.match(r"expired on (\S+)", m["why"])
        label = missing_label(m["for"])
        whose.setdefault(whose_of(m["field"]), []).append(
            label + (" (lo spazio sul portale è più corto)" if "at most" in m["why"]
                     else f": il documento è scaduto il {expired[1]}, ne serve uno valido" if expired
                     else "" if m["why"] == "empty in the vault" else ": da correggere"))
    if whose:
        blocks.append(["Mi mancano questi dati (non sono nei documenti):"]
                      + [f"– {w}: {', '.join(ls)}" for w, ls in sorted(whose.items(), key=lambda x: WHOSE_ORDER.index(x[0]))])
    # Each file once (a file in two slots is one fix); those the sportello refuses grouped by what
    # it refuses, its rules said once, with the fix; any other problem on its own line.
    fix, by, office, seen = [], {}, None, set()
    for x in report.get("files", []):
        if not x.get("problem"):
            continue
        name = Path(x["path"]).name if x.get("path") else x["for"]
        if x.get("refused"):
            office = x["office"]
            names = by.setdefault(tuple(c for c in REFUSED if c in x["refused"]), [])
            if name not in names:
                names.append(name)
        elif (name, x["problem"]) not in seen:
            seen.add((name, x["problem"]))
            fix.append(f"– {name} ({x['for']}): {x['problem']}")
    if by:
        codes = [c for c in REFUSED if any(c in k for k in by)]
        fix = [f"{office} rifiuta questi file:"] + \
              [f"– {', '.join(names)}: {', '.join(REFUSED[c][0] for c in k)}" for k, names in by.items()] + \
              ["Per ciascuno: " + "; ".join(REFUSED[c][1] for c in codes) + "."] + \
              (["Poi:"] + fix if fix else [])
    if fix:
        blocks.append(["Questi file vanno sistemati prima:"] + fix)
    return "\n\n".join("\n".join(b) for b in blocks)


def preflight(steps, values, made_up=False, after=False):
    """Everything a run needs, settled before any browser opens: why this case isn't
    supported, the questions still to ask, the vault fields missing or expired, the files
    to attach, and the person's own steps. ready: nothing is left before the run. A file the
    sportello would refuse (FILING) is a problem, or with made_up (a rehearsal's made-up data,
    never sent) only its `filing` and a warning, and no slot that takes only signed files is
    filled (phase). after: the second run's, after the declarations (phase)."""
    steps = expand(steps, values)
    later = [] if after else after_declarations(steps, values)
    unsigned = [f.get("label") for s in steps["sections"] for f in s["fields"]
                if made_up and signed_only(f) and applies(f, values)]
    steps = phase(steps, after, made_up)
    sportello = filing_rules(steps)
    order = check_asks(steps)
    asks = steps.get("asks", {})
    report = {"ready": False, "unsupported": [], "proposals": [], "questions": [], "missing": [], "files": [],
              "warnings": [], "yours": []}
    if any(r.startswith("t:") for _, t, _ in templates(steps) for r, _ in refs_in(t)):
        try:
            values.titolare
        except StepError as e:  # nobody is titolare yet: a missing field like any other
            report["missing"].append({"field": "*:ruolo.tipo", "why": str(e)})
            return report
    report["unsupported"], _, defects = refusals(steps, values)
    if defects:
        report["defects"] = defects
    report["unsupported"] += outside_comune(steps, values) + portal_changed(steps)
    # The steps files are the ones real users run, so their draft name carries no test marker;
    # a rehearsal's answers put it back, and a made-up draft never looks like a real one.
    if made_up and "descrizione" in asks and not str(values.raw("descrizione") or "").startswith(REHEARSAL_DRAFT):
        report["unsupported"].append(f"A rehearsal names its draft \"{REHEARSAL_DRAFT} - ...\" (answers "
                                     "`descrizione`), so no made-up draft looks like a real one.")
    if report["unsupported"]:
        report["message"] = refusal_text(report)
        return report
    need, groups, lists, pending = needed(steps, values), steps.get("groups", {}), {}, []
    for k in order:
        if k not in need:
            continue
        a, v = asks[k], values.raw(k)
        # A default answers it, unless it reads a vault field that's empty: then it's asked.
        if v is None and "default" in a and values.field("ask." + k) is not None:
            continue
        hangs = {"only_if": sorted(need[k])} if need[k] else {}
        if v is None and "propose" in a:
            # What the rules or the vault say it should be: the person confirms it, or says
            # otherwise, instead of answering from scratch. Never used until confirmed. One
            # that reads a question asked now is proposed in the same message, after the others
            # (conditional_proposals), so it doesn't take a second round.
            if any(r.startswith("ask.") and r[4:] in need and values.field(r) is None for r, _ in refs_in(a["propose"])):
                pending.append((k, hangs))
                continue
            proposal = values.render(a["propose"])
            if proposal is not None and not check_answer(a, proposal):
                report["proposals"].append({"key": k, "question": a["question"], "proposal": proposal}
                                           | {x: a[x] for x in ("why",) if x in a} | hangs)
                continue
        why = "not answered" if v is None else check_answer(a, v)
        if not why:
            continue
        if "group" in a:
            g = a["group"]
            if g not in lists:
                lists[g] = {"key": g, "type": "checklist", "question": values.render(groups[g]["question"])
                            or groups[g]["question"], "items": []}
                report["questions"].append(lists[g])
            lists[g]["items"].append({"key": k, "item": a["item"]} | {x: a[x] for x in ("how", "why") if x in a} | hangs)
            continue
        report["questions"].append({"key": k, "type": a["type"], "question": a["question"]}
                                   | {x: a[x] for x in ("options", "labels", "how", "why") if x in a} | hangs
                                   | ({"error": why} if v is not None else {}))
    report["proposals"] += conditional_proposals(pending, report, values, need)
    held_need = assumed_proposals(steps, values, report)
    if (steps.get("rules") or {}).get("table"):
        # While the table's first fact (what the works are) is asked, it is asked alone, as the
        # rules table's own questions are: which others matter depends on it, even one no field
        # hangs on it formally (a CILA's listed building, read by its Soprintendenza attachment
        # whatever the works, 2026-11-03).
        first = next(iter(rules.table(steps["rules"]["table"])["facts"]))
        if any(q["key"] == first for q in report["questions"]):
            report["questions"] = [q for q in report["questions"] if q["key"] == first]
    for g in groups:
        ticked = values.answers.get(g)
        members = [k for k, a in asks.items() if a.get("group") == g]
        if ticked is not None and (not isinstance(ticked, list) or set(ticked) - set(members)):
            if g not in lists:  # every item looked answered, but by a list that isn't one
                lists[g] = {"key": g, "type": "checklist", "question": values.render(groups[g]["question"])
                            or groups[g]["question"], "items": [{"key": k, "item": asks[k]["item"]} for k in members]}
                report["questions"].insert(0, lists[g])
            lists[g]["error"] = "answer with a list of the keys of the items that apply ([] for none)"
    missing, read = {}, set()
    for where, tmpl, f in templates(steps):
        if where in ("supports", "rules", "yours") or (f.get("optional") and tmpl == f.get("value")):
            continue
        if f and tmpl in (f.get("value"), f.get("when")) and "when" in f:
            # One false word is enough, whatever a later one would say (no other technicians:
            # whether the second is an employee is never asked), for the `when`'s own fields too
            # (a person client's citizenship, under a company client's branch).
            words = list(map(values.render, re.findall(r"\{\{.+?\}\}", f["when"])))
            if any(w is not None and not truthy(w) for w in words):
                continue  # this field isn't filled for this case
            if tmpl == f.get("value") and None in words:
                continue  # not known yet whether it is: the `when`'s own missing fields are asked
                # (born abroad: the birth province first, then the country)
        # Several fields read at once ({{a,b|f}}) take an empty one as "" (a company with no REA).
        several = {r.strip() for m in re.findall(r"\{\{([^}|]*,[^}|]*)", tmpl) for r in m.split(",")}
        for ref, filters in refs_in(tmpl):
            if ref.startswith("ask.") or ref in several:
                continue
            full = values.titolare + ":" + ref[2:] if ref.startswith("t:") else ref
            read.add(full.rsplit(".", 1)[0])
            if values.field(ref) is None and "empty" not in filters:
                # `id`: where the tecnico's answer goes, the role named as its person (c: -> bianchi:).
                role, _, rest = full.partition(":")
                person = (values.answers.get("people") or {}).get(role)
                missing.setdefault(full, {"field": full, "id": f"{person}:{rest}" if person else full,
                                          "why": "empty in the vault", "for": where})
    today = date.today().isoformat()
    for cat in sorted(read):
        end = values.category(cat).get(cat + ".data_scadenza")
        if end and end < today:
            missing.setdefault(cat + ".data_scadenza", {"field": cat + ".data_scadenza", "why": f"expired on {end}",
                                                       "for": cat})
    # A value longer than its box (a protocol "PG/2026/0666666" where the shop's form takes 10)
    # is asked again, or named as the vault field to shorten, before the run instead of by it.
    asked = {q["key"] for q in report["questions"]}
    for sec in steps["sections"]:
        for f in sec["fields"]:
            if not f.get("max") or "value" not in f or ("when" in f and not truthy(values.render(f["when"]) or "")):
                continue
            v = values.render(f["value"])
            if v is None or len(v) <= f["max"]:
                continue
            why = f"{sec['section']}: {f.get('label') or f.get('id')} takes at most {f['max']} characters"
            refs = refs_in(f["value"])
            if len(refs) == 1 and refs[0][0].startswith("ask.") and refs[0][0][4:] in asks:
                k = refs[0][0][4:]
                if k not in asked:
                    asked.add(k)
                    report["questions"].append({"key": k, "type": asks[k]["type"], "question": asks[k]["question"],
                                                "error": why})
            else:
                missing.setdefault(f["value"], {"field": f["value"], "why": why, "for": sec["section"]})
    # A vault value the form can't take (a ruolo with no Carica on the portal, for an architect
    # named in `people` who isn't the titolare) is named here, not met by the run as a crash.
    for sec in steps["sections"]:
        for f in sec["fields"]:
            if "value" not in f or any(r.startswith("ask.") for r, _ in refs_in(f["value"])):
                continue
            try:
                if "when" not in f or truthy(values.render(f["when"]) or ""):
                    values.render(f["value"])
            except ValueError as e:
                missing.setdefault(f["value"], {"field": f["value"], "why": f"{sec['section']}: {e}", "for": sec["section"]})
    report["missing"] = list(missing.values())
    for sec in steps["sections"]:
        for f in sec["fields"]:
            if f["kind"] == "file":
                if "when" in f and any(v is not None and not truthy(v) for v in
                                       map(values.render, re.findall(r"\{\{.+?\}\}", f["when"]))):
                    continue  # not attached in this case
                path = values.render(f.get("value", ""))
                p = Path(path).expanduser() if path else None
                entry = {"for": f"{sec['section']}: {f.get('label') or f.get('id')}", "path": path,
                         "exists": bool(p and p.is_file()), "bytes": p.stat().st_size if p and p.is_file() else None}
                if entry["exists"]:
                    takes = [t for t in f.get("accepts", "").lower().split(";") if t]
                    if entry["bytes"] > SLOT_MAX_BYTES:
                        entry["problem"] = (f"{entry['bytes'] / 1024 / 1024:.1f} MB: il portale accetta al massimo 9,77 MB "
                                            "per file. Lo comprima, o lo divida su più file (il «+» della casella)")
                    elif takes and not any(p.name.lower().endswith("." + t) for t in takes):
                        entry["problem"] = f"la casella accetta solo file {', '.join(takes)}"
                    raw = p.read_bytes()
                    signers = why = None
                    if "problem" not in entry:
                        pades = None if p.name.lower().endswith(".p7m") else pades_signature(raw)
                        if pades is None and p.name.lower().endswith(".p7m"):
                            signers, why = p7m_signers(p)
                        elif pades is not None:  # a PDF signed in itself (PAdES)
                            signers, why = signers_in([("DER", pades)], "la firma dentro il PDF non si legge: "
                                                      "lo firmi di nuovo con la sua firma digitale")
                    if why:
                        entry["problem"] = why
                    elif signers is not None:
                            # Counts and a yes/no, never the codici fiscali: Claude reads this report.
                            try:
                                cf = values.field("t:identity.codice_fiscale")
                            except StepError:
                                cf = None
                            entry["signers"] = len(signers)
                            if not signers:
                                report["warnings"].append(f"{entry['for']}: la firma non riporta un codice fiscale, "
                                                          "quindi non so dire chi ha firmato")
                            elif cf:
                                entry["signed_by_dichiarante"] = cf.upper() in signers
                                if not entry["signed_by_dichiarante"]:
                                    report["warnings"].append(
                                        f"{entry['for']}: firmato da altri ({len(signers)}), non dal dichiarante. "
                                        "Va bene se deve firmarlo un altro; altrimenti lo firmi di nuovo")
                    if sportello and "problem" not in entry:
                        refused = filing_problems(p, raw, sportello)
                        if refused and made_up:
                            entry["filing"] = [t for _, t in refused]
                        elif refused:
                            entry["problem"] = "; ".join(t for _, t in refused)
                            entry["refused"], entry["office"] = [c for c, _ in refused], sportello["office"]
                report["files"].append(entry)
    if made_up and any("filing" in x for x in report["files"]):
        # A rehearsal's made-up files: filled into a draft that is never sent.
        report["warnings"].append(f"made-up data: {sum('filing' in x for x in report['files'])} file(s) "
                                  f"{sportello['office']} would refuse (each one's `filing`): never send this draft")
    if made_up:
        # A box the portal checks against a real register (a company's codice fiscale in the
        # Registro Imprese): made-up data stops there, whatever the mapping (`made_up` in the dictionary).
        # Ready all the same (a real case passes there), but a batch of rehearsals skips it
        # (bench/rerun.py): one was sent and stopped there (2026-11-02).
        report["made_up_stops"] = []
        for sec in steps["sections"]:
            for f in sec["fields"]:
                if f.get("made_up") and truthy(values.render(f.get("when", "true")) or ""):
                    report["warnings"].append(f"made-up data: {sec['section']}: {f['made_up']}")
                    if f.get("made_up_stops"):
                        report["made_up_stops"].append(f"{sec['section']}: {f['made_up']}")
    if unsigned:
        report["warnings"].append(f"made-up data: {len(unsigned)} slot(s) that take only signed files left empty "
                                  "(the portal refuses a made-up signature on upload); a real case attaches them")
    report["pane_ok"] = sum(x["bytes"] or 0 for x in report["files"]) <= PAGE_FILES_LIMIT
    # Over the pane's limit, `page` has the person choose the files in the portal's page at the
    # start of the run (`picked`): the names they'll be asked for, once.
    if not report["pane_ok"]:
        report["pick"] = sorted({Path(x["path"]).name for x in report["files"] if x["exists"]})
    report["yours"] = yours_in_order([values.render(y) or y for y in steps.get("yours", [])],
                                     filing_yours(steps, sportello) + asked_yours(steps, values), later,
                                     apart(steps, values))
    if after:
        report["second_run"] = after_declarations(steps, values)
    report["ready"] = not (report["questions"] or report["proposals"] or report["missing"]
                           or any(not x["exists"] or x.get("problem") for x in report["files"] if x["path"]))
    text = message(report, asks, held_need)
    if text:
        # What comes after, in a line, so nothing at the end surprises them (`yours` has it all).
        end = ["All'inizio della compilazione le chiederò di scegliere i file del lavoro, una volta sola."] \
            if report.get("pick") else []
        end.append("Alla fine restano a Lei: le dichiarazioni, la firma, il pagamento e l'invio."
                   + (" Dopo le dichiarazioni mi darà i file firmati (la procura e gli altri): li allego con una "
                      "seconda compilazione." if later else ""))
        report["message"] = text + "\n\n" + "\n".join(end)
    return report


def p7m_signers(path):
    """The codici fiscali in the certificates a .p7m (CAdES, PKCS#7) carries, read with openssl:
    (set, None); (None, why) when it isn't a readable one; (None, None) with no openssl to ask.
    Who signed it is a name in a certificate, not proof the signature holds: the portal checks
    that, and so does the person's own signing software. This catches the wrong file, an
    unsigned copy renamed, and a signature by someone other than the dichiarante, before upload."""
    return signers_in(p7m_forms(Path(path).read_bytes()),
                      "il file .p7m non si legge: firmi di nuovo il documento con la sua firma digitale")


def p7m_forms(raw):
    """The ways a .p7m may be saved: DER, PEM, or the DER as base64 text (some tools)."""
    forms = [("DER", raw), ("PEM", raw)]
    try:
        forms.append(("DER", base64.b64decode(b"".join(raw.split()), validate=True)))
    except ValueError:
        pass
    return forms


def signers_in(forms, unreadable):
    """The codici fiscali in a PKCS#7 signature's certificates, as p7m_signers says."""
    openssl = shutil.which("openssl")
    if not openssl:
        return None, None
    for form, data in forms:
        try:
            r = subprocess.run([openssl, "pkcs7", "-inform", form, "-print_certs"], input=data,
                               capture_output=True, timeout=20)
        except subprocess.TimeoutExpired:
            continue
        if r.returncode == 0:
            subjects = [x for x in r.stdout.decode(errors="replace").splitlines() if x.startswith("subject=")]
            return {cf for x in subjects for cf in CF.findall(x)}, None
    return None, unreadable


def p7m_content(raw):
    """The document a .p7m wraps (its bytes), or None when openssl can't give it."""
    openssl = shutil.which("openssl")
    for form, data in p7m_forms(raw) if openssl else []:
        try:
            r = subprocess.run([openssl, "cms", "-verify", "-noverify", "-binary", "-inform", form], input=data,
                               capture_output=True, timeout=20)
        except subprocess.TimeoutExpired:
            continue
        if r.returncode == 0:
            return r.stdout
    return None


def pades_signature(raw):
    """The PKCS#7 a PDF's own signature (PAdES) carries: the /Contents of a dictionary with a
    /ByteRange, as DER without the zeros that pad its slot. None: the PDF isn't signed."""
    if b"/ByteRange" not in raw:
        return None
    blobs = [bytes.fromhex(m.group(1).decode()) for m in re.finditer(rb"/Contents\s*<([0-9A-Fa-f\s]{200,})>", raw)
             if len(b"".join(m.group(1).split())) % 2 == 0]
    for blob in sorted(blobs, key=len, reverse=True):
        if len(blob) > 2 and blob[0] == 0x30:  # a DER SEQUENCE: cut it to its own length
            n = blob[1]
            if n < 0x80:
                return blob[:2 + n]
            k = n & 0x7F
            return blob[:2 + k + int.from_bytes(blob[2:2 + k], "big")]
    return None


# PDF/A says so in the XMP metadata, which it keeps unfiltered: pdfaid:part="2" or <pdfaid:part>2<.
PDFA = re.compile(rb"pdfaid:part\s*(?:=\s*[\"']|>)\s*[1-4]")
# A name a SUE's back office takes: letters, digits and underscores, then the extensions.
PLAIN_NAME = re.compile(r"[A-Za-z0-9_]+(\.[A-Za-z0-9]+)+")
# What a sportello refuses before reading a pratica, by comune and sportello (its steps file's
# start: comune=F839&tipoSportello=E). Napoli's SUE since 6 July 2026, DD 501/2026 and its Linee
# Guida (§3 formats, §4 names and signatures, §7 payments, §8 irricevibilità), and the SUE's
# Costi page: a file not in PDF/A or over 20 MB (the portal's slot takes 9.77), a name with
# spaces, accents or other signs, an unsigned document, or diritti paid any other way make the
# pratica irricevibile. The run checks what it attaches; `yours` says it for the rest.
FILING = {
    ("F839", "E"): {
        "office": "Il SUE di Napoli (DD 501/2026)",
        "pdfa": True,
        "signed": True,
        "names": True,
        "yours": [
            "Il SUE di Napoli accetta solo file PDF/A, firmati digitalmente, sotto i 20 MB (immagini entro "
            "200 DPI), con nomi senza spazi, accenti o segni (Tavola01_inquadramento). Altrimenti la pratica è "
            "irricevibile (DD 501/2026). Vale anche per i file che allega Lei",
            "Prima dell'invio paghi e alleghi la ricevuta. Diritti: solo c/c postale 57060964 (Comune di "
            "Napoli Servizio Tesoreria Edilizia Privata). Sanzioni e contributo: bonifico all'IBAN "
            "IT95X0306903496100000046118. Causale: N1051_SUE – tipo pratica, identificativo, anno (o titolare "
            "e indirizzo). Pagata in altro modo, è irricevibile",
            # The portal's Firma e invio (InfoCamere's Manuale funzioni di compilazione pratica, pp. 55-62):
            # it opens only once every required attachment is in, each signature valid, so never on
            # made-up data; the runner stops before it.
            "In Firma e invio firma Lei, come procuratore: prima il PDF della pratica, poi la distinta. Online "
            "servono il dispositivo, il client di firma InfoCamere e il PIN. Offline: scarichi ogni file, lo "
            "firmi senza aprirlo né rinominarlo e lo ricarichi. Poi Invio: la ricevuta arriva in PEC in pochi "
            "minuti",
        ],
        # The building titles of DD 603/2025's forms (the CILA, the SCIA, the SCIA alternativa,
        # the permesso, their sanatorie and landscape combinations), whose attachment tables
        # mark these "sempre obbligatorio"; the zona A and frazionamento ones are the SUE's CILA
        # notes (23/06/2025), the Stato Comparativo the Linee Guida's §9 "nuovo obbligo".
        "titles": {
            "procedures": ["napoli/comune/cila-lavori-edilizi", "napoli/comune/scia-edilizia",
                           "napoli/comune/scia-alternativa-pdc", "napoli/comune/permesso-di-costruire",
                           "napoli/comune/scia-in-sanatoria", "napoli/comune/permesso-in-sanatoria"],
            "yours": [
                "Napoli chiede sempre due dichiarazioni (DD 603/2025): l'Allegato A Nuovo Programma 100 (il "
                "titolare su quanto deve al Comune) e il Modello DP (il compenso pagatoLe, L.R. Campania 59/2018). "
                "Claude le compila. L'Allegato A lo firma il committente, il DP entrambi, digitalmente. Vanno con "
                "la procura nella seconda compilazione",
                "Su un edificio esistente gli elaborati comprendono lo Stato Comparativo: attuale e progetto "
                "sovrapposti, demolizioni in giallo, nuove opere in rosso (verde e blu le opere abbandonate in "
                "corso d'opera), il resto nero su bianco (DD 501/2026 Linee Guida §9)",
                "Se l'edificio è nel centro storico (zona A della Variante generale): alleghi l'attestazione, "
                "firmata ai sensi dell'art. 481 c.p., che l'unità corrisponde al suo tipo edilizio nelle Norme "
                "di attuazione (art. 63 c. 4)",
                "Se i lavori dividono l'unità (frazionamento, art. 22 c. 2 della Variante generale): serve l'atto "
                "d'obbligo a non frazionarla ancora, trascritto in Conservatoria. Va con questa pratica se i "
                "lavori sono già eseguiti, altrimenti con la fine lavori",
            ],
        },
    },
}


def yours_in_order(own, notes, later, apart):
    """The person's steps in the order they take them: the steps file's own, the sportello's and the
    answers' notes, the second run (after the declarations), signing and sending last, then what is
    filed apart. The sportello's own Firma e invio step stands for the steps file's shorter one."""
    sends = [y for y in own + notes if "Firma e invio" in y]
    if any(y in notes for y in sends):
        sends = [y for y in sends if y in notes]
    out = [y for y in own + notes if "Firma e invio" not in y]
    if later:
        out.append(f"Dopo le dichiarazioni, in Allega documenti, scarichi i file che il portale crea solo allora: "
                   f"{'; '.join(dict.fromkeys(later))}. Faccia firmare la procura al committente e firmi "
                   "digitalmente ogni file (.p7m). Poi li dia a Claude: li allega con una seconda compilazione")
    return out + sends + apart


# The comune each sportello serves, by the Belfiore code in a steps file's start.
SPORTELLO_COMUNE = {"F839": "Napoli"}


def outside_comune(steps, values):
    """A property the job names (the client's immobile, the business's locale) outside the comune
    whose sportello the steps file files at: refused, since every steps file files at one comune.
    The comune isn't named: the message reaches Claude."""
    from urllib.parse import parse_qs, urlparse
    code = parse_qs(urlparse(steps.get("start", "")).query).get("comune", [""])[0]
    comune = SPORTELLO_COMUNE.get(code)
    if not comune:
        return []
    def plain(s):
        s = unicodedata.normalize("NFKD", str(s))
        return " ".join("".join(c for c in s if not unicodedata.combining(c)).lower().split())
    for ref in ("c:immobile.comune", "locale.comune", "locale2.comune"):
        try:
            v = values.field(ref)
        except StepError:
            v = None
        if v and plain(v) != plain(comune):
            return [f"L'immobile è fuori dal Comune di {comune}. Portale SUE prepara solo le pratiche del Comune "
                    f"di {comune} (Campania), sui suoi sportelli: per un altro comune non c'è nulla di "
                    "automatico, e non preparo niente."]
    return []


def filing_rules(steps):
    """The rules of the sportello a steps file files at, or None."""
    from urllib.parse import parse_qs, urlparse
    q = parse_qs(urlparse(steps.get("start", "")).query)
    return FILING.get((q.get("comune", [""])[0], q.get("tipoSportello", [""])[0]))


def filing_yours(steps, sportello):
    """The person's steps the sportello asks of every pratica, and of the building titles for one
    that is one (its procedure, or its `rules:` main for a title filed with its landscape one)."""
    if not sportello:
        return []
    titles = sportello.get("titles", {})
    procedure = (steps.get("rules") or {}).get("main", steps.get("procedure"))
    return sportello["yours"] + (titles.get("yours", []) if procedure in titles.get("procedures", []) else [])


def filing_problems(p, raw, rules):
    """Why the sportello would refuse this file, as (code, text): its name, its format, its
    signature. A .p7m is signed (p7m_signers reads it); its content must be PDF/A. Says what it
    couldn't check. The codes (REFUSED) let the message say each rule once for all the files."""
    out = []
    if rules.get("names") and not PLAIN_NAME.fullmatch(p.name):
        out.append(("name", f"{rules['office']} rifiuta questo nome: solo lettere, cifre e trattini bassi "
                            "(Tavola01_inquadramento.pdf), senza spazi, accenti o altri segni"))
    signed_p7m = p.name.lower().endswith(".p7m")
    doc = p7m_content(raw) if signed_p7m else raw
    if rules.get("pdfa"):
        if doc is None:
            out.append(("p7m", "non riesco a leggere il documento dentro il .p7m per controllare che sia PDF/A"))
        elif not doc.startswith(b"%PDF"):
            out.append(("notpdf", f"{rules['office']} accetta solo file PDF/A: questo non è un PDF"))
        elif not PDFA.search(doc):
            out.append(("pdfa", f"{rules['office']} accetta solo file PDF/A: questo PDF non è PDF/A "
                                "(lo esporti di nuovo come PDF/A)"))
    if rules.get("signed") and not signed_p7m and pades_signature(raw) is None:
        out.append(("signed", f"{rules['office']} accetta solo file firmati digitalmente: lo firmi con la sua "
                              "firma digitale (un .p7m, o la firma dentro il PDF)"))
    return out


# What each refusal code says in the message, once for all its files: (what's wrong, the fix).
REFUSED = {"notpdf": ("non è un PDF", "lo converta in PDF/A"),
           "pdfa": ("non è PDF/A", "lo esporti come PDF/A"),
           "p7m": ("non riesco a leggere il PDF dentro il .p7m", "controlli che il .p7m contenga un PDF/A"),
           "signed": ("non è firmato digitalmente", "lo firmi digitalmente (un .p7m, o la firma dentro il PDF)"),
           "name": ("il nome ha spazi, accenti o segni",
                    "lo rinomini con sole lettere, cifre e trattini bassi (Tavola01_inquadramento.pdf)")}


def attachment(path):
    """A file as run.js carries it to inpage.js: its bytes."""
    p = Path(path).expanduser()
    kind = FILE_TYPES.get(p.suffix.lower()) or mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    return {"name": p.name, "type": kind, "b64": base64.b64encode(p.read_bytes()).decode()}




def bundle(out, path, files):
    """runner.js, steps.js and run.js as one file the person picks once in a box on the portal's page
    (pick.js), for a pane that lacks the runner: it is 80 KB, and the pane takes about 40 KB a call
    (2026-11-04), and a long script copied through the conversation can arrive garbled (2026-10-30). The
    box checks the file by sha256 and evaluates it once; it returns what run.js does ("waiting for the
    code", "waiting for the files", "started"). bench/rerun.py does the same for a batch."""
    text = "\n;\n".join(files[k] for k in ("runner.js", "steps.js", "run.js"))
    path.write_text(text)
    sha = hashlib.sha256(text.encode()).hexdigest()
    (out / "pick.js").write_text(f"""document.querySelectorAll("#pv-pick").forEach((x) => x.remove());
const box = document.createElement("div"); box.id = "pv-pick";
box.style.cssText = "position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:2147483647;background:#fff;border:3px solid #1a4fd6;padding:16px 20px;font:16px sans-serif;box-shadow:0 4px 18px rgba(0,0,0,.3);border-radius:8px;max-width:520px";
box.innerHTML = '<b>Scelga il file <code>{path.name}</code> (una volta sola)</b><br><input type="file" accept=".js" style="margin-top:10px"><div style="margin-top:8px;color:#444"></div>';
document.body.appendChild(box);
const [input, msg] = [box.querySelector("input"), box.querySelector("div")];
input.addEventListener("change", async () => {{
  const text = await input.files[0].text();
  const got = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text)))).map((b) => b.toString(16).padStart(2, "0")).join("");
  if (got !== "{sha}") {{ msg.textContent = "Non è il file giusto: non ho caricato nulla."; return; }}
  input.disabled = true;
  try {{ window.pvPicked = String((0, eval)(text)); msg.textContent = "Caricato."; setTimeout(() => box.remove(), 3000); }}
  catch (e) {{ window.pvPicked = "error " + e.message; msg.textContent = window.pvPicked; }}
}});
"box shown: the person picks {path.name}, then poll __pv.wait()"
""")


def resumption(report, fixes=None):
    """How run.js picks up a stopped run: the draft it stopped on, the section it stopped
    in (redone, with any fixes), and what the earlier sections typed, for the fresh load.
    report is report.json plus `kept` from private/kept.json: a report has no values."""
    at = report.get("at") or {}
    if not report.get("url") or not at:
        raise StepError("this report has no place to resume from")
    if at.get("phase") == "section" and at.get("index") and not report.get("kept"):
        raise StepError("no record of what the earlier sections typed (private/kept.json next to report.json): "
                        "resume in the pane's tab with __pv.resume(), or run again from the start")
    return {"url": report["url"], "from": {("section" if at.get("phase") == "section" else "wizard"): at["index"]},
            "kept": report.get("kept", []), "fixes": fixes or []}


def page_scripts(steps, values, files_limit=PAGE_FILES_LIMIT, resume=None, code=None, pick=True):
    """install.js (inpage.js and the steps, no personal data) and run.js (the values)."""
    files = page_files(steps, values, files_limit, resume, code, pick)
    return files["install.js"], files["run.js"]


def page_files(steps, values, files_limit=PAGE_FILES_LIMIT, resume=None, code=None, pick=True):
    """Every file `run.py page` writes, by name: install.js is runner.js and steps.js, and
    check.js says which of those two the pane's storage lacks."""
    return page_bundle(steps, values, files_limit, resume, code, pick)[0]


# --- sealing run.js ---------------------------------------------------------------
# In the pane Claude writes every byte of the run.js call, so the person's values would pass
# through the conversation. With a code, run.js carries them sealed instead, and the code
# reaches the page through the person, not through Claude: shown in a window Claude has no
# output from (show_code) and typed into a box the runner opens (inpage.js, askCode).
# The code is 15 characters of Crockford base32 (75 bits), stretched by PBKDF2-HMAC-SHA256
# and split into an encryption and a MAC key; the plaintext is XORed with an HMAC-SHA256
# keystream and the result authenticated, encrypt-then-MAC. Only the standard library and
# WebCrypto's PBKDF2 and HMAC, which every page has, so there is nothing to install.
SEAL_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
SEAL_CODE_LENGTH = 15
SEAL_ITERATIONS = 200_000


def new_code():
    return "".join(secrets.choice(SEAL_ALPHABET) for _ in range(SEAL_CODE_LENGTH))


def pretty_code(code):
    return "-".join(code[i:i + 5] for i in range(0, len(code), 5))


def seal_keys(code, salt, iterations):
    master = hashlib.pbkdf2_hmac("sha256", code.encode(), salt, iterations, 32)
    return hmac.new(master, b"pv-enc", "sha256").digest(), hmac.new(master, b"pv-mac", "sha256").digest()


def seal_stream(key, nonce, n):
    out = b"".join(hmac.new(key, nonce + i.to_bytes(4, "big"), "sha256").digest() for i in range((n + 31) // 32))
    return out[:n]


def seal(plain, code, iterations=SEAL_ITERATIONS):
    """plain (bytes) sealed under code: {v, i, s, n, c, t}, each binary part in base64."""
    salt, nonce = os.urandom(16), os.urandom(16)
    enc, mac = seal_keys(code, salt, iterations)
    ct = (int.from_bytes(plain, "big") ^ int.from_bytes(seal_stream(enc, nonce, len(plain)), "big")).to_bytes(len(plain), "big")
    tag = hmac.new(mac, b"pv1" + iterations.to_bytes(4, "big") + salt + nonce + ct, "sha256").digest()
    b = lambda x: base64.b64encode(x).decode()
    return {"v": 1, "i": iterations, "s": b(salt), "n": b(nonce), "c": b(ct), "t": b(tag)}


def unseal(sealed, code):
    """The inverse of seal, for tests: raises StepError for a wrong code."""
    d = lambda k: base64.b64decode(sealed[k])
    enc, mac = seal_keys(code, d("s"), sealed["i"])
    ct = d("c")
    want = hmac.new(mac, b"pv1" + sealed["i"].to_bytes(4, "big") + d("s") + d("n") + ct, "sha256").digest()
    if not hmac.compare_digest(want, d("t")):
        raise StepError("that code doesn't open it")
    return (int.from_bytes(ct, "big") ^ int.from_bytes(seal_stream(enc, d("n"), len(ct)), "big")).to_bytes(len(ct), "big")


def show_code(code, give_up=None):
    """The code in a window of its own, for the person: it must not go through the output of
    anything Claude runs, so it is not printed, not in a file, and not in the child's arguments
    or environment (a program's arguments can be listed): the child reads it on stdin. The
    window stays until they close it, so run.py can return. give_up (tests): seconds."""
    text = (f"Scriva questo codice nel riquadro che compare sulla pagina del portale:\n\n{pretty_code(code)}\n\n"
            "Tenga aperta questa finestra fino alla fine della compilazione. Non lo dica a nessuno, "
            "nemmeno a Claude.")
    if sys.platform == "darwin":
        script = (f'display dialog {json.dumps(text)} with title "Portale SUE" buttons {{"Fatto"}} default button "Fatto"'
                  + (f" giving up after {give_up}" if give_up else ""))
        cmd, feed = ["osascript", "-"], script
    elif sys.platform == "win32":
        cmd = [sys.executable, "-I", "-c",
               "import ctypes, sys; ctypes.windll.user32.MessageBoxW(0, sys.stdin.read(), 'Portale SUE', 0x40 | 0x40000)"]
        feed = text
    elif shutil.which("zenity"):
        cmd, feed = ["zenity", "--text-info", "--title=Portale SUE", "--width=420", "--height=200"], text
    else:
        raise StepError("no way to show the code outside this conversation here: use `run` (its window "
                        "needs no code), or --plain if the values may pass through the conversation")
    child = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             text=True, start_new_session=True)
    child.stdin.write(feed)
    child.stdin.close()
    for _ in range(10):  # a window that can't open (no desktop session) fails at once
        time.sleep(0.1)
        if child.poll() is not None:
            break
    if child.poll() not in (None, 0):
        raise StepError("the code window didn't open: use `run`, or --plain if the values may pass through the conversation")
    return child


def page_bundle(steps, values, files_limit=PAGE_FILES_LIMIT, resume=None, code=None, pick=True):
    """page_files, and what runner.js and steps.js leave in the pane's localStorage. code: seal the values under it (see above); None carries them in the clear. pick: files
    over files_limit are chosen by the person in the page (`picked`); False refuses them (a
    batch has no one to pick for each run)."""
    expanded = expand(steps, values)
    blocks, steps = expanded is not steps, expanded
    require_supported(steps, values)
    plan(steps, values)  # stops on a missing required value
    skeleton = {
        "start": steps["start"], "logged_in": steps["logged_in"],
        "wizard": [{k: v for k, v in w.items() if k != "fill"} | (
            {"fill": {"css": w["fill"]["css"]}} if "fill" in w else {}) for w in steps["wizard"]],
        "sections": [{"section": s["section"], "open": s.get("open", True)}
                     | ({"save": s["save"]} if "save" in s else {})
                     | ({"theirs": s["theirs"]} if "theirs" in s else {})
                     | ({"go": s["go"]} if "go" in s else {})
                     | ({"step": s["step"]} if "step" in s else {})
                     # Only these keys reach the page: a new one inpage.js reads goes here too
                     # (`last` didn't, 2026-11-04, and the run ticked the first group's radio).
                     | {"fields": [{k: f[k] for k in ("id", "css", "kind", "label", "anchor", "block", "nth", "last", "describe", "if_present") if k in f}
                                   for f in s["fields"]]}
                     for s in steps["sections"]],
        "forbidden": FORBIDDEN.pattern, "declarations": DECLARATIONS.pattern,
        "label_js": LABEL_JS,
    } | ({"preview_url": steps["preview_url"]} if "preview_url" in steps else {})

    def value(f):
        """False when its `when` is false, true for a tick, a file's bytes, else the value."""
        if "when" in f and not truthy(values.render(f["when"]) or ""):
            return False
        if "value" not in f:
            return True
        v = values.render(f["value"])
        if f["kind"] == "file" and v:
            return attachment(v)
        return v

    # The second run (after the declarations) opens the draft by its name and attaches the signed
    # files alone: it carries no other value, and its files are always picked in the page, so it
    # needs no code (one code a pratica) and nothing of the person's passes through the conversation.
    second = bool(resume and resume.get("reopen"))
    start = (resume or {}).get("from", {}).get("section", 0) if second else 0
    vals = {
        "wizard": [values.render(w["fill"]["value"]) if "fill" in w else None for w in steps["wizard"]],
        "sections": [[value(f) if i >= start else None for f in s["fields"]] for i, s in enumerate(steps["sections"])],
    }
    if second:
        files_limit, pick = 0, True
    if files_limit is not None:
        files = [v for s in vals["sections"] for v in s if isinstance(v, dict) and "b64" in v]
        size = sum(len(f["b64"]) * 3 // 4 for f in files)
        if size > files_limit and not pick:
            raise StepError(f"the attachments come to {size // 1024} KB, more than the {files_limit // 1024} KB "
                            "run.js can carry in the pane: let the person pick them in the page, or use `run`")
        if size > files_limit:
            # Too big to carry: every file the run attaches is chosen in the page, so the person
            # picks them all once, from the job's folder, and none is in the conversation.
            for f in files:
                data = base64.b64decode(f.pop("b64"))
                f.update(size=len(data), sha256=hashlib.sha256(data).hexdigest(), picked=True)
    proc = steps["procedure"]
    if blocks:
        # Its "+" blocks as this case counts them: a case with other counts has other steps, so
        # they are stored apart in the pane (the same counts, the same key).
        proc += "#" + hashlib.sha256(json.dumps(skeleton["sections"], sort_keys=True).encode()).hexdigest()[:8]
    runner_js, steps_js, stored = pane_parts(proc, skeleton)
    load = "if (!window.__pv) (0, eval)(localStorage.getItem('pv-runner'));\n"
    if code:
        plain = json.dumps({"vals": vals, "resume": resume or {}}, ensure_ascii=False, separators=(",", ":"))
        run_js = load + f"__pv.startSealed({json.dumps(proc)}, {json.dumps(seal(plain.encode(), code), separators=(',', ':'))})\n"
    else:
        run_js = (load + f"__pv.start({json.dumps(proc)}, {json.dumps(vals, ensure_ascii=False, separators=(',', ':'))}"
                  + (f", {json.dumps(resume, ensure_ascii=False, separators=(',', ':'))}" if resume else "") + ")\n")
    origin = re.match(r"https?://[^/]+", steps["logged_in"])[0]
    return {"install.js": runner_js + steps_js + "'installed'\n", "runner.js": runner_js, "steps.js": steps_js,
            "check.js": check_script(stored, origin), "run.js": run_js}, stored


def pane_parts(proc, skeleton):
    """runner.js (inpage.js) and steps.js (the steps, no personal data) as install.js holds
    them, and what each leaves in the pane's localStorage, for check.js."""
    runner = Path(__file__).with_name("inpage.js").read_text()
    steps_json = json.dumps(skeleton, ensure_ascii=False, separators=(',', ':'))
    # A function's source is its text, so neither part needs escaping into a string.
    # The runner a page already loaded stays loaded: drop it, so run.js loads this one.
    runner_js = f"localStorage.setItem('pv-runner', '(' + function () {{\n{runner}}} + ')()');\ndelete window.__pv;\n"
    steps_js = f"localStorage.setItem({json.dumps('pv-steps:' + proc)}, JSON.stringify({steps_json}));\n"
    # JSON.stringify of that literal gives back these same bytes; the runner is stored as its source.
    stored = {"pv-runner": "(function () {\n" + runner + "})()", "pv-steps:" + proc: steps_json}
    return runner_js, steps_js, stored


def patch_script(key, old_json, new_json, fallback):
    """A steps script that sends only what changed: the new steps with each section the old ones
    have the same left out, taken from what the pane holds (the old steps, if it holds them), and
    stored only if the whole comes out byte for byte (sha256). Else it says to send `fallback`.
    2026-11-04: a 43 KB and a 90 KB steps file, one section changed in each, went this way, where
    pasting a long script can garble it. None when the two can't be patched section by section."""
    old, new = json.loads(old_json), json.loads(new_json)
    if old_json == new_json or len(old.get("sections", [])) != len(new.get("sections", [])):
        return None
    same = lambda i: json.dumps(old["sections"][i], ensure_ascii=False, separators=(",", ":")) == \
        json.dumps(new["sections"][i], ensure_ascii=False, separators=(",", ":"))
    lite = {**new, "sections": [None if same(i) else s for i, s in enumerate(new["sections"])]}
    want = hashlib.sha256(new_json.encode()).hexdigest()
    return ("(async () => {\n"
            "  const sha = async (s) => Array.from(new Uint8Array(await crypto.subtle.digest(\"SHA-256\", new TextEncoder().encode(s)))).map((b) => b.toString(16).padStart(2, \"0\")).join(\"\");\n"
            f"  const k = {json.dumps(key)}, cur = localStorage.getItem(k);\n"
            f"  if (cur !== null && await sha(cur) === {json.dumps(want)}) return 'stored already';\n"
            "  let s = null; try { s = JSON.parse(cur); } catch (e) {}\n"
            f"  const n = {json.dumps(lite, ensure_ascii=False, separators=(',', ':'))};\n"
            f"  if (!s || !Array.isArray(s.sections) || s.sections.length !== n.sections.length) return {json.dumps('send ' + fallback)};\n"
            "  n.sections = n.sections.map((x, i) => x === null ? s.sections[i] : x);\n"
            "  const txt = JSON.stringify(n);\n"
            f"  if (await sha(txt) !== {json.dumps(want)}) return {json.dumps('the pane holds other steps: send ' + fallback)};\n"
            "  localStorage.setItem(k, txt);\n"
            "  return 'installed';\n"
            "})()\n")


def check_script(stored, origin, files=None, then="run.js"):
    """check.js: on the portal's page, which of runner.js and the steps the pane must still run
    (its localStorage holds something else), and whether the page is on the portal's origin,
    the only one whose storage has them. The rest of install.js need not be sent again.
    files: the file that writes each key (default runner.js, steps.js); then: what follows."""
    want = {k: hashlib.sha256(v.encode()).hexdigest() for k, v in stored.items()}
    files = files or {k: "runner.js" if k == "pv-runner" else "steps.js" for k in stored}
    return ("(async () => {\n"
            "  const sha = async (s) => s === null ? null : Array.from(new Uint8Array(await crypto.subtle.digest(\"SHA-256\", new TextEncoder().encode(s)))).map((b) => b.toString(16).padStart(2, \"0\")).join(\"\");\n"
            f"  const want = {json.dumps(want)};\n"
            "  const stale = [];\n"
            "  for (const [k, v] of Object.entries(want)) if (await sha(localStorage.getItem(k)) !== v) stale.push(k);\n"
            f"  if (location.origin !== {json.dumps(origin)}) return {json.dumps('go to ' + origin + ' first: its storage holds the runner')};\n"
            f"  const files = {json.dumps(files)};\n"
            f"  return \"run \" + stale.map((k) => files[k]).concat([{json.dumps(then)}]).join(\", then \");\n"
            "})()\n")




# --- browser ----------------------------------------------------------------------

LABEL_JS = """(el) => {
  const texts = [];
  const t = el.closest('[title]'); if (t) texts.push(t.title);
  const td = el.closest('td'); if (td) texts.push(td.innerText);
  // A dynaForm puts a label in the row above, in the same column, or to the left.
  for (let tr = td && td.parentElement.previousElementSibling; tr; tr = tr.previousElementSibling) {
    const c = tr.cells[td.cellIndex];
    if (c && c.innerText.trim()) { texts.push(c.innerText); break; }
  }
  for (let c = td && td.previousElementSibling; c; c = c.previousElementSibling) {
    if (c.innerText.trim()) { texts.push(c.innerText); break; }
  }
  const labels = [...document.querySelectorAll('.labelDynaFormControl, label')];
  const before = labels.filter(l => l.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING && !l.contains(el));
  if (before.length) texts.push(before[before.length - 1].innerText);
  return texts.map(s => (s || '').replace(/\\s+/g, ' ').trim());
}"""


def drift(out, steps, resume):
    """What a recovered run changed, for the steps file and the map: never silent."""
    if resume and resume["fixes"]:
        (out / "drift.json").write_text(json.dumps({"procedure": steps["procedure"], "fixes": resume["fixes"],
                                                    "draft": resume["url"]}, indent=2, ensure_ascii=False))


def review_shown(steps, values):
    """What the review page shows besides the run: each value, the choices made in the person's
    name (DECIDED), and the person's own steps."""
    steps = expand(steps, values)
    rows = plan(steps, values)
    decisions = {}
    for v in rows:
        if DECIDED.search(v["section"]):
            what = v["label"] or v["id"]
            decisions.setdefault(v["section"], []).append(what if v["value"] is None else f"{what}: {v['value']}")
    return {"title": steps.get("title"), "yours": [values.render(y) for y in steps.get("yours", [])] + asked_yours(steps, values) + apart(steps, values),
            "decisions": [{"section": s, "choices": c} for s, c in decisions.items()],
            "values": [{"section": v["section"], "label": v["label"] or v["id"],
                        "value": "chosen" if v["value"] is None
                        else "attached: " + Path(v["value"]).name if v["kind"] == "file" else v["value"]}
                       for v in rows]}


def private_dir(out):
    folder = out / "private"
    folder.mkdir(mode=0o700, exist_ok=True)
    folder.chmod(0o700)
    return folder


def private(out, shown, held=None):
    """What no report holds: what each section typed (to resume), what a failed read-back wanted
    and found, every value for the review page, and the declarations' own text. A folder only the
    person reads; the skill tells Claude to send the review page and never to open these."""
    folder = private_dir(out)
    parts = [("shown", shown)]
    if held is not None:  # a run in the pane has only shown: __pv.held() stays in its tab
        parts += [("kept", held.get("kept", [])), ("held", held.get("details", []))]
        # A resume past the declarations reads none: it must not blank what an earlier run kept.
        if held.get("declarations") or not (folder / "declarations.json").exists():
            parts.append(("declarations", held.get("declarations", [])))
    for name, data in parts:
        f = folder / f"{name}.json"
        f.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        f.chmod(0o600)


def capture_preview(page, folder):
    """The portal's own PDF of the draft, which the filled run fetched in the person's logged-in
    browser (__pv.previewPdf), kept as folder/anteprima.pdf for the review page: what the person
    declares is the portal's rendering, not our list of values. None of it passes through Claude.
    Returns (True, "") or (False, why); a missing preview never stops a filled draft."""
    try:
        b64 = page.evaluate("__pv.previewPdf()")
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e).splitlines()[0][:160]}"
    if not b64:
        return False, "the run found no preview to keep"
    body = base64.b64decode(b64)
    if not body.startswith(b"%PDF-"):
        return False, "what the portal gave isn't a PDF"
    f = folder / "anteprima.pdf"
    f.write_bytes(body)
    f.chmod(0o600)
    return True, ""


def run(steps, values, out, cdp=None, profile=None, close=False, resume=None):
    """inpage.js in a Playwright window: the runner the Claude browser pane uses, without
    the pane's 45 s call limit and slowed timers. A window behind others keeps full speed
    with no call of ours: Playwright turns on focus emulation for each page it drives
    (--cdp too) and launches Chromium with background throttling off."""
    steps = expand(steps, values)
    from playwright.sync_api import sync_playwright
    # page.evaluate runs run.js here, not through the conversation, so files of any size.
    install, run_js = page_scripts(steps, values, files_limit=None, resume=resume)
    out.mkdir(parents=True, exist_ok=True)
    drift(out, steps, resume)
    shown = review_shown(steps, values)
    report = {"procedure": steps["procedure"], "result": "stopped"}
    held = {}
    with sync_playwright() as pw:
        if cdp:
            ctx = pw.chromium.connect_over_cdp(cdp).contexts[0]
        else:
            try:
                ctx = pw.chromium.launch_persistent_context(str(profile), headless=False, no_viewport=True)
            except Exception as e:
                if "already in use" not in str(e) and "existing browser session" not in str(e):
                    raise
                # A window an earlier run left open still has the profile, and with it the login.
                raise StepError(f"another Chrome for Testing window is using {profile}: close it (⌘Q) and run "
                                "again, or pass --profile with another folder (and log in there again)") from None
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            page.goto(steps["logged_in"] if resume else steps["start"])  # a resume mustn't start a new pratica
            if not page.url.startswith(steps["logged_in"]):
                print("Log in with SPID in the Playwright window; the run starts when you're in.", flush=True)
                page.wait_for_url(lambda u: u.startswith(steps["logged_in"]), timeout=15 * 60 * 1000)
            page.wait_for_load_state()
            page.evaluate(install)
            page.evaluate(run_js)
            wizard_shown, sections_shown = False, 0
            while True:
                report = page.evaluate("__pv.wait(5000)")
                if not wizard_shown and report.get("wizard_seconds") is not None:
                    print(f"  wizard: {report['wizard_seconds']} s", flush=True)
                    wizard_shown = True
                for sec in report["sections"][sections_shown:]:
                    print(f"  {sec['section']}: {sec['seconds']} s", flush=True)
                sections_shown = len(report["sections"])
                if report["result"] != "running":
                    if report.get("verify_seconds") is not None:
                        print(f"  fresh load of the draft, every value read again: {report['verify_seconds']} s",
                              flush=True)
                    break
        except Exception as e:
            report["result"] = "stopped"
            report["error"] = f"{type(e).__name__}: {e}"
        finally:
            if not page.is_closed():
                try:
                    held = page.evaluate("__pv.held()")
                except Exception:
                    pass
            if report.get("result") == "filled" and not page.is_closed():
                ok, why = capture_preview(page, private_dir(out))
                report["preview_pdf"] = ok
                if why:
                    report["preview_note"] = report.get("preview_note") or why
            # report.json holds no value, so Claude may read it; what the person needs is
            # kept apart and goes to them, never into the conversation.
            (out / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
            private(out, shown, held)
            (out / "review.html").write_text(review.portal_review(report | shown | {"details": held.get("details", [])}, out),
                                             encoding="utf-8")
            (out / "review.html").chmod(0o600)
            print(f"review: {out / 'review.html'}", flush=True)
            print(json.dumps({k: report.get(k) for k in ("result", "error", "wizard_seconds", "total_seconds")}),
                  flush=True)
            if not close and not page.is_closed():
                if report["result"] == "filled":
                    page.evaluate("__pv.open()")
                print("Left open for you: tick the declarations, attach what's left, sign and pay yourself. "
                      "Close the window when done.", flush=True)
                page.wait_for_event("close", timeout=0)
            try:
                ctx.close()
            except Exception:
                pass
    return 0 if report["result"] == "filled" else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("command", choices=["preflight", "plan", "page", "run", "scope"])
    ap.add_argument("--steps", required=True, type=Path)
    ap.add_argument("--answers", type=Path, help="the asks' answers as JSON (none yet: preflight lists them all)")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--server", type=Path)
    src.add_argument("--vault-dir")
    src.add_argument("--values", action="append", help="- or a file: pvault get's JSON of the fields the steps read; "
                     "again for another (intake.py's private values.json): the first to hold a field gives it")
    ap.add_argument("--token", default="prepare", help="--server: which of its tokens")
    ap.add_argument("--keychain", help="--vault-dir: the Keychain service of the token")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--cdp")
    ap.add_argument("--profile", type=Path, default=Path.home() / ".cache/pratica-portal/profile")
    ap.add_argument("--close", action="store_true")
    ap.add_argument("--plain", action="store_true", help="page: run.js carries the values in the clear, through the conversation")
    ap.add_argument("--made-up", action="store_true", help="made-up files, never sent: preflight takes the sportello's "
                    "refusals as warnings, and no slot that takes only signed files is filled")
    ap.add_argument("--after-declarations", action="store_true", help="the second run, once the person has ticked the "
                    "declarations: only what the portal makes then (the procura, signed), on the draft reopened by its name")
    ap.add_argument("--resume", type=Path, help="page/run: a stopped run's report.json, to pick it up where it stopped")
    ap.add_argument("--fix", type=Path, help="with --resume: JSON list of {section, field, set: {id|label|css}}")
    ap.add_argument("--bundle", type=Path, help="page: also write runner.js, steps.js and run.js as this one file "
                    "(in the person's Downloads), and pick.js, a box where the person picks it once")
    a = ap.parse_args()
    steps = rules.load(a.steps)
    if a.command == "scope":
        print(" ".join(shlex.quote(p) for p in scope(steps)))
        return 0
    if not (a.server or a.vault_dir or a.values):
        ap.error("one of --server, --vault-dir or --values is required")
    try:
        answers = json.loads(a.answers.read_text()) if a.answers else {}
        asks = steps.get("asks")
        if a.values:
            if a.values.count("-") > 1:
                ap.error("--values - only once: there is one stdin")
            fields = {}
            for src_ in a.values:
                given = sys.stdin.read() if src_ == "-" else Path(src_).read_text()
                if not given.strip():
                    raise StepError("no values: pvault get printed nothing (its error is above)" if src_ == "-"
                                    else f"no values in {src_}")
                # The vault's first (piped), the documents' after: a field the vault holds
                # isn't replaced by what a document says.
                for k, v in fields_of(given).items():
                    fields.setdefault(k, v)
            values = Values(answers, fields=fields, asks=asks)
        else:
            vaults = fill.connect(argparse.Namespace(server=a.server, vault_dir=a.vault_dir, keychain=a.keychain))
            if a.server and a.token not in vaults:
                ap.error(f"{a.server} has no token {a.token!r}")
            values = Values(answers, vault=vaults[a.token if a.server else "prepare"], asks=asks)
        steps = expand(steps, values)
        if a.command != "preflight":
            steps = phase(steps, a.after_declarations, a.made_up)
        resume = None
        if a.after_declarations and a.command in ("page", "run"):
            if a.resume:
                ap.error("--after-declarations opens the draft by its name: no --resume")
            resume = reopening(steps)
        if a.resume:
            earlier = json.loads(a.resume.read_text())
            kept = a.resume.parent / "private" / "kept.json"
            if kept.exists():
                earlier["kept"] = json.loads(kept.read_text())
            resume = resumption(earlier, json.loads(a.fix.read_text()) if a.fix else None)
        if a.fix and not a.resume:
            ap.error("--fix needs --resume")
        if a.plain and a.command != "page":
            ap.error("--plain is for page: run keeps the values out of the conversation without it")
        if a.command == "preflight":
            report = preflight(steps, values, a.made_up,
                               a.after_declarations)
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return 0 if report["ready"] else 3
        if a.command == "plan":
            require_supported(steps, values)
            print(f"titolare: {values.titolare}")
            for p in plan(steps, values):
                print(f"{p['section'][:28]:28}  {(p['label'] or p['id'] or p.get('css') or '')[:34]:34}  {p['value'] if p['value'] is not None else '(' + p['kind'] + ')'}")
            return 0
        if not a.out:
            ap.error(f"{a.command} needs --out")
        if a.command == "page":
            a.out.mkdir(parents=True, exist_ok=True)
            # The second run carries no values (page_bundle), so it is never sealed: one code a pratica.
            code = None if a.plain or a.after_declarations else new_code()
            files = page_files(steps, values, resume=resume, code=code)
            drift(a.out, steps, resume)
            for name, text in files.items():
                (a.out / name).write_text(text)
            if a.bundle:
                bundle(a.out, a.bundle, files)
                print(f"{a.bundle}: if check.js names runner.js, run pick.js in the pane instead of the files it "
                      "names: the person picks this file once in the box, then poll __pv.wait()")
            # The pane's report has no values or person's steps: review.py OUT adds these, from
            # private/ (Claude sends the review page and never opens that folder).
            private(a.out, review_shown(steps, values))
            if code:
                try:
                    show_code(code)
                except StepError:
                    (a.out / "run.js").unlink(missing_ok=True)
                    raise
                print("run.js is sealed. A window with its code is open on the person's screen: tell them it is "
                      "for the box the portal's page will show when run.js runs, to leave the window open until "
                      "the run is done, and never to tell you the code.")
            elif a.plain:
                print("--plain: run.js carries the values in the clear, so they pass through this conversation.")
            else:
                print("The second run carries no value and no file's bytes (the person picks the signed files in "
                      "the page's box), so there is no code to type.")
            print(f"{a.out}: check.js first (which of runner.js, steps.js the pane lacks), then run.js; "
                  f"install.js is both. Save __pv.last() as report.json here, then review.py {a.out}. "
                  + ", ".join(f"{n} {len(t)} bytes" for n, t in files.items()))
            return 0
        return run(steps, values, a.out, a.cdp, a.profile, a.close, resume)
    except StepError as e:
        print(f"stopped: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
