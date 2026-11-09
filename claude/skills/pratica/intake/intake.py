#!/usr/bin/env python3
"""From a folder of a job's documents to the vault values and the answers a pratica needs.

  intake.py scan DOSSIER --out OUT [--steps STEPS] [--client SLUG]
      Reads every file in DOSSIER (a PDF's text with pdftotext when installed, else its own
      reader; a .p7m's content; a scan or an image has none), tells what each is (a visura, a
      lease, a deed, the relazione, the owner's assent, the notifica preliminare, the drawings,
      the photos, a receipt, an identity document) and writes:
      - OUT/private/values.json: the people's and the property's fields read off them (the
        visura's dati catastali, address and owners, the lease's parties and interno), as
        `pvault get` prints them, for `run.py --values` beside the vault's. Personal: Claude
        never opens it, as it never opens a review page's values.
      - OUT/intake.json: what Claude reads. Each file's kind and the ids of the fields it
        filled (never their values); the router's facts (route.py) and, with --steps, the
        pratica's answers and file slots, each proposed with the document and words it comes
        from; notes (a title the stato legittimo can start from, the receipts' account).
      - OUT/proposed.json: the proposals alone, for `accept`.
      Nothing proposed is an answer until the person confirms it: show them grouped by
      document ("from the relazione tecnica: …"), and on "ok" run accept.

  intake.py accept OUT --into FILE [--part facts|answers]
      Adds the confirmed proposals to FILE (route.py's facts, or the steps file's answers),
      never replacing an answer already there. --part answers also adds `people`.

A document the intake can't read (a scan, a font it can't decode) is listed as unread: its
facts are asked as before. It proposes, it never decides: the art. 3 category, the structures,
the vincoli are the architect's to confirm, and the visura's categoria proposes a use, it doesn't
prove one.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "portal"))
sys.dont_write_bytecode = True
import run  # noqa: E402  (Values, check_answer, refs_in, p7m_content, StepError)
import rules  # noqa: E402  (the router's table: which facts it asks)

# --- reading -----------------------------------------------------------------------------


def pdf_text(data):
    """A PDF's text, its columns side by side as pdftotext -layout gives them; "" for a scan."""
    exe = shutil.which("pdftotext")
    if exe:
        r = subprocess.run([exe, "-layout", "-enc", "UTF-8", "-", "-"], input=data, capture_output=True, timeout=60)
        if r.returncode == 0:
            return r.stdout.decode("utf-8", "replace")
    return own_pdf_text(data)


STREAM = re.compile(rb"<<(.*?)>>\s*stream\r?\n(.*?)\r?\nendstream", re.S)
TOKEN = re.compile(rb"\((?:\\.|[^\\)])*\)|<[0-9A-Fa-f\s]*>|\[|\]|/[^\s/\[\]()<>]+|[-+]?\d*\.?\d+|[A-Za-z'\"*]+")


def own_pdf_text(data):
    """A PDF's text without pdftotext: each content stream's shown strings (Tj, TJ, ', ") at
    their positions (Td, TD, Tm), rows top to bottom, cells left to right. Simple fonts only
    (WinAnsi): a CID font's glyph ids come out as noise, which `readable` refuses."""
    rows = {}
    for head, body in STREAM.findall(data):
        if b"/FlateDecode" in head:
            try:
                body = zlib.decompress(body)
            except zlib.error:
                continue
        elif b"/Filter" in head:
            continue
        x = y = lx = ly = 0.0
        stack, args = [], []
        for tok in TOKEN.findall(body):
            if tok == b"[":
                stack.append(args)
                args = []
            elif tok == b"]":
                arr, args = args, stack.pop() if stack else []
                args.append(arr)
            elif tok[:1] in b"(<" or tok[:1] == b"/" or re.fullmatch(rb"[-+]?\d*\.?\d+", tok):
                args.append(tok)
            else:
                op = tok
                nums = [float(a) for a in args if isinstance(a, bytes) and re.fullmatch(rb"[-+]?\d*\.?\d+", a)]
                if op == b"BT":
                    x = y = lx = ly = 0.0
                elif op in (b"Td", b"TD") and len(nums) >= 2:
                    lx, ly = lx + nums[-2], ly + nums[-1]
                    x, y = lx, ly
                elif op == b"Tm" and len(nums) >= 6:
                    lx, ly = nums[-2], nums[-1]
                    x, y = lx, ly
                elif op in (b"T*", b"'", b'"'):
                    ly -= 12
                    x, y = lx, ly
                if op in (b"Tj", b"TJ", b"'", b'"'):
                    parts = [a for a in args if not isinstance(a, list)] + [b for a in args if isinstance(a, list) for b in a]
                    s = "".join(pdf_string(p) for p in parts if p[:1] in b"(<")
                    if s:
                        rows.setdefault(round(y), []).append((x, s))
                args = []
    lines = []
    for y in sorted(rows, reverse=True):
        lines.append("    ".join(s for _, s in sorted(rows[y])))
    return "\n".join(lines)


