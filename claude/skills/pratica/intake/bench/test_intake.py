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
import dossier_suap  # noqa: E402
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
    # What the tecnico is told was recognised: kinds in Italian, never a file name.
    assert {"visura", "contratto di locazione", "relazione tecnica", "assenso", "notifica preliminare"} <= set(REPORT["riconosciuti"]), REPORT["riconosciuti"]
    assert not [x for x in REPORT["riconosciuti"] if ".pdf" in x or "_" in x] and REPORT["non_riconosciuti"] == 0, REPORT


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
    assert any(x.startswith("planimetria depositata il 1962-05-18: non è di primo impianto") for x in n), n
    assert any(x.startswith("diritti 166,00 €: sul conto") for x in n), n
    assert any(x.startswith("sanzione 333,00 €: sul conto") for x in n), n


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
    (d / "Prospetto.pdf").write_bytes(dossier.one_page(["Prospetto di calcolo preventivo del contributo di costruzione"]))
    (d / "Ricevuta_sanzione.pdf").write_bytes(dossier.one_page(["RICEVUTA", "Sanzione CILA tardiva", "Importo: Euro 333,00"]))
    report, _, proposed = intake.scan(d)
    notes = {x["from"]: x["note"] for x in report["notes"]}
    assert "NON sul conto" in notes["Ricevuta_diritti.pdf"], notes
    # No account named: asked to check, never called irricevibile.
    assert "non indica il conto" in notes["Ricevuta_sanzione.pdf"], notes
    assert {Path(x["file"]).name: x["kind"] for x in report["documents"]}["Prospetto.pdf"] == "prospetto_contributo"
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
    # A property outside Napoli is said first, without the comune's name (Claude reads the notes).
    far = TMP / "pozzuoli"
    far.mkdir()
    (far / "Visura.pdf").write_bytes(dossier.one_page(["Visura attuale per immobile", "Dati identificativi",
                                                       "Dati di classamento"]
                                                      + sole.replace("NAPOLI (F839)", "POZZUOLI (G964)").splitlines()))
    notes = [n["note"] for n in intake.scan(far)[0]["notes"]]
    assert any("non è nel Comune di Napoli" in n for n in notes) and not any("Pozzuoli" in n for n in notes), notes
    assert not any("non è nel Comune di Napoli" in n["note"] for n in intake.scan(d)[0]["notes"])
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
                                                        "impresa_dopo", "altri_tecnici_dopo", "progettista_altro",
                                                        "imprese_quante"}, with_docs["proposals"]  # the job's firms, counted
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
    assert any(n.startswith("manca l'Allegato A Nuovo Programma 100 e il Modello DP") for n in notes), notes
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


# --- the SUAP's path (2026-11-12): made-up dossiers (dossier_suap.py), a shop and a bar taken over --------------------------

SUAP_SHOP = REPO / "rehearsals" / "negozio-fittizio"
SHOP_FIXTURE = dict(json.loads((SUAP_SHOP / "fixture.json").read_text())["fields"])
SHOP_DIR = dossier_suap.write(TMP / "suap-negozio", "negozio")
BAR_DIR = dossier_suap.write(TMP / "suap-bar", "bar")
SHOP, SHOP_VALUES, SHOP_PROPOSED = intake.scan_suap(SHOP_DIR)
BAR, BAR_VALUES, BAR_PROPOSED = intake.scan_suap(BAR_DIR)
# Everything personal in the two dossiers: Claude must read none of it.
SECRETS = ("FTTCML88C61F839H", "SMPGLI70S70F839A", "FTTMRC75E02F839F", "55501230639", "09876540633", "81764350633",
           "1988-03-21", "21/03/1988", "1970-11-30", "30/11/1970", "1975-05-02", "02/05/1975", "Fittizi", "FITTIZI", "Esempio",
           "ESEMPIO", "Cimarosa", "Toledo", "Foria", "Giordano", "Caracciolo", "pec.example.it", "Caffe del Molo", "CAFFE DEL MOLO")


