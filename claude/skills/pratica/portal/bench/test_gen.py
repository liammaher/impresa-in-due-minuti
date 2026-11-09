#!/usr/bin/env python3
"""gen.py offline, on the crawls in catalogue/F839/sections: no browser, no network.

  ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/test_gen.py
"""

import copy
import os
import re
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
os.chdir(ROOT)  # the answers name files from the repo's root, wherever this runs from
# catalogue.py's imports refuse to run without the login's pattern (2026-11-05); these crawls are the
# repo's own, so one that matches no name stands in for it.
os.environ.setdefault("CATALOGUE_PRIVATE", r"\bnessun-nome-fittizio\b")
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True
import gen  # noqa: E402
import run  # noqa: E402  (FILING, refusal_text: what the tecnico reads)
import yaml  # noqa: E402

gen.ensure()  # the rehearsals' steps files are built, never committed (steps.lock)

CILA = ROOT / "rehearsals" / "cila-fittizia"
# The golden case: the CILA P6 the first walk found by hand (2026-10-28), ids and values.
HAND_WALK = HERE / "fixtures" / "cila-p6-hand-walk.yaml"
FINE = ROOT / "rehearsals" / "fine-lavori-fittizia"
results = []


def rehearsal_plan(steps, values):
    """run.plan as a rehearsal's run takes it: made-up files, so no slot that takes only signed
    files, and nothing that waits for the declarations (run.phase)."""
    import run
    return run.plan(run.rehearsal(steps, values), values)


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
  fields:
    - {kind: radio, label: lavori sono/saranno eseguiti dall, if_present: true, when: "{{ask.lavori_in_proprio|not}}"}
    - kind: each
      count: "{{ask.imprese_quante}}"
      when: "{{ask.lavori_in_proprio|not}}"
      anchor: Ragione sociale
      block:
        - {kind: text, label: Ragione sociale, value: "{{f#K:business.denominazione}}"}
        - {kind: text, label: codice fiscale / p. IVA, value: "{{f#K:business.partita_iva}}"}
        - {kind: select, label: Iscritta alla C.C.I.A.A. di, value: "{{f#K:business.cciaa}}"}
        - {kind: text, label: n., nth: 1, value: "{{f#K:business.rea|rea_num}}"}
        - {kind: text, label: con sede in, value: "{{f#K:business.sede_legale_comune|upper}}"}
        - {kind: select, label: provincia, nth: 1, value: "{{f#K:business.sede_legale_provincia}}"}
        - {kind: text, label: "Via, Piazza", value: "{{f#K:business.sede_legale_indirizzo|upper}}"}
        - {kind: text, label: N., nth: 2, value: "{{f#K:business.sede_legale_civico}}"}
        - {kind: text, label: C.A.P., value: "{{f#K:business.sede_legale_cap}}"}
        - {kind: text, label: Cognome, value: "{{f#K:identity.last_name}}"}
        - {kind: text, label: Nome, value: "{{f#K:identity.first_name}}"}
        - {kind: text, label: codice fiscale, nth: 2, value: "{{f#K:identity.codice_fiscale}}"}
        - {kind: text, label: nato a, value: "{{f#K:identity.birth_comune|upper}}"}
        - {kind: select, label: provincia, nth: 2, value: "{{f#K:identity.birth_province}}"}
        - {kind: date, label: nato il, value: "{{f#K:identity.date_of_birth|date_it}}"}
        - {kind: text, label: cell., value: "{{f#K:identity.phone|phone_it}}"}
        - {kind: text, label: posta elettronica, value: "{{f#K:business.pec}}"}
        # DURC: each box opens its own rows (and renumbers what follows).
        - {kind: checkbox, label: INPS}
        - {kind: text, label: sede di, nth: 1, value: "{{f#K:business.sede_legale_comune|upper}}"}
        - {kind: text, label: Matr./Pos. Contr., value: "{{f#K:business.inps_matricola}}"}
        - {kind: checkbox, label: INAIL}
        - {kind: text, label: sede di, nth: 2, value: "{{f#K:business.inail_codice_sede}}"}
        - {kind: text, label: codice impresa, value: "{{f#K:business.inail_codice_ditta}}"}
        - {kind: text, label: pos. assicurativa, value: "{{f#K:business.inail_pat}}"}
