#!/usr/bin/env python3
"""Offline tests of intake.py on a made-up dossier in the documents' real formats (dossier.py).

  ~/.cache/pratica-portal/venv/bin/python -I claude/skills/pratica/intake/bench/test_intake.py

No vault, browser or network. The dossier is the CILA rehearsal's P6 case, so what the intake
reads is checked against fixture-p6.json, and the whole path is run: scan, accept the router's
facts, route.py, scan against the steps file, accept, run.py preflight with the vault's values
and the documents'. No real document of these kinds is public: a real visura's layout may read
differently (see the intake's README).
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]
sys.dont_write_bytecode = True
import dossier  # noqa: E402
import intake  # noqa: E402
import run  # noqa: E402

REPO = HERE.parents[4]
P6 = REPO / "rehearsals" / "cila-fittizia"
FIXTURE = dict(json.loads((P6 / "fixture-p6.json").read_text())["fields"])
PY = sys.executable
TMP = Path(tempfile.mkdtemp(prefix="intake-"))
DOSSIER = dossier.write(TMP / "dossier")
REPORT, VALUES, PROPOSED = intake.scan(DOSSIER)


def kinds_and_unread():
    kinds = {Path(d["file"]).name: d["kind"] for d in REPORT["documents"]}
    assert kinds == {"Assenso_proprietario.pdf": "assenso", "Atto_compravendita_2003.pdf": "atto",
                     "Contratto_di_locazione.pdf": "locazione", "Documentazione_fotografica.pdf": "foto",
                     "Documento_identita_Luca.pdf": "identita", "Elaborati_grafici.pdf": "elaborati",
                     "Notifica_preliminare.pdf": "notifica", "Relazione_tecnica.pdf": "relazione",
                     "Ricevuta_diritti.pdf": "ricevuta_diritti", "Ricevuta_sanzione.pdf": "ricevuta_sanzione",
                     "Visura_attuale_immobile.pdf": "visura", "Allegato_A_Programma_100.pdf": "programma100",
                     "Modello_DP.pdf": "modello_dp"}, kinds
    # The identity card is a scan: known by its name, read for nothing.
    assert REPORT["unread"] == ["Documento_identita_Luca.pdf"], REPORT["unread"]


def values_match_fixture():
    """Every field read off the documents is the fixture's; every one of the property's is read."""
    wrong = {k: (v, FIXTURE[k]) for k, v in VALUES.items() if k in FIXTURE and FIXTURE[k] != v}
    assert not wrong, wrong
    missed = [k for k in FIXTURE if k.startswith("luca:immobile.") and k not in VALUES]
    assert not missed, missed
    for k in ("luca:identity.codice_fiscale", "luca:identity.date_of_birth", "luca:identity.sex",
              "immobiliare:business.partita_iva", "luca:immobile.catasto_sezione"):
        assert VALUES[k] == FIXTURE[k], k
    assert VALUES["luca:immobile.superficie_mq"] == "98"  # the visura's, not in the fixture


def nothing_personal_for_claude():
    """intake.json is what Claude reads: field ids, never their values; no codice fiscale, birth
    date or surname of anyone in the dossier."""
    text = json.dumps(REPORT, ensure_ascii=False)
    for secret in ("FTTLCU91L02F839F", "81764350633", "SMPGLI70S70F839A", "1991-07-02", "Fittizio", "Esempio",
                   "Toledo", "852,15"):
        assert secret not in text, secret
    assert "luca:identity.codice_fiscale" in REPORT["filled"]


def both_readers_agree():
    """Without pdftotext the intake's own reader gives the same values and proposals."""
    if not shutil.which("pdftotext"):
        return
    which = intake.shutil.which
    intake.shutil.which = lambda name: None if name == "pdftotext" else which(name)
    try:
        report, values, proposed = intake.scan(DOSSIER)
    finally:
        intake.shutil.which = which
    assert values == VALUES, {k: (values.get(k), VALUES.get(k)) for k in set(values) | set(VALUES)
                              if values.get(k) != VALUES.get(k)}
    assert proposed == PROPOSED, (proposed, PROPOSED)