def suap_kinds_and_values():
    """The documents are told apart (the Camera's visura from the Agenzia's, the commercial lease, the relazione descrittiva);
    every field read off them is the shop rehearsal's fixture, and what the fixture has that the visura carries is read."""
    kinds = {Path(d["file"]).name: d["kind"] for d in SHOP["documents"]}
    assert kinds == {"Visura_camerale.pdf": "visura_camerale", "Visura_catastale_locale.pdf": "visura",
                     "Contratto_locazione_commerciale.pdf": "locazione", "Relazione_descrittiva_locali.pdf": "relazione_locali",
                     "Certificato_agibilita.pdf": "agibilita", "Ricevuta_diritti.pdf": "ricevuta_diritti",
                     "Documento_identita_titolare.pdf": "identita"}, kinds
    assert {Path(d["file"]).name: d["kind"] for d in BAR["documents"]}["Atto_affitto_azienda.pdf"] == "cessione_azienda"
    assert SHOP["unread"] == ["Documento_identita_titolare.pdf"]
    wrong = {k: (v, SHOP_FIXTURE[k]) for k, v in SHOP_VALUES.items() if k in SHOP_FIXTURE and SHOP_FIXTURE[k] != v}
    assert not wrong, wrong
    # What the fixture holds that no document of the dossier says (an email, a phone, the day the VAT number opened) is not invented.
    from_documents = [k for k in SHOP_FIXTURE if k not in ("business.data_apertura", "business.email", "business.telefono")
                      and not k.endswith((".email", ".phone", ".citizenship"))]
    missed = [k for k in from_documents if k not in SHOP_VALUES]
    assert not missed, missed
    # A company's administrators are people of their own, by first name, each with their role.
    assert BAR_VALUES["giulia:ruolo.tipo"] == "amministratore" and BAR_VALUES["marco:ruolo.tipo"] == "amministratore,socio"
    assert BAR_VALUES["business.forma_giuridica"] == "srl" and BAR_VALUES["locale.destinazione_uso"] == "bar"