def pdf_string(tok):
    if tok[:1] == b"<":
        raw = bytes.fromhex(re.sub(rb"\s", b"", tok[1:-1]).decode() or "")
    else:
        raw = re.sub(rb"\\([nrtbf()\\]|[0-7]{1,3})", lambda m: {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b",
                                                                b"f": b"\f"}.get(m.group(1), m.group(1) if not m.group(1).isdigit()
                                                                                 else bytes([int(m.group(1), 8) & 255])), tok[1:-1])
    return raw.decode("cp1252", "replace")


def readable(text):
    """Text worth reading: words, numbers and punctuation, not a CID font's glyph noise (control
    characters and stray symbols). A receipt's IBAN is mostly digits, and still text."""
    t = text.strip()
    plain = sum(c.isalnum() or c.isspace() or c in ".,;:'\"()/-+%€°&*_[]!?<>=" for c in t)
    return len(t) >= 20 and sum(c.isalpha() for c in t) >= 10 and plain / len(t) > 0.9


def text_of(path):
    """A file's text, or "" when it has none the intake can read (a scan, an image)."""
    raw = path.read_bytes()
    if path.name.lower().endswith(".p7m"):
        raw = run.p7m_content(raw) or b""
    if not raw.startswith(b"%PDF"):
        return ""
    t = pdf_text(raw)
    return t if readable(t) else ""


def norm(s):
    """Lower case, no accents (è and the typewriter's e' alike), one space between words."""
    s = unicodedata.normalize("NFKD", s.replace("’", "'"))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"([aeiou])'(?=[\s.,;:)]|$)", r"\1", s)
    return re.sub(r"\s+", " ", s)


def date(d):
    """dd/mm/yyyy as YYYY-MM-DD."""
    day, month, year = re.split(r"[/.-]", d)
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def cells(text):
    """The text's cells in reading order: each line split where columns part (3+ spaces)."""
    return [c.strip() for line in text.splitlines() for c in re.split(r"\s{3,}", line) if c.strip()]


# --- what a document is ------------------------------------------------------------------

# Its kind, by its own words first (norm()), else by its file name. Order matters: a relazione
# quotes "notifica preliminare", so the more specific heading wins.
KINDS = [
    ("visura", r"visura (attuale|storica)? ?per (immobile|soggetto)|dati identificativi.*dati di classamento", r"visura"),
    ("planimetria", r"planimetria di u\.?\s?i\.?\s?u\.?|catasto dei fabbricati - planimetria", r"planimetri"),
    ("locazione", r"contratto di locazione|denominat[oa] conduttore", r"locazion|affitto"),
    ("comodato", r"contratto di comodato|comodatari", r"comodato"),
    # A notarial act too, so before the deed: Napoli's undertaking not to split a unit further.
    ("atto_obbligo", r"atto d'?obbligo", r"atto.?d.?obbligo"),
    ("atto", r"compravendita|menzioni urbanistiche|innanzi a me.*notaio", r"atto|rogito|compravendita"),
    ("notifica", r"^\W*notifica preliminare", r"notifica"),
    # Napoli's own annexes to the building titles (DD 603/2025; the SUE's CILA notes).
    ("programma100", r"programma 100", r"programma.?100|\bp100\b"),
    ("modello_dp", r"modello dp|(legge regionale|l\.\s?r\.) (campania )?(n\. )?59/2018", r"modello.?dp|\bdp\b"),
    ("relazione", r"relazione tecnica", r"relazione"),
    ("tipo_edilizio", r"(corrispondenza|riconducibil)\w*.{0,80}tipo edilizio", r"tipo.?edilizio"),
    ("assenso", r"prestare il proprio assenso|dichiara(no)? di (prestare|dare) (il proprio )?assenso", r"assenso"),
    ("elaborati", r"stato di fatto|stato di progetto|stato comparativo", r"elaborat|tavol"),
    ("foto", r"documentazione fotografica", r"foto"),
    ("ricevuta_diritti", r"57060964|diritti di (segreteria|istruttoria)", r"diritti"),
    ("ricevuta_sanzione", r"sanzione|oblazione", r"sanzion"),
    # The prospetto first: it names the contributo di costruzione too.
    ("prospetto_contributo", r"prospetto di calcolo", r"prospetto"),
    ("ricevuta_contributo", r"contributo di costruzione|oneri di urbanizzazione", r"ricevuta.*contributo"),
    ("identita", r"carta d'?identita|repubblica italiana.*identity card", r"identit|\bcie\b|carta|passaporto|patente"),
    ("procura", r"procura speciale", r"procura"),
]
# The steps file asks that take each kind of file, in the order they're tried.
SLOTS = {
    "identita": ["documento_identita_cliente"],
    "assenso": ["assenso_proprietario"],
    "notifica": ["notifica_preliminare"],
    "elaborati": ["elaborati_grafici"],
    "relazione": ["relazione_tecnica"],
    "foto": ["documentazione_fotografica"],
    "ricevuta_sanzione": ["ricevuta_sanzione", "sanzione_ricevuta"],
    "ricevuta_contributo": ["ricevuta_contributo"],
    "prospetto_contributo": ["prospetto_contributo"],
}