""")


def p6_recipe():
    return gen.load_yaml(CILA / "recipe.yaml") | {"sections": P6_ONLY}


# A slot the hand walk left empty, Claude's since 2026-11-03.
NEW_SLOT = "Copia del documento di identità del/i titolare/i e/o del tecnico"


def as_p6_ran(steps):
    """A generated CILA as the P6 run took it: its first run with made-up files (run.phase),
    without the slot the hand walk left empty, one cadastral unit and one other holder (no "+"
    template: P6's count of other technicians is none too)."""
    import run
    steps = run.phase(steps, made_up=True)
    plus = {"Dati catastali": "foglio", "Titolarità dell'intervento": "Cognome"}
    one = lambda s, f: f.get("block") == "#N" and f.get("anchor") == plus.get(gen.QUADRO.sub("", s["section"]).strip())
    # P6's two firms: the firms' template written out as its second block, as the hand walk has it.
    firm = lambda f: {k: v for k, v in run.nth_block(f, 2).items() if k != "each"} | {"block": 2} \
        if (f.get("block") == "#N" or f.get("each")) and f.get("anchor") == "Ragione sociale" else f
    return steps | {"sections": [s | {"fields": [firm(f) for f in s["fields"] if f.get("label") != NEW_SLOT and not one(s, f)]}
                                 for s in steps["sections"]]}


@case("the CILA comes out as the hand walk found it, field for field (P6's own entries)")
def _():
    diffs, _ = gen.check(as_p6_ran(gen.generate(p6_recipe())), gen.load_yaml(HAND_WALK))
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
        rehearsal_plan(steps, v)  # stops on a missing value
        for sec in run.expand(steps, v)["sections"]:  # a "+" list's blocks, as many as the case has
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
    hand, ours = filled(gen.load_yaml(HAND_WALK), v), filled(as_p6_ran(gen.generate(gen.load_yaml(CILA / "recipe.yaml"))), v)
    for sec, vals in hand.items():
        assert ours.get(sec) == vals, (sec, vals, ours.get(sec))


@case("the fine lavori, never walked, comes out whole from the shared sections")
def _():
    steps = gen.generate(gen.load_yaml(FINE / "recipe.yaml"))
    names = [s["section"] for s in steps["sections"]]
    assert "ubicazione dell'immobile" in names and "comunicazione di fine lavori" in names, names
    import run
    first = lambda st: next(s for s in st["sections"] if s["section"] == "Gestione degli allegati")["fields"]
    slots = first(run.phase(steps))
    # Works finished in part add the planimetria's own slot (read on a partial draft, 2026-11-03).
    assert [f["label"][:20] for f in slots] == ["Fotocopia di un docu", "Copia dei documenti ", "Dichiarazione di ass", "Copia di elaborato p"], slots
    # What the portal makes once the declarations are ticked, the diritti receipt and Napoli's annexes
    # (under Allegati liberi, each when its pratica takes it: the fine lavori takes neither): the second run's.
    second = first(run.phase(steps, after=True))
    assert [f["label"][:20] for f in second] == ["Procura speciale", "Allegati liberi", "Allegati liberi", "Quadro riepilogativo",
                                                 "copia attestazione v"], second
    assert [f["when"] for f in second if f["label"] == "Allegati liberi"] == ["{{ask.napoli_allegato_a}}", "{{ask.modello_dp}}"]
    assert steps["asks"]["napoli_allegato_a"]["default"] == steps["asks"]["modello_dp"]["default"] == "false"


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
        assert 'querySelectorAll(\'iframe[data-pv="runner"]' in loop, "the batch leaves the run's frame over the portal"
        queue = (t / "out" / "queue-0.js").read_text()
        check = (t / "out" / "check.js").read_text()
        # Each steps file by name; one that differs from main's in some sections by its patch first,
        # the whole file named as what the patch asks for when it can't apply.
        # A case's "+" blocks give its steps a key of their own (steps/<name>-<hash>.js), from steps
        # rerun.py expanded too (2026-11-05: two CILA cases shared one and the second ran the first's).
        js = {n: next(p.stem for p in (t / "out" / "steps").glob(f"{n}*.js") if not p.stem.endswith(".patch")) for n in names}
        assert all(js[n] != n for n in names), js
        assert all(f'"steps/{js[n]}.js"' in check or f'"steps/{js[n]}.patch.js (it says if steps/{js[n]}.js is needed instead)"' in check
                   for n in names) and '"runner.js"' in check
        assert all((t / "out" / "steps" / f"{js[n]}.patch.js").exists() == (f"{js[n]}.patch.js" in check) for n in names)
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
        import re
        assert re.search(r'\["dau-fittizia","napoli/comune/dichiarazione-avvenuto-utilizzo-terre#[0-9a-f]{8}",\{"base":\{"wizard":\["PROVA NON INVIARE - DAU P6 generato"', raw), raw[:200]
        assert (t / "out" / "steps" / f"{js['dau-fittizia']}.js").read_text().startswith('localStorage.setItem("pv-steps:napoli/comune/dichiarazione-avvenuto-utilizzo-terre#')
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
        labels = r["operation"] if isinstance(r["operation"], list) else [r["operation"]]
        # A combination's own wizard, where its crawl read it, can leave out a scelta one operation
        # offers alone (the landscape proroga's assent, filed with a title: 2026-11-04).
        crawl = json.loads((HERE.parent / "catalogue" / "F839" / "sections" / f"{r['crawl']}.json").read_text())
        offered = {o["label"] for x in crawl.get("screens") or [] if gen.norm(x.get("screen")) == "scelte eventuali" for o in x["options"]}
        for label in labels:
            op = next(o for o in wizard["operations"] if o["label"] == label)
            for sc in op.get("scelte", []):
                if len(labels) > 1 and offered and sc["option"] not in offered:
                    continue
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
    assert catalogue.digest(catalogue.stored_fingerprints("sue-comunicazione-di-inizio-lavori-per-opere-temporanee")) == "041974574c75"
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
    recipe["crawl"] = "sue-comunicazione-inizio-lavoro-asseverata"  # a crawl of the CILA alone is not of both
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


@case("docs/portal-defects.md is drawn from defects.yaml, the one defect record, whose `page` stays out of steps files")
def _():
    import defects
    assert (ROOT / "docs" / "portal-defects.md").read_text() == defects.render(), "defects.py --write"
    carried = 0
    for f in sorted((ROOT / "rehearsals").glob("*/portal-steps.generated.yaml")):
        for c in yaml.safe_load(f.read_text()).get("supports", []):
            if isinstance(c.get("defect"), dict):
                carried += 1
                assert "page" not in c["defect"] and c["defect"]["title"], (f, c["defect"]["id"])
    assert carried, "no steps file carries a defect"


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


@case("every SUE pratica's attachments screen names each slot its crawl read, or leaves it to the person")
def _():
    # A fresh crawl marks no slot required (the portal flags one only once it has checked the
    # screen), so gen.py's "required slot in no entry" can't see one nobody named: the standalone
    # ordinaria's relazione paesaggistica was found by a run that stopped on it (2026-11-03).
    import json
    starts = lambda title, labels: any(gen.norm(title).startswith(gen.norm(l)) for l in labels)
    for d in sorted(REH.iterdir()):
        f = d / "portal-steps.generated.yaml"
        if not f.is_file() or gen.resolved(gen.load_yaml(d / "recipe.yaml")).get("sportello") != "sue":
            continue
        steps = gen.load_yaml(f)
        crawl = steps["generated"].split()[2]
        slots = json.loads((ROOT / "claude/skills/pratica/portal/catalogue/F839/sections" / f"{crawl}.json").read_text())["slots"]
        screen = next(s for s in steps["sections"] if s["section"] == "Gestione degli allegati")
        named = [x["label"] for x in screen["fields"]] + screen.get("theirs", [])
        # Allegati liberi is optional everywhere; an ID copy for whoever doesn't sign digitally, here never.
        left = [s["title"][:70] for s in slots["Gestione degli allegati"] if not starts(s["title"], named)
                and not s["title"].startswith("Allegati liberi") and "solo per chi non firma" not in s["title"]]
        assert not left, (d.name, left)


@case("the SUE's diritti, from the Comune's 2026 table: proposed by the case's facts, asked where the table needs what no ask holds")
def _():
    import json
    import run
    fields = dict(json.loads((CILA / "fixture-p6.json").read_text())["fields"])

    def diritti(name, **answers):
        steps = generated(name)
        a = steps["asks"]["diritti_euro"]
        return run.Values(answers, fields=fields, asks=steps["asks"]).render(a.get("default") or a["propose"])
    assert diritti("cila-fittizia", cila_stato="da iniziare") == "151"  # SUE 13
    assert diritti("cila-fittizia", cila_stato="in corso") == diritti("cila-fittizia", cila_stato="realizzato") == "166"  # SUE 15
    assert diritti("scia-fittizia", scia_onerosa="false") == "401" and diritti("scia-fittizia", scia_onerosa="true") == ""
    assert diritti("scia-alternativa-fittizia", scia_onerosa="false") == "401"  # SUE 10
    assert diritti("scia-alternativa-fittizia", scia_onerosa="true") == ""  # SUE 7-9: the contributo's bracket
    assert diritti("pdc-fittizio", pdc_tipo="nuova costruzione", scia_onerosa="false") == "401"
    assert diritti("pdc-fittizio", pdc_tipo="variante essenziale", scia_onerosa="true") == "501"  # SUE 11
    assert diritti("pdc-fittizio", pdc_tipo="parcheggi", scia_onerosa="false") == ""  # SUE 4-6: the floor area
    assert diritti("scia-sanatoria-fittizia", sanatoria_caso="doppia conformita") == "441"  # SUE 16
    assert diritti("scia-sanatoria-fittizia", sanatoria_caso="in corso") == ""  # art. 37 c. 5: not in the table
    assert diritti("proroga-inizio-fittizia", titolo_tipo="permesso di costruire") == "501"
    assert diritti("proroga-fine-fittizia", titolo_tipo="SCIA") == ""
    for name, want in (("pdc-sanatoria-fittizio", "441"), ("agibilita-fittizia", "401"), ("paesaggistica-ordinaria-fittizia", "401"),
                       ("accertamento-paesaggistico-fittizio", "441"), ("voltura-pdc-fittizia", "501"), ("cil-fittizia", "100"),
                       ("inizio-lavori-fittizia", "0"), ("nomina-impresa-fittizia", "0")):
        assert diritti(name) == want, (name, diritti(name))


@case("a slot that takes only signed files takes the person's signed file, never a plain copy, and a rehearsal leaves it (SCIA stato legittimo)")
def _():
    import run
    s = section(generated("scia-fittizia"), "Gestione degli allegati")
    f = field(s, "Documentazione dimostrativa dello stato legittimo")
    # Its `accepts` lets pre-flight refuse a plain copy; the portal checks the signature on upload.
    assert run.signed_only(f) and not f.get("after_declarations") and f["label"] not in s.get("theirs", []), f
    assert not any(x["label"] == f["label"] for x in run.phase({"sections": [s]}, made_up=True)["sections"][0]["fields"])
    # The portal's procura waits for the declarations; its empty slot is the person's until then.
    assert field(s, "Procura speciale")["after_declarations"] and "Procura speciale" in s["theirs"]


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
        plan = rehearsal_plan(steps, v)
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
    crawl = gen.json.loads((HERE.parent / "catalogue/F839/sections/suap-011-aprire-l-attivita-di-acconciatore-procura.json").read_text())
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
    fine = gen.json.loads((base / "catalogue/F839/sections/sue-comunicazione-di-fine-lavori.json").read_text())
    for s in fine["sections"]:
        if s.get("fields") is not None:
            for k in [k for k in s if k != "section"]:
                del s[k]
            s["same_as"] = f"sue-comunicazione-di-fine-lavori#{s['section']}"
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
            {"pratiche": {"sue-comunicazione-di-fine-lavori": {"checked": "2026-10-28", "differences": ["changed: Dati catastali"]}}}))
        try:
            gen.generate(gen.load_yaml(FINE / "recipe.yaml"), base=base)
            raise AssertionError("generated")
        except gen.GenError as e:
            assert "changed: Dati catastali" in str(e), e
        import rules
        old = rules.DRIFT
        rules.DRIFT = base / "catalogue/F839/drift.json"
        try:
            import run
            steps = gen.load_yaml(FINE / "portal-steps.generated.yaml")
            assert "Dati catastali" in run.portal_changed(steps)[0]
            assert run.portal_changed(gen.load_yaml(HAND_WALK)) == []  # hand-written
        finally:
            rules.DRIFT = old


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
            fps = catalogue.stored_fingerprints("sue-comunicazione-di-fine-lavori")
            check = lambda name, change: {"name": name, "like": "sue-comunicazione-di-fine-lavori", "crawled": "2026-10-28T00:00:00Z", "sections":
                [{"section": k, "fingerprint": ("0" * 16 if k == change else v)} for k, v in fps.items()]}
            export = base / "export.json"
            export.write_text(gen.json.dumps({"crawl:check:suap-001-x": check("suap-001-x", None),
                                              "crawl:check:suap-002-x": check("suap-002-x", "Oggetto della pratica")}))
            out = catalogue.cmd_drift(type("a", (), {"export": str(export)}))
            same = gen.json.loads(catalogue.SAME.read_text())
            assert same["same"] == {"suap-001-x": "sue-comunicazione-di-fine-lavori"}, out
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
            rehearsal_plan(steps, v)
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
    crawl = gen.json.loads((HERE.parent / "catalogue" / "F839" / "sections" / "sue-segnalazione-certificata-di-inizio-attivita-edilizia.json").read_text())
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
    plan = rehearsal_plan(steps, run.Values(m, fields=fields, asks=steps.get("asks")))
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
        labels = [p["label"] or "" for p in rehearsal_plan(steps, v)]
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
    plan = [(p["label"] or "", str(p.get("value") or "")) for p in rehearsal_plan(steps, v)]
    assert ("Cognome", "ESEMPIO") in plan and ("Tipologia di atto", "Deroga ai requisiti igienico-sanitari dei locali (inventata)") in plan
    assert [x for l, x in plan if l == "Autorità competente"] == ["ASL Napoli 1 Centro", "Comune di Napoli"], plan
    for name in ("cila-fittizia", "scia-fittizia"):
        steps, v, r = check(name, "answers-altri-tecnici.json")
        assert r["ready"], (name, r)
        labels = [p["label"] for p in rehearsal_plan(steps, v)]
        assert "Incaricato della" in labels and "Iscritto all'ordine/collegio" in labels, name
        assert not any((l or "").startswith("che gli altri tecnici incaricati saranno") for l in labels), name
    # As many as the case has (the national form sets no limit): ten technicians, three filings
    # and three assents, each past the page's first by "+".
    for name in ("cila-fittizia", "scia-fittizia"):
        steps, v, r = check(name, "answers-elenchi-lunghi.json")
        assert r["ready"] and not r["unsupported"], (name, r)
        plan = rehearsal_plan(steps, v)
        tecnici = [p for p in plan if "Altri tecnici" in p["section"]]
        assert sum(p["kind"] == "add" for p in tecnici) == 9 and ("Cognome", "VENTO") in [(p["label"], p["value"]) for p in tecnici], name
    rel = [(p["kind"], p["label"] or "", p["value"]) for p in rehearsal_plan(*check("cila-fittizia", "answers-elenchi-lunghi.json")[:2])
           if p["section"].startswith("Relazione Tecnica")]
    c, t = "Comunicazioni, segnalazioni", "Tipologia di atto"
    assert [l or "+" for k, l, _ in rel if k == "add" or l.startswith((c, t))] == [c, c, "+", c, t, t, "+", t], rel
    # The count first: proposed as one, the second technician's questions wait on a change to it.
    steps, v, r = check("cila-fittizia", "answers-altri-tecnici.json", altri_tecnici_quanti=None)
    assert [p["proposal"] for p in r["proposals"] if p["key"] == "altri_tecnici_quanti"] == ["1"], r
    assert "altro_tecnico2_incarico" not in {q["key"] for q in r["questions"]}, r["questions"]
    assert "altro_tecnico2_incarico" in r["if_changed"]["altri_tecnici_quanti"], r.get("if_changed")


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
        planned = [p for p in rehearsal_plan(steps, v) if "Altri tecnici" in p["section"]]
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
        return r, ([(p["label"] or "", str(p.get("value") or "")) for p in rehearsal_plan(steps, v)] if r["ready"] else [])
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
    assert any("deroga ad almeno un limite" in u for u in r["unsupported"]), r
    for answers, radio in (("answers-variante-scia-alt.json", "segnalazione certificata/denuncia"), ("answers-variante-titolo-unico.json", "titolo unico"),
                           ("answers-variante-sagoma.json", "permesso di costruire")):
        r, p = plan("pdc-fittizio", answers)
        assert r["ready"] and has(p, "variazione essenziale e/o sostanziale") and has(p, radio) and ("n.", "4321") in p, (answers, p)
    r, p = plan("pdc-fittizio", "answers-p6.json", pdc_tipo="piano casa")
    assert any("30 settembre 2022" in u for u in r["unsupported"]), r
    # The sanatoria's quadro a) is art. 36's own radio, not art. 10's.
    r, p = plan("pdc-sanatoria-fittizio", "answers-p6.json")
    assert r["ready"] and has(p, "intervento realizzato, ai sensi dell'articolo 36") and not has(p, "interventi di cui all'articolo 10"), p
    r, _ = plan("pdc-sanatoria-fittizio", "answers-p6.json", pdc_procedura="deroga")
    assert any("si richiede come tale" in u for u in r["unsupported"]), r
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
    # The permesso's prospetto box adds no slot (read 2026-11-01; the prospetto goes under Allegati
    # liberi): without that read, and without that file, it is listed.
    unread = copy.deepcopy(steps)
    for s in unread["sections"]:
        for f in s["fields"]:
            if f.get("label", "").startswith("allega il prospetto di calcolo"):
                f.pop("slot")
        s["fields"] = [f for f in s["fields"] if f.get("describe", "") != "Prospetto di calcolo preventivo del contributo di costruzione"]
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
    p = rehearsal_plan(steps, run.Values(json.loads((REH / name / "answers-paesaggistica.json").read_text()), fields=fields, asks=steps.get("asks")))
    got = [(x["label"], str(x.get("value") or "")) for x in p if x["section"].startswith("Riferimenti titolo")]
    assert ("e autorizzazione paesaggistica", "") in got and ("prot.n.", "PG/2025/0777777") in got and ("del", "10/12/2025") in got, got
    sec = section(steps, "Riferimenti titolo")
    assert [f.get("nth") for f in sec["fields"] if f.get("value") == "{{ask.paes_data|date_it}}" and "titolo_con_paesaggistica" in f["when"]] == [2, 2]
    p = rehearsal_plan(steps, run.Values(json.loads((REH / name / "answers-p6.json").read_text()), fields=fields, asks=steps.get("asks")))
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
            (Path(t) / "pdc-fittizio" / "README.md").write_text("# PdC\n\n## Runs\n\nProse stays.\n")
            done = [{"name": "pdc-fittizio/answers-deroga", "result": "filled", "total_seconds": 142.4},
                    {"name": "pdc-fittizio", "result": "stopped"}]
            rerun.record(done, "answers-p6.json", "2026-10-31")
            rerun.record(done, "answers-p6.json", "2026-10-31")
            runs = json.loads((Path(t) / "pdc-fittizio" / "runs.json").read_text())
            readme = (Path(t) / "pdc-fittizio" / "README.md").read_text()
        finally:
            rerun.REHEARSALS = before
    assert [(r["answers"], r["result"]) for r in runs] == [("answers-deroga.json", "filled"), ("answers-p6.json", "stopped")], runs
    assert "| 2026-10-31 | pane | `answers-deroga.json` | **filled** in 142 s |\n" in readme, readme
    assert readme.count("| 2026-10-31 |") == 2 and readme.endswith("<!-- /runs -->\n\nProse stays.\n"), readme