def suap_nothing_personal_for_claude():
    """intake.json and proposed.json are what Claude reads: kinds, field ids, notes, proposals with their source. No codice
    fiscale, birth date, surname, address or business name of anyone in the dossiers, and the private file is 0600."""
    for name, report, proposed in (("shop", SHOP, SHOP_PROPOSED), ("bar", BAR, BAR_PROPOSED)):
        text = json.dumps(report, ensure_ascii=False) + json.dumps(proposed, ensure_ascii=False)
        for secret in SECRETS:
            assert secret not in text, (name, secret)
    for case, dossier_dir in (("shop", SHOP_DIR), ("bar", BAR_DIR)):
        out = TMP / f"cli-{case}"
        p = subprocess.run([PY, "-I", HERE.parent / "intake.py", "scan", dossier_dir, "--out", out, "--table", "suap-napoli"],
                           capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
        for shown in (p.stdout, (out / "intake.json").read_text(), (out / "proposed.json").read_text()):
            for secret in SECRETS:
                assert secret not in shown, (case, secret)
        vfile = out / "private" / "values.json"
        assert oct(vfile.stat().st_mode & 0o777) == "0o600" and oct(vfile.parent.stat().st_mode & 0o777) == "0o700"
        assert any(secret in vfile.read_text() for secret in ("FTTCML88C61F839H", "SMPGLI70S70F839A")), "the values are there"
    assert "carmela:identity.codice_fiscale" in SHOP["filled"]


def suap_proposes_only_what_a_document_says():
    """The router's facts come with their source and words; the event is a take-over only because a deed says so; the zone,
    the event of a new shop, the declarations and the diritti are never proposed (the person decides, signs, declares)."""
    facts = {p["key"]: p for p in SHOP["proposals"] if p["part"] == "facts"}
    assert facts["attivita"]["value"] == "vicinato_non_alimentare" and "ATECO" in facts["attivita"]["words"]
    assert [facts[k]["value"] for k in ("consumo_sul_posto", "insegna", "musica", "alcolici")] == [False] * 4
    assert "evento" not in facts and "zona" not in facts and "dehors" not in facts, sorted(facts)
    assert facts["insegna"]["words"].startswith("non e prevista") and facts["musica"]["words"].startswith("non e prevista")
    assert any("nessun documento dice che cosa succede" in n["note"] for n in SHOP["notes"]), SHOP["notes"]
    bar = {p["key"]: p for p in BAR["proposals"] if p["part"] == "facts"}
    assert bar["evento"]["value"] == "subingresso" and bar["evento"]["from"].startswith("atto di cessione")
    assert bar["attivita"]["value"] == "somministrazione" and bar["insegna"]["value"] is True and bar["dehors"]["value"] is False
    assert bar["prevenzione_incendi"]["value"] is False and "non e soggetta" in bar["prevenzione_incendi"]["words"]
    assert not any("nessun documento dice" in n["note"] for n in BAR["notes"])
    # Several administrators: the others' antimafia declarations are theirs, so it is asked as "yes", from the visura.
    answers = {p["key"]: p["value"] for p in BAR["proposals"] if p["part"] == "answers"}
    assert answers["altri_soggetti"] is True and {p["key"]: p["value"] for p in SHOP["proposals"]}["altri_soggetti"] is False
    everything = {p["key"] for r in (SHOP, BAR) for p in r["proposals"]}
    assert not everything & {"zona", "diritti_euro", "diritti_esente", "descrizione", "dichiarazioni", "firma"}, everything
    # A premises outside Naples is said first, as the SUE's path does.
    d = TMP / "suap-fuori"
    d.mkdir()
    (d / "Contratto_locazione.pdf").write_bytes(dossier.one_page([
        "CONTRATTO DI LOCAZIONE AD USO DIVERSO DALL'ABITATIVO", "concede in locazione a ROSSI SRL, denominata CONDUTTORE,",
        "l'unita' immobiliare ad uso negozio posta in Roma, Via Appia n. 5, piano terra, CAP 00100,"]))
    notes = [n["note"] for n in intake.scan_suap(d)[0]["notes"]]
    assert any("non sono nel Comune di Napoli" in n for n in notes), notes


def suap_negations_read_as_negations():
    """«non è prevista alcuna insegna né diffusione sonora» is no for both; «non è soggetta a controllo di prevenzione
    incendi» no; a fact no sentence names proposes nothing; a surface over 400 m² gross proposes the fire prevention."""
    found = intake.read_relazione_locali(
        "Non è prevista alcuna insegna né diffusione sonora. L'attività non è soggetta a controllo di prevenzione incendi.")
    assert found["insegna"][0] is False and found["musica"][0] is False and found["prevenzione_incendi"][0] is False, found
    found = intake.read_relazione_locali("La superficie lorda complessiva, servizi e depositi compresi, è di 520 mq. "
                                         "Il locale ha un dehors con tavolini all'aperto su suolo pubblico.")
    assert found["prevenzione_incendi"][0] is True and found["dehors"][0] is True and "insegna" not in found, found
    assert intake.read_relazione_locali("La superficie di vendita è di 40 mq.")["superficie_vendita_mq"][0] == "40"
    # Which activity an ATECO code points to; a code the router has no activity for proposes none.
    assert [intake.suap_attivita(c) for c in ("47.11.10", "47.62.20", "56.10.11", "56.30.00", "96.02.01", "96.02.02", "55.20.51", "10.71.10")] == [
        "vicinato_alimentare", "vicinato_non_alimentare", "somministrazione", "somministrazione", "acconciatore", "estetista",
        "bed_and_breakfast", None]
    # A visura camerale of a shop is not the Agenzia's visura per immobile, and the other way round.
    assert intake.kind_of(Path("x.pdf"), "VISURA ORDINARIA - Estratto dal Registro delle Imprese\nNumero REA: NA - 1") == "visura_camerale"
    assert intake.kind_of(Path("x.pdf"), "Visura attuale per immobile\nSituazione degli atti informatizzati") == "visura"


def suap_end_to_end():
    """The folder of a shop opening, the whole path: scan, accept the router's facts, the tecnico's two answers (the event, the
    zone), route.py names the pratica, scan against its steps file, accept, pre-flight with the documents' values and a vault
    that holds nothing of the business: the documents' fields aren't missing, nothing proposed is asked again."""
    out, work = TMP / "suap-out", TMP / "suap-work"
    work.mkdir()
    intake_py, route_py, run_py = HERE.parent / "intake.py", REPO / "claude/skills/pratica/portal/route.py", \
        REPO / "claude/skills/pratica/portal/run.py"

    def cli(*args):
        p = subprocess.run([PY, "-I", *map(str, args)], capture_output=True, text=True)
        assert p.returncode in (0, 3), (args, p.stderr[-800:])
        return json.loads(p.stdout)
    cli(intake_py, "scan", SHOP_DIR, "--out", out, "--table", "suap-napoli")
    cli(intake_py, "accept", out, "--into", work / "facts.json", "--part", "facts")
    first = cli(route_py, "--table", "suap-napoli", "--answers", work / "facts.json")
    assert not first["routed"] and {q["key"] for q in first["questions"]} == {"evento", "fatti"}, first["questions"]
    facts = json.loads((work / "facts.json").read_text())
    facts.update(evento="apertura", zona="c", fatti=[])  # what the tecnico answers: no document says it
    (work / "facts.json").write_text(json.dumps(facts))
    r = cli(route_py, "--table", "suap-napoli", "--answers", work / "facts.json")
    assert r["routed"] and r["pratica"] == "negozio-fittizio", r
    (work / "answers.json").write_text(json.dumps(dict(r["answers"], descrizione="PROVA NON INVIARE - intake suap")))
    cli(intake_py, "scan", SHOP_DIR, "--out", out, "--table", "suap-napoli", "--steps", r["steps"])
    added = cli(intake_py, "accept", out, "--into", work / "answers.json")["added"]
    assert {"altri_soggetti", "oggetto", "ricevuta_diritti"} <= set(added), added
    vault = {}  # nothing of the business in the vault: the documents bring it
    (work / "vault.json").write_text(json.dumps(vault))
    rep = cli(run_py, "preflight", "--steps", r["steps"], "--answers", work / "answers.json",
              "--values", work / "vault.json", "--values", out / "private" / "values.json", "--made-up")
    assert not rep["unsupported"], rep["unsupported"]
    carried = ("business.denominazione", "business.codice_fiscale", "business.partita_iva", "business.pec", "business.sede_legale_",
               "carmela:identity.", "carmela:residenza.", "locale.indirizzo", "locale.catasto_", "locale.titolo")
    assert not [m for m in rep["missing"] if m["field"].startswith(carried)
                and m["field"] not in ("carmela:identity.email", "carmela:identity.phone")], [m["field"] for m in rep["missing"]]
    # What is left to the vault: the contacts no document of the dossier carries.
    assert {m["field"] for m in rep["missing"]} <= {"carmela:identity.email", "carmela:identity.phone", "business.telefono"}, rep["missing"]
    asked = {q["key"] for q in rep["questions"] + rep["proposals"]} | {i["key"] for q in rep["questions"] for i in q.get("items", [])}
    assert not asked & set(json.loads((out / "proposed.json").read_text())["answers"]), asked
    print(f"  SUAP pre-flight with the documents: {len(rep['questions'])} questions, {len(rep['proposals'])} proposals, "
          f"{len(rep['missing'])} fields missing: {sorted(m['field'] for m in rep['missing'])[:8]}")
    # The bar taken over: the deed says it is a take-over, and the relazione's alcohol is refused with its reason, as the table does.
    cli(intake_py, "scan", BAR_DIR, "--out", TMP / "suap-out-bar", "--table", "suap-napoli")
    cli(intake_py, "accept", TMP / "suap-out-bar", "--into", work / "bar.json", "--part", "facts")
    bar = json.loads((work / "bar.json").read_text())
    bar.update(zona="c")
    (work / "bar.json").write_text(json.dumps(bar))
    rb = cli(route_py, "--table", "suap-napoli", "--answers", work / "bar.json")
    assert not rb["routed"] and "Dogane" in rb["unsupported"][0], rb


def main():
    tests = [kinds_and_unread, values_match_fixture, nothing_personal_for_claude, both_readers_agree, router_facts, notes, stato_legittimo_titles,
             wrong_account_and_signed_files, parsers, end_to_end, napoli_annexes, accept_never_replaces,
             suap_kinds_and_values, suap_nothing_personal_for_claude, suap_proposes_only_what_a_document_says,
             suap_negations_read_as_negations, suap_end_to_end]
    try:
        for t in tests:
            t()
            print(f"ok  {t.__name__}")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    print(f"{len(tests)}/{len(tests)} passed")


if __name__ == "__main__":
    main()