def kind_of(path, text):
    t = norm(text)
    for kind, words, _ in KINDS:
        if t and re.search(words, t[:4000]):
            return kind
    name = norm(path.stem.replace("_", " ").replace("-", " "))
    for kind, _, file_name in KINDS:
        if re.search(file_name, name):
            return kind
    return None


# --- what each says ----------------------------------------------------------------------

STREETS = r"(?:via|viale|piazza|piazzetta|corso|largo|vico|vicoletto|salita|calata|rampa|rampe|traversa|strada|" \
          r"discesa|gradini|parco|riviera|lungomare|vicolo|borgo|contrada|località)"


def title(s):
    small = {"di", "de", "del", "della", "delle", "dei", "degli", "da", "e", "a", "al", "alla", "in"}
    words = s.strip().lower().split()
    return " ".join(w if i and w in small else w[:1].upper() + w[1:] for i, w in enumerate(words))


def slug_of(name):
    """A vault slug from a name: its first word (a person's first name, a company's first)."""
    w = norm(name).split()
    w = [x for x in w if x not in ("la", "il", "lo", "società", "societa", "soc.")] or ["persona"]
    return re.sub(r"[^a-z0-9-]", "", w[0])[:32] or "persona"


def read_visura(text):
    """The unit's identifiers, address and classamento, the planimetria's date, the owners."""
    t, out = norm(text), {}
    m = re.search(r"(?:sezione urbana|sez\. ?urb\.?:?)\s*([a-z0-9]{1,4})\b", t)
    if m:
        out["catasto_sezione"] = m.group(1).upper()
    m = re.search(r"foglio:?\s*(\d+)\s*particella:?\s*(\d+)\s*sub(?:alterno|\.)?:?\s*(\d+)", t)
    if m:
        out["catasto_foglio"], out["catasto_particella"], out["catasto_subalterno"] = m.groups()
    m = re.search(r"comune di ([a-z' ]+?) \((?:codice:)?([a-z]\d{3})\)", t)
    if m:
        out["comune"] = title(m.group(1))
    m = re.search(r"comune di [a-z' ]+? \([a-z]\d{3}\) \(([a-z]{2})\)", t)  # "NAPOLI (F839) (NA)"
    if m:
        out["provincia"] = m.group(1).upper()
    for c in cells(text):
        n = norm(c)
        a = re.match(rf"({STREETS} [a-z' .]+?) n\. ?(\w+)", n)
        if a:
            out["indirizzo"], out["civico"] = title(a.group(1)), a.group(2)
            for field, word in (("scala", "scala"), ("interno", "interno"), ("piano", "piano")):
                p = re.search(rf"\b{word} (\w+)", n)
                if p:
                    out[field] = p.group(1).upper() if field == "scala" else p.group(1)
            break
    m = re.search(r"categoria ([a-f]/\d+)", t)
    if m:
        out["catasto_categoria"] = m.group(1).upper()
    m = re.search(r"\btotale: (\d+) m", t)
    if m:
        out["superficie_mq"] = m.group(1)
    plan = re.search(r"data di presentazione (\d{2}/\d{2}/\d{4})", t)
    owners = []
    cs = cells(text)
    start = next((i for i, c in enumerate(cs) if norm(c).startswith("intestazione attuale")), None)
    for c in cs[start + 1:] if start is not None else []:
        n = norm(c)
        if n.startswith(("visura telematica", "legenda")):
            break
        if re.match(r"^\d+\. ", n) or n.startswith(("sede ", "repertorio", "nota ", "registrazione", "pubblico")):
            if n.startswith("sede ") and owners:
                owners[-1]["sede"] = title(re.sub(r"^sede (in )?|\(.*", "", n))
            continue
        cf = re.search(r"\(cf:? ?([a-z0-9]{11,16})\)", n)
        right = re.search(r"diritto di:? ?(.+?) per (\d+/\d+)", n)
        if cf and owners and "cf" not in owners[-1]:
            owners[-1]["cf"] = cf.group(1).upper()
            c = c[:c.upper().find("(CF")].strip()
        if right and owners:
            owners[-1]["diritto"], owners[-1]["quota"] = right.group(1).strip(), right.group(2)
            continue
        if c and c.upper() == c and re.search(r"[A-Z]{2}", c) and not cf:
            owners.append({"name": c.strip()})
        elif c and cf and (not owners or "cf" in owners[-1] and owners[-1]["cf"] != cf.group(1).upper()):
            owners.append({"name": c.strip(), "cf": cf.group(1).upper()})
    return out, owners, date(plan.group(1)) if plan else None