@case("every README's run table is drawn from its runs.json, the one run record (runs.py --write)")
def _():
    import runs
    assert not runs.stale(), f"run tables out of date (runs.py --write): {runs.stale()}"
    for d in sorted(p for p in runs.REHEARSALS.iterdir() if p.is_dir()):
        readme = d / "README.md"
        text = readme.read_text() if readme.is_file() else ""
        # no dated row left outside the drawn table
        outside = text.split(runs.START)[0] + (text.split(runs.END, 1)[1] if runs.END in text else "")
        assert not re.search(r"^\|\s*20\d\d-\d\d", outside, re.M), d.name



@case("catalogue.py pane --bundle: one picked file installs and starts the crawl; export.js saves what the store couldn't keep")
def _():
    import hashlib
    import json
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        (t / "ops.json").write_text(json.dumps([{"name": "sue-comunicazione-inizio-lavoro-asseverata", "sector": "S", "path": "P"}]))
        subprocess.run([sys.executable, str(HERE.parent / "catalogue.py"), "pane", str(t / "out"), "--bundle",
                        str(t / "pv-prova.js"), "--ops", str(t / "ops.json"), "--fresh"], check=True, capture_output=True)
        text = (t / "pv-prova.js").read_text()
        assert hashlib.sha256(text.encode()).hexdigest() in (t / "out" / "pick.js").read_text()
        assert "window.__crawl.batch(opts)" in text and 'localStorage.removeItem(\"crawl:op:\" + o.name)' in text
        export = (t / "out" / "export.js").read_text()
        assert "__crawlUnsaved" in export and "crawl-batch-prova.json" in export
        assert "crawl:batch" in (t / "out" / "status.js").read_text()
        # start.js: the same batch with no pick, from the pane's stored crawler once its sha256 is
        # the repo's; small enough for one call, so it never carries the crawler itself (2026-11-05).
        start = (t / "out" / "start.js").read_text()
        for f in ("wizard.js", "crawl.js"):
            assert hashlib.sha256((HERE.parent / f).read_text().encode()).hexdigest() in start, f
        body = text[text.index("  const opts = "):text.rindex("})()")]
        assert body in start and len(start) < 30000 and "__wizard" not in start, len(start)
        assert start.index("stale") < start.index("window.__crawl.batch(opts)")
        assert "pvPrintNames" in (t / "out" / "print.js").read_text()


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
    # As the pane's JavaScript tool returns it: one JSON string, quotes and escapes in (2026-11-05).
    quoted = json.dumps(hashlib.sha256(body.encode()).hexdigest() + "\n" + body)
    ok = subprocess.run(cat + ["import", "-"], input=quoted + "\n", capture_output=True, text=True)
    assert ok.returncode == 0, ok.stderr
    bad = subprocess.run(cat + ["import", "-"], input=json.dumps("0" * 64 + "\n" + body), capture_output=True, text=True)
    assert bad.returncode and "sha256 differs" in bad.stderr, bad.stderr


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


