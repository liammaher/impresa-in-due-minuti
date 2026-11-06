#!/usr/bin/env python3
"""review.py's check of a portal draft, offline: Claude's comparison of the portal's preview with
the documents (OUT/check.json) and the portal's files matched to the job's by their bytes
(OUT/portal-files.json).

  python3 -I claude/skills/pratica/portal/bench/test_review_check.py      (no packages)
"""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REVIEW = Path(__file__).resolve().parents[2] / "review.py"
REPORT = {"result": "filled", "procedure": "cila", "title": "CILA", "sections": [], "values": [],
          "total_seconds": 12, "url": "https://example.invalid/draft", "yours": ["Firmare"]}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def build(tmp, check=None, files=None):
    job = tmp / "Bianchi"
    out = job / "run"
    (job / "docs").mkdir(parents=True)
    out.mkdir()
    (job / "docs" / "relazione.pdf").write_bytes(b"%PDF relazione")
    (out / "report.json").write_text(json.dumps(REPORT))
    (out / "stray.pdf").write_bytes(b"%PDF only in run")  # the run's own folder is not a job file
    if check is not None:
        (out / "check.json").write_text(json.dumps(check))
    if files is not None:
        (out / "portal-files.json").write_text(json.dumps({"files": files}))
    r = subprocess.run([sys.executable, "-I", str(REVIEW), str(out)], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"review.py failed:\n{r.stderr}")
    return (out / "review.html").read_text()


def main():
    failed = 0

    def check(name, ok, html):
        nonlocal failed
        print(("ok   " if ok else "FAIL ") + name)
        if not ok:
            failed += 1
            print(html[:3000])

    row = {"section": "Dati catastali", "label": "foglio", "portal": "3", "document": "3",
           "source": "Visura catastale, p. 1", "ok": True}
    good = {"slot": "Allegati liberi", "name": "relazione.pdf", "size": 14, "sha256": sha(b"%PDF relazione")}
    with tempfile.TemporaryDirectory() as t:
        h = build(Path(t), {"rows": [row], "not_in_preview": ["Relazione Tecnica di Asseverazione C.I.L.A."]}, [good])
        check("all agree: one line says so", "1 valore, coincide" in h and "Da guardare" not in h, h)
        check("a portal file matched to the job's by its bytes", "uguale byte per byte a docs/relazione.pdf" in h, h)
        check("the sections the preview leaves out are named", "Relazione Tecnica di Asseverazione C.I.L.A." in h, h)
        check("no 'preview not copied' line once it was checked", "non è stata copiata" not in h, h)
    with tempfile.TemporaryDirectory() as t:
        bad = dict(row, portal="4", ok=False, note="la visura dice 3")
        h = build(Path(t), {"rows": [row, bad]}, [good])
        check("a mismatch comes first, with both values", "Da guardare" in h and "«4»" in h and "«3»" in h
              and h.index("Da guardare") < h.index("Gli allegati sul portale"), h)
        check("its line in the checks is not ticked", "1 valore su 2 da guardare</li>" in h
              and "class='bad'>Anteprima del portale confrontata" in h, h)
    with tempfile.TemporaryDirectory() as t:
        other = {"slot": "Procura speciale", "name": "x.pdf", "size": 3, "sha256": sha(b"%PDF only in run")}
        h = build(Path(t), {"rows": [row]}, [good, other])
        check("a file whose bytes no job file has (one in run/ doesn't count)",
              "nessun file del lavoro ha questi byte" in h and "1 file sul portale diverso" in h, h)
    with tempfile.TemporaryDirectory() as t:
        h = build(Path(t))
        check("nothing checked yet: said, not ticked", "non ancora confrontata" in h and "non riscaricati" in h, h)
    with tempfile.TemporaryDirectory() as t:
        h = build(Path(t), {"rows": [dict(row, portal="<script>x</script>", ok=False)]}, [])
        check("values are escaped", "<script>x" not in h and "&lt;script&gt;" in h, h)

    # run.py run's own review calls portal_review with no job: none of the skill's check lines.
    sys.path.insert(0, str(REVIEW.parent))
    sys.dont_write_bytecode = True  # no __pycache__ in the skill's folder
    import review  # noqa: PLC0415
    h = review.portal_review(dict(REPORT))
    check("run.py run's review: no check lines", "confrontata" not in h and "riscaricati" not in h, h)
    # The Prova: made-up data, so no check against documents, and the portal's warning on a
    # made-up PEC is expected, never a red line for the person to chase.
    alert = {"section": "Domicilio elettronico", "label": "PEC", "text": "Indirizzo Pec non valido"}
    with tempfile.TemporaryDirectory() as t:
        job = Path(t) / "portale-sue-prova"
        out = job / "run"
        out.mkdir(parents=True)
        (out / "report.json").write_text(json.dumps(dict(REPORT, alerts=[alert])))
        r = subprocess.run([sys.executable, "-I", str(REVIEW), str(out), "--prova"], capture_output=True, text=True)
        h = (out / "review.html").read_text() if not r.returncode else r.stderr
        check("the Prova: no check lines, a made-up value's warning expected, said to be a test",
              "confrontata" not in h and "riscaricati" not in h and "normale con dati inventati" in h
              and "Bozza di prova" in h and "lo controlli" not in h, h)

    print(f"{failed} failed" if failed else "all passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