def read_lease(text):
    """The parties (the tenant's name and codice fiscale, the landlord's), the unit's interno,
    CAP and address as the lease writes them."""
    t, out = norm(text), {}
    for field, pat in (("interno", r"\binterno (\w+)"), ("cap", r"\bcap (\d{5})"), ("scala", r"\bscala (\w+)"),
                       ("piano", r"\bpiano (\w+)")):
        m = re.search(pat, t)
        if m:
            out[field] = m.group(1).upper() if field == "scala" else m.group(1)
    tenant = landlord = None
    m = re.search(r"concede in (?:locazione|comodato) a (.+?) denominat[oa] (?:conduttore|comodatario)", t)
    if m:
        seg = m.group(1)
        cf = re.search(r"c\.?\s?f\.?:? ?([a-z0-9]{16})", seg)
        name = re.split(r",| nat[oa] ", seg)[0]
        born = re.search(r"nat[oa] a ([a-z' ]+?) il (\d{2}/\d{2}/\d{4})", seg)
        tenant = {"name": title(name), "cf": cf.group(1).upper() if cf else None,
                  "birth_comune": title(born.group(1)) if born else None, "born": date(born.group(2)) if born else None}
    m = re.search(r"^(.*?) di seguito denominat[oa] (?:locatore|comodante)", t)
    if m:
        seg = re.sub(r"^.*?\b(?:la|il|lo)\s+(?=\S)", "", m.group(1), count=1)
        piva = re.search(r"(?:p\.?\s?iva|c\.?f\.? e p\.?\s?iva)\s*(\d{11})", seg)
        landlord = {"name": title(re.split(r",", seg)[0]), "cf": piva.group(1) if piva else None}
    return out, tenant, landlord


TITOLI = r"(licenza edilizia|concessione edilizia|permesso di costruire|concessione in sanatoria|permesso in sanatoria|" \
         r"d\.?i\.?a\.?|s\.?c\.?i\.?a\.?|c\.?i\.?l\.?a\.?|condono edilizio)"


# A title the deed names, as the stato legittimo's checklist lists it (the dictionary's `precedenti`).
PRECEDENTI = [(r"concessione in sanatoria|condono", "prec_condono"), (r"permesso in sanatoria", "prec_pdc_sanatoria"),
              (r"(licenza|concessione) edilizia|permesso di costruire", "prec_permesso"),
              (r"dia\b", "prec_dia"), (r"scia\b", "prec_scia")]


def read_deed(text):
    """The menzioni urbanistiche: the titles the building was built or changed under, or that
    it predates 1 September 1967 (art. 46 DPR 380/2001, art. 40 L. 47/1985)."""
    t, out = norm(text), []
    for m in re.finditer(TITOLI + r"[^;]{0,60}?n\.? ?([\w/.-]+?)[,]?(?: rilasciat[ao] dal comune di [a-z ]+)? "
                         r"(?:in data|del) (\d{1,2}/\d{1,2}/\d{4})", t):
        kind = re.sub(r"\.", "", m.group(1))
        out.append({"titolo": kind, "numero": m.group(2).rstrip("."), "data": date(m.group(3))})
    ante67 = bool(re.search(r"(anteriormente|prima) (al|del) 1\W? ?settembre 1967|ante ?67", t))
    return out, ante67


# Phrases of a relazione tecnica that propose a fact, each with the value it proposes. The
# words are the ones the national models and Napoli's CILA notes use; a relazione that says
# nothing about a fact proposes nothing for it.
RELAZIONE = [
    ("intervento", "manutenzione_straordinaria", r"manutenzione straordinaria"),
    ("intervento", "restauro", r"restauro e (di )?risanamento conservativo"),
    ("intervento", "ristrutturazione", r"ristrutturazione edilizia"),
    ("intervento", "nuova_costruzione", r"\bnuova costruzione"),
    ("strutture", False, r"non (interessano|riguardano|toccano) (le )?(parti )?strutturali|non strutturali"),
    ("strutture", True, r"(interessano|riguardano|toccano) (le )?(parti )?strutturali|opere strutturali"),
    ("prospetti", False, r"non (modificano|alterano|interessano) (i )?prospetti|senza modifiche (dei|ai) prospetti"),
    ("prospetti", True, r"(modificano|alterano|modifica dei|modifiche (dei|ai)) prospetti"),
    ("cambio_uso", "no", r"(non comporta\w*|senza|nessun) (alcun )?(mutamento|cambio|modifica\w*) (della )?destinazione d'?uso|"
                         r"destinazione d'?uso[^.]{0,30}invariat"),
    ("paesaggio", "no", r"non (e )?sottopost\w* a vincolo paesaggistico|non ricade in (area|zona) (sottoposta a )?vincol\w* paesaggistic"),
    ("bene_culturale", False, r"ne a tutela ai sensi della parte ii|non (e )?(sottoposto a tutela|un bene culturale)|"
                              r"non (e )?vincolat\w* ai sensi della parte ii"),
    ("parti_comuni", "nessuna", r"non interessano (le )?parti comuni"),
    ("onerosa", False, r"a titolo gratuito|(non comporta\w*|senza|ne) (alcun )?aumento del carico urbanistico"),
    ("sotto_200", True, r"inferiore a 200 uomini.?giorno"),
    ("sotto_200", False, r"superiore a 200 uomini.?giorno"),
    ("imprese", True, r"impres[ae] esecutric"),
    ("piu_imprese", True, r"(due|tre|piu) imprese"),
    ("tolleranze", False, r"(non (sussistono|si dichiarano|sono dichiarate|vengono dichiarate)|nessuna) tolleranz"),
    ("tolleranze", True, r"si dichiarano (le seguenti )?tolleranz"),
    ("atti_da_acquisire", False, r"non sono necessari altri (atti di assenso|pareri|nulla osta)"),
    ("altri_tecnici", False, r"non sono (stati )?incaricati altri tecnici"),
    ("direttore_lavori", "progettista", r"direttore dei lavori:? (e )?(il sottoscritto|lo stesso) progettista"),
    ("frazionamento", False, r"(senza|non comporta\w*|nessun) (alcun )?frazionament"),
    ("frazionamento", True, r"\bfrazionament\w*|\bfrazionare\b"),
]
# The CILA's checklist of what the works are (its group `cila_interventi`), from the art. 3
# category the relazione gives.
CILA_INTERVENTI = {"manutenzione_straordinaria": "cila_manutenzione", "restauro": "cila_restauro"}