def router_facts():
    """The relazione's words propose the router's facts; with them the table names the CILA."""
    assert PROPOSED["facts"] == {"intervento": "manutenzione_straordinaria", "strutture": False, "prospetti": False,
                                 "cambio_uso": "no", "paesaggio": "no", "bene_culturale": False,
                                 "sanatoria": True}, PROPOSED["facts"]
    import route
    r = route.route("sue-napoli", PROPOSED["facts"])
    assert r["pratica"] == "cila-fittizia" and not r["questions"], r
    words = {p["key"]: p.get("words") for p in REPORT["proposals"] if p["part"] == "facts"}
    assert words["strutture"] == "non strutturali" and words["sanatoria"].startswith("lavori sono iniziati"), words


def notes():
    n = [x["note"] for x in REPORT["notes"]]
    assert "licenza edilizia n. 1234 del 1960-03-12" in n and "licenza edilizia n. 567 del 1961-06-05" in n, n
    assert any(x.startswith("planimetria filed on 1962-05-18: not a primo impianto") for x in n), n
    assert any(x.startswith("diritti 151,00 €, to the account") for x in n), n
    assert any(x.startswith("sanzione 333,00 €, to the account") for x in n), n


def stato_legittimo_titles():
    """The deed's titles as the whole checklist of the stato legittimo: the first licenza on its own
    line, the second of the same kind on an "altro" row, each with its number and date."""
    a = PROPOSED["answers"]
    assert a["precedenti"] == ["prec_permesso", "prec_altro"], a.get("precedenti")
    assert (a["prec_permesso_numero"], a["prec_permesso_data"]) == ("1234", "1960-03-12"), a
    assert (a["prec_altro_quale"], a["prec_altro_numero"], a["prec_altro_data"]) == ("licenza edilizia", "567", "1961-06-05"), a
    assert a["prec_altro_quanti"] == "1", a


def wrong_account_and_signed_files():
    """A receipt paid elsewhere is flagged; a .p7m is read for the document it wraps."""
    d = TMP / "other"
    d.mkdir()
    (d / "Ricevuta_diritti.pdf").write_bytes(dossier.one_page(["RICEVUTA DI BONIFICO", "Diritti di istruttoria SUE",
                                                               "IBAN: IT00X0000000000000000000000", "Importo: Euro 151,00"]))
    if shutil.which("openssl"):
        key, crt = d / "k.pem", d / "c.pem"
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", crt, "-days",
                        "2", "-subj", "/CN=Firma Finta"], check=True, capture_output=True)
        subprocess.run(["openssl", "cms", "-sign", "-signer", crt, "-inkey", key, "-in", DOSSIER / "Relazione_tecnica.pdf",
                        "-outform", "DER", "-out", d / "Relazione_tecnica.pdf.p7m", "-nodetach", "-binary"],
                       check=True, capture_output=True)
        key.unlink()
        crt.unlink()
    report, _, proposed = intake.scan(d)
    assert any("NOT to the account" in x["note"] for x in report["notes"]), report["notes"]
    if shutil.which("openssl"):
        assert {Path(x["file"]).name: x["kind"] for x in report["documents"]}["Relazione_tecnica.pdf.p7m"] == "relazione"
        assert proposed["facts"]["intervento"] == "manutenzione_straordinaria"


