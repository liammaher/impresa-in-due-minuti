#!/usr/bin/env python3
"""Construction tolerances (art. 34-bis / 34-ter DPR 380/2001) in the technician's asseverazione,
offline: the SCIA's, the SCIA alternativa's and the permesso's stato legittimo page asks "Sono
previste tolleranze?" and opens the CILA's block on a yes. gen.py on the crawls, then run.py's
pre-flight and plan with each rehearsal's answers-tolleranze* case. No browser, vault or network.

  ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/test_tolleranze.py
"""

import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
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
    return run.preflight(steps, values(steps, a))


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


@case("refused: a structurally relevant tolerance (what its art. 94-bis class opens isn't crawled), the CILA's too")
def _():
    for recipe in CASES:
        r = preflight(recipe, answers(recipe, toll_strutturale=True))
        assert any("structurally relevant tolerance" in u for u in r["unsupported"]), (recipe, r["unsupported"])
    r = preflight("cila-fittizia", answers("cila-fittizia", "answers-proprietario.json", toll_strutturale=True))
    assert any("structurally relevant tolerance" in u for u in r["unsupported"]), r["unsupported"]


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
                         or f.get("label", "").startswith(("trattandosi", "non ha rilevanza"))]
                assert block and all("id" not in f for f in block), (recipe, [f for f in block if "id" in f])


print(f"\n{sum(results)} of {len(results)} passed")
sys.exit(0 if all(results) else 1)
