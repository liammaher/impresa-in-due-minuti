#!/usr/bin/env python3
"""A problem report for Portale SUE's developers, as a link to the repository's bug form filled in.

  report.py REPORT.json [--values VALUES.json ...]

REPORT.json: {"title", "cosa", "atteso", "output", "dove"}, written by Claude in Italian. "dove"
is one of the form's options (DOVE). The plugin's version and the computer's system are added
here. Prints the link (one line), or each problem and exits 1.

Nothing is sent: the tecnico opens the link, reads the text on GitHub and submits it. A report
never carries a job's data, so it is refused when it holds a value of a --values file (the
job's own, as check.py and the intake wrote them), or anything shaped like a codice fiscale,
partita IVA, IBAN, e-mail or phone number. The home folder in a path becomes "~". A value whose
every word is in the skill's own texts (SKILL.md, the catalog's titles: "Napoli", "bozza") is
anyone's word, not the job's; a surname that is also such a word is left to the skill's rule.
"""

import argparse
import json
import platform
import re
import sys
from pathlib import Path
from urllib.parse import quote, urlencode

FORM = "https://github.com/liammaher/portale-sue/issues/new"
TEMPLATE = "3-qualcosa-non-funziona.yml"
SKILL = Path(__file__).resolve().parent
PLUGIN_JSON = SKILL.parents[1] / ".claude-plugin" / "plugin.json"
DOVE = ("Cowork", "Claude desktop, Code", "Claude Code nel terminale / in a terminal")
TEXTS = ("title", "cosa", "atteso", "output")
# GitHub answers 414 past its limit; well under it, so a browser and a proxy take it too.
MAX_URL = 6000

SHAPES = {
    "un codice fiscale": r"\b[A-Z]{6}[0-9LMNPQRSTUV]{2}[A-Z][0-9LMNPQRSTUV]{2}[A-Z][0-9LMNPQRSTUV]{3}[A-Z]\b",
    "una partita IVA": r"\b\d{11}\b",
    "un IBAN": r"\bIT\d{2}[A-Z]\d{10}[0-9A-Z]{12}\b",
    "un indirizzo e-mail": r"[\w.+-]+@[\w-]+\.[\w.-]+",
    "un numero di telefono": r"(?<!\d)(?:\+39[ ]?)?3\d{2}[ ]?\d{6,7}(?!\d)",
}
# A value of these fields is a place or a code anyone may name ("Napoli", "M"), not the job's own.
# Whole parts of the field's name ("birth_comune"), never a part of a word ("denominazione").
PUBLIC_PARTS = {"comune", "provincia", "nazione", "cittadinanza", "regione", "sesso", "tipo", "stato", "categoria"}


def words(text):
    return set(re.findall(r"\w+", text.casefold()))


def public_words():
    """Every word of the skill's own texts, which a report may well use."""
    out = set()
    for f in (SKILL / "SKILL.md", SKILL / "catalog.json"):
        try:
            text = f.read_text()
        except OSError:
            continue
        if f.suffix == ".json":  # one pratica a line; only its title is prose
            text = " ".join(re.findall(r'"title": "([^"]*)"', text))
        out |= words(text)
    return out


def private_values(paths):
    """The job's values a report must not hold: strings of 4 characters or more, other than a
    place or a code anyone may name, or words the skill's own texts use."""
    public = public_words()
    out = set()
    for p in paths:
        try:
            data = json.loads(Path(p).read_text())
        except FileNotFoundError:
            continue
        for fid, v in data.items():
            if not isinstance(v, str) or len(v.strip()) < 4 or PUBLIC_PARTS & set(fid.rsplit(".", 1)[-1].split("_")):
                continue
            if words(v) - public:
                out.add(v.strip())
    return out


def problems(report, values):
    found = []
    for key in TEXTS:
        text = report.get(key, "")
        for name, shape in SHAPES.items():
            if re.search(shape, text, re.IGNORECASE):
                found.append(f"{key}: contiene {name}")
        low = text.casefold()
        for v in sorted(values):
            if re.search(r"(?<!\w)" + re.escape(v.casefold()) + r"(?!\w)", low):
                found.append(f"{key}: contiene un valore del lavoro ({len(v)} caratteri)")
    return found


def system():
    mac = platform.mac_ver()[0]
    if mac:
        return f"macOS {mac}, {platform.machine()}"
    if sys.platform == "win32":
        return f"Windows {platform.release()} ({platform.version()}), {platform.machine()}"
    return f"{platform.system()} {platform.release()}, {platform.machine()}"


def version():
    try:
        return "portale-sue " + json.loads(PLUGIN_JSON.read_text())["version"]
    except (OSError, ValueError, KeyError):
        return "portale-sue (versione sconosciuta)"


def link(report):
    fields = {"template": TEMPLATE, "title": "[Bug] " + report["title"], "cosa": report["cosa"],
              "atteso": report.get("atteso", ""), "dove": report["dove"], "versione": version(),
              "sistema": system(), "output": report.get("output", "")}
    url = lambda: FORM + "?" + urlencode({k: v for k, v in fields.items() if v}, quote_via=quote)
    for key in ("output", "cosa"):  # the error output first, then the account, cut where the limit falls
        if len(url()) <= MAX_URL:
            break
        whole, lo, hi = fields[key], 0, len(fields[key])
        while lo < hi:  # the longest start of it that fits
            mid = (lo + hi + 1) // 2
            fields[key] = whole[:mid].rstrip() + " [...]"
            lo, hi = (mid, hi) if len(url()) <= MAX_URL else (lo, mid - 1)
        fields[key] = whole[:lo].rstrip() + " [...]" if lo else ""
    return url()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("report")
    ap.add_argument("--values", action="append", default=[], help="a job's values file (repeatable)")
    a = ap.parse_args()
    report = json.loads(Path(a.report).read_text())
    home = str(Path.home())
    for key in TEXTS:
        report[key] = str(report.get(key) or "").replace(home, "~").strip()
    bad = [f"manca {k}" for k in ("title", "cosa") if not report[k]]
    if report.get("dove") not in DOVE:
        bad.append(f"dove: una di {', '.join(DOVE)}")
    bad += problems(report, private_values(a.values))
    if bad:
        print("\n".join(bad))
        sys.exit(1)
    print(link(report))


if __name__ == "__main__":
    main()