def parsers():
    """The visura's owners as the client (one at 1/1, or co-owners), the deed's pre-1967 clause,
    noise a CID font gives (unread, not misread)."""
    sole = ("Intestazione attuale dell'immobile n. 1 - totale intestati: 1\n"
            "ROSSI MARIO\n(CF RSSMRA80A01F839Q)\nnato a NAPOLI (NA) il 01/01/1980\n"
            "Diritto di: Proprieta' per 1/1 deriva dall'atto 1)\nVisura telematica\n"
            "Comune di NAPOLI (F839) (NA)\nFoglio 3 Particella 77 Subalterno 12\n")
    _, owners, _ = intake.read_visura(sole)
    assert owners == [{"name": "ROSSI MARIO", "cf": "RSSMRA80A01F839Q", "diritto": "proprieta", "quota": "1/1"}], owners
    d = TMP / "sole"
    d.mkdir()
    (d / "Visura.pdf").write_bytes(dossier.one_page(["Visura attuale per immobile", "Dati identificativi",
                                                     "Dati di classamento"] + sole.splitlines()))
    report, values, proposed = intake.scan(d)
    assert values["rossi:immobile.titolo"] == "proprietario" and proposed["answers"]["titolo_esclusivo"] is True, values
    assert values["rossi:identity.last_name"] == "Rossi" and values["rossi:ruolo.tipo"] == "cliente", values
    co = sole.replace("totale intestati: 1", "totale intestati: 2").replace("per 1/1", "per 1/2") + \
        "BIANCHI ANNA\n(CF BNCNNA82A41F839X)\nDiritto di: Proprieta' per 1/2\n"
    _, owners, _ = intake.read_visura(co)
    assert [o["name"] for o in owners] == ["ROSSI MARIO"], "a block after 'Visura telematica' is not an owner"
    _, owners, _ = intake.read_visura(co.replace("Visura telematica\n", "") + "Visura telematica\n")
    assert [(o["name"], o["quota"]) for o in owners] == [("ROSSI MARIO", "1/2"), ("BIANCHI ANNA", "1/2")], owners
    titoli, ante67 = intake.read_deed("il fabbricato e' stato costruito anteriormente al 1° settembre 1967")
    assert titoli == [] and ante67
    assert not intake.readable("\x01\x02 ÿþ " * 20) and intake.readable("Visura attuale per immobile " * 2)


