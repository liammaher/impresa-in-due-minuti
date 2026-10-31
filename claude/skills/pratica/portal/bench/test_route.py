#!/usr/bin/env python3
"""Offline tests of route.py: from a case's facts to the one steps file that files it.

  ~/.cache/pratica-portal/venv/bin/python -I claude/skills/pratica/portal/bench/test_route.py

No browser, vault or network. Walks every case the SUE rules table decides (each fact
asked as the table asks it), and checks each is routed to a steps file that agrees or
refused with a reason, that every rules-gated SUE rehearsal is reached, and that each
rehearsal's own cases come back to it. Prints the combinations the table decides that no
steps file files yet: what is left to map.
"""

import json
import shutil
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True  # no __pycache__ in the skill's folder
import route  # noqa: E402
import rules  # noqa: E402
import run  # noqa: E402

REHEARSALS = HERE.parents[4] / "rehearsals"
TABLE = "sue-napoli"
T = rules.table(TABLE)


def values_of(name):
    f = T["facts"][name]
    return [True, False] if f["type"] == "yes_no" else list(f["values"])


def leaves():
    """Every case the table decides, as the facts it asked on the way (first one first)."""
    out = []

    def walk(facts):
        d = rules.decide(T, facts)
        if d["ask"]:
            for v in values_of(d["ask"][0]):
                walk({**facts, d["ask"][0]: v})
        else:
            out.append((facts, d))
    walk({})
    return out


LEAVES = leaves()


def every_case_routed_or_refused():
    """Each decided case reaches the one steps file for its pratiche, which reads the case
    the same way (its fixed facts, its wizard), or is refused with the reason; the
    combinations no steps file files are the mapping still to do."""
    idx, unmapped, routed = route.index(TABLE, REHEARSALS), defaultdict(int), 0
    for facts, d in LEAVES:
        r = route.route(TABLE, facts, REHEARSALS)
        assert not r["questions"], (facts, r["questions"])
        if d["refused"] or d["none"]:
            assert not r["routed"] and r["unsupported"], (facts, r)
            continue
        k = route.key(d["main"]["procedure"], [a["procedure"] for a in d["also"]])
        if k not in idx:
            assert not r["routed"] and r["unsupported"][0].startswith("Not mapped yet"), (facts, r)
            unmapped[k] += 1
            continue
        assert r["routed"], (facts, r["unsupported"])
        assert r["pratica"] == idx[k][0]
        routed += 1
    print(f"  {len(LEAVES)} cases: {routed} routed, {sum(unmapped.values())} not mapped yet")
    for (main, also), n in sorted(unmapped.items(), key=lambda x: -x[1]):
        print(f"    to map: {main}" + (f" + {', '.join(also)}" if also else "") + f" ({n} cases)")


def every_recipe_reached():
    """Every SUE steps file with a `rules:` block is where some case goes, but one for a pratica
    the table never names (the parere di esonero, mapped and refused in Napoli)."""
    reached = {route.route(TABLE, facts, REHEARSALS)["pratica"] for facts, d in LEAVES if d["main"]}
    named = {r["then"]["procedure"] for r in T["rules"] if r["then"].get("role") == "main"}
    idx = route.index(TABLE, REHEARSALS)
    names = {n for (main, _), (n, _, _) in idx.items() if main in named}
    assert names <= reached, f"never routed to: {sorted(names - reached)}"
    assert len(idx) >= 14 and {n for n, _, _ in idx.values()} - names == {"parere-esonero-fittizio"}, sorted(idx)


def answers_carry_into_preflight():
    """The answers route.py hands on fit the steps file's own asks, and leave its rules
    waiting on nothing but what it says it asks again."""
    by_name = {n: s for n, _, s in route.index(TABLE, REHEARSALS).values()}
    for facts, d in LEAVES:
        if not d["main"] or d["refused"]:
            continue
        r = route.route(TABLE, facts, REHEARSALS)
        if not r["routed"]:
            continue
        steps = by_name[r["pratica"]]
        asks = steps["asks"]
        for k, v in r["answers"].items():
            assert k in asks and run.check_answer(asks[k], v) is None, (r["pratica"], k, v)
        _, waiting = run.ruled(steps, run.Values(r["answers"], fields={}, asks=asks))
        assert set(waiting) <= {x["fact"] for x in r["asked_again"]}, (r["pratica"], facts, waiting)
        for name in facts:  # a fact the person answered here is never asked there again
            tmpl = steps["rules"]["facts"][name]
            if tmpl == "{{ask.%s}}" % name:
                assert name in r["answers"], (r["pratica"], name)


def cila_reads_sanatoria_its_way():
    """The CILA reads `sanatoria` from cila_stato: one option fits "no", two fit "yes"."""
    base = {"intervento": "manutenzione_straordinaria", "cambio_uso": "no", "paesaggio": "no", "fatti": []}
    r = route.route(TABLE, base, REHEARSALS)
    assert r["pratica"] == "cila-fittizia" and r["answers"]["cila_stato"] == "da iniziare", r
    assert "sanatoria" not in r["answers"]
    r = route.route(TABLE, {**base, "fatti": ["sanatoria"]}, REHEARSALS)
    assert r["pratica"] == "cila-fittizia", r
    assert r["asked_again"] == [{"fact": "sanatoria", "ask": "cila_stato", "fits": ["in corso", "realizzato"]}], r