@case("a combination states only what is its own: its operations, comune, sportello and rules main follow from its main pratica and parts")
def _():
    n = 0
    for f in sorted(REH.glob("*/recipe.yaml")):
        own = gen.load_yaml(f)
        if not own.get("extends"):
            continue
        # A combination of two rehearsed pratiche (a proroga with the landscape proroga, the
        # agibilità with the DAU, a title with the landscape proroga in place of the authorization
        # its main combination files) states its operations and rules main: they are not the
        # main's plus a part's (combo_answers takes its case from both).
        if any(not p.startswith("parts/") for p in own["extends"][1:]):
            continue
        n += 1
        assert not {"operation", "comune", "sportello"} & set(own) and "main" not in (own.get("rules") or {}), f.parent.name
        main, *parts = own["extends"]
        m = gen.resolved(gen.load_yaml(REH / main / "recipe.yaml"))
        r = gen.resolved(own)
        mops = m["operation"] if isinstance(m["operation"], list) else [m["operation"]]
        assert r["operation"] == mops + [gen.load_yaml(HERE.parent / f"{p}.yaml")["operation"] for p in parts], f.parent.name
        assert (r["comune"], r["sportello"]) == (m["comune"], m["sportello"]), f.parent.name
        assert r["rules"]["main"] == m["rules"].get("main", m["procedure"]), f.parent.name
        assert set(m["rules"].get("handles", [])) < set(r["rules"]["handles"]), f.parent.name
    assert n == 28, n


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
    import run
    steps = gen.generate(gen.load_yaml(ROOT / "rehearsals" / "scia-fittizia" / "recipe.yaml"))
    sec = section(steps, "i) Impresa esecutrice")
    cassa = next(f for f in sec["fields"] if f.get("label") == "Cassa edile" and f["block"] == 1)
    assert cassa["when"] == "{{ask.lavori_in_proprio|not}} {{ask.impresa_dopo|not}} {{f1:business.cassa_edile_codice_impresa|empty|not}}", cassa
    # A later firm's, after its count (the CILA case's third firm is enrolled with one).
    cila = gen.generate(gen.load_yaml(CILA / "recipe.yaml"))
    v = p6_values("cila-fittizia", "answers-imprese-tre.json")(cila)
    third = next(f for f in section(run.expand(cila, v), "h) Impresa esecutrice")["fields"]
                 if f.get("label") == "Cassa edile" and f["block"] == 3)
    assert third["when"].endswith("{{ask.imprese_quante|atleast_3}} {{f3:business.cassa_edile_codice_impresa|empty|not}}"), third
    assert run.truthy(v.render(third["when"])), third


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
    crawl = json.loads((HERE.parent / "catalogue" / "F839" / "sections" / "sue-segnalazione-certificata-di-inizio-attivita-edilizia.json").read_text())
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
        return [p["label"] for p in rehearsal_plan(steps, v) if p["kind"] == "file"]
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
        assert r["ready"] and any("del progettista architettonico" in y for y in r["yours"]) == signs, (answers, r["yours"])
        plan = [(p["section"], p["label"], p["value"]) for p in rehearsal_plan(steps, v)]
        assert (("Asseverazione SCIA - Tipologia di intervento", "Cognome", "Disegno") in plan) == signs, answers



