#!/usr/bin/env python3
"""gen.py offline, on the crawls in catalogue/F839/sections: no browser, no network.

  ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/test_gen.py
"""

import copy
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
os.chdir(ROOT)  # the answers name files from the repo's root, wherever this runs from
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True
import gen  # noqa: E402
import yaml  # noqa: E402

CILA = ROOT / "rehearsals" / "cila-fittizia"
FINE = ROOT / "rehearsals" / "fine-lavori-fittizia"
results = []


def case(name):
    def run(fn):
        try:
            fn()
            results.append(True)
            print(f"ok    {name}")
        except Exception as e:  # noqa: BLE001
            results.append(False)
            print(f"FAIL  {name}: {e}")
    return run


# The hand walk was P6's case: a tenant (altro + locatario, the owner company's assent) and
# works under way (d.2). The dictionary now maps every title and stage under `when`; these
# entries are P6's alone, as the dictionary had them, so the id arithmetic is still checked.
P6_ONLY = gen.yaml.safe_load("""
- section: a) Titolarità dell'intervento
  fields:
    - {kind: select, label: "Il richiedente dichiara di avere titolo", value: altro}
    - {kind: text, label: specificare, value: locatario}
    - {kind: radio, label: non avere titolarità esclusiva}
    - {kind: text, label: Cognome, value: "{{r:identity.last_name}}"}
    - {kind: text, label: Nome, value: "{{r:identity.first_name}}"}
    - {kind: text, label: C.F., value: "{{r:identity.codice_fiscale}}"}
    - {kind: date, label: Data di nascita, value: "{{r:identity.date_of_birth|date_it}}"}
    - {kind: select, label: Sesso, value: "{{r:identity.sex|sesso}}"}
    - {kind: select, label: Provincia, value: "{{r:identity.birth_province}}"}
    - {kind: text, label: Comune italiano, value: "{{r:identity.birth_comune|upper}}"}
    - {kind: select, label: Provincia, nth: 2, value: "{{r:residenza.provincia}}"}
    - {kind: text, label: Comune italiano, nth: 2, value: "{{r:residenza.comune|upper}}"}
    - {kind: text, label: "Via, Piazza", value: "{{r:residenza.indirizzo|upper}}"}
    - {kind: text, label: "N.", value: "{{r:residenza.civico}}"}
    - {kind: text, label: C.A.P., value: "{{r:residenza.cap}}"}
    - {kind: text, label: PEC / posta elettronica, value: "{{o:business.pec}}"}
    - {kind: text, label: Telefono, value: "{{o:business.telefono|phone_it}}"}
    - {kind: checkbox, label: Da compilare solo nel caso in cui il titolare sia}
    - {kind: text, label: in qualità di, value: legale rappresentante}
    - {kind: text, label: della ditta / società, value: "{{o:business.denominazione}}"}
    - {kind: text, label: con codice fiscale / p. IVA, value: "{{o:business.partita_iva}}"}
- section: d) Qualificazione dell'intervento
  fields:
    - {kind: radio, label: intervento in corso di esecuzione}
    - {kind: date, label: intervento iniziato in data, value: "{{ask.data_inizio_lavori|date_it}}"}
    - {kind: file, label: "Tipologie ammesse", value: "{{ask.ricevuta_sanzione}}"}
- section: e) Destinazione d'uso
  fields:
    - {kind: select, label: "L'intervento interessa l'immobile", value: "{{c:immobile.destinazione_uso}}"}
- section: h) Impresa esecutrice dei lavori
  leave: [Telefono, fax]
  firms: [f1, f2]
  firm_when: "{{ask.lavori_in_proprio|not}}"
  fields:
    - {kind: radio, label: lavori sono/saranno eseguiti dall, if_present: true, when: "{{ask.lavori_in_proprio|not}}"}
  block:
    - {kind: text, label: Ragione sociale, value: "{{F:business.denominazione}}"}
    - {kind: text, label: codice fiscale / p. IVA, value: "{{F:business.partita_iva}}"}
    - {kind: select, label: Iscritta alla C.C.I.A.A. di, value: "{{F:business.cciaa}}"}
    - {kind: text, label: n., nth: 1, value: "{{F:business.rea|rea_num}}"}
    - {kind: text, label: con sede in, value: "{{F:business.sede_legale_comune|upper}}"}
    - {kind: select, label: provincia, nth: 1, value: "{{F:business.sede_legale_provincia}}"}
    - {kind: text, label: "Via, Piazza", value: "{{F:business.sede_legale_indirizzo|upper}}"}
    - {kind: text, label: N., nth: 2, value: "{{F:business.sede_legale_civico}}"}
    - {kind: text, label: C.A.P., value: "{{F:business.sede_legale_cap}}"}
    - {kind: text, label: Cognome, value: "{{F:identity.last_name}}"}
    - {kind: text, label: Nome, value: "{{F:identity.first_name}}"}
    - {kind: text, label: codice fiscale, nth: 2, value: "{{F:identity.codice_fiscale}}"}
    - {kind: text, label: nato a, value: "{{F:identity.birth_comune|upper}}"}
    - {kind: select, label: provincia, nth: 2, value: "{{F:identity.birth_province}}"}
    - {kind: date, label: nato il, value: "{{F:identity.date_of_birth|date_it}}"}
    - {kind: text, label: cell., value: "{{F:identity.phone|phone_it}}"}
    - {kind: text, label: posta elettronica, value: "{{F:business.pec}}"}
    # DURC: each box opens its own rows (and renumbers what follows).
    - {kind: checkbox, label: INPS}
    - {kind: text, label: sede di, nth: 1, value: "{{F:business.sede_legale_comune|upper}}"}
    - {kind: text, label: Matr./Pos. Contr., value: "{{F:business.inps_matricola}}"}
    - {kind: checkbox, label: INAIL}
    - {kind: text, label: sede di, nth: 2, value: "{{F:business.inail_codice_sede}}"}
    - {kind: text, label: codice impresa, value: "{{F:business.inail_codice_ditta}}"}
    - {kind: text, label: pos. assicurativa, value: "{{F:business.inail_pat}}"}
""")


def p6_recipe():
    return gen.load_yaml(CILA / "recipe.yaml") | {"sections": P6_ONLY}


@case("the CILA comes out as the hand walk found it, field for field (P6's own entries)")
def _():
    diffs, _ = gen.check(gen.generate(p6_recipe()), gen.load_yaml(CILA / "portal-steps.yaml"))
    assert not diffs, diffs


@case("two choices the crawl tried apart add up to the hand walk's ids (a), owner rows)")
def _():
    steps = gen.generate(p6_recipe())
    a = next(s for s in steps["sections"] if s["section"].startswith("a)"))
    ids = {f["label"]: f["id"] for f in a["fields"]}
    assert ids["Cognome"] == "r11c1p13reg:txt" and ids["con codice fiscale / p. IVA"] == "r32c2p77reg:txt", ids


def p6_values(name, answers="answers-p6.json"):
    import json
    import run
    fields = dict(json.loads((CILA / "fixture-p6.json").read_text())["fields"])
    return lambda steps: run.Values(json.loads((ROOT / "rehearsals" / name / answers).read_text()),
                                    fields=fields, asks=steps.get("asks"))


def filled(steps, values):
    """Each section's values in order, as run.py's plan fills them for these answers."""
    import os
    import run
    here = os.getcwd()
    os.chdir(ROOT)  # answers name files from the repo's root
    try:
        out, v = {}, values(steps)
        run.plan(steps, v)  # stops on a missing value
        for sec in steps["sections"]:
            for f in sec["fields"]:
                # A box only some pratiche show is skipped where it isn't, so it isn't compared.
                if f.get("on_page") or f.get("if_present") or "when" in f and not run.truthy(v.render(f["when"]) or ""):
                    continue
                out.setdefault(gen.norm(gen.QUADRO.sub("", sec["section"])), []).append(
                    v.render(f["value"]) if "value" in f else True)
        return out
    finally:
        os.chdir(here)


@case("the dictionary's every-case CILA fills P6 with the hand walk's values, section for section")
def _():
    v = p6_values("cila-fittizia")
    hand, ours = filled(gen.load_yaml(CILA / "portal-steps.yaml"), v), filled(gen.generate(gen.load_yaml(CILA / "recipe.yaml")), v)
    for sec, vals in hand.items():
        assert ours.get(sec) == vals, (sec, vals, ours.get(sec))


@case("the fine lavori, never walked, comes out whole from the shared sections")
def _():
    steps = gen.generate(gen.load_yaml(FINE / "recipe.yaml"))
    names = [s["section"] for s in steps["sections"]]
    assert "ubicazione dell'immobile" in names and "comunicazione di fine lavori" in names, names
    slots = next(s for s in steps["sections"] if s["section"] == "Gestione degli allegati")["fields"]
    # Works finished in part add the planimetria's own slot (read on a partial draft, 2026-11-03).
    assert [f["label"][:20] for f in slots] == ["Fotocopia di un docu", "Copia dei documenti ", "Dichiarazione di ass", "Copia di elaborato p"], slots


@case("a section the dictionary doesn't have stops it, nothing written")
def _():
    real = gen.load_yaml
    def without(p):
        d = real(p)
        if p.name == "fnsuap.yaml":
            d = copy.deepcopy(d)
            d["sections"] = [s for s in d["sections"] if s["section"] != "comunicazione di fine lavori"]
        return d
    gen.load_yaml = without
    try:
        gen.generate(real(FINE / "recipe.yaml"))
        raise AssertionError("generated anyway")
    except gen.GenError as e:
        assert "comunicazione di fine lavori: no dictionary entry" in str(e), e
    finally:
        gen.load_yaml = real


@case("an attachments screen nobody has crawled stops it")
def _():
    recipe = gen.load_yaml(FINE / "recipe.yaml")
    real = gen.json.loads
    gen.json.loads = lambda s: {k: v for k, v in real(s).items() if k != "slots"} if isinstance(real(s), dict) else real(s)
    try:
        gen.generate(recipe)
        raise AssertionError("generated anyway")
    except gen.GenError as e:
        assert "slots aren't crawled yet" in str(e), e
    finally:
        gen.json.loads = real


REH = ROOT / "rehearsals"


def generated(name):
    return gen.generate(gen.load_yaml(REH / name / "recipe.yaml"))


