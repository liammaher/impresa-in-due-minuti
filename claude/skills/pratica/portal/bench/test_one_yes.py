#!/usr/bin/env python3
"""A complete real folder asks one confirmation only: the summary of every answer, then «sì».

  ~/.cache/pratica-portal/venv/bin/python -I claude/skills/pratica/portal/bench/test_one_yes.py

The made-up P6 dossier (intake/bench/dossier.py) as a tecnico hands over a complete job, through
the skill's commands as SKILL.md runs them, not --made-up: the intake reads the documents, route.py
picks the pratica, the tecnico's note gives what no document holds (the client's contacts, the
owner's legale rappresentante, the firms: the P6 fixture's values), every file is PDF/A and signed
(PAdES, a self-signed certificate made here with openssl). Pre-flight must then ask nothing but the
proposals, and give `riepilogo`, naming every answer the compilation uses; `confirm` with its id
makes it ready, and refuses an id the answers no longer match. Then every rehearsal: once its
answers are in, the summary covers each answer it uses. No browser, vault or network.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True
import gen  # noqa: E402
import run  # noqa: E402

ROOT = HERE.parents[4]
SKILLS = ROOT / "claude" / "skills" / "pratica"
REH = ROOT / "rehearsals"
FIXTURE = dict(json.loads((REH / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])
NOTE_PEOPLE = {"r": "giulia", "f1": "edil", "f2": "impianti"}  # the assenso and the notifica name them
STUDIO = "chiara"
PDFA = (b"\n%<x:xmpmeta xmlns:x=\"adobe:ns:meta/\"><rdf:RDF><rdf:Description "
        b"xmlns:pdfaid=\"http://www.aiim.org/pdfa/ns/id/\" pdfaid:part=\"2\" pdfaid:conformance=\"B\"/>"
        b"</rdf:RDF></x:xmpmeta>\n")


def sh(*args, cwd, ok=(0,)):
    r = subprocess.run([sys.executable, "-I", *map(str, args)], cwd=cwd, capture_output=True, text=True)
    assert r.returncode in ok, (args, r.returncode, r.stderr[-2000:], r.stdout[-2000:])
    return json.loads(r.stdout) if r.stdout.strip().startswith("{") else r.stdout


def sign(path, cf, tmp):
    """The file as the tecnico's signed PDF/A export: the PDF/A mark and a PAdES signature (as in
    test_preflight's signed_file) whose certificate carries the tecnico's codice fiscale."""
    key, crt, doc, sig = tmp / "k.pem", tmp / "c.pem", tmp / "doc.pdf", tmp / "sig.der"
    content = path.read_bytes() + PDFA
    doc.write_bytes(content)
    subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", crt, "-days", "2",
                    "-subj", f"/C=IT/O=Fittizio/CN=Firma Finta/serialNumber=TINIT-{cf}"], check=True, capture_output=True)
    subprocess.run(["openssl", "cms", "-sign", "-signer", crt, "-inkey", key, "-in", doc, "-outform", "DER", "-out", sig,
                    "-binary"], check=True, capture_output=True)
    path.write_bytes(content + b"1 0 obj\n<< /Type /Sig /Filter /Adobe.PPKLite /SubFilter /ETSI.CAdES.detached "
                     b"/ByteRange [0 100 200 300] /Contents <" + (sig.read_bytes().hex().upper() + "0" * 2048).encode()
                     + b"> >>\nendobj\n%%EOF\n")
    for f in (key, crt, doc, sig):
        f.unlink()


def job(tmp, note=True):
    """The tecnico's folder of jobs with the P6 job in it, through route.py and the intake as
    SKILL.md steps 1-2 run them; with `note`, what the tecnico's note says is in the job too."""
    jobs = tmp / "lavori"
    folder = jobs / "Fittizio"
    folder.mkdir(parents=True)
    studio = {k: v for k, v in FIXTURE.items() if ":" not in k or k.startswith(STUDIO + ":")}
    (jobs / "studio.json").write_text(json.dumps(studio, ensure_ascii=False))
    subprocess.run([sys.executable, "-I", SKILLS / "intake" / "bench" / "dossier.py", folder / "docs"], check=True,
                   capture_output=True)
    intake = SKILLS / "intake" / "intake.py"
    sh(intake, "scan", "docs", "--out", "run/intake", cwd=folder)
    sh(intake, "accept", "run/intake", "--into", "facts.json", "--part", "facts", cwd=folder)
    routed = sh(SKILLS / "portal" / "route.py", "--table", "sue-napoli", "--answers", "facts.json", cwd=folder)
    assert routed["routed"] and not routed["questions"] and routed["pratica"] == "cila-fittizia", routed
    (folder / "answers.json").write_text(json.dumps(routed["answers"]))
    sh(intake, "scan", "docs", "--out", "run/intake", "--steps", routed["steps"], cwd=folder)
    sh(intake, "accept", "run/intake", "--into", "answers.json", cwd=folder)
    values = {}
    if note:
        answers = json.loads((folder / "answers.json").read_text())
        answers["people"] |= NOTE_PEOPLE
        (folder / "answers.json").write_text(json.dumps(answers, ensure_ascii=False))
        slugs = set(answers["people"].values())
        read = json.loads((folder / "run" / "intake" / "private" / "values.json").read_text())
        values = {k: v for k, v in FIXTURE.items() if k.split(":")[0] in slugs and k not in read}
        cf = FIXTURE[f"{STUDIO}:identity.codice_fiscale"]
        for k, v in answers.items():
            if isinstance(v, str) and v.startswith("docs/"):
                sign(folder / v, cf, tmp)
    (folder / "values.json").write_text(json.dumps(values, ensure_ascii=False))
    # check.py's merge (it needs the built plugin's schema; test_build runs it there)
    (folder / "run" / "values.json").write_text(json.dumps(studio | values, ensure_ascii=False))
    return folder, routed["steps"]