def read_relazione(text):
    """What the architect's own relazione says, as facts the router and the steps file ask:
    each with the words that propose it. The first phrase that matches a fact wins."""
    t, found = norm(text), {}
    for fact, value, pat in RELAZIONE:
        if fact not in found:
            m = re.search(pat, t)
            if m:
                found[fact] = (value, m.group(0))
    m = re.search(r"lavori (sono|sono stati) iniziati (in data|il) (\d{2}/\d{2}/\d{4})", t)
    if m:
        found["data_inizio_lavori"] = (date(m.group(3)), m.group(0))
        done = re.search(r"(sono stati|risultano) (ultimati|completati|conclusi)", t)
        found["stato"] = ("realizzato" if done else "in corso", (done or m).group(0))
    else:
        m = re.search(r"lavori (inizieranno|avranno inizio) (in data|il) (\d{2}/\d{2}/\d{4})", t)
        if m:
            found["data_inizio_lavori"] = (date(m.group(3)), m.group(0))
            found["stato"] = ("da iniziare", m.group(0))
    m = re.search(r"\bzona ([a-g])\b(?: ?- ?[a-z ]{0,60})?(?: della variante generale| del prg)", t)
    if m:
        found["zona_prg"] = (m.group(1).upper(), m.group(0))
    # The architect's own sentences, as the form's free text: OGGETTO, and the description.
    m = re.search(r"OGGETTO:\s*(.+?)(?:\n\s*\n|\n\s*[A-Z]{4,}[A-Z ']*:)", text, re.S)
    if m:
        found["oggetto"] = (re.sub(r"\s+", " ", m.group(1)).strip()[:300], "OGGETTO")
    m = re.search(r"DESCRIZIONE DELL.INTERVENTO\s*\n(.+?)(?:\n\s*\n|\n\s*\d+\.\s+[A-Z])", text, re.S)
    if m:
        found["dettaglio"] = (re.sub(r"\s+", " ", m.group(1)).strip()[:500], "DESCRIZIONE DELL'INTERVENTO")
    return found


def read_notifica(text):
    t = norm(text)
    m = re.search(r"numero previsto di imprese[^:]*: ?(\d+)", t)
    return int(m.group(1)) if m else None


def read_receipt(text):
    """The account a payment went to, and its amount: whether Napoli takes it that way."""
    t = norm(text)
    amount = re.search(r"(?:importo|euro|eur)\s*:?\s*(?:euro |eur )?(\d{1,3}(?:\.\d{3})*,\d{2})", t)
    # An account it names at all: an IBAN (spaces dropped, so no word boundary), or a c/c number.
    names = bool(re.search(r"it\d{2}[a-z]\d{10}[0-9a-z]{12}", t.replace(" ", ""))
                 or re.search(r"\b(?:c/c|c\.c\.|conto(?: corrente)?(?: postale)?)\s*(?:n\.?|nr\.?|numero)?\s*:?\s*\d{6,}", t))
    return {"postale_57060964": "57060964" in t, "iban_sue": "it95x0306903496100000046118" in t.replace(" ", ""),
            "names_account": names, "importo": amount.group(1) if amount else None}


# --- the scan ----------------------------------------------------------------------------