@case("every two of a combination's operations are a pair the SUE's wizard took together (sue-wizard.json `pairs`), and every pair is recorded")
def _():
    import json
    import catalogue
    w = json.loads((catalogue.CAT / "sue-wizard.json").read_text())
    key = {o["label"]: o["key"] for o in w["operations"]}
    order = [o["key"] for o in w["operations"]]  # a pair's keys in the wizard's order, as sue_pairs()
    pairs = {tuple(p["keys"]): p for p in w["pairs"]}
    assert set(pairs) == {(a["key"], b["key"]) for a, b in catalogue.sue_pairs()[1]}, "probe the missing pairs (catalogue.py pairs)"
    for d in sorted(ROOT.glob("rehearsals/*/recipe.yaml")):
        r = gen.resolved(gen.load_yaml(d))
        if r.get("sportello") != "sue" or not isinstance(r.get("operation"), list):
            continue
        ks = sorted((key[o] for o in r["operation"]), key=order.index)
        # Three operations (a title, its landscape authorization, the dichiarazione): each two of them.
        for i, a in enumerate(ks):
            for b in ks[i + 1:]:
                p = pairs.get((a, b))
                assert p and p["together"] and p.get("accepted"), (d.parent.name, a, b, p)


@case("two operations in one pratica: the adempimenti are both's, every section one of theirs, a location, land register, diritti or bollo section kept once (sue-wizard.json `pairs`, probed 2026-11-03)")
def _():
    import json
    import catalogue
    w = json.loads((catalogue.CAT / "sue-wizard.json").read_text())
    S, ops = w["sections"], {o["key"]: o for o in w["operations"]}
    dup = re.compile(r"(?i)ubicazione|localizzazione|sede dell|dati catastali|diritti di segreteria|imposta di bollo|tipologia lavori")
    for p in w["pairs"]:
        if not p.get("accepted"):
            continue
        a, b = (ops[k] for k in p["keys"])
        union = {S[i] for i in a["sections"]} | {S[i] for i in b["sections"]}
        got = {S[i] for i in p["sections"]}
        assert got <= union, (p["keys"], got - union)
        assert all(dup.search(x) for x in union - got), (p["keys"], union - got)
        ad = lambda o: {(x["adempimento"], x["amministrazione"]) for x in o["adempimenti"]}
        assert ad(p) == ad(a) | ad(b), p["keys"]