def preflight(folder, steps, *more, ok=(0, 3)):
    return sh(SKILLS / "portal" / "run.py", *more or ("preflight",), "--steps", steps, "--answers", "answers.json",
              "--values", "run/values.json", "--values", "run/intake/private/values.json", cwd=folder, ok=ok)


def complete_folder(tmp):
    folder, steps = job(tmp)
    r = preflight(folder, steps)
    assert not r["unsupported"] and not r["questions"], r["questions"]
    assert not r["missing"], [m["id"] for m in r["missing"]]
    assert not [f for f in r["files"] if f["path"] and (not f["exists"] or f.get("problem"))], r["files"]
    assert r["proposals"] and all("proposal" in p for p in r["proposals"]), r["proposals"]
    assert r.get("riepilogo") and r.get("riepilogo_id"), "no summary for a complete folder"
    rows = {x["key"]: x for x in r["riepilogo_rows"]}
    # Every proposal is a line of it, said to be one; the documents' answers name their document.
    for p in r["proposals"]:
        assert rows[p["key"]]["source"] == run.PROPOSED, rows.get(p["key"])
    answers = json.loads((folder / "answers.json").read_text())
    for k, source in answers["fonti"].items():
        if k in rows:
            assert rows[k]["source"] == source, (k, rows[k])
    assert rows["cila_stato"]["source"] == "relazione tecnica" and rows["cila_stato"]["answer"] == "in corso", rows["cila_stato"]
    # Short, as a review by exception: a line for each proposal, the rest counted by source; every
    # answer, a line each, under «tutte».
    short, full = r["riepilogo"], r["riepilogo_tutte"]
    assert short.count("– ") == len(r["proposals"]) and "«tutte»" in short and "Scriva «sì»" in short, short
    assert "relazione tecnica" in short and len(short.splitlines()) <= 6 + len(r["proposals"]) + 3, short
    assert full.count("\n– ") == len(rows) and "Scriva «sì»" in full, full
    assert rows["allegati"]["answer"].count(",") >= 5, rows["allegati"]
    # The «sì» to another summary changes nothing.
    stale = preflight(folder, steps, "confirm", "--riepilogo", "000000000000", ok=(4,))
    assert stale["confirmed"] is False and stale["riepilogo_id"] == r["riepilogo_id"], stale
    assert json.loads((folder / "answers.json").read_text()) == answers
    done = preflight(folder, steps, "confirm", "--riepilogo", r["riepilogo_id"], ok=(0,))
    assert done["ready"] and done["confirmed"] == sorted(p["key"] for p in r["proposals"]), done
    assert done["riepilogo_id"] == r["riepilogo_id"], "the summary changed once confirmed"
    # A changed answer is a new summary, which the old «sì» doesn't confirm.
    answers = json.loads((folder / "answers.json").read_text())
    (folder / "answers.json").write_text(json.dumps(answers | {"parti_comuni": "condominio"}, ensure_ascii=False))
    changed = preflight(folder, steps)
    assert changed.get("riepilogo_id") != r["riepilogo_id"], "a changed answer kept the summary"
    print(f"ok    complete P6 folder: one message of {len(rows)} answers, {len(r['proposals'])} of them proposals")