def scan(dossier, steps=None, client=None):
    """What the dossier holds: (report for Claude, private values, proposals)."""
    files = sorted(p for p in Path(dossier).iterdir() if p.is_file() and not p.name.startswith("."))
    report = {"documents": [], "unread": [], "notes": [], "proposals": [], "filled": []}
    values, proposals, docs = {}, {"facts": {}, "answers": {}, "people": {}}, {}

    def propose(part, key, value, source, words=None):
        if key in proposals[part]:
            return
        proposals[part][key] = value
        report["proposals"].append({"part": part, "key": key, "value": value, "from": source}
                                   | ({"words": words} if words else {}))
    for p in files:
        text = text_of(p)
        kind = kind_of(p, text)
        entry = {"file": str(p), "kind": kind, "read": bool(text)}
        report["documents"].append(entry)
        if kind:
            docs.setdefault(kind, []).append((p, text))
        if not text:
            report["unread"].append(p.name)

    # Who: the lease's tenant is the client (they file it); else the visura's one owner.
    unit, owners, planimetria = {}, [], None
    for p, text in docs.get("visura", []):
        if text:
            unit, owners, planimetria = read_visura(text)
    lease_unit, tenant, landlord = {}, None, None
    for kind in ("locazione", "comodato"):
        for p, text in docs.get(kind, []):
            if text:
                lease_unit, tenant, landlord = read_lease(text)
                titolo = "locatario" if kind == "locazione" else "comodatario"
    people, c = {}, client
    owner_is_client = not tenant and len(owners) == 1
    if tenant:
        c = c or slug_of(tenant["name"])
        first, _, last = tenant["name"].partition(" ")
        for field, v in (("first_name", first), ("last_name", last), ("codice_fiscale", tenant["cf"]),
                         ("date_of_birth", tenant["born"]), ("birth_comune", tenant["birth_comune"])):
            if v:
                values[f"{c}:identity.{field}"] = v
        if tenant["cf"] and re.fullmatch(r"[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]", tenant["cf"]):
            # A person's codice fiscale says their sex: the day of birth plus 40 for a woman.
            values[f"{c}:identity.sex"] = "F" if int(tenant["cf"][9:11]) > 40 else "M"
        values[f"{c}:immobile.titolo"] = titolo
    elif owner_is_client:
        c = c or slug_of(owners[0]["name"])
        right = owners[0].get("diritto", "").lower()
        values[f"{c}:immobile.titolo"] = "usufruttuario" if "usufrutto" in right else \
            "proprietario" if owners[0].get("quota") in ("1/1", None) else "comproprietario"
    if c:
        people["c"] = c
        values[f"{c}:ruolo.tipo"] = "cliente"
    for o in owners:
        slug = c if owner_is_client else slug_of(o["name"])
        if slug == c and not owner_is_client:
            slug += "-2"  # an owner who shares the client's first name
        if slug != c:
            people.setdefault("o", slug)
        if re.search(r"\b(s\.?r\.?l|s\.?p\.?a|s\.?n\.?c|s\.?a\.?s|societa)\b", norm(o["name"])):
            values[f"{slug}:business.denominazione"] = title(o["name"])
            if o.get("cf"):
                values[f"{slug}:business.codice_fiscale"] = o["cf"]
                if o["cf"].isdigit():
                    values[f"{slug}:business.partita_iva"] = o["cf"]
            if o.get("sede"):
                values[f"{slug}:business.sede_legale_comune"] = o["sede"]
        else:
            words = o["name"].split()
            values[f"{slug}:identity.last_name"] = title(words[0]) if words else ""
            values[f"{slug}:identity.first_name"] = title(" ".join(words[1:]))
            if o.get("cf"):
                values[f"{slug}:identity.codice_fiscale"] = o["cf"]
        values.setdefault(f"{slug}:ruolo.tipo", "altro")
    c = people.get("c")
    if c:
        for k, v in {**unit, **{k: v for k, v in lease_unit.items() if k not in unit}}.items():
            values[f"{c}:immobile.{k}"] = v
        if unit.get("catasto_categoria", "").startswith("A/") and unit["catasto_categoria"] != "A/10":
            values[f"{c}:immobile.destinazione_uso"] = "residenziale"
    for k in ("titolo",):
        if c and f"{c}:immobile.{k}" in values:
            propose("answers", "titolo", values[f"{c}:immobile.{k}"], "visura" if not tenant else "contratto di locazione")
    if c and (tenant or owners and (len(owners) > 1 or owners[0].get("quota") not in ("1/1", None))):
        propose("answers", "titolo_esclusivo", False, "contratto di locazione" if tenant else "visura",
                "serve l'assenso del proprietario" if tenant else "altri proprietari nella visura")
    elif c and owners:
        propose("answers", "titolo_esclusivo", True, "visura", "unico proprietario, 1/1")
    if people:
        proposals["people"] = people
    # Impresa in un minuto files only on the Comune di Napoli's sportelli: a property elsewhere is said first.
    where = unit.get("comune") or lease_unit.get("comune")
    if where and norm(where) != "napoli":
        report["notes"].append({"from": "visura" if unit.get("comune") else "contratto di locazione",
                                "note": "l'immobile non è nel Comune di Napoli: Impresa in un minuto prepara solo pratiche "
                                        "del Comune di Napoli, quindi questa non la posso preparare"})
    if planimetria:
        report["notes"].append({"from": "visura", "note": f"planimetria depositata il {planimetria}"
                                + (" (catasto di primo impianto: un principio di prova dello stato legittimo, "
                                   "art. 9-bis c. 1-bis)" if planimetria < "1943-01-01" else
                                   ": non è di primo impianto, quindi non prova lo stato legittimo")})

    # The stato legittimo's starting point: the titles the deed names.
    for p, text in docs.get("atto", []):
        titoli, ante67 = read_deed(text) if text else ([], False)
        for t in titoli:
            report["notes"].append({"from": "atto", "note": f"{t['titolo']} n. {t['numero']} del {t['data']}"})
        if titoli:
            src = "atto (menzioni urbanistiche)"
            propose("answers", "stato_legittimo", "titoli", src)
            # The whole checklist of the stato legittimo's titles, as the deed names them: each kind's
            # first on its own line with its number and date; a kind the form has no line for, or a
            # second of a kind, on the "altro" rows (the first, then #2, #3: prec_altro_quanti).
            items, extra = [], []
            for t in titoli:
                item = next((i for pat, i in PRECEDENTI if re.match(pat, t["titolo"])), None)
                if item is None or item in items:
                    extra.append(t)
                    continue
                items.append(item)
                propose("answers", f"{item}_numero", t["numero"], src)
                propose("answers", f"{item}_data", t["data"], src)
            for n, t in enumerate(extra, 1):
                row = "prec_altro" if n == 1 else f"prec_altro_{n}"
                propose("answers", f"{row}_quale", t["titolo"], src)
                propose("answers", f"{row}_numero", t["numero"], src)
                propose("answers", f"{row}_data", t["data"], src)
            if extra:
                items.append("prec_altro")
                propose("answers", "prec_altro_quanti", str(len(extra)), src)
            propose("answers", "precedenti", items, src)
        if ante67:
            report["notes"].append({"from": "atto", "note": "costruito prima del 1° settembre 1967"})

    # The works: the architect's own relazione.
    for p, text in docs.get("relazione", []):
        found = read_relazione(text) if text else {}
        src = "relazione tecnica"
        for fact in ("intervento", "strutture", "prospetti", "cambio_uso", "paesaggio", "bene_culturale"):
            if fact in found:
                propose("facts", fact, found[fact][0], src, found[fact][1])
        if "stato" in found:
            propose("facts", "sanatoria", found["stato"][0] != "da iniziare", src, found["stato"][1])
            propose("answers", "cila_stato", found["stato"][0], src, found["stato"][1])
        for key, fact in (("data_inizio_lavori", "data_inizio_lavori"), ("parti_comuni", "parti_comuni"),
                          ("cila_onerosa", "onerosa"), ("scia_onerosa", "onerosa"), ("sotto_200", "sotto_200"),
                          ("oggetto", "oggetto"), ("dettaglio_intervento", "dettaglio"), ("prg_zona", "zona_prg")):
            if fact in found:
                propose("answers", key, found[fact][0], src, found[fact][1])
        if "imprese" in found:
            propose("answers", "dlgs81", True, src, found["imprese"][1])
            propose("answers", "lavori_in_proprio", False, src, found["imprese"][1])
        if "piu_imprese" in found:
            propose("answers", "notifica_dovuta", True, src, found["piu_imprese"][1])
        for key in ("tolleranze", "atti_da_acquisire", "altri_tecnici", "direttore_lavori"):
            if key in found:
                propose("answers", key, found[key][0], src, found[key][1])
        if found.get("intervento", (None,))[0] in CILA_INTERVENTI:
            propose("answers", "cila_interventi", [CILA_INTERVENTI[found["intervento"][0]]], src, found["intervento"][1])
    for p, text in docs.get("notifica", []):
        n = read_notifica(text) if text else None
        propose("answers", "dlgs81", True, "notifica preliminare")
        if n is not None and n > 1:
            propose("answers", "notifica_dovuta", True, "notifica preliminare", f"{n} imprese")

    # Receipts: Napoli takes the diritti only on its postal account, sanzioni by bonifico.
    for kind in ("ricevuta_diritti", "ricevuta_sanzione"):
        for p, text in docs.get(kind, []):
            if not text:
                continue
            r = read_receipt(text)
            ok = r["postale_57060964"] if kind == "ricevuta_diritti" else r["iban_sue"]
            # A receipt that names no account says nothing either way: never call it irricevibile.
            where = ("sul conto che il SUE di Napoli accetta" if ok else
                     "NON sul conto che il SUE di Napoli accetta: irricevibile" if r["names_account"] else
                     "la ricevuta non indica il conto: verifichi che sia quello che il SUE di Napoli accetta")
            report["notes"].append({"from": p.name, "note": f"{kind.split('_')[1]} {r['importo'] or '?'} €: {where}"})

    # The files, each in the steps file's slot for its kind.
    asks = (steps or {}).get("asks", {})
    for kind, slots in SLOTS.items():
        for p, _ in docs.get(kind, []):
            slot = next((s for s in slots if s in asks and s not in proposals["answers"]), None)
            if slot:
                propose("answers", slot, str(p), f"{p.name} ({kind})")
    # Napoli's own annexes: what the relazione says the case needs, and, for a building title,
    # those always required, when the dossier lacks them.
    relazione = next((read_relazione(t) for _, t in docs.get("relazione", []) if t), {})
    if relazione.get("zona_prg", ("",))[0] == "A" and "tipo_edilizio" not in docs:
        report["notes"].append({"from": "relazione tecnica", "note": "zona A (centro storico): manca l'attestazione, "
                                "firmata ai sensi dell'art. 481 c.p., che l'unità corrisponde al suo tipo edilizio "
                                "(art. 63 c. 4 della Variante generale)"})
    if relazione.get("frazionamento", (False,))[0] and "atto_obbligo" not in docs:
        report["notes"].append({"from": "relazione tecnica", "note": "frazionamento: manca l'atto d'obbligo a non frazionare "
                                "ancora l'unità (art. 22 c. 2 della Variante generale), trascritto: va con questa "
                                "pratica se i lavori sono eseguiti, altrimenti con la fine lavori"})
    sportello = run.filing_rules(steps) if steps else None
    if sportello and len(run.filing_yours(steps, sportello)) > len(sportello["yours"]):
        lacking = [name for kind, name in (("programma100", "l'Allegato A Nuovo Programma 100"),
                                           ("modello_dp", "il Modello DP")) if kind not in docs]
        if lacking:
            report["notes"].append({"from": "dossier", "note": f"manca {' e '.join(lacking)}, sempre "
                                    "obbligatorio con questa pratica a Napoli (DD 603/2025)"})
    # Only what the router or the steps file asks, and fits there.
    facts = rules.table("sue-napoli")["facts"]
    for key in list(proposals["facts"]):
        if rules.fact_value(facts[key], proposals["facts"][key]) is None:
            proposals["facts"].pop(key)
    if steps is not None:
        groups = steps.get("groups", {})
        for key in list(proposals["answers"]):
            v, a = proposals["answers"][key], asks.get(key)
            if key in groups:  # a checklist: the items ticked, each one of its own
                fits = isinstance(v, list) and all(asks.get(i, {}).get("group") == key for i in v)
            else:
                fits = a is not None and run.check_answer(a, v) is None
            if not fits:
                proposals["answers"].pop(key)
        if not any(r.startswith(("c:", "o:")) for _, t, _ in run.templates(steps) for r, _ in run.refs_in(t)):
            proposals.pop("people", None)
    report["proposals"] = [x for x in report["proposals"] if x["key"] in proposals.get(x["part"], {})]
    report["filled"] = sorted(values)
    return report, values, proposals


