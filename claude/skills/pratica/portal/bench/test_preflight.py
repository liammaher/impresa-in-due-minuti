#!/usr/bin/env python3
"""Offline tests of run.py preflight and the steps files' `asks:` and `supports:`.

  ~/.cache/pratica-portal/venv/bin/python -I claude/skills/pratica/portal/bench/test_preflight.py

No browser, vault or network: the SCIA rehearsal's steps file, fixture and answers
(rehearsals/pizzeria-fittizia/), changed one fact at a time.
"""

import copy
import json
import os
import sys
import tempfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True  # no __pycache__ in the skill's folder
import gen  # noqa: E402
import run  # noqa: E402

gen.ensure()  # the rehearsals' steps files are built, never committed (steps.lock)

REHEARSAL = HERE.parents[4] / "rehearsals" / "pizzeria-fittizia"
STEPS = yaml.safe_load((REHEARSAL / "portal-steps.yaml").read_text())
FIELDS = dict(json.loads((REHEARSAL / "fixture.json").read_text())["fields"])
ANSWERS = json.loads((REHEARSAL / "answers.json").read_text())


def rehearsal_plan(steps, values):
    """run.plan as a rehearsal's run takes it: made-up files, so no slot that takes only signed
    files, and nothing that waits for the declarations (run.phase)."""
    import run
    return run.plan(run.rehearsal(steps, values), values)


def values(answers=ANSWERS, fields=FIELDS, steps=STEPS):
    return run.Values(dict(answers), fields=dict(fields), asks=steps.get("asks"))


def raises(fn, words):
    try:
        fn()
    except run.StepError as e:
        assert words in str(e), str(e)
        return
    raise AssertionError(f"no error ({words!r} expected)")


def ready():
    r = run.preflight(STEPS, values(), made_up=True)
    assert r["ready"], r
    assert not (r["questions"] or r["missing"] or r["unsupported"]), r
    assert any("120 €" in y for y in r["yours"]), r["yours"]


def outside_napoli():
    """Every steps file files at the Comune di Napoli's sportello: a premises or a client's property
    in another comune is refused before anything opens, without naming the comune; Napoli in any
    case or accent passes."""
    for v in ("Pozzuoli", "Casoria"):
        r = run.preflight(STEPS, values(fields=FIELDS | {"locale.comune": v}), made_up=True)
        assert not r["ready"] and any("fuori dal Comune di Napoli" in u for u in r["unsupported"]), r
        assert v not in r["message"], r["message"]
    assert run.preflight(STEPS, values(fields=FIELDS | {"locale.comune": " NAPOLI "}), made_up=True)["ready"]
    # The SUE's client: their immobile, by the role c.
    people = {"people": {**ANSWERS.get("people", {}), "c": "luca"}}
    r = run.preflight(STEPS, values(answers=ANSWERS | people, fields=FIELDS | {"luca:immobile.comune": "Pozzuoli"}),
                      made_up=True)
    assert any("fuori dal Comune di Napoli" in u for u in r["unsupported"]), r
    # A sportello of another comune isn't Portale SUE's to judge.
    other = copy.deepcopy(STEPS)
    other["start"] = "https://suap.impresainungiorno.gov.it/fnsuap/cmd/create?comune=G964"
    assert run.outside_comune(other, values(fields=FIELDS | {"locale.comune": "Pozzuoli"})) == []


def rehearsal_draft_name():
    """The steps file's own default names a real draft; a rehearsal must say PROVA NON INVIARE."""
    r = run.preflight(STEPS, values(answers=ANSWERS | {"descrizione": "SCIA Rossi"}), made_up=True)
    assert any("PROVA NON INVIARE" in u for u in r["unsupported"]), r["unsupported"]
    unanswered = {k: v for k, v in ANSWERS.items() if k != "descrizione"}
    assert run.preflight(STEPS, values(answers=unanswered), made_up=True)["unsupported"]
    assert run.preflight(STEPS, values(answers=unanswered))["ready"]


def vault_scope():
    """run.py scope: one pvault get reads every field the steps file names, and nothing else."""
    patterns = run.scope(STEPS)
    assert "*:ruolo.*" in patterns and "business.*" in patterns, patterns
    assert not any(p.startswith(("ask", "*:ask")) for p in patterns), patterns
    reads = {r.partition(".")[0].rpartition(":")[2] for _, t, _ in run.templates(STEPS)
             for r, _ in run.refs_in(t) if "." in r and not r.startswith("ask.")}
    assert reads <= {p.removeprefix("*:").removesuffix(".*") for p in patterns}, (reads, patterns)


def all_questions():
    r = run.preflight(STEPS, values(answers={"descrizione": ANSWERS["descrizione"]}), made_up=True)
    keys = [q["key"] for q in r["questions"]]
    assert keys == ["extras", "insegna", "superficie_somministrazione_mq"], keys
    items = [i["key"] for i in r["questions"][0]["items"]]
    assert r["questions"][0]["type"] == "checklist" and items[:4] == [
        "zona_tutelata", "alcolici", "musica", "insegna_esterna"], items
    assert len(items) == 6 and all(i["item"] for i in r["questions"][0]["items"]), items
    assert not r["ready"]


def alcohol():
    r = run.preflight(STEPS, values(answers=ANSWERS | {"extras": ["alcolici"]}), made_up=True)
    assert not r["ready"] and r["unsupported"] == ["La vendita di alcolici aggiunge la comunicazione alle "
                                                   "Dogane: non la preparo ancora."], r
    # The one message Claude sends as it is: the refusal, in Italian.
    assert r["message"] == "Non posso preparare questa pratica.\n" + r["unsupported"][0], r["message"]
    assert not r["questions"], "asked questions for an unsupported case"


def company():
    r = run.preflight(STEPS, values(fields=FIELDS | {"business.forma_giuridica": "srl"}), made_up=True)
    assert r["unsupported"] and "ditta individuale" in r["unsupported"][0], r


def page_refuses():
    raises(lambda: run.page_scripts(STEPS, values(answers=ANSWERS | {"extras": ["musica"]})), "not supported: Music")
    raises(lambda: run.page_scripts(STEPS, values(answers={k: v for k, v in ANSWERS.items() if k != "extras"})),
           "unanswered: ask.alcolici")


def missing_vault_field():
    fields = {k: v for k, v in FIELDS.items() if k != "business.partita_iva"}
    r = run.preflight(STEPS, values(fields=fields), made_up=True)
    assert [m["field"] for m in r["missing"]] == ["business.partita_iva"], r["missing"]
    assert not r["ready"]


def no_titolare():
    fields = {k: v for k, v in FIELDS.items() if not k.endswith(":ruolo.tipo")}
    r = run.preflight(STEPS, values(fields=fields), made_up=True)
    assert r["missing"] and r["missing"][0]["field"] == "*:ruolo.tipo", r["missing"]


def bad_answer():
    r = run.preflight(STEPS, values(answers=ANSWERS | {"superficie_somministrazione_mq": "trenta"}), made_up=True)
    q = [q for q in r["questions"] if q["key"] == "superficie_somministrazione_mq"]
    assert q and q[0]["error"] == "answer with a number", r["questions"]


def default_used():
    v = values(answers={k: x for k, x in ANSWERS.items() if k != "descrizione"})
    assert v.field("ask.descrizione") == "SCIA somministrazione - " + FIELDS["business.denominazione"]


def ask_without_question():
    steps = copy.deepcopy(STEPS)
    del steps["asks"]["insegna"]
    raises(lambda: run.preflight(steps, values(steps=steps), made_up=True), "no question in asks: for insegna")


def expired():
    steps = copy.deepcopy(STEPS)
    steps["sections"][0]["fields"].append({"id": "x", "kind": "text", "label": "CIE", "value": "{{t:cie.numero}}"})
    slug = run.Values({}, fields=FIELDS).titolare
    r = run.preflight(steps, values(steps=steps, fields=FIELDS | {f"{slug}:cie.numero": "CA00000AA",
                                                                  f"{slug}:cie.data_scadenza": "2020-01-01"}), made_up=True)
    assert any(m["why"] == "expired on 2020-01-01" for m in r["missing"]), r["missing"]


def files():
    steps = copy.deepcopy(STEPS)
    tmp = Path(tempfile.mkdtemp(prefix="preflight-"))
    big = tmp / "planimetria.pdf"
    big.write_bytes(b"%PDF" + b"0" * 300 * 1024)
    steps["asks"]["planimetria"] = {"type": "file", "question": "The planimetria (PDF)"}
    steps["sections"][-1]["fields"].append({"id": "p", "kind": "file", "label": "Planimetria",
                                            "value": "{{ask.planimetria}}"})
    r = run.preflight(steps, values(steps=steps, answers=ANSWERS | {"planimetria": str(big)}), made_up=True)
    assert r["ready"] and r["files"][0]["exists"] and not r["pane_ok"], r
    assert r["pick"] == ["planimetria.pdf"], r.get("pick")  # chosen by the person in the page
    r = run.preflight(steps, values(steps=steps, answers=ANSWERS | {"planimetria": str(tmp / "nope.pdf")}), made_up=True)
    assert not r["ready"] and r["questions"][0]["error"].startswith("no file"), r
    # Over the portal's 9.77 MB, or a type the slot doesn't take: not ready, and why.
    huge = tmp / "rilievo.pdf"
    with huge.open("wb") as f:
        f.truncate(run.SLOT_MAX_BYTES + 1)
    r = run.preflight(steps, values(steps=steps, answers=ANSWERS | {"planimetria": str(huge)}), made_up=True)
    assert not r["ready"] and "al massimo 9,77 MB" in r["files"][0]["problem"], r["files"]
    steps["sections"][-1]["fields"][-1]["accepts"] = "pdf.p7m;jpg.p7m"
    # A slot that takes only signed files (a real case's: a rehearsal leaves it out, run.phase).
    r = run.preflight(steps, values(steps=steps, answers=ANSWERS | {"planimetria": str(big)}))
    assert not r["ready"] and r["files"][0]["problem"] == "la casella accetta solo file pdf.p7m, jpg.p7m", r["files"]
    r = run.preflight(steps, values(steps=steps, answers=ANSWERS | {"planimetria": str(big)}), made_up=True)
    assert r["ready"] and not r["files"] and "1 slot(s) that take only signed files left empty" in r["warnings"][-1], r
    signed = tmp / "planimetria.pdf.p7m"
    signed.write_bytes(b"0")
    r = run.preflight(steps, values(steps=steps, answers=ANSWERS | {"planimetria": str(signed)}))
    assert not r["ready"] and "il file .p7m non si legge" in r["files"][0]["problem"], r["files"]
    for f in (big, huge, signed):
        f.unlink()
    tmp.rmdir()