@case("every steps file is the one steps.lock names, and every combination's answers as the dictionary, recipes and crawls write them now (regen.py --check)")
def _():
    import regen
    changed, refused = regen.regenerate(check=True)
    assert not refused, refused
    assert not changed, "regenerate (bench/regen.py), then commit steps.lock: " + ", ".join(changed)
    # Built, never committed: one hash per recipe, and nothing of them in git.
    import subprocess
    lock = gen.read_lock()
    assert set(lock) == {p.parent.name for p in (ROOT / "rehearsals").glob("*/recipe.yaml")}, "steps.lock: one line per recipe"
    tracked = subprocess.run(["git", "ls-files", "rehearsals/*/" + gen.STEPS], cwd=ROOT, capture_output=True, text=True).stdout
    assert not tracked.strip(), "generated steps files are committed: " + tracked


@case("gen.ensure builds a missing steps file and one the lock doesn't name, and leaves one it names")
def _():
    import shutil
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        for name in ("cila-fittizia", "fine-lavori-fittizia"):
            shutil.copytree(ROOT / "rehearsals" / name, root / name, ignore=shutil.ignore_patterns(gen.STEPS))
        shutil.copy(gen.LOCK, root / gen.LOCK.name)
        assert sorted(p.parent.name for p in gen.ensure(root=root)) == ["cila-fittizia", "fine-lavori-fittizia"]
        assert gen.ensure(root=root) == []
        for name in ("cila-fittizia", "fine-lavori-fittizia"):
            assert gen.sha256((root / name / gen.STEPS).read_text()) == gen.read_lock()[name], name
        (root / "fine-lavori-fittizia" / gen.STEPS).write_text("stale\n")
        assert [p.parent.name for p in gen.ensure(root=root)] == ["fine-lavori-fittizia"]