def section(steps, start):
    return next(s for s in steps["sections"] if s["section"].startswith(start))


def field(sec, start):
    return next(f for f in sec["fields"] if f.get("label", "").startswith(start))


@case("a quadro is matched without its letter, and a tick is a radio or a checkbox as the page has it (CIL)")
def _():
    steps = generated("cil-fittizia")
    g = section(steps, "g) Rispetto")  # the CILA's i)
    assert field(g, "dichiara che l'entità presunta")["kind"] == "checkbox"  # a radio in the CILA
    f = section(steps, "f) Impresa")["fields"]
    assert next(x for x in f if "anchor" in x)["anchor"] == "Ragione sociale"


@case("two exclusive branches keep their own crawled ids (agibilità, fine lavori filed or not)")
def _():
    s = section(generated("agibilita-fittizia"), "dichiarazione sulla comunicazione")
    assert field(s, "prot./n.")["id"] == "r4c1p6reg:txt"
    assert "id" not in field(s, "che la presente segnalazione")  # after the other branch's rows: by label


@case("a field below a conditional choice that shifts rows goes by label; one above keeps its id (SCIA impianti)")
def _():
    s = section(generated("scia-fittizia"), "Asseverazione SCIA - Sicurezza impianti")
    assert field(s, "idrici e sanitari")["id"] == "r9c1p9reg:chk"
    assert "id" not in field(s, "non è soggetto agli obblighi")


@case("rerun.py queues each rehearsal with run.js's own values, and check.js names each steps file")
def _():
    import json, subprocess, tempfile
    fixture = json.loads((REH / "cila-fittizia" / "fixture-p6.json").read_text())
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        (t / "values.json").write_text(json.dumps(dict(fixture["fields"])))
        names = ["dau-fittizia", "paesaggistica-semplificata-fittizia"]
        subprocess.run([sys.executable, str(HERE / "rerun.py"), "--values", str(t / "values.json"), "--out", str(t / "out"),
                        "--bundle", str(t / "bundle.js"), *names], check=True, capture_output=True)
        # A bundle is a new batch: an earlier batch's result under the same name would skip a run.
        bundle = (t / "bundle.js").read_text()
        assert bundle.index('sessionStorage.removeItem("pv-batch")') < bundle.index("window.pvBatchRun = ")
        loop = (t / "out" / "loop.js").read_text()
        assert "moved: r.moved || []" in loop and "r.snapshot.boxes" in loop and "gaps" in loop
        assert 'querySelectorAll(\'[data-pv="review"]' in loop, "the batch leaves the review over the portal"
        queue = (t / "out" / "queue-0.js").read_text()
        check = (t / "out" / "check.js").read_text()
        assert all(f'"steps/{n}.js"' in check for n in names) and '"runner.js"' in check
        # The piece's values as a string it checks before adding them (a garbled copy throws): its
        # length and FNV-1a hash as the page computes them.
        line = next(x for x in queue.splitlines() if x.strip().startswith("const raw = "))
        raw = json.loads(line.strip()[len("const raw = "):-1])
        import importlib.util
        spec = importlib.util.spec_from_file_location("rerun", HERE / "rerun.py")
        rerun = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rerun)
        n, h = rerun.fnv1a(raw)
        assert f"raw.length !== {n} || h !== {h}" in queue
        # Each procedure's first run whole ({"base": ...}); a later one is what differs from it.
        assert '["dau-fittizia","napoli/comune/dichiarazione-avvenuto-utilizzo-terre",{"base":{"wizard":["PROVA NON INVIARE - DAU P6 generato"' in raw
        assert (t / "out" / "steps" / "dau-fittizia.js").read_text().startswith('localStorage.setItem("pv-steps:napoli/comune/dichiarazione-avvenuto-utilizzo-terre"')
        # A case on other values (a copy of the fixture) goes in the same batch, labelled with them,
        # and isn't recorded: the repo's fixture wouldn't give that run again.
        other = dict(fixture["fields"]) | {"chiara:identity.birth_province": "EE", "chiara:identity.birth_country": "ARGENTINA"}
        (t / "estero.json").write_text(json.dumps(other))
        subprocess.run([sys.executable, str(HERE / "rerun.py"), "--values", str(t / "values.json"), "--out", str(t / "out2"),
                        "dau-fittizia", f"dau-fittizia:answers-p6.json:{t / 'estero.json'}"], check=True, capture_output=True)
        assert "dau-fittizia/answers-p6@estero" in (t / "out2" / "queue-0.js").read_text()
        r = subprocess.run([sys.executable, str(HERE / "rerun.py"), "--record", "-"], input='[{"name": "dau-fittizia/answers-p6@estero", "result": "filled"}]',
                           check=True, capture_output=True, text=True)
        assert "not recorded" in r.stdout


@case("every SUE recipe takes, gates or answers every choice its operations' wizard offers (a co-holder, a new direttore, the sanatoria's Si/No)")
def _():
    # Until 2026-11-02 a voltura always ticked a co-holder and a cambio d'intestazione never did,
    # whatever the case: a choice a recipe never names is filed as not taken, without a word.
    import json
    wizard = json.loads((HERE.parent / "catalogue" / "F839" / "sue-wizard.json").read_text())
    missing = []
    for f in sorted(REH.glob("*/recipe.yaml")):
        r = gen.resolved(gen.load_yaml(f))
        if r.get("sportello") != "sue":
            continue
        taken = {s if isinstance(s, str) else s["option"] for s in r.get("scelte") or []}
        answered = {gen.norm(k) for k in (r.get("si_no") or {})}
        for label in r["operation"] if isinstance(r["operation"], list) else [r["operation"]]:
            op = next(o for o in wizard["operations"] if o["label"] == label)
            for sc in op.get("scelte", []):
                if sc["option"] not in taken and not (sc.get("type") == "SIN" and any(gen.norm(sc["option"]).startswith(a) for a in answered)):
                    missing.append(f"{f.parent.name}: {sc['option'][:60]}")
    assert not missing, missing


@case("the dictionary: every question is read somewhere, and no key is given twice (gen.load_yaml refuses it)")
def _():
    import re, tempfile
    # A question nothing reads is a box nobody connected: the renewal's design changes were one
    # (paes_rinnovo_variazioni, 2026-11-02), so a renewal with changes was filed as one without.
    asked = re.compile(r"(?:\{\{|[+*,])\s*ask\.([\w#]+)")
    d = gen.load_yaml(HERE.parent / "dictionary" / "fnsuap.yaml")
    texts = [yaml.safe_dump({k: v for k, v in d.items() if k != "asks"}, allow_unicode=True), yaml.safe_dump(d["asks"], allow_unicode=True)]
    texts += [f.read_text() for f in [*REH.glob("*/recipe.yaml"), *REH.glob("*/portal-steps.yaml"), *(HERE.parent / "parts").glob("*.yaml")]]
    reads = {r for t in texts for r in asked.findall(t)}
    for f in (HERE.parent / "rules").glob("*.yaml"):
        reads |= set(gen.load_yaml(f).get("facts") or {})
    unread = sorted(k for k in d["asks"] if k not in reads)
    assert not unread, unread
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as t:
        t.write("asks:\n  a: {type: text}\n  a: {type: date}\n")
    try:
        gen.load_yaml(t.name)
        raise AssertionError("a key given twice was read")
    except gen.GenError as e:
        assert "twice" in str(e)
    finally:
        os.unlink(t.name)


@case("a drift check's digests: catalogue.py computes what the pane's digest.js computed on the live portal (2026-11-02)")
def _():
    import catalogue
    assert catalogue.digest(catalogue.stored_fingerprints("cil")) == "041974574c75"
    assert catalogue.digest(catalogue.stored_fingerprints("sue-permesso-di-costruire-art-10-d-p-r-380-2001")) == "6e4da66eda5f"


@case("two operations in one pratica: their sections once each, in the combination's crawl's order, and both ticked")
def _():
    steps = generated("cila-paesaggistica-fittizia")
    names = [x["section"] for x in steps["sections"]]
    # 22 in the form, then Pagamento degli oneri and Gestione degli allegati (read 2026-10-31).
    assert len(names) == len(set(n.lower() for n in names)) == 24
    assert names.index("a) Titolarità dell'intervento") < names.index("Qualificazione dell'intervento") < names.index("Ambito dell'intervento")
    assert "dichiarazione ubicazione dell'intervento" not in names  # the CILA's Localizzazione, the same section
    assert steps["wizard"][3]["tree"] == ["Comunicazione Inizio Lavoro Asseverata (C.I.L.A.)",
                                          "Autorizzazione paesaggistica semplificata (DPR 31/2017 - Comune)"]
    recipe = gen.load_yaml(REH / "cila-paesaggistica-fittizia" / "recipe.yaml")
    recipe["crawl"] = "cila"  # a crawl of the CILA alone is not of both
    try:
        gen.generate(recipe)
        assert False, "generated from the wrong crawl"
    except gen.GenError as e:
        assert "isn't a crawl of these operations together" in str(e)


@case("a recipe drops a slot its part adds that its form never opens (the CILA with the ordinaria)")
def _():
    labels = lambda name: [f["label"] for f in section(generated(name), "Gestione degli allegati")["fields"]]
    cila, scia = labels("cila-paesaggistica-ordinaria-fittizia"), labels("scia-paesaggistica-ordinaria-fittizia")
    assert "Relazione paesaggistica e documentazione per il rilascio" in scia
    assert "Relazione paesaggistica e documentazione per il rilascio" not in cila
    assert "Relazione paesaggistica (redatta ai sensi del D.P.C.M" in cila


@case("a refusal naming a known portal defect carries its record into the steps file; an unknown one is an error")
def _():
    steps = generated("scia-sanatoria-fittizia")
    d = [c["defect"] for c in steps["supports"] if "defect" in c]
    assert [x["id"] for x in d] == ["scia-36bis-c1", "scia-34ter"] and all(x["choices"] and x["law"] for x in d), d
    recipe = gen.load_yaml(REH / "scia-sanatoria-fittizia" / "recipe.yaml")
    recipe["supports"] = recipe["supports"] + [{"value": "x", "in": ["x"], "else": "x", "defect": "no-such-defect"}]
    try:
        gen.generate(recipe)
        assert False, "generated with an unknown defect"
    except gen.GenError as e:
        assert "no-such-defect" in str(e)