def private_dir(out):
    d = out / "private"
    d.mkdir(parents=True, exist_ok=True)
    os.chmod(d, 0o700)
    return d


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("dossier", type=Path)
    s.add_argument("--out", type=Path, required=True)
    s.add_argument("--steps", type=Path, help="the routed pratica's steps file: bind answers and file slots to it")
    s.add_argument("--client", help="the client's vault slug, when no lease or sole owner names them")
    a_ = sub.add_parser("accept")
    a_.add_argument("out", type=Path)
    a_.add_argument("--into", type=Path, required=True)
    a_.add_argument("--part", choices=["facts", "answers"], default="answers")
    a = ap.parse_args()
    try:
        if a.cmd == "scan":
            if not a.dossier.is_dir():
                raise run.StepError(f"no folder {a.dossier}")
            steps = rules.load(a.steps) if a.steps else None
            report, values, proposals = scan(a.dossier, steps, a.client)
            a.out.mkdir(parents=True, exist_ok=True)
            vfile = private_dir(a.out) / "values.json"
            fd = os.open(vfile, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as f:
                json.dump(values, f, indent=1, ensure_ascii=False)
            report["values"] = str(vfile)
            (a.out / "proposed.json").write_text(json.dumps(proposals, indent=1, ensure_ascii=False))
            (a.out / "intake.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
            print(json.dumps(report, indent=1, ensure_ascii=False))
            return 0
        proposals = json.loads((a.out / "proposed.json").read_text())
        have = json.loads(a.into.read_text()) if a.into.exists() else {}
        if not isinstance(have, dict):
            raise run.StepError(f"{a.into}: not a JSON object")
        added = [k for k in proposals.get(a.part, {}) if k not in have]
        have.update({k: proposals[a.part][k] for k in added})
        if a.part == "answers" and proposals.get("people"):
            # Roles merge: the documents name the client and the owner; the vault's people
            # (the firms, the owner's representative) keep the roles already given them.
            roles = have.setdefault("people", {})
            for role, slug in proposals["people"].items():
                if role not in roles:
                    roles[role] = slug
                    added.append(f"people.{role}")
        # Where each answer comes from, for the one message's summary (run.py `riepilogo`): every
        # proposal of the documents that the file holds as proposed, the facts route.py passed on too.
        if a.part == "answers":
            fonti = have.setdefault("fonti", {})
            for p in json.loads((a.out / "intake.json").read_text()).get("proposals", []):
                if p["key"] in have and have[p["key"]] == p["value"] and p.get("from"):
                    fonti.setdefault(p["key"], p["from"])
        a.into.write_text(json.dumps(have, indent=1, ensure_ascii=False))
        print(json.dumps({"added": added, "into": str(a.into)}, ensure_ascii=False))
        return 0
    except (run.StepError, OSError, ValueError) as e:
        print(f"stopped: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