def end_to_end():
    """Scan, accept the facts, route, scan against the steps file, accept, pre-flight with the
    vault's values and the documents': nothing proposed is asked again, and fewer questions
    remain than with the vault alone."""
    out, work = TMP / "out", TMP / "work"
    work.mkdir()
    # The vault: the studio, the firms and the owner's representative; nothing of this client's
    # property or identity, which the documents bring.
    vault = {k: v for k, v in FIXTURE.items() if not k.startswith(("luca:immobile.", "luca:identity."))
             and not k.startswith("immobiliare:business.")}
    (work / "vault.json").write_text(json.dumps(vault))
    intake_py, route_py, run_py = HERE.parent / "intake.py", REPO / "claude/skills/pratica/portal/route.py", \
        REPO / "claude/skills/pratica/portal/run.py"

    def cli(*args):
        p = subprocess.run([PY, "-I", *map(str, args)], capture_output=True, text=True)
        assert p.returncode in (0, 3), (args, p.stderr[-800:])
        return json.loads(p.stdout)
    cli(intake_py, "scan", DOSSIER, "--out", out)
    cli(intake_py, "accept", out, "--into", work / "facts.json", "--part", "facts")
    r = cli(route_py, "--table", "sue-napoli", "--answers", work / "facts.json")
    assert r["pratica"] == "cila-fittizia" and not r["questions"], r
    answers = dict(r["answers"], people={"r": "giulia", "f1": "edil", "f2": "impianti"},  # the vault's, the architect's
                   descrizione="PROVA NON INVIARE - intake")  # a rehearsal names its draft (--made-up)
    (work / "answers.json").write_text(json.dumps(answers))
    cli(intake_py, "scan", DOSSIER, "--out", out, "--steps", r["steps"])
    added = cli(intake_py, "accept", out, "--into", work / "answers.json")["added"]
    assert {"people.c", "people.o", "relazione_tecnica", "assenso_proprietario", "cila_interventi"} <= set(added), added
    merged = json.loads((work / "answers.json").read_text())
    assert merged["people"] == {"r": "giulia", "f1": "edil", "f2": "impianti", "c": "luca", "o": "immobiliare"}

    def asked(rep):
        keys = {q["key"] for q in rep["questions"] + rep["proposals"]}
        return keys | {i["key"] for q in rep["questions"] for i in q.get("items", [])}
    with_docs = cli(run_py, "preflight", "--steps", r["steps"], "--answers", work / "answers.json",
                    "--values", work / "vault.json", "--values", out / "private" / "values.json", "--made-up")
    assert not with_docs["unsupported"] and not asked(with_docs) & set(json.loads((out / "proposed.json").read_text())["answers"])
    # What the documents carry is no longer missing; a phone or a PEC they don't carry still is.
    carried = ("c:immobile.", "c:identity.codice_fiscale", "c:identity.date_of_birth", "c:identity.sex",
               "o:business.denominazione", "o:business.codice_fiscale", "o:business.partita_iva")
    assert not [m for m in with_docs["missing"] if m["field"].startswith(carried)], with_docs["missing"]
    # Files under a question still open (the proposed "no other filings" too) are listed, not missing.
    assert all(f["exists"] for f in with_docs["files"]
               if "sismica" not in f["for"] and "altre comunicazioni" not in f["for"]), with_docs["files"]
    baseline = dict(r["answers"], people={"c": "luca", "o": "immobiliare", "r": "giulia", "f1": "edil", "f2": "impianti"},
                    descrizione=answers["descrizione"])
    (work / "baseline.json").write_text(json.dumps(baseline))
    without = cli(run_py, "preflight", "--steps", r["steps"], "--answers", work / "baseline.json",
                  "--values", work / "vault.json", "--made-up")
    # Asked now (not under another answer), a checklist's items each counted; a proposal is an "ok".
    count = lambda rep: sum(len(q.get("items", [])) or 1 for q in rep["questions"] if not q.get("only_if"))
    print(f"  pre-flight asks {count(without)} questions, proposes {len(without['proposals'])} and lacks "
          f"{len(without['missing'])} vault fields without the documents; {count(with_docs)}, "
          f"{len(with_docs['proposals'])} and {len(with_docs['missing'])} with them")
    assert count(with_docs) == 0 and count(without) >= 15, (count(with_docs), count(without))
    # Left to confirm: only the steps file's own defaults, which no document answers (no filings
    # presented with it, no assents to acquire; no firm or technicians still to be named, since
    # 2026-11-01; the architect is the designer, since 2026-11-02).
    assert {p["key"] for p in with_docs["proposals"]} <= {"comunicazioni_contestuali", "atti_da_acquisire",
                                                        "impresa_dopo", "altri_tecnici_dopo", "progettista_altro"}, with_docs["proposals"]
    # The lease carries no citizenship: the Scheda anagrafica's Cittadinanza is asked of the vault
    # (since 2026-11-02; before, every client went as the portal's preset ITALIA).
    assert len(with_docs["missing"]) <= 6 < len(without["missing"]), with_docs["missing"]
    assert any(m["field"] == "c:identity.citizenship" for m in with_docs["missing"]), with_docs["missing"]
    # The vault's value wins over a document's (--values in order), and a document fills the rest.
    (work / "one.yaml").write_text(json.dumps({"procedure": "x", "sections": [{"section": "S", "fields": [
        {"id": "p", "kind": "text", "label": "Piano", "value": "{{c:immobile.piano}}"},
        {"id": "f", "kind": "text", "label": "Foglio", "value": "{{c:immobile.catasto_foglio}}"}]}]}))
    (work / "one.json").write_text(json.dumps({"people": {"c": "luca"}}))
    (work / "other.json").write_text(json.dumps({"luca:immobile.piano": "9", "luca:ruolo.tipo": "titolare"}))
    p = subprocess.run([PY, "-I", run_py, "plan", "--steps", work / "one.yaml", "--answers", work / "one.json",
                        "--values", work / "other.json", "--values", out / "private" / "values.json"],
                       capture_output=True, text=True)
    rows = {line.split()[1]: line.split()[-1] for line in p.stdout.splitlines() if line.startswith("S ")}
    assert rows == {"Piano": "9", "Foglio": "12"}, (p.stdout, p.stderr)