@case("the agibilità's art. 24 boxes stay theirs: the portal asks for one even where neither applies")
def _():
    # a592b60 mapped the boxes and dropped the section's `theirs`: every case ticking neither stopped
    # on the portal's "deve essere selezionata almeno un'opzione" (2026-10-31).
    sec = section(generated("agibilita-fittizia"), "Attestazione tecnica - Agibilità")
    assert any("articolo 24" in t for t in sec.get("theirs", [])), sec.get("theirs")


@case("two scelte both keep the sections they add, and the wizard ticks both; one the case decides waits on it, its section too (voltura's co-holder)")
def _():
    steps = generated("voltura-pdc-fittizia")
    names = [x["section"] for x in steps["sections"]]
    assert "Informazioni su eventuali altri aventi titolo" in names and "Qualifica e dati del procuratore" in names
    tree = steps["wizard"][-1]["tree"]
    assert tree[0] == {"leaf": "ci sono cointestatari", "when": "{{ask.cointestatario}}"} and len(tree) == 2, tree
    sec = section(steps, "Informazioni su eventuali altri aventi titolo")
    assert sec["when"] == "{{ask.cointestatario}}" and all(f["when"].startswith("{{ask.cointestatario}}") for f in sec["fields"])


@case("a section name two pratiche share takes the entry that fits; a tick that renumbers itself and what follows go by label (paesaggistica semplificata)")
def _():
    steps = generated("paesaggistica-semplificata-fittizia")
    q = section(steps, "Qualificazione dell'intervento")  # the SCIA's has one radio
    assert len(q["fields"]) == 42 and field(q, "B.10.")["id"] == "r12c1p13reg:chk"
    a = section(steps, "Ambito dell'intervento")
    both = [f for f in a["fields"] if f["when"] == "{{ask.vincolo|is_art_136_and_142}}"]
    # Ticking art. 136 opens its rows above itself: r2c1p2 becomes r3c1p3 (run of 2026-10-29).
    ticks = [f for f in a["fields"] if f["kind"] == "checkbox" and f["label"] == "dell'art. 136"]
    assert len(ticks) == 2 and all("id" not in f for f in ticks)
    assert all("id" not in f for f in both[1:] if f["label"] != "dell'art. 136")
    # A pair of same-label boxes crawl.js matched isn't a move (the SCIA's tutela radio).
    scia = generated("scia-fittizia")
    assert any(f.get("id") == "r10c1p10reg:radio:3_clone" for s in scia["sections"] for f in s["fields"])
    assert "allegato_b" in steps["groups"]


@case("a slot that takes only signed files is the person's, never a plain copy (SCIA stato legittimo)")
def _():
    s = section(generated("scia-fittizia"), "Gestione degli allegati")
    assert "Documentazione dimostrativa dello stato legittimo" in s["theirs"]
    assert not any(f["label"].startswith("Documentazione dimostrativa") for f in s["fields"])


@case("one entry fills the SCIA's and the SCIA alternativa's shared quadri; boxes a choice opens are found on the page; every assent or deroga holds the start date back")
def _():
    scia, alt = generated("scia-fittizia"), generated("scia-alternativa-fittizia")
    for s in (scia, alt):
        imp = next(x for x in s["sections"] if "Sicurezza impianti" in x["section"])
        assert field(imp, "allega i relativi elaborati")["when"] == "{{ask.impianti}} {{ask.progetto_impianti}}"
    am = section(scia, "Asseverazione SCIA - Amianto")
    assert field(am, "alloggio monostanza per due persone").get("on_page")
    assert field(section(scia, "Asseverazione SCIA - Sicurezza impianti"), "specificare")["value"] == "{{ask.impianto_altro_quale}}"
    b = field(section(scia, "b) Presentazione"), "Per SCIA/SCIA Unica")["when"]
    for w in ("barriere_deroga|not", "antincendio_deroga|not", "vvf_valutazione|not", "fascia_cimiteriale|is_non_consentito|not"):
        assert w in b, w


@case("a low one-room flat: both cases of art. 24 c. 5-bis, each with its own 5-ter conditions under its box (SCIA), both boxes (agibilità)")
def _():
    import json
    import run
    fields = dict(json.loads((CILA / "fixture-p6.json").read_text())["fields"])
    for name, n in (("scia-fittizia", 2), ("agibilita-fittizia", 1)):
        steps = generated(name)
        v = run.Values(json.loads((REH / name / "answers-bassa-monostanza.json").read_text()), fields=fields, asks=steps.get("asks"))
        r = run.preflight(steps, v, made_up=True)
        assert r["ready"] and not r["unsupported"], (name, r)
        plan = run.plan(steps, v)
        labels = [p["label"] or "" for p in plan]
        assert any(l.startswith("locali con un’altezza minima interna") for l in labels), name
        assert any(l.startswith(("alloggio monostanza per una persona", "alloggio mono-stanza")) for l in labels), name
        conds = [p for p in plan if (p["label"] or "").startswith(("che soddisfano il requisito", "i locali sono situati in edifici"))]
        assert len([p for p in conds if (p["label"] or "").startswith("i locali")]) == n, (name, conds)
    am = section(generated("scia-fittizia"), "Asseverazione SCIA - Amianto")
    assert {f.get("anchor") for f in am["fields"] if f["label"].startswith("che soddisfano")} == {
        "locali con un’altezza minima interna", "alloggio monostanza per una persona", "alloggio monostanza per due persone"}


@case("a question only a missing field reads isn't asked (SCIA has no firm-documents check)")
def _():
    assert "verificato_idoneita" not in generated("scia-fittizia")["asks"]


@case("draft.py drafts the hairdresser's own sections from the national schema, every box with its meaning")
def _():
    import draft
    crawl = gen.json.loads((HERE.parent / "catalogue/F839/sections/acconciatore.json").read_text())
    schema = gen.json.loads((HERE.parent / "schema/mod_acconciatori_estetisti_apertura_v1.0.7-fields.json").read_text())
    sec = lambda name: next(x for x in crawl["sections"] if x["section"].startswith(name))
    e, asks, n, missed = draft.draft_section(sec("Dati sull"), schema)
    got = [f.get("value") or f.get("when") for f in e["fields"]]
    assert missed == 0 and got[:2] == ["{{ask.superficie_complessiva}}", "{{ask.superficie_attivita}}"], got
    assert "{{ask.congiunta_denominazione}}" in got and "{{ask.data_protocollo|date_it}}" in got, got
    e, asks, n, missed = draft.draft_section(sec("Dichiarazione sul possesso dei requisiti antimafia"), schema)
    assert e.get("theirs") and not e["fields"], e  # a declaration is the person's
    e, asks, n, missed = draft.draft_section(sec("Dichiarazione sul possesso dei requisiti professionali"), schema)
    by = {(f["label"][:12], f.get("nth", 1)): f.get("value") for f in e["fields"] if f.get("value")}
    assert by[("rilasciata d", 1)] == "{{ask.ente_abilitazione_professionale}}", by
    assert by[("rilasciata d", 2)] == "{{ask.ente_qualifica_professionale}}", by
    assert by[("Nome", 1)] == "{{ask.nome}}", by


def batch_copy(tmp):
    """A copy of the catalogue where a batch crawled the fine lavori again: every section it
    had seen before named by reference (`same_as`), as crawl.js's batch writes them."""
    import shutil
    base = Path(tmp)
    shutil.copytree(HERE.parent / "catalogue", base / "catalogue")
    shutil.copytree(HERE.parent / "dictionary", base / "dictionary")
    fine = gen.json.loads((base / "catalogue/F839/sections/fine-lavori.json").read_text())
    for s in fine["sections"]:
        if s.get("fields") is not None:
            for k in [k for k in s if k != "section"]:
                del s[k]
            s["same_as"] = f"fine-lavori#{s['section']}"
    (base / "catalogue/F839/sections/fine-batch.json").write_text(gen.json.dumps(fine))
    return base


@case("a section a batch crawl names by reference (same_as) generates as the section itself")
def _():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        base = batch_copy(tmp)
        recipe = gen.load_yaml(FINE / "recipe.yaml")
        want = gen.generate(recipe)
        got = gen.generate(dict(recipe, crawl="fine-batch"), base=base)
        want.pop("generated"), got.pop("generated")
        assert got == want


@case("a section's fingerprint is the one crawl.js computed in the page, for every crawled section")
def _():
    import catalogue
    n = 0
    for name, c in catalogue.crawls().items():
        for s in c["sections"]:
            if s.get("fields") is not None and s.get("fingerprint"):
                assert catalogue.fingerprint(s["fields"]) == s["fingerprint"], (name, s["section"])
                n += 1
    assert n > 100, n


@case("a pratica the last drift check found changed is refused by gen.py and by pre-flight")
def _():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        base = batch_copy(tmp)
        (base / "catalogue/F839/drift.json").write_text(gen.json.dumps(
            {"pratiche": {"fine-lavori": {"checked": "2026-10-28", "differences": ["changed: Dati catastali"]}}}))
        try:
            gen.generate(gen.load_yaml(FINE / "recipe.yaml"), base=base)
            raise AssertionError("generated")
        except gen.GenError as e:
            assert "changed: Dati catastali" in str(e), e
        import catalogue
        old = catalogue.CAT
        catalogue.CAT = base / "catalogue/F839"
        try:
            import run
            steps = gen.load_yaml(FINE / "portal-steps.generated.yaml")
            assert "Dati catastali" in run.portal_changed(steps)[0]
            assert run.portal_changed(gen.load_yaml(CILA / "portal-steps.yaml")) == []  # hand-written
        finally:
            catalogue.CAT = old


