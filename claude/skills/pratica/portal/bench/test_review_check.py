#!/usr/bin/env python3
"""review.py's closing message for a portal draft, offline: what Claude says in the chat once a
compilation ends (did it work, what to check, what is left), with Claude's comparison of the
portal's preview with the documents (OUT/check.json) and the portal's files matched to the job's
by their bytes (OUT/portal-files.json) as its warnings. No page and no file for the tecnico.

  python3 -I claude/skills/pratica/portal/bench/test_review_check.py      (no packages)
"""

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REVIEW = Path(__file__).resolve().parents[2] / "review.py"
REPORT = {"result": "filled", "procedure": "cila", "sections": [], "total_seconds": 95.4,
          "url": "https://example.invalid/draft"}
# What run.py page writes to private/shown.json for the pane's report.
SHOWN = {"title": "CILA: lavori interni non strutturali, SUE Napoli (tecnico con procura)", "values": [],
         "yours": ["Paghi i diritti di 120 € prima della seconda compilazione"], "second_run": [], "apart": []}
ALERT = {"section": "Domicilio elettronico", "label": "PEC", "text": "Indirizzo Pec non valido"}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def build(tmp, check=None, files=None, report=None, shown=None, *args):
    job = tmp / "Bianchi"
    out = job / "run"
    (job / "docs").mkdir(parents=True)
    (out / "private").mkdir(parents=True)
    (job / "docs" / "relazione.pdf").write_bytes(b"%PDF relazione")
    (out / "report.json").write_text(json.dumps(REPORT | (report or {})))
    (out / "private" / "shown.json").write_text(json.dumps(SHOWN | (shown or {})))
    (out / "stray.pdf").write_bytes(b"%PDF only in run")  # the run's own folder is not a job file
    if check is not None:
        (out / "check.json").write_text(json.dumps(check))
    if files is not None:
        (out / "portal-files.json").write_text(json.dumps({"files": files}))
    r = subprocess.run([sys.executable, "-I", str(REVIEW), str(out), *args], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"review.py failed:\n{r.stderr}")
    assert not (out / "review.html").exists(), "a page was written for the tecnico"
    return json.loads(r.stdout)