def napoli_annexes():
    """Napoli's annexes to a building title (DD 603/2025, the SUE's CILA notes): pre-flight says
    them for the titles only; the intake says which the dossier lacks, and what zona A or a
    frazionamento adds."""
    import yaml
    reh = REPO / "rehearsals"
    cila = yaml.safe_load((reh / "cila-fittizia" / "portal-steps.generated.yaml").read_text())
    proroga = yaml.safe_load((reh / "proroga-fine-fittizia" / "portal-steps.generated.yaml").read_text())
    sp = run.filing_rules(cila)
    lines = run.filing_yours(cila, sp)
    assert any("Programma 100" in y and "Modello DP" in y for y in lines), lines
    assert any("Stato Comparativo" in y for y in lines) and any("tipo edilizio" in y for y in lines)
    assert any("atto d'obbligo" in y for y in lines) and len(run.filing_yours(proroga, sp)) == len(sp["yours"])
    combined = yaml.safe_load((reh / "scia-paesaggistica-semplificata-fittizia" / "portal-steps.generated.yaml").read_text())
    assert len(run.filing_yours(combined, sp)) == len(lines), "a title filed with its landscape one is a title"
    # The P6 dossier has both annexes: nothing lacking. Without them, said; zona A and a
    # frazionamento in the relazione add theirs.
    report, _, _ = intake.scan(DOSSIER, cila)
    assert not [n for n in report["notes"] if n["from"] == "dossier"], report["notes"]
    d = TMP / "annexes"
    d.mkdir()
    rel = [line.replace("zona B - agglomerati urbani di recente formazione", "zona A - insediamenti di interesse storico")
           for line in dossier.relazione_lines()] + ["Le opere comprendono il frazionamento dell'unita' immobiliare."]
    (d / "Relazione_tecnica.pdf").write_bytes(dossier.one_page(rel))
    notes = [n["note"] for n in intake.scan(d, cila)[0]["notes"]]
    assert any(n.startswith("not in the dossier: the Allegato A Nuovo Programma 100 and the Modello DP") for n in notes), notes
    assert any(n.startswith("zona A (centro storico)") for n in notes) and any(n.startswith("frazionamento") for n in notes), notes
    assert not [n for n in intake.scan(d, proroga)[0]["notes"] if n["from"] == "dossier"], "a proroga needs neither"
    # An atto d'obbligo is a notarial act, and not the deed.
    (d / "Atto_obbligo.pdf").write_bytes(dossier.one_page([
        "ATTO D'OBBLIGO UNILATERALE", "innanzi a me notaio Mario Esempio", "si obbliga a non frazionare ulteriormente"]))
    kinds = {Path(x["file"]).name: x["kind"] for x in intake.scan(d, cila)[0]["documents"]}
    assert kinds["Atto_obbligo.pdf"] == "atto_obbligo", kinds


def accept_never_replaces():
    out = TMP / "out2"
    subprocess.run([PY, "-I", HERE.parent / "intake.py", "scan", DOSSIER, "--out", out], check=True, capture_output=True)
    f = TMP / "facts.json"
    f.write_text(json.dumps({"intervento": "restauro"}))
    subprocess.run([PY, "-I", HERE.parent / "intake.py", "accept", out, "--into", f, "--part", "facts"], check=True,
                   capture_output=True)
    assert json.loads(f.read_text())["intervento"] == "restauro"


def main():
    tests = [kinds_and_unread, values_match_fixture, nothing_personal_for_claude, both_readers_agree, router_facts, notes, stato_legittimo_titles,
             wrong_account_and_signed_files, parsers, end_to_end, napoli_annexes, accept_never_replaces]
    try:
        for t in tests:
            t()
            print(f"ok  {t.__name__}")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    print(f"{len(tests)}/{len(tests)} passed")


if __name__ == "__main__":
    main()