@case("draft.py drafts a restaurant's opening from two national forms (its SCIA and the Reg. 852 notifica)")
def _():
    import draft
    crawl = gen.json.loads((HERE.parent / "catalogue/F839/sections/suap-060-aprire-l-attivita.json").read_text())
    schema = [x for f in ("mod_somministrazione_zone_non_tutelate_apertura", "mod_notifica_sanitaria")
              for x in gen.json.loads((HERE.parent / f"schema/{f}_v1.0.7-fields.json").read_text())]
    sec = lambda name: next(x for x in crawl["sections"] if x["section"].startswith(name))
    leaf = lambda asks, v: asks[gen.re.findall(r"ask\.(\w+)", v)[-1]]["schema"].rsplit("/", 1)[-1]
    e, asks, n, missed = draft.draft_section(sec("Dati dell'esercizio"), schema)
    got = {f["label"]: leaf(asks, f.get("value") or f["when"]) for f in e["fields"]}
    assert got["mq"] == "superficie" and got["Tipologia di esercizio"] == "tipologia_esercizio", got  # not the form's own word
    assert got["dal (gg/mm)"] == "da_stagionale", got
    e, asks, n, missed = draft.draft_section(sec("tipologia di attivit"), schema)
    assert e["schema"].endswith("avvio_attivita_section"), e["schema"]  # the second form's group
    got = lambda start: next(leaf(asks, f["when"]) for f in e["fields"] if f["label"].startswith(start))
    assert got("COMMERCIO AL DETTAGLIO") == "commercio_dettaglio"
    assert got("Carne, prodotti") == "carne"  # the rare word, not "prodotti"
    assert got("Ristorazione pubblica con") == "ristorazione_pubblica"
    e, asks, n, missed = draft.draft_section(sec("DICHIARAZIONE ESENZIONE"), schema)
    assert e.get("theirs") and not e["fields"], e  # "Presa visione": the person's


@case("draft.py pairs by order and type: the portal's address block on the form's one-line address, the previous site's side")
def _():
    import draft
    crawl = gen.json.loads((HERE.parent / "catalogue/F839/sections/suap-060-trasferire-la-sede-dell-attivita.json").read_text())
    schema = gen.json.loads((HERE.parent / "schema/mod_somministrazione_zone_non_tutelate_trasferimento_v1.0.7-fields.json").read_text())
    e, asks, n, missed = draft.draft_section(next(x for x in crawl["sections"] if x["section"].startswith("precedente")), schema)
    own = [f["label"] for f in e["fields"] if f.get("note")]
    assert "Frazione" in own and "Via, Viale, Piazza" not in own, own  # the address block: its Via is the line
    leaf = lambda f: asks[gen.re.findall(r"ask\.(\w+)", f.get("value") or f["when"])[-1]]["schema"].rsplit("/", 1)[-1]
    got = {f["label"]: leaf(f) for f in e["fields"] if not f.get("note")}
    assert got["Via, Viale, Piazza"] == "indirizzo_da" and got["CAP"] == "cap_da", got  # "precedente": the _da side
    assert got["Si"] == "centro_commerciale_si_da", got


@case("the dictionary names each question once (YAML keeps the last of two quietly)")
def _():
    seen = []

    class Strict(gen.yaml.SafeLoader):
        def construct_mapping(self, node, deep=False):
            keys = [self.construct_object(k, deep=deep) for k, _ in node.value]
            seen.extend(k for k in set(keys) if keys.count(k) > 1)
            return super().construct_mapping(node, deep)
    gen.yaml.load((HERE.parent / "dictionary/fnsuap.yaml").read_text(), Loader=Strict)
    assert not seen, seen


@case("a choice's answer picks its branch (is_<answer>), and an ordine's name its albo option")
def _():
    import run
    assert run.FILTERS["is_permesso_di_costruire"]("Permesso di costruire") == "true"
    assert run.FILTERS["is_scia"]("permesso di costruire") == "false"
    assert run.FILTERS["albo_tipo"]("Ordine degli Architetti P.P.C.") == "Architetto"


@case("an operation checked in another sector is that pratica when every fingerprint matches, else one to crawl")
def _():
    import tempfile, catalogue
    with tempfile.TemporaryDirectory() as tmp:
        base = batch_copy(tmp)
        old = (catalogue.CAT, catalogue.SECTIONS, catalogue.SAME)
        catalogue.CAT = base / "catalogue/F839"
        catalogue.SECTIONS, catalogue.SAME = catalogue.CAT / "sections", catalogue.CAT / "same.json"
        try:
            fps = catalogue.stored_fingerprints("fine-lavori")
            check = lambda name, change: {"name": name, "like": "fine-lavori", "crawled": "2026-10-28T00:00:00Z", "sections":
                [{"section": k, "fingerprint": ("0" * 16 if k == change else v)} for k, v in fps.items()]}
            export = base / "export.json"
            export.write_text(gen.json.dumps({"crawl:check:suap-001-x": check("suap-001-x", None),
                                              "crawl:check:suap-002-x": check("suap-002-x", "Oggetto della pratica")}))
            out = catalogue.cmd_drift(type("a", (), {"export": str(export)}))
            same = gen.json.loads(catalogue.SAME.read_text())
            assert same["same"] == {"suap-001-x": "fine-lavori"}, out
            assert same["different"]["suap-002-x"]["differences"] == ["changed: Oggetto della pratica"], out
            assert not (catalogue.CAT / "drift.json").exists() or "suap-001-x" not in (catalogue.CAT / "drift.json").read_text()
        finally:
            catalogue.CAT, catalogue.SECTIONS, catalogue.SAME = old


@case("a choice made for only some answers inside a branch sends what follows by label (CILA tolerances, d.1)")
def _():
    steps = gen.generate(gen.load_yaml(CILA / "recipe.yaml"))
    rel = section(steps, "Relazione Tecnica")
    assert field(rel, "2%, per le U.I.")["id"]  # opened by the 1-bis tolerance: its own state
    assert "id" not in field(rel, "TOLLERANZA DI CUI ALL’ART. 34-BIS, COMMA 2:")  # after 1-bis's rows, ticked or not
    d = section(steps, "d) Qualificazione")
    assert field(d, "data inizio lavori")["id"] and "id" not in field(d, "i lavori avranno inizio dopo")


@case("a firm's block is filled only when the job has that firm, and none when the client works in proprio")
def _():
    steps = gen.generate(gen.load_yaml(CILA / "recipe.yaml"))
    p6 = [v for v in filled(steps, p6_values("cila-fittizia"))[gen.norm("Impresa esecutrice dei lavori")] if v]
    owner = filled(steps, p6_values("cila-fittizia", "answers-proprietario.json"))[gen.norm("Impresa esecutrice dei lavori")]
    alone = filled(steps, p6_values("cila-fittizia", "answers-comodatario.json"))[gen.norm("Impresa esecutrice dei lavori")]
    assert "Impianti Fittizi" in str(p6) and "Impianti" not in str(owner) and "Edil" in str(owner), owner
    assert alone == [True], alone  # just "in proprio"


@case("a SCIA on structures fills the structural designer's block by label, and a SCIA condizionata gives no start date")
def _():
    steps = gen.generate(gen.load_yaml(ROOT / "rehearsals" / "scia-fittizia" / "recipe.yaml"))
    h1 = section(steps, "h1) Tecnici")
    block = [f for f in h1["fields"] if f.get("anchor") == "Cognome"]
    assert block and all("id" not in f for f in block)  # its labels repeat the architect's
    structural = filled(steps, p6_values("scia-fittizia", "answers-strutture.json"))
    plain = filled(steps, p6_values("scia-fittizia"))
    assert "SMPDVD80E20F839S" in structural[gen.norm("Tecnici incaricati")]
    assert "SMPDVD80E20F839S" not in plain[gen.norm("Tecnici incaricati")]
    b = gen.norm("Presentazione della SCIA/SCIA Unica/SCIA Condizionata")
    assert structural[b] == ["23/11/2026"], structural[b]
    assert filled(steps, p6_values("scia-fittizia", "answers-tutele.json")).get(b, []) == []  # assents asked with it


@case("the SCIA with its landscape authorization is one pratica with no start date; a variant names the title it changes")
def _():
    steps = gen.generate(gen.load_yaml(ROOT / "rehearsals" / "scia-paesaggistica-semplificata-fittizia" / "recipe.yaml"))
    names = [s["section"] for s in steps["sections"]]
    assert any(n.startswith("Asseverazione SCIA") for n in names) and "Ambito dell'intervento" in names, names
    combo = filled(steps, p6_values("scia-paesaggistica-semplificata-fittizia"))
    assert combo.get(gen.norm("Presentazione della SCIA/SCIA Unica/SCIA Condizionata"), []) == []
    assert "PG/2026/0888888" in combo[gen.norm("Qualificazione dell'intervento")]
    scia = gen.generate(gen.load_yaml(ROOT / "rehearsals" / "scia-fittizia" / "recipe.yaml"))
    pdc = filled(scia, p6_values("scia-fittizia", "answers-variante-pdc.json"))
    assert "PDC123" in pdc[gen.norm("Qualificazione dell'intervento")]
    assert "ART. 17" not in str(pdc[gen.norm("Calcolo del contributo di costruzione")]).upper()  # onerosa: no rule why it's free


@case("the permesso and the SCIA alternativa: a choice a tipologia opens is in its branch, and a fact of the case is proposed, never silent")
def _():
    alt = gen.generate(gen.load_yaml(ROOT / "rehearsals" / "scia-alternativa-fittizia" / "recipe.yaml"))
    d = section(alt, "Asseverazione SCIA Alternativa - Dati progettista")
    under = next(f for f in d["fields"] if f["label"].startswith("non comporta") and "is_ristrutturazione_edilizia" in f["when"])
    assert "id" not in under and "nth" not in under, under  # opened by ticking 1., which moves it: by label
    pdc = gen.generate(gen.load_yaml(ROOT / "rehearsals" / "pdc-fittizio" / "recipe.yaml"))
    assert "default" not in pdc["asks"]["acustica"] and pdc["asks"]["acustica"]["propose"] == "false"
    p6 = filled(pdc, p6_values("pdc-fittizio"))
    of = lambda start: next(v for k, v in p6.items() if k.startswith(gen.norm(start)))
    assert of("Qualificazione pratica") == [True, True], of("Qualificazione pratica")  # art. 10, no change of use
    assert "240" in of("Asseverazione PdC - Dati immobile")