def held_follow_ups(tmp):
    """P6 as handed over (no note): the details of other filings, a "+" list held behind the
    proposal "no other filings", are never asked (2026-11-09: comunicazione_2 and _3 were)."""
    folder, steps = job(tmp, note=False)
    r = preflight(folder, steps)
    asked = [q["key"] for q in r["questions"]]
    assert not any(k.startswith("comunicazion") for k in asked), asked
    held = r["if_changed"]["comunicazioni_contestuali"]
    assert {"comunicazioni_quante", "comunicazione_2", "comunicazione_3_autorita"} <= set(held), held
    assert "riepilogo" not in r, "a summary while details are missing"
    print("ok    P6 without the note: no comunicazione_* asked, the details missing, no summary")


def detail_behind_a_proposal(tmp):
    """The note lacks the second firm's VAT number, which only the proposed count of firms (two)
    makes needed: the first message asks it with the rest, no summary is given, and there is no «sì»
    for `confirm` to take."""
    folder, steps = job(tmp)
    values = json.loads((folder / "run" / "values.json").read_text())
    values.pop("impianti:business.partita_iva")
    (folder / "run" / "values.json").write_text(json.dumps(values, ensure_ascii=False))
    r = preflight(folder, steps)
    assert "imprese_quante" in [p["key"] for p in r["proposals"]], r["proposals"]
    assert [m["id"] for m in r["missing"]] == ["impianti:business.partita_iva"], r["missing"]
    assert "riepilogo" not in r and "Mi mancano questi dati" in r["message"], r.get("message")
    refused = preflight(folder, steps, "confirm", "--riepilogo", "000000000000", ok=(4,))
    assert refused["confirmed"] is False and refused["why"].startswith("no summary"), refused["why"]
    print("ok    a detail only a proposal needs is asked in the first message; nothing to confirm")


def firms_with_the_rest(tmp):
    """Details missing and firms named but not described: the firms' details, which only the
    proposal "the firm is already chosen" makes needed, are asked with the rest, in one message."""
    folder, steps = job(tmp, note=False)
    answers = json.loads((folder / "answers.json").read_text())
    answers["people"] |= NOTE_PEOPLE
    (folder / "answers.json").write_text(json.dumps(answers, ensure_ascii=False))
    r = preflight(folder, steps)
    ids = [m["id"] for m in r["missing"]]
    assert "luca:identity.email" in ids and "edil:business.partita_iva" in ids, ids
    assert "impresa_dopo" in [p["key"] for p in r["proposals"]] and "riepilogo" not in r
    print(f"ok    a firm only a proposal needs is asked with the other {len(ids) - 1} details")


def every_rehearsal():
    """Each rehearsal's answers in full (made-up files): the summary is there and names every
    answer the compilation uses."""
    fields, here, bad, n = FIXTURE, Path.cwd(), [], 0
    import os
    os.chdir(ROOT)
    try:
        for d in sorted(x for x in REH.iterdir() if (x / "recipe.yaml").exists() and (x / "answers-p6.json").exists()):
            steps = gen.generate(gen.load_yaml(d / "recipe.yaml"))
            answers = json.loads((d / "answers-p6.json").read_text())
            r = run.preflight(steps, run.Values(dict(answers), fields=fields, asks=steps.get("asks")), made_up=True)
            if r["unsupported"] or r["questions"] or r["missing"]:
                continue  # refused on purpose, or more to give: test_rounds' and test_preflight's
            n += 1
            if not r.get("riepilogo"):
                bad.append(f"{d.name}: no summary")
                continue
            values = run.Values(dict(answers), fields=fields, asks=steps.get("asks"))
            shown = {x["key"] for x in r["riepilogo_rows"]} | {k for x in r["riepilogo_rows"] for k in [x["key"]]}
            steps_ = run.expand(steps, values)
            for k in run.needed(steps_, values):
                a = steps_["asks"][k]
                if values.raw(k) is None or a.get("type") == "file":
                    continue
                if (a.get("group") or k) not in shown:
                    bad.append(f"{d.name}: {k} not in the summary")
    finally:
        os.chdir(here)
    for b in bad:
        print("FAIL ", b)
    print(f"{n - len({b.split(':')[0] for b in bad})}/{n} ready rehearsals with every answer in the summary")
    return not bad


def main():
    if not shutil.which("openssl"):
        print("skip: no openssl to sign the files")
        return 0
    tmp = Path(tempfile.mkdtemp(prefix="one-yes-"))
    try:
        complete_folder(tmp / "a")
        held_follow_ups(tmp / "b")
        detail_behind_a_proposal(tmp / "c")
        firms_with_the_rest(tmp / "d")
        return 0 if every_rehearsal() else 1
    finally:
        shutil.rmtree(tmp)


if __name__ == "__main__":
    sys.exit(main())
