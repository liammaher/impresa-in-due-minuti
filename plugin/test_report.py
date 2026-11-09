#!/usr/bin/env python3
"""The skill's report.py: the link it prints fills the repository's bug form field by field, and
a report holding a job's data is refused.

  python3 plugin/test_report.py      (needs PyYAML, as test_build.py)
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import yaml

HERE = Path(__file__).resolve().parent
SKILL = HERE / "impresa-in-due-minuti" / "skills" / "pratiche"
FORM = HERE.parent / ".github" / "ISSUE_TEMPLATE"
sys.path.insert(0, str(SKILL))
sys.dont_write_bytecode = True
import report  # noqa: E402

GOOD = {"title": "CILA: la compilazione si ferma in Dati catastali",
        "cosa": "Pratica cila, passo 4.\nSi è fermata nella sezione «Dati catastali», campo «Foglio».",
        "atteso": "La bozza compilata fino agli allegati.",
        "output": "error: 0 fields with this label\nat: section 7, field 3",
        "dove": "Claude desktop, Code"}
VALUES = {"zanf:identity.last_name": "Zanfardino", "zanf:identity.first_name": "Lia",
          "zanf:residenza.comune": "Napoli", "immobile.via": "Via dei Mille",
          "zanf:identity.sesso": "M"}


def run(rep, values=None):
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "r.json").write_text(json.dumps(rep))
        args = [sys.executable, "-B", str(SKILL / "report.py"), str(Path(d) / "r.json")]
        if values is not None:
            (Path(d) / "v.json").write_text(json.dumps(values))
            args += ["--values", str(Path(d) / "v.json"), "--values", str(Path(d) / "missing.json")]
        r = subprocess.run(args, capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def main():
    fails = []

    def expect(name, ok):
        if not ok:
            fails.append(name)

    # The form the link names, and its fields: every key the link sets is a field id there, and
    # "dove" one of its options. The form changes, this test says so.
    form = yaml.safe_load((FORM / report.TEMPLATE).read_text())
    ids = {f["id"]: f for f in form["body"] if "id" in f}
    expect("the form has every field the link fills", {"cosa", "atteso", "dove", "versione", "sistema", "output"} <= ids.keys())
    expect("DOVE is the form's options, less pvault on its own", set(report.DOVE) <= set(ids["dove"]["attributes"]["options"]))

    code, out = run(GOOD, VALUES)
    expect("a clean report gives a link", code == 0 and out.startswith(report.FORM + "?"))
    q = {k: v[0] for k, v in parse_qs(urlsplit(out).query).items()}
    expect("template", q.get("template") == report.TEMPLATE)
    expect("title", q.get("title") == "[Bug] " + GOOD["title"])
    expect("text kept, accents and line breaks", q.get("cosa") == GOOD["cosa"])
    expect("dove", q.get("dove") == GOOD["dove"])
    expect("version from plugin.json", q.get("versione", "").startswith("impresa-in-due-minuti ") and "sconosciuta" not in q["versione"])
    expect("system", bool(q.get("sistema")))
    expect("one line", "\n" not in out and " " not in out)

    for name, text in [("codice fiscale", "per RSSMRA80A01F839X"), ("lower-case CF", "rssmra80a01f839x"),
                       ("omocodia", "RSSMRA8LA01F839X"), ("partita IVA", "P.IVA 01234567890"),
                       ("IBAN", "IT60X0542811101000000123456"), ("e-mail", "scriva a lia@studio.it"),
                       ("phone", "tel. 333 1234567"), ("job's surname", "per la signora Zanfardino."),
                       ("job's street, other case", "in VIA DEI MILLE 4")]:
        code, out = run(GOOD | {"cosa": text}, VALUES)
        expect(f"refused: {name}", code == 1 and out.startswith("cosa: "))
    code, out = run(GOOD | {"output": "Zanfardino"}, VALUES)
    expect("refusal never repeats the value", code == 1 and "Zanfardino" not in out)

    # A place or a sex is anyone's word; a short value or part of a word is no match; nor is a
    # value made only of words the skill's own texts use (a surname "Bozza", the word "bozza").
    code, _ = run(GOOD | {"cosa": "Comune di Napoli, sesso M, Liana e Lia2, la bozza"},
                  VALUES | {"olga:identity.last_name": "Bozza", "x:albo.sede": "Napoli"})
    expect("public fields, short values, parts of words and the skill's words pass", code == 0)
    code, _ = run(GOOD | {"cosa": "per lo Studio Olga Tarallo"}, VALUES | {"olga:business.denominazione": "Studio Olga Tarallo"})
    expect("a value with a word of its own is still refused, denominazione no place", code == 1)
    code, _ = run(GOOD | {"cosa": "nata a Zanfardinia"}, VALUES | {"zanf:identity.birth_comune": "Zanfardinia"})
    expect("a birth comune is a place anyone may name", code == 0)
    code, _ = run(GOOD, None)
    expect("no values file: shapes only", code == 0)

    home = str(Path.home())
    code, out = run(GOOD | {"output": f"File \"{home}/Lavori/x.py\", line 3"})
    q = {k: v[0] for k, v in parse_qs(urlsplit(out).query).items()}
    expect("home folder becomes ~", code == 0 and home not in q["output"] and "~/Lavori/x.py" in q["output"])

    code, out = run(GOOD | {"dove": "Chrome"})
    expect("dove outside the form's options refused", code == 1 and out.startswith("dove:"))
    code, out = run({k: v for k, v in GOOD.items() if k != "cosa"})
    expect("cosa required", code == 1 and "manca cosa" in out)

    code, out = run(GOOD | {"output": "àè " * 4000, "cosa": "x " * 500})
    q = {k: v[0] for k, v in parse_qs(urlsplit(out).query).items()}
    expect("a long output is cut visibly, the account kept",
           code == 0 and len(out) <= report.MAX_URL and q.get("output", "").endswith(" [...]")
           and len(q["output"]) > 500 and q.get("cosa") == ("x " * 500).strip())
    code, out = run(GOOD | {"output": "àè " * 4000, "cosa": "x " * 4000})
    q = {k: v[0] for k, v in parse_qs(urlsplit(out).query).items()}
    expect("an account too long alone: output dropped, account cut",
           code == 0 and len(out) <= report.MAX_URL and "output" not in q and q.get("cosa", "").endswith(" [...]")
           and len(out) > report.MAX_URL - 10)

    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("ok: report.py's link and its refusals")


if __name__ == "__main__":
    main()