@case("the agibilità: works on structures name their collaudo or its references by the block of their own choice; the fire SCIA makes it a SCIA Unica with its slot; a partial one attaches its plan; every system ticks")
def _():
    import os
    import run
    steps = gen.generate(gen.load_yaml(ROOT / "rehearsals" / "agibilita-fittizia" / "recipe.yaml"))

    def ticked(answers):
        here = os.getcwd()
        os.chdir(ROOT)
        try:
            v = p6_values("agibilita-fittizia", answers)(steps)
            run.plan(steps, v)
            return [(s["section"], f.get("label"), f.get("anchor"), f.get("nth"), v.render(f["value"]) if "value" in f else True)
                    for s in steps["sections"] for f in s["fields"]
                    if "when" not in f or run.truthy(v.render(f["when"]) or "")]
        finally:
            os.chdir(here)
    has = lambda rows, label, **k: [r for r in rows if r[1] and r[1].startswith(label) and all(
        r[{"anchor": 2, "nth": 3, "value": 4}[x]] == y for x, y in k.items())]
    allegato = ticked("answers-collaudo.json")
    assert has(allegato, "si allega certificato di collaudo statico")
    assert has(allegato, "Certificato di collaudo statico", value="rehearsals/agibilita-fittizia/files/collaudo-statico.pdf")
    assert has(allegato, "l'agibilità relativa all'immobile", nth=2)  # SCIA Unica
    assert has(allegato, "SCIA ai sensi dell’art. 4 comma 1")
    assert has(allegato, "specificare:", value="Impianto fotovoltaico")
    assert len(has(allegato, "Subalt. n.")) == 10, has(allegato, "Subalt. n.")
    assert not has(allegato, "reperibile presso")
    estremi = ticked("answers-estremi.json")
    dl = "si comunicano gli estremi della dichiarazione di regolare esecuzione"
    assert has(estremi, "reperibile presso", anchor=dl, value="Genio Civile di Napoli")
    assert not has(estremi, "reperibile presso", anchor="si comunicano gli estremi del certificato di collaudo statico")
    assert has(estremi, "prot./n.", anchor="si comunicano gli estremi della richiesta di assegnazione", value="PG/2026/0999996")
    assert has(estremi, "prot./n.", value="PG/2026/0999995")  # the lift's communication
    assert has(estremi, "l'agibilità parziale relativa a singole unità immobiliari", nth=None)
    assert not has(estremi, "SCIA ai sensi")
    assert has(estremi, "Copia di elaborato planimetrico")  # a partial agibilità's plan
    assert not has(allegato, "Copia di elaborato planimetrico")
    parziale = ticked("answers-parziale.json")
    assert has(parziale, "interessa un edificio privato aperto al pubblico")
    assert not has(parziale, "interessa un edificio privato ed è soggetto")


@case("the SCIA in sanatoria: the wizard's Si adds its quadro; each case fills its own rows, by label where another case moves them; no start date")
def _():
    steps = gen.generate(gen.load_yaml(ROOT / "rehearsals" / "scia-sanatoria-fittizia" / "recipe.yaml"))
    assert steps["wizard"][-1]["answers"] == {"Le opere ricadono nell'ambito della Sanatoria": "Sì"}
    q = section(steps, "SANATORIA e regolarizzazioni")
    assert field(q, "sanatoria di intervento soggetto a SCIA, in assenza della SCIA stessa")["kind"] == "checkbox"
    a = section(steps, "Asseverazione SCIA - Stato legittimo")
    for label in ("realizzato in data", "in euro", "presentata con prot.", "dichiara che l’intervento da sanare"):
        assert "id" not in field(a, label), label  # moved by the case ticked before them
    doppia = filled(steps, p6_values("scia-sanatoria-fittizia"))
    assert "516" in doppia[gen.norm("SANATORIA e regolarizzazioni per interventi già realizzati")]
    assert "NA0888888" in doppia[gen.norm("Asseverazione SCIA - Stato legittimo")]
    assert doppia.get(gen.norm("Presentazione della SCIA/SCIA Unica/SCIA Condizionata"), []) == []
    corso = filled(steps, p6_values("scia-sanatoria-fittizia", "answers-in-corso.json"))
    assert "IUV 0000000000000000 (inventato)" in corso[gen.norm("SANATORIA e regolarizzazioni per interventi già realizzati")]
    plain = filled(gen.generate(gen.load_yaml(ROOT / "rehearsals" / "scia-fittizia" / "recipe.yaml")), p6_values("scia-fittizia"))
    assert plain[gen.norm("Presentazione della SCIA/SCIA Unica/SCIA Condizionata")] == ["23/11/2026"]


@case("an unquoted label with a comma, which YAML splits into a label and an empty key, is refused")
def _():
    d = {"sections": [{"section": "X", "fields": gen.yaml.safe_load("[{kind: checkbox, label: a, comma 4, allegata, when: x}]")}]}
    try:
        gen.split_by_yaml(d, {})
    except gen.GenError as e:
        assert "comma 4" in str(e), e
    else:
        raise AssertionError("not refused")
    gen.split_by_yaml({"sections": [{"section": "X", "fields": [{"kind": "checkbox", "label": "a, comma 4"}]}]}, {})


@case("an id from a choice seen only nested under another isn't guessed: the permesso's specificare goes by label")
def _():
    st = gen.generate(gen.load_yaml(REH / "pdc-fittizio" / "recipe.yaml"))
    f = [f for s in st["sections"] for f in s["fields"] if (f.get("label") or "").startswith("specificare tipo intervento")]
    assert f and "id" not in f[0], f


@case("a choice the crawl tried apart moves its reveals by the earlier choices' offsets, not by its own (SCIA tolerances)")
def _():
    crawl = gen.json.loads((HERE.parent / "catalogue" / "F839" / "sections" / "scia.json").read_text())
    s = gen.Section(next(x for x in crawl["sections"] if x["section"].startswith("Asseverazione SCIA - Stato legittimo")))
    s.choose(s.find("radio", "si")[0])     # the state: one row more from r7c13
    s.choose(s.find("radio", "si", 2)[0])  # the tolerances, crawled apart: 20 rows more from r7c13
    # The crawl's r7c1p12 already has the 20 rows; only the first choice's one is added.
    assert s.find("checkbox", "TOLLERANZA DI CUI ALL’ART. 34-BIS, COMMA 1 E 1-TER")[0]["id"] == "r8c1p13reg:chk"


@case("a yes or a no is a whole word, other short labels stay prefixes (the sanatoria's no below the tolerances)")
def _():
    assert gen.starts_label("no", "no") and gen.starts_label("No (barrare)", "no") and gen.starts_label("sì", "si")
    assert not gen.starts_label("non ha rilevanza strutturale;", "no") and not gen.starts_label("sistema di", "si")
    assert gen.starts_label("Telefono", "tel") and gen.starts_label("dell'immobile", "del")
    assert not gen.matches({"kind": "radio", "label": "non ha rilevanza strutturale;"}, "radio", "no")
    assert gen.matches({"kind": "radio", "label": "no"}, "radio", "no")


@case("the bollo: pagoPA proposed, never assumed; with marche, two serials and dates by label; no section, no question")
def _():
    import json
    import run
    fields = dict(json.loads((CILA / "fixture-p6.json").read_text())["fields"])
    steps = generated("paesaggistica-semplificata-fittizia")
    a = json.loads((REH / "paesaggistica-semplificata-fittizia" / "answers-p6.json").read_text())
    del a["bollo_marche"]
    r = run.preflight(steps, run.Values(a, fields=fields, asks=steps.get("asks")), made_up=True)
    assert [p["proposal"] for p in r["proposals"] if p["key"] == "bollo_marche"] == ["false"], r["proposals"]
    m = json.loads((REH / "paesaggistica-semplificata-fittizia" / "answers-marche.json").read_text())
    plan = run.plan(steps, run.Values(m, fields=fields, asks=steps.get("asks")))
    bollo = [(p["label"], p.get("value")) for p in plan if "bollo" in p["section"].lower()]
    # Both serial boxes are titled "numero seriale (1)" on the portal: the first, then the second.
    assert [v for l, v in bollo if l == "numero seriale (1)"] == ["01234567890123", "01234567890124"], bollo
    assert [l for l, _ in bollo].index("Marca da €16,00 per l'autorizzazione") < [l for l, _ in bollo].index("numero seriale (1)")
    sec = section(steps, "Dichiarazione relativa all'assolvimento")
    assert all("id" not in f for f in sec["fields"] if (f.get("label") or "").startswith(("numero seriale", "data")))
    assert "bollo_marche" not in generated("nomina-impresa-fittizia").get("asks", {})


@case("systems needing a project: the permesso's every kind, and each project's slot, in the five pratiche that refused them")
def _():
    import json
    import run
    fields = dict(json.loads((CILA / "fixture-p6.json").read_text())["fields"])
    for name in ("pdc-fittizio", "pdc-sanatoria-fittizio", "scia-alternativa-fittizia",
                 "scia-paesaggistica-ordinaria-fittizia", "scia-paesaggistica-semplificata-fittizia"):
        steps = generated(name)
        assert not any("Systems needing a project" in c.get("else", "") for c in steps["supports"]), name
        v = run.Values(json.loads((REH / name / "answers-impianti.json").read_text()), fields=fields, asks=steps.get("asks"))
        assert run.preflight(steps, v, made_up=True)["ready"], name
        labels = [p["label"] or "" for p in run.plan(steps, v)]
        assert any(l.startswith("è soggetto agli obblighi di presentazione del progetto") for l in labels), name
        assert any(l.startswith("Progetto degli impianti radiotelevisivi") for l in labels), name
        assert "radiotelevisivi" in labels and "di protezione antincendio" in labels, name