def signed_file(tmp, name, cf, base64_text=False, content=b"%PDF-1.4 finto\n", pades=False):
    """A real CAdES .p7m (a self-signed certificate carrying cf as TINIT-cf, as a firma digitale's
    does), or with pades the PDF itself carrying a detached PKCS#7 as a PAdES one does: a
    /ByteRange and the signature in /Contents, padded with zeros."""
    import base64
    import shutil
    import subprocess
    openssl = shutil.which("openssl")
    key, crt, doc, out = tmp / "k.pem", tmp / "c.pem", tmp / "doc.pdf", tmp / name
    doc.write_bytes(content)
    subprocess.run([openssl, "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", str(key), "-out", str(crt),
                    "-days", "2", "-subj", f"/C=IT/O=Fittizio/CN=Firma Finta/serialNumber=TINIT-{cf}"],
                   check=True, capture_output=True)
    subprocess.run([openssl, "cms", "-sign", "-signer", str(crt), "-inkey", str(key), "-in", str(doc),
                    "-outform", "DER", "-out", str(out)] + ([] if pades else ["-nodetach"]) + ["-binary"],
                   check=True, capture_output=True)
    if pades:
        sig = out.read_bytes().hex().upper()
        out.write_bytes(content + b"1 0 obj\n<< /Type /Sig /Filter /Adobe.PPKLite /SubFilter /ETSI.CAdES.detached "
                        b"/ByteRange [0 100 200 300] /Contents <" + (sig + "0" * 2048).encode() + b"> >>\nendobj\n%%EOF\n")
    if base64_text:
        out.write_bytes(base64.encodebytes(out.read_bytes()))
    for f in (key, crt, doc):
        f.unlink()
    return out


# A PDF that declares PDF/A in its XMP, as an export to PDF/A writes it.
PDFA_CONTENT = (b"%PDF-1.7\n<x:xmpmeta xmlns:x=\"adobe:ns:meta/\"><rdf:RDF><rdf:Description "
                b"xmlns:pdfaid=\"http://www.aiim.org/pdfa/ns/id/\"><pdfaid:part>2</pdfaid:part>"
                b"<pdfaid:conformance>B</pdfaid:conformance></rdf:Description></rdf:RDF></x:xmpmeta>\n")


def napoli_filing():
    """Napoli's SUE (DD 501/2026): a file the run attaches must be PDF/A, signed digitally (a
    .p7m, or the PDF's own PAdES signature) and plainly named, else the pratica is irricevibile;
    made-up files are only warned about; the person is told how Firma e invio goes. A SUAP pratica
    isn't checked."""
    import shutil
    if not shutil.which("openssl"):
        return
    suap = copy.deepcopy(STEPS)
    suap["asks"]["relazione"] = {"type": "file", "question": "The relazione tecnica"}
    suap["sections"][-1]["fields"].append({"id": "r", "kind": "file", "label": "Relazione",
                                           "value": "{{ask.relazione}}"})
    sue = copy.deepcopy(suap)
    sue["start"] = "https://suap.impresainungiorno.gov.it/fnsuap/cmd/create?comune=F839&tipoSportello=E"
    tmp = Path(tempfile.mkdtemp(prefix="preflight-filing-"))
    own = "FTTGNR90E12F839R"

    def check(path, steps=sue, made_up=False):
        r = run.preflight(steps, values(steps=steps, answers=ANSWERS | {"relazione": str(path)}), made_up=made_up)
        return r, r["files"][0]
    plain = tmp / "relazione tecnica.pdf"
    plain.write_bytes(b"%PDF-1.4 non firmato\n")
    r, f = check(plain)
    assert not r["ready"] and all(w in f["problem"] for w in ("questo nome", "PDF/A", "firmati digitalmente")), f
    assert any(y.startswith("Il SUE di Napoli accetta solo file PDF/A") for y in r["yours"]), r["yours"]
    assert any("c/c postale 57060964" in y for y in r["yours"]), r["yours"]
    # Firma e invio is the person's (the portal opens it only with every signature valid): how to sign.
    assert any(y.startswith("In Firma e invio") and "distinta" in y for y in r["yours"]), r["yours"]
    # The same file with made-up data: ready, each refusal noted, and a warning never to send it.
    r, f = check(plain, made_up=True)
    assert r["ready"] and len(f["filing"]) == 3 and "problem" not in f, f
    assert r["warnings"][-1].startswith("made-up data: 1 file(s)"), r["warnings"]
    # PDF/A but unsigned: refused for its signature only.
    unsigned = tmp / "Relazione_tecnica.pdf"
    unsigned.write_bytes(PDFA_CONTENT)
    r, f = check(unsigned)
    assert not r["ready"] and "PDF/A" not in f["problem"] and "firmati digitalmente" in f["problem"], f
    # PDF/A signed in itself (PAdES), by the dichiarante: taken, its signer read as a .p7m's is.
    r, f = check(signed_file(tmp, "Relazione_firmata.pdf", own, content=PDFA_CONTENT, pades=True))
    assert r["ready"] and f["signers"] == 1 and f["signed_by_dichiarante"] is True, f
    # A .p7m: its content must be PDF/A.
    r, f = check(signed_file(tmp, "Relazione_tecnica.pdf.p7m", own, content=PDFA_CONTENT))
    assert r["ready"] and "problem" not in f, f
    r, f = check(signed_file(tmp, "Relazione_vecchia.pdf.p7m", own))
    assert not r["ready"] and f["problem"].endswith("(lo esporti di nuovo come PDF/A)"), f
    # A PDF that says it's signed and isn't readable as a signature: refused, as a bad .p7m is.
    broken = tmp / "Relazione_rotta.pdf"
    broken.write_bytes(PDFA_CONTENT + b"/ByteRange [0 1 2 3] /Contents <30" + b"AB" * 300 + b">")
    r, f = check(broken)
    assert not r["ready"] and "la firma dentro il PDF non si legge" in f["problem"], f
    # Not Napoli's SUE (the pizzeria's SUAP): none of this is checked.
    r, f = check(plain, steps=suap)
    assert r["ready"] and "problem" not in f and not any("PDF/A" in y for y in r["yours"]), (f, r["yours"])
    rehearsals = HERE.parents[4] / "rehearsals"
    assert run.filing_rules(yaml.safe_load((rehearsals / "cila-fittizia" / "portal-steps.generated.yaml").read_text()))
    assert run.filing_rules(STEPS) is None
    shutil_rmtree(tmp)


def p7m_signer():
    import shutil
    if not shutil.which("openssl"):
        return  # nothing to check with: p7m_signers says so and pre-flight lets the file through
    steps = copy.deepcopy(STEPS)
    steps["asks"]["planimetria"] = {"type": "file", "question": "The planimetria (signed)"}
    steps["sections"][-1]["fields"].append({"id": "p", "kind": "file", "label": "Planimetria",
                                            "value": "{{ask.planimetria}}"})
    tmp = Path(tempfile.mkdtemp(prefix="preflight-p7m-"))
    own, other = "FTTGNR90E12F839R", "RSSMRA80A01H501U"

    def check(path):
        return run.preflight(steps, values(steps=steps, answers=ANSWERS | {"planimetria": str(path)}), made_up=True)
    r = check(signed_file(tmp, "mio.pdf.p7m", own))
    assert r["ready"] and r["files"][0]["signed_by_dichiarante"] is True and not r["warnings"], r
    r = check(signed_file(tmp, "mio-b64.pdf.p7m", own, base64_text=True))
    assert r["ready"] and r["files"][0]["signed_by_dichiarante"] is True, "a base64 .p7m wasn't read"
    # Someone else's signature: a warning (a technician may be the one who signs), never a block,
    # and never the codici fiscali themselves: Claude reads this report.
    r = check(signed_file(tmp, "altro.pdf.p7m", other))
    assert r["ready"] and r["files"][0]["signed_by_dichiarante"] is False, r["files"]
    assert len(r["warnings"]) == 1 and "non dal dichiarante" in r["warnings"][0], r["warnings"]
    assert other not in json.dumps(r) and own not in json.dumps(r["files"]) + json.dumps(r["warnings"]), "a codice fiscale in the report"
    # Not a signature at all (an unsigned file renamed, a truncated download): not ready, and why.
    junk = tmp / "finto.pdf.p7m"
    junk.write_bytes(b"%PDF-1.4 non firmato\n")
    r = check(junk)
    assert not r["ready"] and "il file .p7m non si legge" in r["files"][0]["problem"], r["files"]
    shutil_rmtree(tmp)


def shutil_rmtree(p):
    import shutil
    shutil.rmtree(p, ignore_errors=True)