def _all(x, key):
    """Every value of `key` anywhere in x."""
    if isinstance(x, dict):
        return [v for k, v in x.items() if k == key] + [w for v in x.values() for w in _all(v, key)]
    if isinstance(x, list):
        return [w for v in x for w in _all(v, key)]
    return []


@case("what the tecnico reads is Italian: every title, question, checklist item, refusal and end step, no role codes")
def _():
    english = re.compile(r"\b(the|which|what|does|will|have|with|your|their|tick|every|must|before|after|only|of|and|"
                         r"new|other|another|number|time|systems|how|many|something|lifts|protection|beer)\b", re.I)
    bad = []
    for d in sorted(p for p in REH.iterdir() if (p / "recipe.yaml").exists()):
        steps = generated(d.name)
        texts = [a.get(k) for a in steps.get("asks", {}).values() for k in ("question", "item", "how", "why")]
        texts += [v for a in steps.get("asks", {}).values() for v in (a.get("labels") or {}).values()]
        texts += [g.get("question") for g in steps.get("groups", {}).values()]
        texts += [c.get("else") for c in steps.get("supports", [])] + list(steps.get("yours", []))
        texts.append(steps.get("title"))  # the catalog's and the closing line's name (2026-11-07: "… of a CILA")
        # every refusal, a field's own included (2026-11-06: the tolerances' one was in English)
        texts += [x for x in _all(steps, "else") if isinstance(x, str)]
        for t in filter(None, texts):
            plain = re.sub(r"\{\{.*?\}\}|\"[^\"]*\"", "", str(t))  # templates and the portal's own quoted words
            if english.search(plain) or "`" in plain:
                bad.append((d.name, str(t)[:90]))
    assert not bad, f"{len(bad)} English or coded texts, e.g. {bad[:3]}"


# What the tecnico reads, short and with no software word: a path, a file type, a library id
# (napoli/comune/...), or the words of how Portali is built.
SOFTWARE = re.compile(r"docs/|rehearsals/|catalogue/|schema/|\b(napoli|italia)/[a-z]|\.(md|json|ya?ml|js)\b|"
                      r"\b(slug|recipe|steps file|json|pre-?flight|sha256|runner|script|crawl|mappat[oa]|gestit[oa])\b",
                      re.I)
# Caps in characters, one idea a sentence: the refusal a recipe gives, an end step, a defect's lines.
CAPS = {"else": 300, "yours": 350, "title": 120, "what": 200, "works": 200, "law": 200, "checked": 200, "choice": 140}


@case("what the tecnico reads is short and plain: refusals, end steps and defects within their caps, no software words; "
      "a refusal behind a defect names the case, the portal's flaw and 1-3 choices")
def _():
    bad = []

    def check(where, kind, t, cap=None):
        t = re.sub(r"\{\{.*?\}\}", "", str(t))
        if SOFTWARE.search(t):
            bad.append(f"{where}: {kind} says {SOFTWARE.search(t).group(0)!r}: {t[:80]}")
        if cap and len(t) > cap:
            bad.append(f"{where}: {kind} is {len(t)} characters (at most {cap}): {t[:80]}")
    for d in sorted(p for p in REH.iterdir() if (p / "recipe.yaml").exists()):
        steps = generated(d.name)
        for a in steps.get("asks", {}).values():
            for k in ("question", "item", "how", "why", "yours"):
                if a.get(k):
                    check(d.name, k, a[k])
        for c in steps.get("supports", []):
            if c.get("else"):
                check(d.name, "else", c["else"], CAPS["else"])
        for y in steps.get("yours", []):
            check(d.name, "yours", y, CAPS["yours"])
    for y in run.FILING[("F839", "E")]["yours"] + run.FILING[("F839", "E")]["titles"]["yours"]:
        check("run.FILING", "yours", y, CAPS["yours"])
    for id_, d in yaml.safe_load((HERE.parent / "defects.yaml").read_text()).items():
        for k in ("title", "what", "works", "law", "checked"):
            check(id_, k, d.get(k) or "", CAPS[k])
        if not 1 <= len(d.get("choices", [])) <= 3:
            bad.append(f"{id_}: {len(d.get('choices', []))} choices (one to three)")
        for c in d.get("choices", []):
            check(id_, "choice", c, CAPS["choice"])
        m = run.refusal_text({"unsupported": ["x"], "defects": [{**d, "id": id_, "else": "x"}]})
        if not (m.startswith(f"Non posso preparare: {d['title']}.") and "difetto del portale" in m and d["works"] in m):
            bad.append(f"{id_}: its refusal doesn't name the case, the portal's flaw and what still fills:\n{m}")
    assert not bad, f"{len(bad)} problems:\n" + "\n".join(bad[:12])