@case("the CILA's technicians: another direttore dei lavori, another technician (G2, the SCIA's H2 too), filings presented with it and assents for the SUE")
def _():
    import json
    import run
    fields = dict(json.loads((CILA / "fixture-p6.json").read_text())["fields"])
    def check(name, answers, **change):
        steps = generated(name)
        a = json.loads((REH / name / answers).read_text()); a.update(change)
        v = run.Values(a, fields=fields, asks=steps.get("asks"))
        return steps, v, run.preflight(steps, v, made_up=True)
    steps, v, r = check("cila-fittizia", "answers-direttore-atti.json")
    assert r["ready"], r
    plan = [(p["label"] or "", str(p.get("value") or "")) for p in run.plan(steps, v)]
    assert ("Cognome", "ESEMPIO") in plan and ("Tipologia di atto", "Deroga ai requisiti igienico-sanitari dei locali (inventata)") in plan
    assert [x for l, x in plan if l == "Autorità competente"] == ["ASL Napoli 1 Centro", "Comune di Napoli"], plan
    for name in ("cila-fittizia", "scia-fittizia"):
        steps, v, r = check(name, "answers-altri-tecnici.json")
        assert r["ready"], (name, r)
        labels = [p["label"] for p in run.plan(steps, v)]
        assert "Incaricato della" in labels and "Iscritto all'ordine/collegio" in labels, name
        assert not any((l or "").startswith("che gli altri tecnici incaricati saranno") for l in labels), name
    # As many as the case has (the national form sets no limit): ten technicians, three filings
    # and three assents, each past the page's first by "+".
    for name in ("cila-fittizia", "scia-fittizia"):
        steps, v, r = check(name, "answers-elenchi-lunghi.json")
        assert r["ready"] and not r["unsupported"], (name, r)
        plan = run.plan(steps, v)
        tecnici = [p for p in plan if "Altri tecnici" in p["section"]]
        assert sum(p["kind"] == "add" for p in tecnici) == 9 and ("Cognome", "VENTO") in [(p["label"], p["value"]) for p in tecnici], name
    rel = [(p["kind"], p["label"] or "", p["value"]) for p in run.plan(*check("cila-fittizia", "answers-elenchi-lunghi.json")[:2])
           if p["section"].startswith("Relazione Tecnica")]
    c, t = "Comunicazioni, segnalazioni", "Tipologia di atto"
    assert [l or "+" for k, l, _ in rel if k == "add" or l.startswith((c, t))] == [c, c, "+", c, t, t, "+", t], rel
    # The count first: before it is answered, the second technician's questions wait on it.
    steps, v, r = check("cila-fittizia", "answers-altri-tecnici.json", altri_tecnici_quanti=None)
    assert [p["proposal"] for p in r["proposals"] if p["key"] == "altri_tecnici_quanti"] == ["1"], r
    assert {q["key"]: q.get("only_if") for q in r["questions"]}.get("altro_tecnico2_incarico") == ["altri_tecnici_quanti"], r["questions"]


@case("other technicians repeat by \"+\" (a, a2, a3), each an employee of a firm or not (ad: its seat is the studio)")
def _():
    import json
    import run
    fields = dict(json.loads((CILA / "fixture-p6.json").read_text())["fields"])
    for name, answers, n in (("cila-fittizia", "answers-altri-tecnici-tre.json", 3), ("scia-fittizia", "answers-altri-tecnici-due.json", 2),
                             ("pdc-fittizio", "answers-altri-tecnici.json", 2), ("cila-fittizia", "answers-altri-tecnici.json", 1)):
        steps = generated(name)
        v = run.Values(json.loads((REH / name / answers).read_text()), fields=fields, asks=steps.get("asks"))
        r = run.preflight(steps, v, made_up=True)
        assert r["ready"], (name, r)
        planned = [p for p in run.plan(steps, v) if "Altri tecnici" in p["section"]]
        assert sum(p["kind"] == "add" for p in planned) == n - 1, name
        assert sum(p.get("label") == "Incaricato della" for p in planned) == n, name
        employed = any(p.get("label") == "Ragione sociale" and p.get("value") == "Impianti Fittizi S.n.c." for p in planned)
        assert employed == (answers != "answers-altri-tecnici.json" or name == "pdc-fittizio"), name
    # No other technicians: whether one is an employee is never asked, nor their studio read.
    steps = generated("cila-fittizia")
    r = run.preflight(steps, run.Values(json.loads((REH / "cila-fittizia" / "answers-p6.json").read_text()), fields=fields, asks=steps.get("asks")), made_up=True)
    assert r["ready"] and "altro_tecnico_dipendente" not in json.dumps(r), r


@case("the permesso's other kinds: Campania's (quadro a's procedimento ordinario), convenzionato, deroga, variants, art. 36; the piano casa closed by law")
def _():
    import json
    import run
    import branches
    fields = dict(json.loads((CILA / "fixture-p6.json").read_text())["fields"])
    def plan(name, answers, **change):
        steps = generated(name)
        a = json.loads((REH / name / answers).read_text()); a.update(change)
        v = run.Values(a, fields=fields, asks=steps.get("asks"))
        r = run.preflight(steps, v, made_up=True)
        return r, ([(p["label"] or "", str(p.get("value") or "")) for p in run.plan(steps, v)] if r["ready"] else [])
    has = lambda p, label: any(l.startswith(label) for l, _ in p)
    r, p = plan("pdc-fittizio", "answers-sottotetti.json")
    assert r["ready"] and has(p, "attività che rientrano nell'ambito del procedimento ordinario"), r
    assert has(p, "interventi di recupero abitativo dei sottotetti") and has(p, "Interventi di recupero abitativo dei sottotetti")
    assert not has(p, "interventi di cui all'articolo 10") and "pdc_procedura" not in json.dumps(r)
    r, p = plan("pdc-fittizio", "answers-mutamento-lr.json")
    assert has(p, "Mutamento di destinazione d'uso, ai sensi dell'articolo 2") and has(p, "con opere che determinino un aumento plano volumetrico")
    r, p = plan("pdc-fittizio", "answers-convenzionato.json")
    assert has(p, "permesso di costruire convenzionato") and has(p, "Permesso di costruire convenzionato") and has(p, "Interventi di ristrutturazione edilizia che portino")
    r, p = plan("pdc-fittizio", "answers-deroga.json")
    assert [v for l, v in p if l == "(specificare)"] == ["Indice fondiario 3,5 mc/mq invece di 3 (inventato)", "Altezza 14 m invece di 12 m (inventato)", "Distanza 8 m invece di 10 m (inventato)"], p
    assert has(p, "intervento in deroga alle previsioni") and not has(p, "alla destinazione d'uso")
    r, p = plan("pdc-fittizio", "answers-deroga.json", deroga_densita="false", deroga_altezza="false", deroga_distanza="false")
    assert any("derogates from at least one limit" in u for u in r["unsupported"]), r
    for answers, radio in (("answers-variante-scia-alt.json", "segnalazione certificata/denuncia"), ("answers-variante-titolo-unico.json", "titolo unico"),
                           ("answers-variante-sagoma.json", "permesso di costruire")):
        r, p = plan("pdc-fittizio", answers)
        assert r["ready"] and has(p, "variazione essenziale e/o sostanziale") and has(p, radio) and ("n.", "4321") in p, (answers, p)
    r, p = plan("pdc-fittizio", "answers-p6.json", pdc_tipo="piano casa")
    assert any("30 September 2022" in u for u in r["unsupported"]), r
    # The sanatoria's quadro a) is art. 36's own radio, not art. 10's.
    r, p = plan("pdc-sanatoria-fittizio", "answers-p6.json")
    assert r["ready"] and has(p, "intervento realizzato, ai sensi dell'articolo 36") and not has(p, "interventi di cui all'articolo 10"), p
    r, _ = plan("pdc-sanatoria-fittizio", "answers-p6.json", pdc_procedura="deroga")
    assert any("asked as such" in u for u in r["unsupported"]), r
    # A sewer connection to request adds its own required slot (read on the permesso 2026-10-31).
    for name, answers in (("pdc-fittizio", "answers-cambio-tra.json"), ("scia-alternativa-fittizia", "answers-condominio-strutture.json")):
        r, p = plan(name, answers)
        assert r["ready"] and has(p, "Documentazione necessaria per la richiesta di autorizzazione all'allaccio"), (name, r)
    law = [x for x in branches.rows() if x["state"] == "law"]
    # The permesso's impianti name the piano casa by its law (l.r. 19/2009).
    assert len(law) >= 20 and all("piano casa" in x["choice"].lower() or "19/2009" in x["choice"] or x.get("depth", 0) > 1
                                  for x in law), len(law)



@case("a ticked \"si allega\" with no slot under its condition is listed, unless the portal was read for it (`slot`)")
def _():
    import copy
    steps = generated("pdc-fittizio")
    assert gen.unslotted(steps) == [], gen.unslotted(steps)
    # The permesso's prospetto box adds no slot (read 2026-11-01): without that read it is listed.
    unread = copy.deepcopy(steps)
    for s in unread["sections"]:
        for f in s["fields"]:
            if f.get("label", "").startswith("allega il prospetto di calcolo"):
                f.pop("slot")
    assert [l for _, l, _ in gen.unslotted(unread)] == ["allega il prospetto di calcolo preventivo"], gen.unslotted(unread)


@case("the semplificata's \"Si allega\" adds a required slot on the SCIA, the permesso and the SCIA alternativa, not on a CILA or a CIL")
def _():
    files = lambda name: [f["label"] for s in generated(name)["sections"] for f in s["fields"] if f["kind"] == "file"]
    slot = "Relazione paesaggistica semplificata e documentazione necessaria"
    for name in ("scia-paesaggistica-semplificata-fittizia", "pdc-paesaggistica-semplificata-fittizio",
                 "scia-alt-paesaggistica-semplificata-fittizia", "scia-sanatoria-paesaggistica-semplificata-fittizia"):
        assert slot in files(name), name
    for name in ("cil-paesaggistica-semplificata-fittizia", "cila-paesaggistica-fittizia"):
        assert slot not in files(name), name


@case("a SCIA never sanates works done without a permesso (art. 36: the permesso in sanatoria's), only partial difformity")
def _():
    import json
    import run
    fields = dict(json.loads((CILA / "fixture-p6.json").read_text())["fields"])
    for name in ("scia-fittizia", "scia-sanatoria-fittizia", "scia-sanatoria-paesaggistica-ordinaria-fittizia"):
        steps = generated(name)
        for caso, refused in (("assenza", True), ("parziale", False)):
            a = json.loads((REH / name / "answers-p6.json").read_text()) | {"sanatoria_titolo": "permesso", "pdc_sanatoria_caso": caso}
            r = run.preflight(steps, run.Values(a, fields=fields, asks=steps.get("asks")), made_up=True)
            assert any("art. 36 DPR" in u for u in r["unsupported"]) == refused, (name, caso, r["unsupported"])


