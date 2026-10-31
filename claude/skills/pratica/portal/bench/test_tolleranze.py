#!/usr/bin/env python3
"""Construction tolerances (art. 34-bis / 34-ter DPR 380/2001) in the technician's asseverazione,
offline: the SCIA's, the SCIA alternativa's and the permesso's stato legittimo page asks "Sono
previste tolleranze?" and opens the CILA's block on a yes. gen.py on the crawls, then run.py's
pre-flight and plan with each rehearsal's answers-tolleranze* case. No browser, vault or network.

  ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/test_tolleranze.py
"""

import json
import os
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
os.chdir(ROOT)  # the answers name files from the repo's root, wherever this runs from
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True
import gen  # noqa: E402
import run  # noqa: E402

REHEARSALS = ROOT / "rehearsals"
FIELDS = dict(json.loads((REHEARSALS / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])
CASES = {"scia-fittizia": "answers-tolleranze-asseverate.json", "scia-alternativa-fittizia": "answers-tolleranze.json",
         "pdc-fittizio": "answers-tolleranze.json"}
STEPS = {r: gen.generate(yaml.safe_load((REHEARSALS / r / "recipe.yaml").read_text()))
         for r in (*CASES, "cila-fittizia")}
results = []


def case(name):
    def run_(fn):
        try:
            fn()
            results.append(True)
            print(f"ok    {name}")
        except Exception as e:  # noqa: BLE001
            results.append(False)
            print(f"FAIL  {name}: {e}")
    return run_


def answers(recipe, name=None, **change):
    a = json.loads((REHEARSALS / recipe / (name or CASES[recipe])).read_text())
    a.update(change)
    return {k: v for k, v in a.items() if v is not None}


def values(steps, a):
    return run.Values(dict(a), fields=dict(FIELDS), asks=steps.get("asks"))


def preflight(recipe, a):
    steps = STEPS[recipe]
    return run.preflight(steps, values(steps, a), made_up=True)


def labels(recipe, a):
    """The labels this case ticks on the asseverazione's stato legittimo page, after a pre-flight
    that must be ready (its questions' "si"/"no": the state, the tolerances and, but for the SCIA
    alternativa's, the sanatoria)."""
    r = preflight(recipe, a)
    assert r["ready"], {k: r[k] for k in ("unsupported", "questions", "proposals", "missing") if r[k]}
    steps = STEPS[recipe]
    return [gen.norm(p["label"] or "") for p in run.plan(steps, values(steps, a))
            if p["section"].lower().startswith("asseverazione") and "stato legittimo" in p["section"].lower()]


def sanatoria(recipe):
    """1 where the page has the sanatoria's question (answered no in these cases), else 0."""
    return 0 if recipe == "scia-alternativa-fittizia" else 1


def has(ls, start):
    return any(x.startswith(gen.norm(start)) for x in ls)


@case("declared tolerances: the yes, the box in the stato legittimo, each kind, the 6% band, zone 2")
def _():
    for recipe in CASES:
        ls = labels(recipe, answers(recipe))
        assert (ls.count("si"), ls.count("no")) == (2, sanatoria(recipe)), (recipe, ls)
        assert has(ls, "dalle tolleranze di cui all’articolo 34-bis"), (recipe, ls)
        assert has(ls, "TOLLERANZA DI CUI ALL’ART. 34-BIS, COMMI 1-BIS") and has(ls, "TOLLERANZA DI CUI ALL’ART. 34-BIS, COMMA 2:"), (recipe, ls)
        assert not has(ls, "TOLLERANZA DI CUI ALL’ART. 34-BIS, COMMA 1 E 1-TER") and not has(ls, "TOLLERANZA DI CUI ALL’ART. 34-TER"), (recipe, ls)
        assert has(ls, "6%, per le U.I.") and not has(ls, "5%, per le U.I."), (recipe, ls)
        assert has(ls, "trattandosi di immobile ubicato in zona sismica a media o alta"), (recipe, ls)
        assert has(ls, "non ha rilevanza strutturale"), (recipe, ls)


@case("no tolerances: the no, and nothing of the block")
def _():
    for recipe in CASES:
        ls = labels(recipe, answers(recipe, "answers-p6.json"))
        assert (ls.count("si"), ls.count("no")) == (1, 1 + sanatoria(recipe)), (recipe, ls)
        assert not any("tolleranz" in x for x in ls), (recipe, ls)


@case("unanswered, no tolerances is proposed, and the kinds hang on a yes")
def _():
    for recipe in CASES:
        r = preflight(recipe, answers(recipe, "answers-p6.json", tolleranze=None))
        assert [p["proposal"] for p in r["proposals"] if p["key"] == "tolleranze"] == ["false"], (recipe, r["proposals"])
        kinds = [q for q in r["questions"] if q["key"] == "tolleranze_tipi"]
        assert kinds and all(i.get("only_if") == ["tolleranze"] for i in kinds[0]["items"]), (recipe, kinds)


@case("structurally relevant: its art. 94-bis class, then the authorization, the silenzio assenso or the term run out")
def _():
    # One case per branch, over the SCIA, the CILA, the permesso and the SCIA alternativa.
    want = {("scia-fittizia", "answers-tolleranze-autorizzazione.json"):
                ["intervento rilevante", "allega lautorizzazione sismica", "rilasciata in data", "prot. n."],
            ("scia-fittizia", "answers-tolleranze-silenzio.json"):
                ["intervento rilevante", "attesta che sulla istanza", "in data", "prot. n."],
            ("cila-fittizia", "answers-tolleranze-minore.json"):
                ["intervento di minore rilevanza", "dichiara il decorso del termine"],
            ("pdc-fittizio", "answers-tolleranze-privo.json"):
                ["intervento privo di rilevanza", "dichiara il decorso del termine"],
            ("scia-alternativa-fittizia", "answers-tolleranze-minore.json"):
                ["intervento di minore rilevanza", "dichiara il decorso del termine"]}
    others = ["intervento rilevante", "intervento di minore", "intervento privo", "allega lautorizzazione",
              "attesta che sulla istanza", "dichiara il decorso"]
    for (recipe, name), labels_ in want.items():
        steps = STEPS.get(recipe) or gen.generate(yaml.safe_load((REHEARSALS / recipe / "recipe.yaml").read_text()))
        a = answers(recipe, name)
        r = run.preflight(steps, values(steps, a), made_up=True)
        assert r["ready"], (name, {k: r[k] for k in ("unsupported", "questions", "proposals", "missing") if r[k]})
        ls = [gen.norm(p["label"] or "") for p in run.plan(steps, values(steps, a))]
        assert has(ls, "ha rilevanza strutturale") and not has(ls, "non ha rilevanza strutturale"), (name, ls)
        for x in labels_:
            assert has(ls, x), (name, x)
        for x in others:
            assert has(ls, x) == any(gen.norm(x) == gen.norm(y) or gen.norm(y).startswith(gen.norm(x)) for y in labels_), (name, x)


@case("refused: a relevant one with neither authorization nor silenzio assenso, the others before the term runs out")
def _():
    for recipe in CASES:
        r = preflight(recipe, answers(recipe, toll_strutturale=True, toll_classe="rilevante", toll_sismica="nessuno"))
        assert any("seismic authorization" in u for u in r["unsupported"]), (recipe, r["unsupported"])
        for classe in ("minore rilevanza", "privo di rilevanza"):
            r = preflight(recipe, answers(recipe, toll_strutturale=True, toll_classe=classe, toll_decorso="false"))
            assert any("control term has run out" in u for u in r["unsupported"]), (recipe, classe, r["unsupported"])
    # Asked in order: the class only once structurally relevant, then its proof.
    r = preflight("scia-fittizia", answers("scia-fittizia", toll_strutturale=True))
    keys = {q["key"]: q.get("only_if") for q in r["questions"]}
    assert "toll_classe" in keys and "toll_sismica" in keys and keys["toll_sismica"] == ["toll_classe"], keys
    assert not preflight("scia-fittizia", answers("scia-fittizia"))["questions"]  # not structural: nothing asked


@case("refused: tolerances declared with no kind")
def _():
    for recipe in CASES:
        r = preflight(recipe, answers(recipe, tolleranze_tipi=[]))
        assert any("at least one kind" in u for u in r["unsupported"]), (recipe, r["unsupported"])


@case("the CILA's own tolerance case is still ready")
def _():
    r = preflight("cila-fittizia", answers("cila-fittizia", "answers-proprietario.json"))
    assert r["ready"], {k: r[k] for k in ("unsupported", "questions", "proposals", "missing") if r[k]}


@case("the block goes by label: its ids would be offsets of choices crawled apart")
def _():
    for recipe in CASES:
        for sec in STEPS[recipe]["sections"]:
            if sec["section"].lower().startswith("asseverazione") and "stato legittimo" in sec["section"].lower():
                block = [f for f in sec["fields"] if "{{ask.tolleranze}} {{ask.toll" in f.get("when", "")
                         or f.get("label", "").startswith(("trattandosi", "non ha rilevanza", "ha rilevanza"))]
                assert block and all("id" not in f for f in block), (recipe, [f for f in block if "id" in f])


print(f"\n{sum(results)} of {len(results)} passed")
sys.exit(0 if all(results) else 1)