def bollo_chosen():
    # The imposta di bollo route is a choice made in the person's name: the review lists it
    # apart from the table of values, with the serials when marche are used.
    steps = copy.deepcopy(STEPS)
    steps["asks"]["serial"] = {"type": "text", "question": "Serial?"}
    steps["sections"].append({"section": "Dichiarazione relativa all'assolvimento dell'imposta di bollo", "fields": [
        {"kind": "radio", "label": "Il pagamento è dovuto e si intende assolvere l'obbligo tramite pagoPA"},
        {"kind": "text", "label": "numero seriale (1)", "value": "{{ask.serial}}"}]})
    shown = run.review_shown(steps, values(steps=steps, answers=ANSWERS | {"serial": "01234567890123"}))
    assert shown["decisions"] == [{"section": "Dichiarazione relativa all'assolvimento dell'imposta di bollo", "choices": [
        "Il pagamento è dovuto e si intende assolvere l'obbligo tramite pagoPA", "numero seriale (1): 01234567890123"]}], shown["decisions"]
    assert not run.review_shown(STEPS, values())["decisions"], "a pratica with no bollo section lists a decision"
    filled = {"procedure": "x", "result": "filled", "sections": [], "total_seconds": 1, "values": [], "yours": []}
    page = run.review.portal_review(filled | shown)
    assert "Scelto a suo nome" in page and "tramite pagoPA" in page and "01234567890123" in page
    assert "Scelto a suo nome" not in run.review.portal_review(filled | {"decisions": []})


def checklist_forms():
    # The items ticked as a list, or each item on its own: the same answer.
    each = {k: v for k, v in ANSWERS.items() if k != "extras"} | {
        k: k == "stagionale" for k in ("zona_tutelata", "alcolici", "musica", "insegna_esterna",
                                       "centro_commerciale", "stagionale")}
    listed = ANSWERS | {"extras": ["stagionale"]}
    a, b = run.page_scripts(STEPS, values(answers=each)), run.page_scripts(STEPS, values(answers=listed))
    assert a == b, "a list and per-item answers filled differently"
    r = run.preflight(STEPS, values(answers=ANSWERS | {"extras": ["vino"]}), made_up=True)
    assert r["questions"] and r["questions"][0]["key"] == "extras" and "error" in r["questions"][0], r["questions"]


def unused_ask():
    steps = copy.deepcopy(STEPS)
    steps["asks"]["colore"] = {"type": "text", "question": "Favourite colour?"}
    raises(lambda: run.preflight(steps, values(steps=steps), made_up=True), "no field reads asks.colore")


def not_needed_here():
    # A question only a field this case skips would read isn't asked; one a field reads
    # only if another answer says so says which.
    steps = copy.deepcopy(STEPS)
    steps["asks"]["data_stagione"] = {"type": "date", "question": "When does the season start?"}
    steps["sections"][0]["fields"].append({"id": "s", "kind": "text", "label": "Inizio stagione",
                                           "when": "{{ask.stagionale}}", "value": "{{ask.data_stagione}}"})
    r = run.preflight(steps, values(steps=steps), made_up=True)
    assert r["ready"] and not r["questions"], r["questions"]
    r = run.preflight(steps, values(steps=steps, answers=ANSWERS | {"extras": ["stagionale"]}), made_up=True)
    assert [q["key"] for q in r["questions"]] == ["data_stagione"], r["questions"]
    r = run.preflight(steps, values(steps=steps, answers={k: v for k, v in ANSWERS.items() if k != "extras"}), made_up=True)
    q = [q for q in r["questions"] if q["key"] == "data_stagione"]
    assert q and q[0]["only_if"] == ["stagionale"], r["questions"]


def proposals():
    # A proposal the vault can fill is offered for confirmation, not asked; confirmed, it's
    # an answer. One the vault can't fill falls back to the question.
    steps = copy.deepcopy(STEPS)
    steps["asks"]["insegna"]["propose"] = "{{business.denominazione}}"
    no_sign = {k: v for k, v in ANSWERS.items() if k != "insegna"}
    r = run.preflight(steps, values(steps=steps, answers=no_sign), made_up=True)
    assert [p["key"] for p in r["proposals"]] == ["insegna"], r["proposals"]
    assert r["proposals"][0]["proposal"] == FIELDS["business.denominazione"], r["proposals"]
    assert "insegna" not in [q["key"] for q in r["questions"]] and not r["ready"], r
    confirmed = no_sign | {"insegna": r["proposals"][0]["proposal"]}
    assert run.preflight(steps, values(steps=steps, answers=confirmed), made_up=True)["ready"]
    fields = {k: v for k, v in FIELDS.items() if k != "business.denominazione"}
    r = run.preflight(steps, values(steps=steps, answers=no_sign, fields=fields), made_up=True)
    assert "insegna" in [q["key"] for q in r["questions"]] and not r["proposals"], r
    steps["asks"]["alcolici"]["propose"] = "false"
    raises(lambda: run.preflight(steps, values(steps=steps), made_up=True), "no propose")


def sums():
    # A total the portal wants (rooms, beds) from what was asked: each term is a question.
    asks = {"a": {"type": "number", "question": "a", "default": "0"}, "b": {"type": "number", "question": "b"}}
    v = run.Values({"b": "3"}, fields={}, asks=asks)
    assert v.render("{{ask.a+2*ask.b}}") == "6", v.render("{{ask.a+2*ask.b}}")
    assert v.render("{{ask.a+ask.b|positive}}") == "true"
    assert run.Values({}, fields={}, asks=asks).render("{{ask.a+ask.b}}") is None  # b unanswered
    assert [r for r, _ in run.refs_in("{{ask.a+2*ask.b|positive}}")] == ["ask.a", "ask.b"]
    assert v.render("{{ask.b|atleast_3}} {{ask.b|atleast_4}}") == "true false"


def too_long():
    # A box's max is checked before the run: an answer is asked again, a vault value named.
    steps = copy.deepcopy(STEPS)
    asked = next(f for sec in steps["sections"] for f in sec["fields"]
                 if str(f.get("value", "")).startswith("{{ask.") and "when" not in f and "|" not in f["value"])
    vault = next(f for sec in steps["sections"] for f in sec["fields"]
                 if str(f.get("value", "")).startswith("{{business.denominazione") and "when" not in f)
    asked["max"], vault["max"] = 3, 3
    r = run.preflight(steps, values(steps=steps), made_up=True)
    key = asked["value"][6:].split("}")[0]
    assert any(q["key"] == key and "at most 3" in q.get("error", "") for q in r["questions"]), r["questions"]
    assert any("at most 3" in m["why"] for m in r["missing"]), r["missing"]
    assert not r["ready"]


def nested_when():
    """The CILA's quadro f: "oneroso, and then paid?" asks the second only once the first is
    yes; the tolerance details only once there are tolerances."""
    cila = HERE.parents[4] / "rehearsals" / "cila-fittizia"
    steps = yaml.safe_load((cila / "portal-steps.generated.yaml").read_text())
    fields = dict(json.loads((cila / "fixture-p6.json").read_text())["fields"])
    owner = json.loads((cila / "answers-proprietario.json").read_text())
    drop = {"cila_onerosa", "contributo_pagato", "ricevuta_contributo", "tolleranze", "tolleranze_tipi",
            "toll_superficie", "toll_strutturale"}
    base = {k: v for k, v in owner.items() if k not in drop}
    here = os.getcwd()
    os.chdir(HERE.parents[4])  # the answers name files from the repo's root
    try:
        ask = lambda a: {q["key"]: q for q in run.preflight(steps, values(a, fields, steps), made_up=True)["questions"]}
        # Unanswered, both are proposed (not onerosa, no tolerances): what a yes would open isn't
        # in the message, but kept under the proposal (`if_changed`) for a person who changes it.
        r = run.preflight(steps, values(base, fields, steps), made_up=True)
        q = {x["key"]: x for x in r["questions"]}
        assert "contributo_pagato" not in q and "toll_strutturale" not in q, list(q)
        assert "contributo_pagato" in r["if_changed"]["cila_onerosa"], r.get("if_changed")
        assert "toll_strutturale" in r["if_changed"]["tolleranze"], r.get("if_changed")
        q = ask(base | {"cila_onerosa": False, "tolleranze": False})
        assert not {"contributo_pagato", "ricevuta_contributo", "tolleranze_tipi", "toll_superficie", "toll_strutturale"} & set(q), q
        q = ask(base | {"cila_onerosa": True, "tolleranze": True})
        assert "only_if" not in q["contributo_pagato"] and q["ricevuta_contributo"]["only_if"] == ["contributo_pagato"], q
    finally:
        os.chdir(here)