@case("the proroga's permesso with its landscape authorization: the box, its prot. n. and the second \"del\" (crawled 2026-11-01)")
def _():
    import json
    import run
    fields = dict(json.loads((CILA / "fixture-p6.json").read_text())["fields"])
    name = "proroga-straordinaria-ultimazione-fittizia"
    steps = generated(name)
    p = run.plan(steps, run.Values(json.loads((REH / name / "answers-paesaggistica.json").read_text()), fields=fields, asks=steps.get("asks")))
    got = [(x["label"], str(x.get("value") or "")) for x in p if x["section"].startswith("Riferimenti titolo")]
    assert ("e autorizzazione paesaggistica", "") in got and ("prot.n.", "PG/2025/0777777") in got and ("del", "10/12/2025") in got, got
    sec = section(steps, "Riferimenti titolo")
    assert [f.get("nth") for f in sec["fields"] if f.get("value") == "{{ask.paes_data|date_it}}" and "titolo_con_paesaggistica" in f["when"]] == [2, 2]
    p = run.plan(steps, run.Values(json.loads((REH / name / "answers-p6.json").read_text()), fields=fields, asks=steps.get("asks")))
    assert not any(x["label"] == "e autorizzazione paesaggistica" for x in p)



@case("rerun.py --record files each run in its rehearsal's runs.json, once")
def _():
    import json
    import tempfile
    sys.path.insert(0, str(HERE))
    import rerun
    with tempfile.TemporaryDirectory() as t:
        before, rerun.REHEARSALS = rerun.REHEARSALS, Path(t)
        try:
            (Path(t) / "pdc-fittizio").mkdir()
            done = [{"name": "pdc-fittizio/answers-deroga", "result": "filled", "total_seconds": 142.4},
                    {"name": "pdc-fittizio", "result": "stopped"}]
            rerun.record(done, "answers-p6.json", "2026-10-31")
            rerun.record(done, "answers-p6.json", "2026-10-31")
            runs = json.loads((Path(t) / "pdc-fittizio" / "runs.json").read_text())
        finally:
            rerun.REHEARSALS = before
    assert [(r["answers"], r["result"]) for r in runs] == [("answers-deroga.json", "filled"), ("answers-p6.json", "stopped")], runs



@case("catalogue.py pane --bundle: one picked file installs and starts the crawl; export.js saves what the store couldn't keep")
def _():
    import hashlib
    import json
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        (t / "ops.json").write_text(json.dumps([{"name": "cila", "sector": "S", "path": "P"}]))
        subprocess.run([sys.executable, str(HERE.parent / "catalogue.py"), "pane", str(t / "out"), "--bundle",
                        str(t / "pv-prova.js"), "--ops", str(t / "ops.json"), "--fresh"], check=True, capture_output=True)
        text = (t / "pv-prova.js").read_text()
        assert hashlib.sha256(text.encode()).hexdigest() in (t / "out" / "pick.js").read_text()
        assert "window.__crawl.batch(opts)" in text and 'localStorage.removeItem(\"crawl:op:\" + o.name)' in text
        export = (t / "out" / "export.js").read_text()
        assert "__crawlUnsaved" in export and "crawl-batch-prova.json" in export
        assert "crawl:batch" in (t / "out" / "status.js").read_text()


@case("catalogue.py: a combination is one op (the procura only, its slots read), and a printed batch that changed is refused")
def _():
    import json
    import subprocess
    cat = [sys.executable, str(HERE.parent / "catalogue.py")]
    ops = json.loads(subprocess.run(cat + ["ops", "sue", "--combo", "sue-combo-prova", "Permesso di Costruire (P.d.C) - Art.10 D.P.R. 380/2001",
                                           "Autorizzazione paesaggistica semplificata (DPR 31/2017 - Comune)"],
                                    check=True, capture_output=True, text=True).stdout)
    assert len(ops) == 1 and ops[0]["slots"] and ops[0]["also"][0].endswith("(DPR 31/2017 - Comune)") and "PROCURA" in ops[0]["scelte"][0], ops
    two = json.loads(subprocess.run(cat + ["ops", "sue", "--combo", "a", "Permesso di Costruire (P.d.C) - Art.10 D.P.R. 380/2001",
                                           "Autorizzazione paesaggistica semplificata (DPR 31/2017 - Comune)",
                                           "--combo", "b", "Permesso di Costruire (P.d.C) - Art.10 D.P.R. 380/2001",
                                           "Autorizzazione paesaggistica ordinaria (art.146 del D.Lgs 42/2004 - Comune)"],
                                    check=True, capture_output=True, text=True).stdout)
    assert [o["name"] for o in two] == ["a", "b"] and two[1]["also"][0].endswith("(art.146 del D.Lgs 42/2004 - Comune)"), two
    bad = subprocess.run(cat + ["import", "-"], input="0" * 64 + "\n{}", capture_output=True, text=True)
    assert bad.returncode and "sha256 differs" in bad.stderr, bad.stderr
    # A copy with the newline a heredoc adds is the same text: hashed without it.
    import hashlib
    body = '{"other": 1}'
    ok = subprocess.run(cat + ["import", "-"], input=hashlib.sha256(body.encode()).hexdigest() + "\n" + body + "\n",
                        capture_output=True, text=True)
    assert ok.returncode == 0, ok.stderr


@case("catalogue.py graft: a deeper crawl of a section goes into every stored copy of it; a changed one is refused")
def _():
    import argparse
    import json
    import tempfile
    sys.path.insert(0, str(HERE.parent))
    import catalogue
    sec = lambda **k: {"section": "Asseverazione X - stato legittimo", "fingerprint": "f1", "fields": [], **k}
    with tempfile.TemporaryDirectory() as t:
        before, catalogue.SECTIONS = catalogue.SECTIONS, Path(t)
        try:
            for name, s in (("a", sec(branches=[])), ("b", sec(branches=[])), ("c", {"section": "Asseverazione X - stato legittimo", "same_as": "a#x"})):
                (Path(t) / f"{name}.json").write_text(json.dumps({"by": "crawl.js batch, depth 3", "sections": [s]}))
            deeper = {"crawl:op:d8": {"name": "d8", "crawled": "2026-11-01T10:00:00Z", "depth": 8,
                                      "sections": [sec(branches=[{"choice": "una classe"}], section="Asseverazione X - stato legittimo, altro")]}}
            (Path(t) / "in").mkdir()
            (Path(t) / "in" / "export.json").write_text(json.dumps(deeper))
            args = argparse.Namespace(export=str(Path(t) / "in" / "export.json"), section=["Asseverazione X - stato legittimo"])
            out = catalogue.cmd_graft(args)
            got = {n: json.loads((Path(t) / f"{n}.json").read_text())["sections"][0] for n in "abc"}
            deeper["crawl:op:d8"]["sections"][0]["fingerprint"] = "f2"
            (Path(t) / "in" / "export.json").write_text(json.dumps(deeper))
            try:
                catalogue.cmd_graft(args)
                refused = False
            except SystemExit as e:
                refused = "crawl the pratica again" in str(e)
        finally:
            catalogue.SECTIONS = before
    assert len(out) == 2 and all(got[n]["branches"] == [{"choice": "una classe"}] and got[n]["depth"] == 8 for n in "ab"), (out, got)
    assert got["a"]["section"] == "Asseverazione X - stato legittimo" and "branches" not in got["c"] and refused, got


@case("extends: later ones win, attachments and supports add up, asks and rules merge, null drops")
def _():
    out = {}
    gen.merge_recipe(out, {"title": "a", "asks": {"x": 1, "y": 2}, "rules": {"table": "t", "facts": {}},
                           "supports": [{"when": "1"}], "attachments": {"S": [{"label": "A"}]}, "after": ["P"]})
    gen.merge_recipe(out, {"title": "b", "asks": {"y": None, "z": 3}, "rules": {"main": "m"},
                           "supports": [{"when": "1"}, {"when": "2"}], "attachments": {"S": [{"label": "B"}]}, "after": None})
    assert out == {"title": "b", "asks": {"x": 1, "z": 3}, "rules": {"table": "t", "facts": {}, "main": "m"},
                   "supports": [{"when": "1"}, {"when": "2"}], "attachments": {"S": [{"label": "A"}, {"label": "B"}]}}, out
    try:
        gen.resolved({"extends": ["parts/nessuna"]})
        raise AssertionError("a missing part went unnoticed")
    except gen.GenError:
        pass


@case("a combination carries its main pratica's slots and refusals, and its part's (2026-10-31: the SCIA's had drifted)")
def _():
    for main, part, combos in [("scia-fittizia", None, ["scia-paesaggistica-semplificata-fittizia", "scia-paesaggistica-ordinaria-fittizia"]),
                               ("pdc-fittizio", None, ["pdc-paesaggistica-semplificata-fittizio", "pdc-paesaggistica-ordinaria-fittizio"])]:
        base = gen.resolved(gen.load_yaml(ROOT / "rehearsals" / main / "recipe.yaml"))
        for c in combos:
            r = gen.resolved(gen.load_yaml(ROOT / "rehearsals" / c / "recipe.yaml"))
            for screen, slots in base["attachments"].items():
                missing = [s["label"] for s in slots if s not in r["attachments"][screen]]
                assert not missing, f"{c} lacks {main}'s slots {missing}"
            assert all(s in r["supports"] for s in base["supports"]), c
            kind = c.split("-")[-2]
            assert r["asks"]["paesaggio"]["default"] == kind and r["rules"]["handles"] == [f"napoli/comune/autorizzazione-paesaggistica-{kind}"], c
    ordinaria = gen.resolved(gen.load_yaml(ROOT / "rehearsals" / "pdc-paesaggistica-ordinaria-fittizio" / "recipe.yaml"))
    assert any(s["label"].startswith("Relazione paesaggistica e documentazione") for s in ordinaria["attachments"]["Gestione degli allegati"])


@case("a combination's P6 answers are its main pratica's, its part's and its own: none has drifted (gen.py --answers)")
def _():
    import json
    combos = [p.parent for p in sorted(REH.glob("*/recipe.yaml")) if (gen.load_yaml(p) or {}).get("answers")]
    assert len(combos) >= 7, combos
    for d in combos:
        want = gen.combo_answers(gen.load_yaml(d / "recipe.yaml"))
        assert json.loads((d / "answers-p6.json").read_text()) == want, f"{d.name}: regenerate with gen.py --answers"
    # A part's null drops the main pratica's answer, its value replaces one (paesaggio, stated since
    # the CILA's steps don't take the ask's default); the recipe's own win over the part's.
    o = gen.combo_answers(gen.load_yaml(REH / "pdc-paesaggistica-ordinaria-fittizio" / "recipe.yaml"))
    assert o["paesaggio"] == "ordinaria" and "assenso_proprietario" not in o and o["titolo"] == "proprietario", o
    c = gen.combo_answers(gen.load_yaml(REH / "cila-paesaggistica-fittizia" / "recipe.yaml"))
    assert c["paesaggio"] == "semplificata", c.get("paesaggio")