def rehearsal_cases_come_home():
    """Each rehearsal's answers files, read as its steps file reads the facts, route back to it
    (a case its own rules refuse is left out: it tests the refusal)."""
    n = 0
    for name, path, steps in route.index(TABLE, REHEARSALS).values():
        for f in sorted(path.parent.glob("answers*.json")):
            a = json.loads(f.read_text())
            v = run.Values(a, fields={}, asks=steps["asks"])
            out, waiting = run.ruled(steps, v)
            if out or waiting:
                continue
            facts = {k: x for k, t in steps["rules"]["facts"].items() if (x := v.render(t)) is not None}
            r = route.route(TABLE, facts, REHEARSALS)
            assert r["pratica"] == name, (name, f.name, r["unsupported"] or r["questions"])
            n += 1
    assert n >= 30, n
    print(f"  {n} rehearsal cases routed back")


def asks_as_the_table_asks():
    """The first fact alone; then the rest at once, yes/no ones as one checklist, the seismic
    choice only under the structures; a wrong answer asked again with why."""
    r = route.route(TABLE, {}, REHEARSALS)
    assert [q["key"] for q in r["questions"]] == ["intervento"] and not r["routed"]
    r = route.route(TABLE, {"intervento": "manutenzione_straordinaria"}, REHEARSALS)
    qs = {q["key"]: q for q in r["questions"]}
    assert set(qs) == {"sismica", "cambio_uso", "paesaggio", "fatti"}, set(qs)
    assert qs["sismica"]["only_if"] == ["strutture"]
    assert "strutture" in [i["key"] for i in qs["fatti"]["items"]]
    assert qs["fatti"]["question"] == route.CHECKLIST
    r = route.route(TABLE, {"intervento": "rifare il bagno"}, REHEARSALS)
    assert [q["key"] for q in r["questions"]] == ["intervento"] and "error" in r["questions"][0]
    r = route.route(TABLE, {"intervento": "manutenzione_straordinaria", "fatti": "nessuna"}, REHEARSALS)
    assert "error" in {q["key"]: q for q in r["questions"]}["fatti"]
    # The options as a recipe words them ("senza autorizzazione") are the table's values.
    r = route.route(TABLE, {"intervento": "manutenzione straordinaria", "cambio_uso": "no",
                            "paesaggio": "senza autorizzazione", "fatti": []}, REHEARSALS)
    assert r["pratica"] == "cila-fittizia", r


def refusals_say_why():
    r = route.route(TABLE, {"intervento": "edilizia_libera", "cambio_uso": "no", "paesaggio": "no", "fatti": []},
                    REHEARSALS)
    assert not r["routed"] and r["unsupported"][0].startswith("This case needs no pratica"), r
    r = route.route(TABLE, {"intervento": "altro"}, REHEARSALS)
    assert not r["routed"] and "proroghe" in r["unsupported"][0], r
    r = route.route(TABLE, {"intervento": "manutenzione_straordinaria", "cambio_uso": "no", "paesaggio": "ordinaria",
                            "fatti": []}, REHEARSALS)
    assert r["unsupported"] == ["Not mapped yet: napoli/comune/cila-lavori-edilizi (comunicazione) filed with "
                                "napoli/comune/autorizzazione-paesaggistica-ordinaria."], r


def apart_is_the_persons():
    """Works on the structures: the seismic filing at the Genio Civile is filed apart."""
    for facts, d in LEAVES:
        if d["apart"] and d["main"] and not d["refused"]:
            r = route.route(TABLE, facts, REHEARSALS)
            if r["routed"]:
                assert r["apart"] and r["apart"][0].startswith("File apart"), r
                return
    raise AssertionError("no routed case files anything apart")


def one_steps_file_per_combination():
    with tempfile.TemporaryDirectory() as tmp:
        for n in ("scia-fittizia", "scia-fittizia-copia"):
            (Path(tmp) / n).mkdir()
            shutil.copy(REHEARSALS / "scia-fittizia" / "portal-steps.generated.yaml", Path(tmp) / n)
        try:
            route.index(TABLE, Path(tmp))
        except run.StepError as e:
            assert "one steps file per combination" in str(e)
        else:
            raise AssertionError("two steps files for one combination were indexed")


def plugin_layout():
    """The plugin's pratiche/<name>.json are indexed as the rehearsals are."""
    with tempfile.TemporaryDirectory() as tmp:
        steps = yaml.safe_load((REHEARSALS / "scia-fittizia" / "portal-steps.generated.yaml").read_text())
        (Path(tmp) / "scia-fittizia.json").write_text(json.dumps(steps, default=str))
        (Path(tmp) / "catalog.json").write_text("[]")
        assert [n for n, _, _ in route.index(TABLE, Path(tmp)).values()] == ["scia-fittizia"]


def main():
    tests = [every_case_routed_or_refused, every_recipe_reached, answers_carry_into_preflight, cila_reads_sanatoria_its_way,
             rehearsal_cases_come_home, asks_as_the_table_asks, refusals_say_why, apart_is_the_persons,
             one_steps_file_per_combination, plugin_layout]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"{len(tests)}/{len(tests)} passed")


if __name__ == "__main__":
    main()