@case("a steps file's own defaults never name a draft PROVA NON INVIARE: real users run them; rehearsals answer it")
def _():
    # Built from each recipe, as regen.py builds them (the steps files aren't committed), and
    # the hand-written ones as they are.
    for d in sorted(p for p in REH.iterdir() if p.is_dir()):
        if (d / "recipe.yaml").exists():
            steps = generated(d.name)
        elif (d / "portal-steps.yaml").exists():
            steps = yaml.safe_load((d / "portal-steps.yaml").read_text())
        else:
            continue
        default = str(steps.get("asks", {}).get("descrizione", {}).get("default", ""))
        assert "PROVA" not in default, (d.name, default)


@case("every filter a template names is run.py's, in the dictionary, recipes, parts, steps files and main's steps files")
def _():
    # An unknown filter is a KeyError, which render() takes for a missing value: a renamed one
    # (one_catasto, 2026-11-04) made main's steps refuse every case quietly, so plan_diff showed
    # 252 changed plans and patch.js none. Old names stay in run.py while a steps file names them.
    import subprocess
    import run
    filters = lambda text: {f for t in re.findall(r"\{\{(.+?)\}\}", text) for f in [p.strip() for p in t.split("|")[1:]]}
    texts = {str(p.relative_to(ROOT)): p.read_text() for p in [HERE.parent / "dictionary" / "fnsuap.yaml",
             *(HERE.parent / "parts").glob("*.yaml"), *REH.glob("*/recipe.yaml"), *REH.glob("*/portal-steps*.yaml")]}
    listed = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", "HEAD", "rehearsals"],
                            capture_output=True, text=True).stdout.split()
    for name in [n for n in listed if re.search(r"/portal-steps[^/]*\.yaml$", n)]:
        texts["HEAD:" + name] = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{name}"], capture_output=True, text=True).stdout
    unknown = {}
    for where, text in texts.items():
        for f in filters(text):
            try:
                run.FILTERS[f]
            except KeyError:
                unknown.setdefault(f, where)
    assert not unknown, unknown


@case("two pratiche rehearsed alone, filed together: the main's answers, the other's fill what they don't say, the people of both (a proroga with the landscape proroga)")
def _():
    a = gen.combo_answers({"extends": ["proroga-inizio-fittizia", "proroga-paesaggistica-fittizia"],
                           "answers": {"descrizione": "combinazione"}})
    main = json.loads((gen.REHEARSALS / "proroga-inizio-fittizia" / "answers-p6.json").read_text())
    other = json.loads((gen.REHEARSALS / "proroga-paesaggistica-fittizia" / "answers-p6.json").read_text())
    assert a["descrizione"] == "combinazione"
    assert a["pdc_data"] == main["pdc_data"], "a key both say is the main's"
    assert a["paes_protocollo"] == other["paes_protocollo"], "the other's own section's answer"
    assert a["people"] == {**other["people"], **main["people"]}, a["people"]
    assert gen.combo_answers({"extends": ["cila-fittizia"]}) is None, "one rehearsal and no answers: nothing to write"


@case("rules with no table (a combination no table routes yet): main and handles only, nothing asked")
def _():
    asks, groups = {}, {}
    assert gen.rules_block({"main": "napoli/comune/fine-lavori", "handles": ["napoli/comune/dichiarazione-avvenuto-utilizzo-terre"]},
                           asks, groups) == {"main": "napoli/comune/fine-lavori", "handles": ["napoli/comune/dichiarazione-avvenuto-utilizzo-terre"]}
    assert not asks and not groups
    for bad in ({"handles": ["x"]}, {"main": "x", "facts": {"sanatoria": "false"}}):
        try:
            gen.rules_block(bad, {}, {})
        except gen.GenError:
            continue
        raise AssertionError(f"accepted {bad}")


@case("every SUE steps file opens with the Scheda anagrafica and has its payment and attachments screens (2026-11-04: twenty combinations lost both)")
def _():
    # A recipe built on another that inherits `first` and `after` copied them as null, which drops
    # the screens: their runs "filled" without ever reaching Allega documenti.
    bad = []
    for f in sorted(REH.glob("*/portal-steps.generated.yaml")):
        if yaml.safe_load((f.parent / "recipe.yaml").read_text()).get("sportello") != "sue":
            continue
        names = [s["section"] for s in yaml.safe_load(f.read_text())["sections"]]
        if not names or names[0] != "Scheda anagrafica" or not {"Pagamento degli oneri", "Gestione degli allegati"} <= set(names):
            bad.append(f"{f.parent.name}: {names[:1]}")
    assert not bad, bad


@case("every \"+\" a SUE crawl saw is a list the dictionary maps (`each`, `firms`) or says why not (`plus:`)")
def _():
    # The co-holders' "+" was in the 2026-10-31 crawl (`plus`) and nobody read it: a portal defect
    # was written for it, until a draft showed the "+" (2026-11-05).
    import json
    d = gen.load_yaml(HERE.parent / "dictionary" / "fnsuap.yaml")

    def plus(node):
        if isinstance(node, dict):
            return "plus" in node or any(plus(v) for v in node.values())
        return isinstance(node, list) and any(plus(v) for v in node)

    def lists(e):
        return "firms" in e or "plus" in e or '"kind": "each"' in json.dumps(e.get("fields", []))
    bad = set()
    for f in sorted((HERE.parent / "catalogue" / "F839" / "sections").glob("*.json")):
        if f.stem.startswith("suap") or f.stem == "acconciatore":
            continue
        for s in json.loads(f.read_text())["sections"]:
            if s.get("same_as") or not plus(s):
                continue
            entries = gen.dictionary_entries(d["sections"], s["section"])
            if entries and not any(lists(e) for e, _ in entries):
                bad.add(f"{s['section']} ({f.stem})")
    assert not bad, sorted(bad)


print(f"{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