@case("the permesso with its landscape authorization: the asseverazione names the procedure")
def _():
    for kind, label in [("semplificata", "è assoggettato al procedimento semplificato"), ("ordinaria", "è assoggettato al procedimento ordinario")]:
        import run
        steps = gen.generate(gen.load_yaml(ROOT / "rehearsals" / f"pdc-paesaggistica-{kind}-fittizio" / "recipe.yaml"))
        v = p6_values(f"pdc-paesaggistica-{kind}-fittizio")(steps)
        sec = section(steps, "Asseverazione PdC - tutela storico")
        ticked = [f["label"] for f in sec["fields"] if run.truthy(v.render(f.get("when", "true")) or "")]
        assert label in ticked and "ricade in zona tutelata e le opere comportano alterazione" in ticked, (kind, ticked)


@case("a firm block's field keeps its own `when` after the block's: the Cassa edile's rows only for a firm enrolled")
def _():
    steps = gen.generate(gen.load_yaml(ROOT / "rehearsals" / "scia-fittizia" / "recipe.yaml"))
    sec = section(steps, "i) Impresa esecutrice")
    cassa = next(f for f in sec["fields"] if f.get("label") == "Cassa edile" and f["block"] == 1)
    assert cassa["when"] == "{{ask.lavori_in_proprio|not}} {{ask.impresa_dopo|not}} {{f1:business.cassa_edile_codice_impresa|empty|not}}", cassa
    second = next(f for f in sec["fields"] if f.get("label") == "Cassa edile" and f["block"] == 2)
    assert "{{f2:business.denominazione|empty|not}} {{f2:business.cassa_edile_codice_impresa|empty|not}}" in second["when"], second


@case("the SCIA's h1: under another technician's direction the structural designer is the second Cognome block")
def _():
    import run
    steps = gen.generate(gen.load_yaml(ROOT / "rehearsals" / "scia-fittizia" / "recipe.yaml"))
    sec = section(steps, "h1) Tecnici incaricati")
    for answers, d_block, s_block in [("answers-direttori.json", 1, 2), ("answers-strutture.json", None, 1)]:
        v = p6_values("scia-fittizia", answers)(steps)
        on = [f for f in sec["fields"] if run.truthy(v.render(f.get("when", "true")) or "")]
        blocks = lambda role: {f["block"] for f in on if "{{%s:" % role in str(f.get("value"))}
        assert blocks("s") == {s_block} and blocks("d") == ({d_block} if d_block else set()), (answers, blocks("s"), blocks("d"))


@case("one box ticked by two labels under one condition is ticked once: the second choice would move the rows after it")
def _():
    steps = gen.generate(gen.load_yaml(ROOT / "rehearsals" / "cila-fittizia" / "recipe.yaml"))
    sec = section(steps, "h) Impresa esecutrice")
    radios = [f for f in sec["fields"] if f["kind"] == "radio"]
    # "lavori sono/saranno eseguiti dall" is inside the CILA's own "che i lavori ...": one step
    assert [f["label"] for f in radios] == ["che, in quanto opere di modesta entità", "che i lavori sono/saranno eseguiti dall"], radios


@case("an on_page tick box isn't sent where the crawl has its label as the other kind (the SCIA alternativa's notifica radio)")
def _():
    steps = gen.generate(gen.load_yaml(ROOT / "rehearsals" / "scia-alternativa-fittizia" / "recipe.yaml"))
    sec = section(steps, "l) Rispetto degli obblighi")
    hits = [f["kind"] for f in sec["fields"] if f.get("label") == "e allega alla presente segnalazione la notifica"]
    assert hits == ["radio"], hits


@case("a box only a choice opens, under a `when` that starts elsewhere: the problem says to start it with that choice's term")
def _():
    import json
    d = gen.load_yaml(HERE.parent / "dictionary" / "fnsuap.yaml")
    e = next(x for x in d["sections"] if x["section"] == "Tecnici incaricati" and x.get("aliases"))
    next(f for f in e["fields"] if f.get("label") == "si")["when"] = "{{ask.direttore_lavori|is_altro_tecnico}}"
    crawl = json.loads((HERE.parent / "catalogue" / "F839" / "sections" / "scia.json").read_text())
    c = next(s for s in crawl["sections"] if s["section"].startswith("h1)"))
    recipe = gen.resolved(gen.load_yaml(ROOT / "rehearsals" / "scia-fittizia" / "recipe.yaml"))
    probs = gen.fill(e, "h1) Tecnici incaricati", c, recipe, "h1)")[1]
    assert probs and "start its `when` with that choice's first term" in probs[0], probs


@case("the permesso's g1: the designer's second block comes after the director's tick that opens the first; its slots aren't the SCIA's")
def _():
    import json
    import run
    steps = generated("pdc-fittizio")
    sec = section(steps, "g1) Tecnici incaricati")
    order = [(f["kind"], f.get("label"), f.get("block"), str(f.get("value")), f.get("when", "")) for f in sec["fields"]]
    tick = next(i for i, (k, l, _, _, _) in enumerate(order) if k == "radio" and l == "si")
    # The structural designer's block below the director's: the second, or the third under another
    # architectural designer (whose block, opened by its own radio earlier, is the first).
    second = [i for i, (_, _, b, v, w) in enumerate(order) if "{{s:" in v and b in (2, 3)
              and "{{ask.direttore_lavori|is_altro_tecnico}}" in w.split()]
    # A block 2 exists only once the director's block has opened above it (read 2026-11-02).
    assert second and min(second) > tick, (tick, second)
    # The permesso has no slot for a barriers deroga or a scomputo proposal; the SCIA
    # alternativa has the scomputo's (read on each screen, 2026-11-02).
    fields = dict(json.loads((CILA / "fixture-p6.json").read_text())["fields"])
    def slots(name, answers):
        steps = generated(name)
        v = run.Values(json.loads((REH / name / answers).read_text()), fields=fields, asks=steps.get("asks"))
        assert run.preflight(steps, v, made_up=True)["ready"]
        return [p["label"] for p in run.plan(steps, v) if p["kind"] == "file"]
    pdc = slots("pdc-fittizio", "answers-strumenti-barriere.json")
    assert not any(l.startswith(("Documentazione per la richiesta di deroga", "Proposta di progetto")) for l in pdc), pdc
    alt = slots("scia-alternativa-fittizia", "answers-scomputo-pozzi.json")
    assert "Proposta di progetto per la realizzazione delle opere di urbanizzazione" in alt, alt


@case("the Scheda anagrafica's client: a person keeps its ids, a company's three ways each keep the crawl's; a when's own fields aren't missing under a false word")
def _():
    import json
    import run
    sec = section(generated("cila-fittizia"), "Scheda anagrafica")
    person = [f for f in sec["fields"] if f.get("when", "").startswith("{{c:business.denominazione|empty}}")]
    assert next(f for f in person if f.get("label") == "Nome")["id"] == "r10c1p23reg:txt"
    iscritta = [f for f in sec["fields"] if "impresa_iscritta" in f.get("when", "")]
    # ISCRITTA moves every row below it 3 down: the company's sede, after Forma giuridica flags
    # its empty boxes, is found by its id (its label lookup counted two Provincia, 2026-11-02).
    sede = [f for f in iscritta if f.get("label") == "Provincia" and f.get("nth") == 3]
    assert sede and sede[0]["id"] == "r47c2p121reg", sede
    fields = dict(json.loads((CILA / "fixture-p6.json").read_text())["fields"])
    steps = generated("cila-fittizia")
    for answers in ("answers-condominio.json", "answers-non-ue.json", "answers-p6.json"):
        v = run.Values(json.loads((CILA / answers).read_text()), fields=fields, asks=steps.get("asks"))
        r = run.preflight(steps, v, made_up=True)
        assert r["ready"] and not r["missing"], (answers, r["missing"])


@case("another designer (`p:`): their block is the first Cognome, every other block counts one more under it (`shift`), the architect's own rows only without; the person is told to have them sign")
def _():
    import json
    import run
    fields = dict(json.loads((CILA / "fixture-p6.json").read_text())["fields"])
    for name, sec_name in (("cila-fittizia", "G1) Tecnici incaricati"), ("scia-fittizia", "h1) Tecnici incaricati"),
                           ("pdc-fittizio", "g1) Tecnici incaricati")):
        sec = section(generated(name), sec_name)
        cognomi = [f for f in sec["fields"] if f.get("label") == "Cognome"]
        designer = [f for f in cognomi if f["value"].startswith("{{p:")]
        assert [f.get("block") for f in designer] == [1], (name, designer)
        others = [f for f in cognomi if f not in designer]
        without = [f for f in others if f["when"].endswith(" {{ask.progettista_altro|not}}")]
        under = [f for f in others if f["when"].endswith(" {{ask.progettista_altro}}")]
        assert others and len(without) == len(under) == len(others) // 2, (name, others)
        assert all(g["value"] == f["value"] and g["block"] == f["block"] + 1 for f, g in zip(without, under)), name
        own = [f for f in sec["fields"] if "{{t:" in f.get("value", "") or "{{business." in f.get("value", "")]
        assert own and all(f["when"].startswith("{{ask.progettista_altro|not}}") for f in own), (name, own)
    steps = generated("scia-fittizia")
    for answers, signs in (("answers-progettista.json", True), ("answers-direttori.json", False)):
        v = run.Values(json.loads((ROOT / "rehearsals/scia-fittizia" / answers).read_text()), fields=fields, asks=steps.get("asks"))
        r = run.preflight(steps, v, made_up=True)
        assert r["ready"] and any("designer's (`p:`)" in y for y in r["yours"]) == signs, (answers, r["yours"])
        plan = [(p["section"], p["label"], p["value"]) for p in run.plan(steps, v)]
        assert (("Asseverazione SCIA - Tipologia di intervento", "Cognome", "Disegno") in plan) == signs, answers



@case("every steps file and combination's answers are as the dictionary, recipes and crawls write them now (regen.py --check)")
def _():
    import regen
    changed, refused = regen.regenerate(check=True)
    assert not refused, refused
    assert not changed, "regenerate (bench/regen.py): " + ", ".join(str(p.relative_to(regen.REHEARSALS)) for p in changed)


print(f"{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