def gated_support():
    """A `supports` check with `if` applies, and asks its question, only once the gate holds:
    how a permesso's contributo is paid matters only when one is due."""
    pdc = HERE.parents[4] / "rehearsals" / "pdc-fittizio"
    steps = yaml.safe_load((pdc / "portal-steps.generated.yaml").read_text())
    fields = dict(json.loads((HERE.parents[4] / "rehearsals" / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])
    p6 = json.loads((pdc / "answers-p6.json").read_text())
    base = {k: v for k, v in p6.items() if k not in ("scia_onerosa", "contributo_pagamento", "contributo_calcolo",
                                                     "documentazione_calcolo_contributo")}
    here = os.getcwd()
    os.chdir(HERE.parents[4])  # the answers name files from the repo's root
    try:
        pre = lambda a: run.preflight(steps, values(a, fields, steps), made_up=True)
        r = pre(base | {"scia_onerosa": "false", "contributo_normativa": "art. 17 (inventato)"})
        assert r["ready"] and not r["unsupported"], r
        # Unanswered, onerosa is proposed: how the contributo is paid is asked if it is onerosa,
        # in the message when the proposal says so, else kept for a change to it (`if_changed`).
        r = pre(base)
        q = {x["key"]: x for x in r["questions"]}
        held = (r.get("if_changed") or {}).get("scia_onerosa", [])
        assert (q.get("contributo_pagamento") or {}).get("only_if") == ["scia_onerosa"] or "contributo_pagamento" in held, (q.get("contributo_pagamento"), held)
        r = pre(p6 | {"contributo_pagamento": "pagato"})
        assert any("mai prima della presentazione" in u for u in r["unsupported"]), r["unsupported"]
        assert pre(p6)["ready"]
    finally:
        os.chdir(here)


def agibilita_systems():
    """The agibilità's systems: certified by their dichiarazione di conformità alone it fills; by
    others it asks system by system, one checklist a certificate (a filed one's P.G. only once
    ticked), and asks only with systems."""
    agi = HERE.parents[4] / "rehearsals" / "agibilita-fittizia"
    steps = yaml.safe_load((agi / "portal-steps.generated.yaml").read_text())
    fields = dict(json.loads((HERE.parents[4] / "rehearsals" / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])
    collaudo = json.loads((agi / "answers-collaudo.json").read_text())
    here = os.getcwd()
    os.chdir(HERE.parents[4])
    try:
        pre = lambda a: run.preflight(steps, values(a, fields, steps), made_up=True)
        assert pre(collaudo)["ready"]
        r = pre(collaudo | {"impianti_certificazione": "altro"})
        lists = {q["key"] for q in r["questions"] if q["type"] == "checklist"}
        assert not r["unsupported"] and lists == {"impianti_dichiarazione", "impianti_depositato", "impianti_collaudo",
                                                  "impianti_atto_notorio"}, r
        assert not any(q["key"].endswith("_pg") and not q.get("only_if") for q in r["questions"]), r["questions"]
        assert pre(json.loads((agi / "answers-impianti-depositati.json").read_text()))["ready"]
        none = {k: v for k, v in collaudo.items() if k != "impianti_certificazione"} | {"impianti": "false"}
        assert pre(none)["ready"], pre(none)
    finally:
        os.chdir(here)


def agibilita_slots():
    """The agibilità's systems decide its attachment slots (read on the portal 2026-10-31): the
    dichiarazione's slot only while some system has one (none when all are deposited); a
    collaudo or atto notorio opens its own required slot."""
    root = HERE.parents[4] / "rehearsals"
    fields = dict(json.loads((root / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])
    slots = {"Dichiarazione di conformità degli impianti", "Certificato di collaudo ove previsto, degli impianti installati",
             "Atto notorio relativo alla conformità degli impianti"}

    def filed(rehearsal, answers):
        steps = yaml.safe_load((root / rehearsal / "portal-steps.generated.yaml").read_text())
        a = json.loads((root / rehearsal / answers).read_text())
        return {f["label"] for f in rehearsal_plan(steps, values(a, fields, steps)) if f["kind"] == "file"} & slots

    here = os.getcwd()
    os.chdir(HERE.parents[4])
    try:
        assert filed("agibilita-fittizia", "answers-collaudo.json") == {"Dichiarazione di conformità degli impianti"}
        assert filed("agibilita-fittizia", "answers-impianti-depositati.json") == set()
        assert filed("agibilita-fittizia", "answers-impianti-collaudo.json") >= {
            "Certificato di collaudo ove previsto, degli impianti installati", "Atto notorio relativo alla conformità degli impianti"}
    finally:
        os.chdir(here)


def sanatoria_cases():
    """The SCIA in sanatoria: works in progress and double conformity fill, the payment by its estremi
    or its receipt; the conformity of art. 36-bis c. 1 and pre-1977 variants (art. 34-ter) are refused,
    each with its defect: the portal's asseverazione can't state either case."""
    d = HERE.parents[4] / "rehearsals" / "scia-sanatoria-fittizia"
    steps = yaml.safe_load((d / "portal-steps.generated.yaml").read_text())
    fields = dict(json.loads((HERE.parents[4] / "rehearsals" / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])
    p6 = json.loads((d / "answers-p6.json").read_text())
    here = os.getcwd()
    os.chdir(HERE.parents[4])
    try:
        pre = lambda a: run.preflight(steps, values(a, fields, steps), made_up=True)
        for a in ("in-corso", "ricevuta", "in-corso-ricevuta"):
            assert pre(json.loads((d / f"answers-{a}.json").read_text()))["ready"], a
        assert pre(p6)["ready"]
        # The receipt has no slot of its own: the person attaches it signed, so pre-flight asks no file.
        r = pre(p6 | {"sanatoria_prova": "ricevuta"})
        assert r["ready"] and not r["questions"], r["questions"]
        r = pre(p6 | {"sanatoria_caso": "conformita urbanistica"})
        assert any("difetto del portale" in u for u in r["unsupported"]), r["unsupported"]
        # The known defect comes with it, for the person to choose (defects.yaml through gen.py).
        assert [d["id"] for d in r["defects"]] == ["scia-36bis-c1"] and len(r["defects"][0]["choices"]) == 3, r.get("defects")
        r = pre(p6 | {"sanatoria_caso": "variante pre 1977"})
        assert any("art. 34-ter" in u and "difetto del portale" in u for u in r["unsupported"]), r["unsupported"]
        assert [d["id"] for d in r["defects"]] == ["scia-34ter"], r.get("defects")
    finally:
        os.chdir(here)


def scelte_follow_the_case():
    """A wizard choice a recipe takes only for some cases ({leaf, when}): ticked, with the section
    it adds, only when the case's answer says so; asked when unanswered; several co-holders, each
    a block of the section by its "+" (the voltura, the cambio d'intestazione, a proroga)."""
    root = HERE.parents[4] / "rehearsals"
    fields = dict(json.loads((root / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])
    here = os.getcwd()
    os.chdir(HERE.parents[4])

    def load(name):
        steps = yaml.safe_load((root / name / "portal-steps.generated.yaml").read_text())
        return steps, (lambda a: values(json.loads((root / name / f"answers-{a}.json").read_text()) if isinstance(a, str) else a, fields, steps))

    def ticks(steps, v):
        w = next(w for w in run.expand(steps, v)["wizard"] if w["screen"] == "Scelte eventuali")
        return run.leaves(w)
    try:
        steps, v = load("voltura-pdc-fittizia")
        coholder = "Informazioni su eventuali altri aventi titolo"
        for a, has in (("p6", True), ("senza-cointestatari", False)):
            assert run.preflight(steps, v(a), made_up=True)["ready"], a
            assert ("ci sono cointestatari" in ticks(steps, v(a))) == has, a
            assert any(s["section"] == coholder for s in run.expand(steps, v(a))["sections"]) == has, a
        p6 = json.loads((root / "voltura-pdc-fittizia" / "answers-p6.json").read_text())
        r = run.preflight(steps, v({k: x for k, x in p6.items() if k != "cointestatario"}), made_up=True)
        # Proposed (none) for the person to confirm, never assumed.
        assert [q["key"] for q in r["proposals"]] == ["cointestatario"] and not r["ready"], r["proposals"]
        # More co-holders, one block each by the section's "+" (2026-11-05: the coholders-one
        # defect was wrong); one unasked while the job names no `a2:`.
        assert "cointestatari_quanti" not in str(run.preflight(steps, v("p6"), made_up=True)["proposals"])
        three = json.loads((root / "voltura-pdc-fittizia" / "answers-tre-cointestatari.json").read_text())
        r = run.preflight(steps, v({k: x for k, x in three.items() if k != "cointestatari_quanti"}), made_up=True)
        assert {"key": "cointestatari_quanti", "proposal": "3"}.items() <= next(
            p for p in r["proposals"] if p["key"] == "cointestatari_quanti").items(), r["proposals"]
        assert run.preflight(steps, v(three), made_up=True)["ready"]
        sec = next(s for s in run.expand(steps, v(three))["sections"] if s["section"] == coholder)
        live = [f for f in sec["fields"] if run.truthy(v(three).render(f.get("when", "true")) or "")]
        assert [f["kind"] for f in live].count("add") == 2 and [f.get("label") for f in live].count("sesso: M") == 3, live

        steps, v = load("cambio-intestazione-fittizio")
        assert len(ticks(steps, v("p6"))) == 1
        assert len(ticks(steps, v("subentro"))) == 4 and run.preflight(steps, v("subentro"), made_up=True)["ready"]
        sub = json.loads((root / "cambio-intestazione-fittizio" / "answers-subentro.json").read_text())
        r = run.preflight(steps, v(sub | {"cambio_dl": False, "cambio_ditta": False}), made_up=True)
        assert any("indichi quale" in u for u in r["unsupported"]), r["unsupported"]

        steps, v = load("proroga-paesaggistica-fittizia")
        assert len(ticks(steps, v("p6"))) == 1 and len(ticks(steps, v("assenso"))) == 2
    finally:
        os.chdir(here)


def assents_and_filings():
    """The CILA relazione's lists as the national form words them (2026-11-03): filings presented
    with it and assents the SUE acquires (art. 23-bis DPR 380/2001), each with its slot; assents
    to acquire mean no start date, and works under way can't wait for one. The CIL lists filings
    only. A partial fine lavori attaches its planimetria in the slot the answer adds."""
    root = HERE.parents[4] / "rehearsals"
    fields = dict(json.loads((root / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])
    here = os.getcwd()
    os.chdir(HERE.parents[4])

    def case(name, answers):
        steps = yaml.safe_load((root / name / "portal-steps.generated.yaml").read_text())
        return steps, (lambda a: values(a, fields, steps)), json.loads((root / name / f"answers-{answers}.json").read_text())

    def attached(r):  # what the case attaches, each "section: slot", and the file
        return [(f["for"], Path(f["path"]).name) for f in r["files"]]
    try:
        steps, v, a = case("cila-fittizia", "direttore-atti")
        r = run.preflight(steps, v(a), made_up=True)
        got = attached(r)
        assert r["ready"] and ("Gestione degli allegati: Documentazione necessaria per il rilascio di atti di assenso obbligatori", "documentazione-assensi.pdf") in got, got
        assert ("Gestione degli allegati: Documentazione necessaria per la presentazione di altre comunicazioni, segnalazioni", "documentazione-comunicazioni.pdf") in got, got
        r = run.preflight(steps, v(a | {"inizio_dopo_assensi": "false", "data_inizio_lavori": "2026-12-01"}), made_up=True)
        assert any("iniziano dopo la sua comunicazione" in u for u in r["unsupported"]), r["unsupported"]
        r = run.preflight(steps, v(a | {"cila_stato": "in corso", "ricevuta_sanzione": "rehearsals/cila-fittizia/files/ricevuta-sanzione.pdf"}), made_up=True)
        assert any("non possono avere assensi ancora da acquisire" in u for u in r["unsupported"]), r["unsupported"]
        # An authorization already obtained isn't one to acquire: the bene culturale lists none.
        steps, v, a = case("cila-fittizia", "bene-culturale")
        assert a["atti_da_acquisire"] is False and run.preflight(steps, v(a), made_up=True)["ready"]

        steps, v, a = case("cil-fittizia", "comunicazioni")
        r = run.preflight(steps, v(a), made_up=True)
        # Their documents under Allegati liberi, the runner's since 2026-11-03 (a slot named again
        # takes its next box), no longer the person's.
        assert r["ready"] and ("Gestione degli allegati: Allegati liberi", "documentazione-comunicazioni.pdf") in attached(r), attached(r)
        assert not any("quadro e" in y for y in r["yours"]), r["yours"]
        r = run.preflight(steps, v(a | {"atti_da_acquisire": True}), made_up=True)
        assert any("non prevede la richiesta di assensi" in u for u in r["unsupported"]), r["unsupported"]

        steps, v, a = case("fine-lavori-fittizia", "parziale")
        r = run.preflight(steps, v(a), made_up=True)
        assert r["ready"] and ("Gestione degli allegati: Copia di elaborato planimetrico del progetto con eventuali varianti", "planimetria-parte-ultimata.pdf") in attached(r), attached(r)
        steps, v, a = case("fine-lavori-fittizia", "p6")
        assert not [x for x in attached(run.preflight(steps, v(a), made_up=True)) if x[1] == "planimetria-parte-ultimata.pdf"]
    finally:
        os.chdir(here)


def catasto_terreni():
    """A unit with a categoria in the vault is in the Catasto Fabbricati, unasked; a plot (the
    a made-up company's plot (lotto), no categoria) only in the Catasto Terreni: its radio, foglio and
    particella, no subalterno or categoria (the permesso's new building on free land)."""
    d = HERE.parents[4] / "rehearsals" / "pdc-fittizio"
    steps = yaml.safe_load((d / "portal-steps.generated.yaml").read_text())
    fields = dict(json.loads((HERE.parents[4] / "rehearsals" / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])
    here = os.getcwd()
    os.chdir(HERE.parents[4])
    try:
        def ticked(a):
            v = values(json.loads((d / f"answers-{a}.json").read_text()), fields, steps)
            assert run.preflight(steps, v, made_up=True)["ready"], a
            sec = next(s for s in run.expand(steps, v)["sections"] if s["section"] == "Dati catastali")
            return [f["label"] for f in sec["fields"] if run.truthy(v.render(f.get("when", "true")) or "")]
        assert ticked("p6")[0] == "Nuovo Catasto Edilizio Urbano" and "categoria" in ticked("p6")
        assert ticked("terreno") == ["Nuovo Catasto Terreni", "foglio", "particella/mappale", "sezione Censuaria"], ticked("terreno")
        # No categoria in the vault and no answer: asked, never assumed either way.
        a = json.loads((d / "answers-p6.json").read_text())
        no_cat = {k: x for k, x in fields.items() if k != "luca:immobile.catasto_categoria"}
        r = run.preflight(steps, values(a, no_cat, steps), made_up=True)
        assert "catasto_terreni" in [q["key"] for q in r["questions"]], r["questions"]
    finally:
        os.chdir(here)


def cadastral_units():
    """Several units (the client's immobile, immobile2 ...): one unit unasked, as before; a second
    in the vault proposes the count, never assumes it; each unit after the first takes its own
    block by the unit's "+", the radios once; a unit in the other catasto by the group's "+" and
    that group's own radio; a third group (back to the first catasto) the same way."""
    d = HERE.parents[4] / "rehearsals" / "cila-fittizia"
    steps = yaml.safe_load((d / "portal-steps.generated.yaml").read_text())
    fields = dict(json.loads((d / "fixture-p6.json").read_text())["fields"])
    here = os.getcwd()
    os.chdir(HERE.parents[4])
    try:
        def catastali(a, flds=fields):
            v = values(a, flds, steps)
            sec = next(s for s in run.expand(steps, v)["sections"] if s["section"] == "Dati catastali")
            return [(f["kind"], f.get("label"), v.render(f["value"]) if "value" in f else f.get("nth"), f.get("block"))
                    for f in sec["fields"] if run.truthy(v.render(f.get("when", "true")) or "")]
        one = json.loads((d / "answers-proprietario.json").read_text())
        r = run.preflight(steps, values(one, fields, steps), made_up=True)
        assert r["ready"] and "unita_catastali" not in str(r["proposals"]), r["proposals"]
        assert [x for x in catastali(one) if x[0] == "add"] == [], catastali(one)
        two = json.loads((d / "answers-accorpamento.json").read_text())
        unasked = {k: x for k, x in two.items() if k != "unita_catastali"}
        r = run.preflight(steps, values(unasked, fields, steps), made_up=True)
        assert {"key": "unita_catastali", "proposal": "2"}.items() <= next(
            p for p in r["proposals"] if p["key"] == "unita_catastali").items(), r["proposals"]
        assert run.preflight(steps, values(two, fields, steps), made_up=True)["ready"]
        rows = catastali(two)
        assert [x[1] for x in rows].count("Nuovo Catasto Edilizio Urbano") == 1, rows
        assert ("add", None, None, 2) in rows and ("add", None, 2, 2) not in rows, rows
        assert ("text", "se non presente indicare il numero 0", "8", 2) in rows, rows
        assert ("text", "se non presente indicare il numero 0", "7", 1) in rows, rows
        # A flat, then its garden plot: the group's "+" (the second), its Catasto Terreni radio
        # (the page's last NCT), the plot's foglio and particella, no subalterno or categoria.
        mixed = json.loads((d / "answers-catasti-misti.json").read_text())
        assert run.preflight(steps, values(mixed, fields, steps), made_up=True)["ready"]
        rows = catastali(mixed)
        assert ("add", None, 2, 2) in rows and ("add", None, None, 2) not in rows, rows
        assert ("radio", "NCT", None, 2) in rows, rows
        assert [x for x in rows if x[3] == 2 and x[0] == "text"] == [
            ("text", "foglio", "12", 2), ("text", "particella/mappale", "679", 2), ("text", "sezione Censuaria", None, 2)], rows
        # Asked, not assumed: a unit with no categoria in the vault may be a flat missing it.
        r = run.preflight(steps, values({k: x for k, x in mixed.items() if k != "catasto_terreni2"}, fields, steps), made_up=True)
        assert "catasto_terreni2" in [q["key"] for q in r["questions"]], r["questions"]
        # A flat, two plots, a garage: three groups (back to the first catasto). Each change of
        # catasto is the group's "+" and that group's radio, the middle group's second plot its
        # unit's "+"; units count across groups, so the garage is block 4.
        three = json.loads((d / "answers-catasti-tre-gruppi.json").read_text())
        r = run.preflight(steps, values(three, fields, steps), made_up=True)
        assert r["ready"] and not r["unsupported"], r["unsupported"]
        rows = catastali(three)
        assert [x for x in rows if x[0] == "add"] == [("add", None, 2, 2), ("add", None, None, 3), ("add", None, 2, 4)], rows
        assert ("radio", "NCT", None, 2) in rows and ("radio", "NCEU", None, 4) in rows, rows
        assert not any(x[0] == "radio" and x[3] == 3 for x in rows), rows
        assert ("text", "se non presente indicare il numero 0", "5", 4) in rows, rows
        # Two cases of one pratica with other counts get their own steps in the pane, from steps
        # expanded already too, as rerun.py passes them (2026-11-05: they shared one key, and the
        # catasto case ran on the three holders' steps).
        holders = json.loads((d / "answers-comproprietari-tre.json").read_text())
        keys = set()
        for a in (three, holders):
            v = values(a, fields, steps)
            for st in (run.phase(steps, made_up=True), run.rehearsal(steps, v)):
                _, parts = run.page_bundle(st, v, files_limit=None, pick=False)
                keys.add(next(k for k in parts if k.startswith("pv-steps:")))
        assert len(keys) == 2 and all("#" in k for k in keys), keys
    finally:
        os.chdir(here)


def third_firm():
    """The firms repeat by "+" (`f1:`, `f2:`, `f3:` ...: 2026-11-05, the "+" lists the crawls saw,
    each held to a mapping): a third firm's block is filled, its Cassa edile rows too, and the
    count is never silent once the job names more than one. The landscape form's second
    technician beside the architect presenting is refused with the portal's defect."""
    root = HERE.parents[4] / "rehearsals"
    d = root / "cila-fittizia"
    steps = yaml.safe_load((d / "portal-steps.generated.yaml").read_text())
    fields = dict(json.loads((d / "fixture-p6.json").read_text())["fields"])
    here = os.getcwd()
    os.chdir(HERE.parents[4])
    try:
        p6 = json.loads((d / "answers-p6.json").read_text())
        three = p6 | {"people": p6["people"] | {"f3": "muratori"}}
        three.pop("imprese_quante")
        assert not run.preflight(steps, values(three, fields, steps), made_up=True)["ready"]  # the count is asked
        case = json.loads((d / "answers-imprese-tre.json").read_text())
        v = values(case, fields, steps)
        assert run.preflight(steps, v, made_up=True)["ready"]
        firms = [p["value"] for p in run.plan(run.rehearsal(steps, v), v)
                 if p["section"].startswith("h) Impresa") and p.get("label") == "Ragione sociale"]
        assert firms == ["Edil Fittizia di Marco Esempio", "Impianti Fittizi S.n.c.", "Muratori Fittizi S.r.l."], firms
        o = root / "paesaggistica-ordinaria-fittizia"
        ost = yaml.safe_load((o / "portal-steps.generated.yaml").read_text())
        op6 = json.loads((o / "answers-p6.json").read_text())
        r = run.preflight(ost, values(op6 | {"people": op6["people"] | {"p2": "elena"}}, fields, ost), made_up=True)
        assert not r["ready"] and "paesaggio-altri-tecnici" in json.dumps(r), r.get("unsupported")
        tre = json.loads((o / "answers-tecnici-tre.json").read_text())
        v = values(tre, fields, ost)
        assert run.preflight(ost, v, made_up=True)["ready"]
        names = [p["value"] for p in run.plan(run.rehearsal(ost, v), v) if p.get("label") == "cognome"]
        assert names == ["DISEGNO", "PROVA", "ESEMPIO"], names
    finally:
        os.chdir(here)


def group_two_choices():
    """A variant to a landscape authorization ticks its box and gives that one's details; an
    ordinaria's renewal with design changes ticks its box, a semplificata's is refused (no box);
    an architect born abroad (birth province EE) is "all'Estero" with the Stato, not "in Italia"."""
    root = HERE.parents[4] / "rehearsals"
    fields = dict(json.loads((root / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])
    here = os.getcwd()
    os.chdir(HERE.parents[4])

    def labels(name, a, flds=fields, section=None):
        steps = yaml.safe_load((root / name / "portal-steps.generated.yaml").read_text())
        v = values(json.loads((root / name / f"answers-{a}.json").read_text()) if isinstance(a, str) else a, flds, steps)
        r = run.preflight(steps, v, made_up=True)
        return r, [(p["label"], p["value"]) for p in rehearsal_plan(steps, v) if section is None or p["section"].startswith(section)] if r["ready"] else []
    try:
        _, b = labels("paesaggistica-semplificata-fittizia", "variante", section="Ambito")
        assert ("In caso di intervento in VARIANTE", None) in b and ("Num.", "PG/2025/0444444") in b, b
        _, b = labels("paesaggistica-semplificata-fittizia", "p6", section="Ambito")
        assert not any(l == "In caso di intervento in VARIANTE" for l, _ in b), b
        _, b = labels("rinnovo-paesaggistica-fittizia", "variazioni", section="Qualificazione")
        assert any(l == "sono richieste variazioni progettuali" for l, _ in b), b
        a = json.loads((root / "rinnovo-paesaggistica-fittizia" / "answers-p6.json").read_text())
        r, _ = labels("rinnovo-paesaggistica-fittizia", a | {"paes_rinnovo_variazioni": True})
        assert any("non ha una casella per le modifiche progettuali" in u for u in r["unsupported"]), r["unsupported"]
        # The studio's titolare (chiara) born in Buenos Aires.
        abroad = fields | {"chiara:identity.birth_province": "EE", "chiara:identity.birth_country": "ARGENTINA",
                           "chiara:identity.birth_comune": "Buenos Aires"}
        _, b = labels("cila-fittizia", "p6", abroad, "Qualifica e dati del procuratore")
        assert ("all'Estero", None) in b and ("Stato", "ARGENTINA") in b and not any(l == "in Italia" for l, _ in b), b
        _, b = labels("cila-fittizia", "p6", fields, "Qualifica e dati del procuratore")
        assert ("in Italia", None) in b and not any(l == "Stato" for l, _ in b), b
    finally:
        os.chdir(here)


def exemptions_and_other_kinds():
    """The bollo: proposed "no" for any client (a farmer can be exempt too), an exemption ticks its
    reason whatever its spacing, a virtual payment its radio and upload, and the person's step
    follows the case. The diritti's exemption and its reason (a text box, never a textarea the
    page can't find); the permesso's "altro" and the SCIA alternativa's regional works; a studio's
    other architect named as `t`, one with nothing in the vault reported, not guessed."""
    root = HERE.parents[4] / "rehearsals"
    fields = dict(json.loads((root / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])
    here = os.getcwd()
    os.chdir(HERE.parents[4])

    def case(name, a):
        steps = yaml.safe_load((root / name / "portal-steps.generated.yaml").read_text())
        v = values(json.loads((root / name / f"answers-{a}.json").read_text()) if isinstance(a, str) else a, fields, steps)
        r = run.preflight(steps, v, made_up=True)
        return r, ([(p["label"] or "", p["value"]) for p in rehearsal_plan(steps, v)] if r["ready"] else [])
    semplificata = "paesaggistica-semplificata-fittizia"
    try:
        for a in ("p6", "bollo-virtuale"):
            base = json.loads((root / semplificata / f"answers-{a}.json").read_text())
            base.pop("bollo_esenzione")
            r, _ = case(semplificata, base)
            assert ("bollo_esenzione", "no") in [(p["key"], p["proposal"]) for p in r["proposals"]], (a, r["proposals"])
        # An exempt client isn't asked how it pays; one that pays is, once that's known.
        unasked = json.loads((root / semplificata / "answers-esenzioni.json").read_text())
        unasked.pop("bollo_marche")
        r, _ = case(semplificata, unasked)
        assert r["ready"] and not any(p["key"] == "bollo_marche" for p in r["proposals"]), r["proposals"]
        paying = json.loads((root / semplificata / "answers-p6.json").read_text())
        paying.pop("bollo_marche"); paying.pop("bollo_esenzione")
        r, _ = case(semplificata, paying)
        # (the ONLUS follow-up waits on the exemption: `only_if`; how it is paid is proposed in the
        # same message, worded from the exemption proposed with it: `assumes`, or per answer: `cases`)
        plain = [p["key"] for p in r["proposals"] if p["key"].startswith("bollo") and not p.get("only_if")
                 and not p.get("assumes") and not p.get("cases")]
        assert plain == ["bollo_esenzione"], r["proposals"]
        marche = [p for p in r["proposals"] if p["key"] == "bollo_marche"]
        assert marche and (marche[0].get("assumes") == ["bollo_esenzione"] or marche[0].get("cases")), marche
        r, b = case(semplificata, "esenzioni")
        assert ("Il pagamento non è dovuto poiché esentati", None) in b and not any(l.startswith("Il pagamento è dovuto") for l, _ in b), b
        assert ("per la seguente motivazione", run.BOLLO_ESENZIONE["cooperativa sociale"]) in b, b
        assert ("poiché esentati", None) in b and any(l == "specificare la motivazione" and v for l, v in b), b
        assert any(y.startswith("Nessuna imposta di bollo da pagare") for y in r["yours"]) and not any("pagoPA" in y for y in r["yours"]), r["yours"]
        spaced = json.loads((root / semplificata / "answers-esenzioni.json").read_text()) | {"bollo_esenzione": "cooperativa sociale "}
        _, b2 = case(semplificata, spaced)
        assert [x for x in b2 if x[0].startswith(("Il pagamento", "per la seguente"))] == [x for x in b if x[0].startswith(("Il pagamento", "per la seguente"))], b2
        # An ONLUS only for a tax year begun before 2026, when the regime ended.
        onlus = json.loads((root / semplificata / "answers-esenzioni.json").read_text()) | {"bollo_esenzione": "onlus"}
        r, _ = case(semplificata, onlus | {"bollo_onlus_esercizio": False})
        assert any("esenzione ONLUS è cessata" in u for u in r["unsupported"]), r["unsupported"]
        r, b = case(semplificata, onlus | {"bollo_onlus_esercizio": True})
        assert ("per la seguente motivazione", run.BOLLO_ESENZIONE["onlus"]) in b, b
        r, b = case(semplificata, "bollo-virtuale")
        assert any(l.startswith("Per gli Enti autorizzati") for l, _ in b), b
        assert ("dichiarazione relativa all'assolvimento dell'imposta di bollo", "rehearsals/scia-fittizia/files/dichiarazione-bollo-virtuale.pdf") in b, b
        r, _ = case(semplificata, "p6")
        assert "Paghi l'imposta di bollo con pagoPA, come chiede il portale" in r["yours"], r["yours"]
        # The reason's box, wherever the crawl didn't see it (a SUAP draft), goes as the text box it reads as.
        for name in ("dehors-fittizio", "cila-fittizia"):
            steps = yaml.safe_load((root / name / "portal-steps.generated.yaml").read_text())
            box = [f for s in steps["sections"] for f in s["fields"] if f.get("label") == "specificare la motivazione"]
            assert box and all(f["kind"] == "text" for f in box), (name, box)
        _, b = case("pdc-fittizio", "altro")
        assert ("altro non indicato nei punti precedenti", None) in b and ("interventi di cui all'articolo 10", None) in b, b
        _, b = case("scia-alternativa-fittizia", "regionale")
        assert ("4. Altri interventi individuati dalla legislazione regionale", None) in b, b
        assert not any(l.startswith("1. Interventi di ristrutturazione") for l, _ in b), b
        _, b = case("cila-fittizia", "procuratore-estero")
        assert ("Nome", "Sofia") in b and ("Stato", "Argentina") in b, b
        a = json.loads((root / "cila-fittizia" / "answers-procuratore-estero.json").read_text())
        r, _ = case("cila-fittizia", a | {"people": a["people"] | {"t": "nessuno"}})
        assert not r["ready"] and "nessuno" in r["missing"][0]["why"], r["missing"]
    finally:
        os.chdir(here)


def carica_not_crash():
    """An architect named in `people` who isn't the titolare has no Carica on the portal: pre-flight
    names the box (the run would have crashed on it), and the titolare's own still passes."""
    steps = {"sections": [{"section": "Scheda anagrafica", "fields": [
        {"id": "x", "kind": "select", "label": "Carica", "value": "{{t:ruolo.tipo|carica}}"}]}]}
    flds = {"chiara:ruolo.tipo": "titolare", "sofia:ruolo.tipo": "collaboratore", "sofia:identity.first_name": "Sofia"}
    r = run.preflight(steps, run.Values({"people": {"t": "sofia"}}, fields=flds, asks={}), made_up=True)
    assert not r["ready"] and any("carica" in m["field"] and "Scheda anagrafica" in m["why"] for m in r["missing"]), r["missing"]
    r = run.preflight(steps, run.Values({}, fields=flds, asks={}), made_up=True)
    assert r["ready"], r


def materiali_di_risulta_agree():
    """The asseverazione's materiali di risulta say what the terre e rocce filings file (2026-11-03:
    the SCIA with its dichiarazione declared "nessuno"): by-products with the dichiarazione or the
    piano, and the small-site line with the dichiarazione, the large one with the piano."""
    root = HERE.parents[4] / "rehearsals"
    fields = dict(json.loads((root / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])
    d = root / "scia-terre-rocce-fittizia"
    steps = yaml.safe_load((d / "portal-steps.generated.yaml").read_text())
    base = json.loads((d / "answers-p6.json").read_text())
    pre = lambda a: run.preflight(steps, run.Values(a, fields=fields, asks=steps["asks"]), made_up=True)
    # The steps name their files from the repo's root.
    here = os.getcwd()
    os.chdir(HERE.parents[4])
    try:
        assert pre(base)["ready"]
        for change, words in (({"scavo": "nessuno"}, "devono essere dichiarati come sottoprodotti"),
                              ({"scavo_piano_utilizzo": "true"}, "non la voce dell'asseverazione per i grandi cantieri"),
                              ({"terre_rocce": "no"}, "non ha né la dichiarazione")):
            r = pre({**base, **change})
            assert not r["ready"] and any(words in u for u in r["unsupported"]), (change, r["unsupported"])
        # Proposed from the table's answer, for a case that hasn't said.
        a = {k: v for k, v in base.items() if k not in ("scavo", "scavo_piano_utilizzo")}
        props = {p["key"]: p["proposal"] for p in pre(a)["proposals"]}
        assert props.get("scavo") == "sottoprodotti", props
    finally:
        os.chdir(here)


def every_sue_case_ready():
    """Every SUE rehearsal's every answers file pre-flights ready, but those refused on purpose: a
    case that stops being ready drops out of the counts without a word (schema_branches.py skips
    it): a new question proposed instead of answered from the vault would have stopped some 170 at
    once (the land register, 2026-11-02). And only the registered company's case can't pass the
    portal on made-up data (`made_up_stops`)."""
    root = HERE.parents[4] / "rehearsals"
    fields = dict(json.loads((root / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])
    refused = {("scia-fittizia", "answers-cambio-immobile-6bis.json"): "Questo caso è un'altra pratica",
               ("pdc-sanatoria-fittizio", "answers-parziale.json"): "Permesso in sanatoria dell'art. 36-bis",
               ("parere-esonero-fittizio", "answers-p6.json"): "A Napoli il Comune non rilascia",
               ("cila-fittizia", "answers-impresa-dopo.json"): "La CILA indica la sua impresa esecutrice",
               # The permesso's landscape quadro has no line for the art. 167 accertamento (pdc-36-paesaggio).
               ("pdc-sanatoria-accertamento-fittizio", "answers-p6.json"): "Sanatoria dell'art. 36 in area tutelata",
               # A whole building to another category: no change-of-use line states it (cambio-uso-regionale).
               ("pdc-sanatoria-fittizio", "answers-cambio-intero.json"): "Il modulo non ha una voce per questo cambio d'uso"}
    here, seen, stops = os.getcwd(), 0, set()
    os.chdir(HERE.parents[4])
    try:
        for d in sorted(root.iterdir()):
            f = d / "portal-steps.generated.yaml"
            if not f.is_file() or gen.resolved(gen.load_yaml(d / "recipe.yaml")).get("sportello") != "sue":
                continue
            steps = yaml.safe_load(f.read_text())
            for a in sorted(d.glob("answers*.json")):
                seen += 1
                r = run.preflight(steps, values(json.loads(a.read_text()), fields, steps), made_up=True)
                if (d.name, a.name) in refused:
                    assert r["unsupported"][0].startswith(refused[d.name, a.name]), (d.name, a.name, r["unsupported"])
                    continue
                assert r["ready"], (d.name, a.name, {k: r[k] for k in ("unsupported", "questions", "proposals", "missing") if r[k]})
                if r["made_up_stops"]:
                    stops.add((d.name, a.name))
    finally:
        os.chdir(here)
    assert seen > 150, seen
    assert stops == {("cila-fittizia", "answers-societa.json")}, stops


def streets_and_lists():
    """A street that isn't a Via, Viale, Piazza, Corso or Largo (a third of Naples') is ALTRO with
    its type in "Dettaglio DUG", the name after it; a type the portal lists nowhere (Naples' cupe) is
    named by pre-flight. Citizenship takes a masculine adjective and a country's name; any of the
    107 province sigle has its name (2026-11-04)."""
    root = HERE.parents[4] / "rehearsals" / "cila-fittizia"
    fields = dict(json.loads((root / "fixture-p6.json").read_text())["fields"])
    a = json.loads((root / "answers-p6.json").read_text())
    steps = yaml.safe_load((root / "portal-steps.generated.yaml").read_text())
    client = a["people"]["c"]

    def street(addr):
        v = values(a, fields | {f"{client}:residenza.indirizzo": addr}, steps)
        r = run.preflight(steps, v, made_up=True)
        if not r["ready"]:
            return r, None
        boxes = ("Toponimo (DUG)", "da compilare obbligatoriamente", "Denominazione stradale")
        return r, [(x["label"], x["value"]) for x in rehearsal_plan(steps, v)
                   if x["section"] == "Scheda anagrafica" and x["label"] in boxes][:3]
    here = os.getcwd()
    os.chdir(HERE.parents[4])
    try:
        _, got = street("Via Toledo")
        assert got == [("Toponimo (DUG)", "VIA"), ("Denominazione stradale", "TOLEDO")], got
        _, got = street("Vico Lungo Gelso")
        assert got == [("Toponimo (DUG)", "ALTRO"), ("da compilare obbligatoriamente", "VICO"),
                       ("Denominazione stradale", "LUNGO GELSO")], got
        _, got = street("Capo di Piazza Mercato")
        assert got[1] == ("da compilare obbligatoriamente", "CAPO DI PIAZZA") and got[2][1] == "MERCATO", got
        r, _ = street("Cupa Caiafa")
        assert not r["ready"] and "no street type the portal lists" in r["missing"][0]["why"], r["missing"]
        # `page` without pre-flight says the same and stops, not a traceback.
        cupa = values(a, fields | {f"{client}:residenza.indirizzo": "Cupa Caiafa"}, steps)
        raises(lambda: run.page_files(run.rehearsal(steps, cupa), cupa), "no street type the portal lists")
        for cit, country in (("moldavo", "MOLDAVIA"), ("Moldavia", "MOLDAVIA"), ("britannica", "REGNO UNITO")):
            assert run.FILTERS["cittadinanza"](cit) == country, cit
        r = run.preflight(steps, values(a, fields | {f"{client}:identity.citizenship": "tagika"}, steps), made_up=True)
        assert not r["ready"] and "no Cittadinanza for 'tagika'" in r["missing"][0]["why"], r["missing"]
    finally:
        os.chdir(here)
    assert len(run.PROVINCE) == 107 and run.FILTERS["provincia_nome"]("ba") == "BARI"
    assert run.FILTERS["straniera"]("Italia") == "false" and run.FILTERS["straniera"]("moldava") == "true"


def wizard_description_too_long():
    """The pratica's description (the wizard's first box) takes 60 characters: a longer one is asked
    again at pre-flight, not met when the batch is built (2026-11-04: 88 characters passed)."""
    reh = HERE.parents[4] / "rehearsals" / "cil-fittizia"
    steps = yaml.safe_load((reh / "portal-steps.generated.yaml").read_text())
    fixture = dict(json.loads((HERE.parents[4] / "rehearsals" / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])
    answers = json.loads((reh / "answers-p6.json").read_text())
    here = os.getcwd()
    os.chdir(HERE.parents[4])  # the answers name their files from the repo's root
    try:
        ok = run.preflight(steps, values(answers=answers, fields=fixture, steps=steps), made_up=True)
        r = run.preflight(steps, values(answers={**answers, "descrizione": "PROVA NON INVIARE - " + "x" * 41},
                                        fields=fixture, steps=steps), made_up=True)
    finally:
        os.chdir(here)
    assert ok["ready"], ok["questions"]
    q = [q for q in r["questions"] if q["key"] == "descrizione"]
    assert q and "at most 60" in q[0]["error"] and not r["ready"], r["questions"]


def diritti_brackets():
    """The SUE's 2026 table (G.C. 239/2026) at its edges: SUE 7-9 by the contributo ("fino a
    € 5.000,00", "da € 5.000,00 ad € 30.000", "oltre € 30.000,00": exactly 5,000 € is in two rows),
    SUE 4-6 by the car park's floor area ("fino a 300 mq", "da 301 mq a 1000 mq", "oltre 1001 mq":
    what falls between is in none). Where the table can't tell, nothing is proposed."""
    c = run.FILTERS["diritti_scia_alt"]
    for contributo, want in (("1", "1003"), ("4999,99", "1003"), ("5000", ""), ("5000.00", ""), ("5000,01", "1505"),
                             ("12500", "1505"), ("12500,50", "1505"), ("30000", "1505"), ("30000.01", "1998"),
                             ("250000", "1998"), ("0", ""), ("", ""), ("abc", ""),
                             ("12.500", ""), ("1.250.000", "")):  # a thousands separator, never read as 12.5
        assert c(f"true/{contributo}") == want, (contributo, c(f"true/{contributo}"), want)
    assert c("false/") == c("false/12500") == "401" and c("/12500") == "", "SUE 10 when free; unknown: nothing"
    p = run.FILTERS["diritti_pdc"]
    for mq, want in (("1", "677"), ("300", "677"), ("300,5", ""), ("301", "1129"), ("1000", "1129"),
                     ("1000.5", ""), ("1001", ""), ("1001,5", "1998"), ("5000", "1998"), ("", ""), ("0", "")):
        assert p(f"parcheggi/true//{mq}") == p(f"parcheggi/false//{mq}") == want, (mq, p(f"parcheggi/true//{mq}"), want)
    assert p("nuova costruzione/false//") == "401" and p("nuova costruzione/true/30001/") == "1998"
    assert p("variante essenziale/true//") == p("variante sagoma/false//") == "501"  # SUE 11
    assert p("nuova costruzione/true//") == p("nuova costruzione///") == "", "onerous with no contributo, or not yet known"
    g = run.FILTERS["diritti_gratuito"]
    assert g("false") == "401" and g("true") == "", "an onerous SCIA (art. 22) is in no row"


def diritti_from_the_case():
    """The permesso and the SCIA alternativa: the contributo's amount is asked only when onerous with
    the progettista's prospetto (the SUE working it out leaves the diritti asked), the car park's area
    only for car parks; the diritti wait for it, then are proposed. The SCIA's onerous case stays
    asked, with no contributo asked for it; a combination asks what its main pratica asks."""
    root = HERE.parents[4] / "rehearsals"
    fields = dict(json.loads((root / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])

    def case(name, base="p6", **change):
        steps = yaml.safe_load((root / name / "portal-steps.generated.yaml").read_text())
        a = json.loads((root / name / f"answers-{base}.json").read_text())
        a.pop("diritti_euro", None)
        r = run.preflight(steps, values({**a, **change}, fields, steps), made_up=True)
        return [q["key"] for q in r["questions"]], {p["key"]: p["proposal"] for p in r["proposals"]}
    onerous = {"scia_onerosa": "true", "contributo_pagamento": "rateizzazione"}
    for name in ("pdc-fittizio", "scia-alternativa-fittizia", "pdc-proroga-paesaggistica-fittizio", "scia-alt-rinnovo-paesaggistica-fittizia"):
        q, p = case(name, **onerous, contributo_calcolo="sportello")
        assert "diritti_euro" in q and "contributo_euro" not in q and "diritti_euro" not in p, (name, q, p)
        q, p = case(name, **onerous, contributo_calcolo="prospetto")
        assert "contributo_euro" in q and "diritti_euro" not in q + list(p), (name, q, p)  # waits for the amount
        for amount, want in (("4800", "1003"), ("12500", "1505"), ("45000", "1998")):
            q, p = case(name, **onerous, contributo_calcolo="prospetto", contributo_euro=amount)
            assert p.get("diritti_euro") == want and "contributo_euro" not in q, (name, amount, q, p)
        q, p = case(name, **onerous, contributo_calcolo="prospetto", contributo_euro="5000")
        assert "diritti_euro" in q and "diritti_euro" not in p, (name, q, p)
        q, p = case(name, scia_onerosa="false", contributo_normativa="art. 17 c. 3 DPR 380/2001")
        assert p.get("diritti_euro") == "401" and "contributo_euro" not in q, (name, q, p)
    q, p = case("pdc-fittizio", "parcheggi")
    assert "parcheggio_mq" in q and "diritti_euro" not in q + list(p), (q, p)
    for mq, want in (("280", "677"), ("450", "1129"), ("1200", "1998")):
        q, p = case("pdc-fittizio", "parcheggi", parcheggio_mq=mq)
        assert p.get("diritti_euro") == want and "contributo_euro" not in q, (mq, q, p)
    q, p = case("pdc-fittizio", "parcheggi", parcheggio_mq="300,5")
    assert "diritti_euro" in q, q
    q, p = case("pdc-fittizio")
    assert "parcheggio_mq" not in q, q
    q, p = case("scia-fittizia", **onerous, contributo_calcolo="prospetto")
    assert "diritti_euro" in q and "contributo_euro" not in q, (q, p)


def diritti_main_row():
    """Two adempimenti in one pratica pay the main pratica's line alone: SUE 2 and 3 apply only to a
    landscape authorization "quando oggetto di autonoma istanza", and the table has no line for the
    terre e rocce or the DAU. Every combination's diritti ask is its main pratica's."""
    root = HERE.parents[4] / "rehearsals"
    load = lambda d: yaml.safe_load((d / "recipe.yaml").read_text())
    checked = 0
    for d in sorted(root.iterdir()):
        if not (d / "portal-steps.generated.yaml").exists() or not isinstance(load(d).get("operation"), list):
            continue
        main = d
        while isinstance(load(main).get("operation"), list):  # a combination's main may be one itself
            main = root / (load(main)["extends"][0])
        ask = lambda x: yaml.safe_load((x / "portal-steps.generated.yaml").read_text())["asks"].get("diritti_euro")
        assert ask(d) == ask(main), (d.name, main.name, ask(d), ask(main))
        checked += 1
    assert checked >= 60, checked


CASES = [
    ("the SCIA with its answers is ready", ready),
    ("run.py scope: the pvault get patterns cover every field the steps read, and only those", vault_scope),
    ("a rehearsal's draft must be named PROVA NON INVIARE; a real one takes the steps file's own name", rehearsal_draft_name),
    ("no answers: one checklist, branch items first, then two questions, no defaults", all_questions),
    ("alcohol stops at pre-flight with its reason, nothing else asked", alcohol),
    ("a company is refused: only ditte individuali are mapped", company),
    ("page_scripts refuses an unsupported or unanswered case", page_refuses),
    ("an empty vault field is named", missing_vault_field),
    ("no titolare is a missing field, not a crash", no_titolare),
    ("a bad answer is asked again with why", bad_answer),
    ("a default fills an unanswered ask", default_used),
    ("an ask with no question is a steps-file error", ask_without_question),
    ("an expired document the steps read is named", expired),
    ("files: found, too big for the pane or the portal, of a type the slot doesn't take, or missing", files),
    ("a checklist answers as a list or item by item, and a bad list is asked again", checklist_forms),
    ("a question no field reads is a steps-file error", unused_ask),
    ("a question this case doesn't need isn't asked; a conditional one says on what", not_needed_here),
    ("a proposal is offered to confirm, used once confirmed, and asked when the vault can't fill it", proposals),
    ("a sum of answers renders, needs every term, and each term is asked", sums),
    ("a value longer than its box is asked again, or named in the vault, before the run", too_long),
    ("the wizard's description longer than its 60 characters is asked again at pre-flight", wizard_description_too_long),
    ("a .p7m is read: signed by the dichiarante, by someone else (a warning without any codice fiscale), or not a signature (not ready)", p7m_signer),
    ("Napoli's SUE: PDF/A, signed (.p7m or PAdES), plain names, else not ready; made-up files only warned; the SUAP unchecked", napoli_filing),
    ("the imposta di bollo route is listed as a choice made in the person's name", bollo_chosen),
    ("a condition's words gate each other: a later question waits on the earlier answer (CILA contributo)", nested_when),
    ("a supports check with `if` applies, and is asked, only once its gate holds (permesso contributo)", gated_support),
    ("a premises or a client's property outside the Comune di Napoli is refused before anything opens", outside_napoli),
    ("the agibilità's systems: their dichiarazione is filled, other certificates asked system by system, asked only with systems", agibilita_systems),
    ("the agibilità's systems decide its slots: the dichiarazione's only with one, collaudo and atto notorio their own", agibilita_slots),
    ("the SCIA in sanatoria: in progress and double conformity ready, art. 36-bis c. 1 and pre-1977 variants refused", sanatoria_cases),
    ("a landscape variant, a renewal with changes (refused for a semplificata), an architect born abroad", group_two_choices),
    ("every SUE case is ready but those refused on purpose; only the registered company can't pass on made-up data", every_sue_case_ready),
    ("the Catasto Terreni: a plot's radio and boxes, a unit's from its categoria unasked, asked when the vault can't tell", catasto_terreni),
    ("cadastral units: one unasked, a second proposed, each after the first by its \"+\", in up to three groups", cadastral_units),
    ("firms repeat by \"+\"; a landscape technician beside the presenter is the portal's defect", third_firm),
    ("a wizard choice follows the case: co-holders, a new direttore or firm, the others' assent; asked, and three co-holders by the section's \"+\"", scelte_follow_the_case),
    ("the CILA's filings presented with it and assents for the SUE (art. 23-bis), the CIL's filings, a partial fine lavori's planimetria", assents_and_filings),
    ("the bollo and diritti exemptions, the virtual bollo, the permesso's altro, the SCIA alternativa's regional works, a studio's other architect", exemptions_and_other_kinds),
    ("the materiali di risulta agree with the terre e rocce filings, and are proposed from them", materiali_di_risulta_agree),
    ("a value the vault has but the form can't take (a Carica for a named architect who isn't the titolare) is reported, not crashed on", carica_not_crash),
    ("a street of any type (a Vico, a Capo di Piazza; a Cupa named), a citizenship by adjective or country, every province", streets_and_lists),
    ("the SUE's diritti at the 2026 table's edges: the contributo's brackets (5,000 € in two rows), a car park's area (300-301 and 1,000-1,001 m² in none)", diritti_brackets),
    ("the diritti from the case: the contributo asked only with the prospetto, a car park's area only for one, then proposed; the onerous SCIA asked", diritti_from_the_case),
    ("two adempimenti in one pratica pay the main pratica's line alone (SUE 2-3 only on their own; no line for terre e rocce or the DAU)", diritti_main_row),
]


def main():
    failed = 0
    for name, fn in CASES:
        try:
            fn()
            print(f"ok    {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {name}: {e}")
    print(f"{len(CASES) - failed}/{len(CASES)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