def main():
    failed = 0

    said_all = []

    def check(name, ok, said):
        nonlocal failed
        if isinstance(said, dict) and said.get("message"):
            said_all.append(said["message"])
        print(("ok   " if ok else "FAIL ") + name)
        if not ok:
            failed += 1
            print(json.dumps(said, indent=1, ensure_ascii=False)[:3000])

    row = {"section": "Dati catastali", "label": "foglio", "portal": "3", "document": "3",
           "source": "Visura catastale, p. 1", "ok": True}
    good = {"slot": "Allegati liberi", "name": "relazione.pdf", "size": 14, "sha256": sha(b"%PDF relazione")}
    with tempfile.TemporaryDirectory() as t:
        r = build(Path(t), {"rows": [row]}, [good])
        check("a real job that worked: two lines, the pratica by its short name, no warning",
              r["message"] == "✅ CILA compilata sul portale in 95 secondi: ogni valore è stato riletto.\nResta a Lei:\n"
              "1. Controlli l'anteprima della bozza\n2. Spunti le dichiarazioni\n3. Firmi\n4. Paghi\n5. Invii"
              and r["warnings"] == [], r)
        check("the steps in full stay for Claude to answer from, unsaid", r["yours"] == SHOWN["yours"]
              and "120 €" not in r["message"], r)
    with tempfile.TemporaryDirectory() as t:
        bad = dict(row, portal="4", ok=False, note="la visura dice 3")
        r = build(Path(t), {"rows": [row, bad]}, [good], {"alerts": [ALERT, ALERT]})
        lines = r["message"].split("\n")
        check("a mismatch and the portal's warning are each a ⚠️ line, between done and what's left",
              lines[0].startswith("✅") and lines[3] == "Resta a Lei:"
              and "⚠️ Dati catastali, foglio: sul portale «4», nel documento «3» (Visura catastale, p. 1)." in lines
              and "⚠️ Domicilio elettronico: il portale segnala «Indirizzo Pec non valido». Lo controlli." in lines, r)
    with tempfile.TemporaryDirectory() as t:
        parcel = [{"section": "DATI CATASTALI", "label": x, "text": "Attenzione! Dati catastali sconosciuti"}
                  for x in ("foglio", "se non presente indicare il numero 0")]
        r = build(Path(t), report={"alerts": parcel})
        check("one warning on several boxes of a section is one line, by the section, in plain case",
              r["warnings"] == ["Dati catastali: il portale segnala «Attenzione! Dati catastali sconosciuti». "
                                "Lo controlli."], r)
    with tempfile.TemporaryDirectory() as t:
        other = {"slot": "Procura speciale", "name": "x.pdf", "size": 3, "sha256": sha(b"%PDF only in run")}
        r = build(Path(t), {"rows": [row]}, [good, other])
        check("a file whose bytes no job file has (one in run/ doesn't count)",
              r["warnings"] == ["Allegato «Procura speciale»: il file sul portale (x.pdf) non è nessuno dei Suoi file."], r)
    with tempfile.TemporaryDirectory() as t:
        r = build(Path(t))
        check("nothing checked against the documents (the archive's flow): no warning made up", r["warnings"] == [], r)
    with tempfile.TemporaryDirectory() as t:
        later = ["Procura speciale", "Quadro riepilogativo della documentazione",
                 "copia attestazione versamento oneri, diritti e spese"]
        r = build(Path(t), shown={"second_run": later})
        check("a second compilation: the diritti paid first, its receipt and the procura then attached",
              r["steps"] == ["controlli l'anteprima della bozza", "spunti le dichiarazioni", "paghi i diritti",
                             "mi mandi i file firmati (la procura, la ricevuta del pagamento e gli altri documenti): "
                             "li allego io", "firmi", "invii"], r)
        r2 = build(Path(t) / "2", shown={"second_run": later[:1]})
        check("a second compilation with nothing paid first: paying after signing, as on any pratica",
              r2["steps"][-3:] == ["firmi", "paghi", "invii"] and "paghi" not in r2["steps"][:3]
              and "mi mandi i file firmati (la procura): li allego io" in r2["steps"], r2)
        r3 = build(Path(t) / "3", report={"reopened": True}, shown={"second_run": later})
        check("the second compilation itself: the signed files attached, then sign and send",
              r3["message"].startswith("✅ CILA: file firmati allegati sul portale in 95 secondi")
              and r3["steps"] == ["controlli l'anteprima della bozza", "firmi", "invii"], r3)
    with tempfile.TemporaryDirectory() as t:
        r = build(Path(t), shown={"apart": ["Da presentare a parte, al suo ufficio: Deposito sismico"]})
        check("what is filed apart is its own line, after the portal's steps",
              r["message"].split("\n")[-1] == "Da presentare a parte, al suo ufficio: Deposito sismico.", r)
    with tempfile.TemporaryDirectory() as t:
        r = build(Path(t), None, None, {"total_seconds": 250},
                  {"title": "Permesso di costruire, SUE Napoli (tecnico con procura)"})
        check("a masculine pratica, in minutes",
              r["message"].startswith("✅ Permesso di costruire compilato sul portale in 4 minuti"), r)
    with tempfile.TemporaryDirectory() as t:
        r = build(Path(t), {"rows": [row, row]}, [good], {"alerts": [ALERT]}, None, "--prova")
        check("the Prova: the work, the PDF check and the files as ✅, no portal warning (made-up data raises them), nothing to send",
              r["message"] == "✅ CILA di prova compilata in 95 secondi, con dati inventati.\n"
              "✅ Anteprima PDF del portale letta e confrontata con il caso di prova: tutti i 2 dati corrispondono.\n"
              "✅ 1 file allegato sul portale è proprio quello del caso di prova (stessi byte).\n"
              "Nulla da inviare: la cancelli da «Pratiche in bozza»." and r["warnings"] == [], r)
    with tempfile.TemporaryDirectory() as t:
        # The compilation attached two files; «Allega documenti» lists the one (in two slots), the other sits in a quadro.
        receipt = {"name": "ricevuta-sanzione.pdf", "section": "d) Qualificazione dell'intervento", "sha256": sha(b"%PDF ricevuta")}
        listed = {"name": "relazione.pdf", "section": "Gestione degli allegati", "sha256": sha(b"%PDF relazione")}
        slots = [good, dict(good, slot="Allegati liberi 2")]
        r = build(Path(t), {"rows": [row]}, slots, None, {"attached": [listed, receipt]}, "--prova")
        lines = r["message"].split("\n")
        check("the Prova: two slots of one file count once, and the file in a quadro is said not read back",
              "✅ Dei 2 file allegati ne ho riletto 1 sul portale: è proprio quello del caso di prova (stessi byte)." in lines
              and any(l.startswith("⚠️ Il file «ricevuta-sanzione.pdf» non l'ho ritrovato sul portale") for l in lines), r)
        out = Path(t) / "Bianchi" / "run"
        q = json.loads(subprocess.run([sys.executable, "-I", str(REVIEW), str(out), "--quadri"],
                                      capture_output=True, text=True).stdout)
        check("--quadri names the quadro holding the file «Allega documenti» lacks, not «Gestione degli allegati»",
              q == {"quadri": ["d) Qualificazione dell'intervento"]}, q)
        (out.parent / "docs" / "ricevuta-sanzione.pdf").write_bytes(b"%PDF ricevuta")  # the job has the receipt too
        (out / "portal-files-2.json").write_text(json.dumps({"files": [dict(receipt, slot="allegare qui la ricevuta", size=13)]}))
        q = json.loads(subprocess.run([sys.executable, "-I", str(REVIEW), str(out), "--quadri"],
                                      capture_output=True, text=True).stdout)
        r = json.loads(subprocess.run([sys.executable, "-I", str(REVIEW), str(out), "--prova"],
                                      capture_output=True, text=True).stdout)
        check("once the quadro was read (portal-files-2.json): nothing left to open, every file read back, no warning",
              q == {"quadri": []} and r["warnings"] == [] and "✅ 2 file allegati sul portale sono proprio quelli del caso di prova (stessi byte)."
              in r["message"].split("\n"), r)
        r = build(Path(t) / "2", {"rows": [row]}, slots, None, {"attached": [listed]}, "--prova")
        check("the Prova: every attached file read back is a plain count, no warning",
              "✅ 1 file allegato sul portale è proprio quello del caso di prova (stessi byte)." in r["message"].split("\n")
              and r["warnings"] == [], r)
    with tempfile.TemporaryDirectory() as t:
        r = build(Path(t), {"rows": [row, dict(row, portal="4", ok=False)]}, [good], None, None, "--prova")
        check("the Prova: a value that doesn't match the case is a ⚠️ line, not hidden",
              "⚠️ Dati catastali, foglio: sul portale «4», nel documento «3» (Visura catastale, p. 1)." in r["message"].split("\n")
              and "✅ Anteprima PDF del portale letta e confrontata con il caso di prova: 1 dati su 2 corrispondono."
              in r["message"].split("\n"), r)
    with tempfile.TemporaryDirectory() as t:
        r = build(Path(t), None, None, None, None, "--prova")
        check("the Prova: no check made says so, never silence",
              any(l.startswith("⚠️ Il confronto con l'anteprima") for l in r["message"].split("\n"))
              and not any(l.startswith("✅ Anteprima") for l in r["message"].split("\n")), r)
    with tempfile.TemporaryDirectory() as t:
        r = build(Path(t), report={"result": "stopped", "error": "a reason for Claude"})
        check("a stopped run: no message (Claude recovers it, or says what's left)",
              r["result"] == "stopped" and r["message"] is None, r)

    # What the tecnico reads is Italian: none of the words an English message would have.
    english = re.compile(r"\b(the|your|you|and|of|was|draft|saved|every|value|left|filled|sign|send|pay|file was)\b", re.I)
    hits = sorted({w.lower() for m in said_all for w in english.findall(m)})
    check(f"every message is Italian ({len(said_all)} read)", len(said_all) >= 8 and not hits, hits)

    # Every pratica's short name reads as one: no sportello, no role, no subtitle.
    sys.path.insert(0, str(REVIEW.parent))
    sys.dont_write_bytecode = True  # no __pycache__ in the skill's folder
    import review  # noqa: PLC0415
    titles = re.findall(r'^title: "([^"]+)"', "\n".join(p.read_text() for p in
                        (REVIEW.parents[3] / "rehearsals").glob("*/recipe.yaml")), re.M)
    names = {review.pratica_name({"title": x}) for x in titles}
    check(f"each recipe's title gives a short name ({len(names)})",
          len(names) > 50 and not [n for n in names if "Napoli" in n or "procura" in n or ":" in n], sorted(names))

    print(f"{failed} failed" if failed else "all passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
