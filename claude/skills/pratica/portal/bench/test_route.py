#!/usr/bin/env python3
"""Offline tests of route.py: from a case's facts to the one steps file that files it.

  ~/.cache/pratica-portal/venv/bin/python -I claude/skills/pratica/portal/bench/test_route.py

No browser, vault or network. Walks every case the SUE rules tables decide (each fact
asked as the table asks it): sue-napoli, the title for new works, and sue-napoli-adempimenti,
what is filed on a title held. Checks each is routed to a steps file that agrees or refused
with a reason, that every rules-gated SUE rehearsal is reached, and that each rehearsal's own
cases come back to it. Prints the combinations a table decides that no steps file files yet:
what is left to map.
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
FOLLOW = "sue-napoli-adempimenti"  # filings on a title held (2026-11-04)
T = rules.table(TABLE)


LEAVES = route.cases(TABLE)
CASES = {TABLE: LEAVES, FOLLOW: route.cases(FOLLOW)}


def every_case_routed_or_refused(table=TABLE):
    """Each decided case reaches the one steps file for its pratiche, which reads the case
    the same way (its fixed facts, its wizard), or is refused with the reason; the
    combinations no steps file files are the mapping still to do."""
    idx, unmapped, routed = route.index(table, REHEARSALS), defaultdict(int), 0
    for facts, d in CASES[table]:
        r = route.route(table, facts, REHEARSALS)
        assert not r["questions"], (facts, r["questions"])
        if d["refused"] or d["none"]:
            assert not r["routed"] and r["unsupported"], (facts, r)
            continue
        k = route.key(d["main"]["procedure"], [a["procedure"] for a in d["also"]])
        if k not in idx:
            assert not r["routed"] and r["unsupported"][0].startswith("Non ancora prevista"), (facts, r)
            unmapped[k] += 1
            continue
        assert r["routed"], (facts, r["unsupported"])
        assert r["pratica"] == idx[k][0]
        routed += 1
    c = route.coverage(table, REHEARSALS)  # what scoreboard.py prints: the same count
    assert (c["routed"], dict(c["unmapped"])) == (routed, dict(unmapped)), c
    print(f"  {table}: {len(CASES[table])} cases, {routed} routed, {sum(unmapped.values())} not mapped yet")
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


def answers_carry_into_preflight(table=TABLE):
    """The answers route.py hands on fit the steps file's own asks, and leave its rules
    waiting on nothing but what it says it asks again."""
    by_name = {n: s for n, _, s in route.index(table, REHEARSALS).values()}
    for facts, d in CASES[table]:
        if not d["main"] or d["refused"]:
            continue
        r = route.route(table, facts, REHEARSALS)
        if not r["routed"]:
            continue
        steps = by_name[r["pratica"]]
        asks = steps["asks"]
        for k, v in r["answers"].items():
            assert k in asks and run.check_answer(asks[k], v) is None, (r["pratica"], k, v)
        _, waiting = run.ruled(steps, run.Values(r["answers"], fields={}, asks=asks))
        again = {x["fact"] for x in r["asked_again"]}
        # A fact the table never needed for this case may wait behind one asked again: the CILA's
        # sanatoria comes from "have the works started?", and until then the terre e rocce rule,
        # which wants no sanatoria, is open (2026-11-03). Answered, it no longer waits.
        assert set(waiting) <= again | ({f for f in waiting if f not in facts} if again else set()), \
            (r["pratica"], facts, waiting)
        for name in facts:  # a fact the person answered here is never asked there again
            tmpl = steps["rules"]["facts"][name]
            if tmpl == "{{ask.%s}}" % name:
                assert name in r["answers"], (r["pratica"], name)


def as_a_conversation():
    """Each decided case asked as a person would answer it: the works, then one reply to
    everything the second message shows (the checklist as the items ticked). It ends where
    the case does, and nothing is handed on that the person wasn't shown."""
    first = next(iter(T["facts"]))  # T, LEAVES and TABLE: the table under test (follow_ups_routed swaps them)
    for facts, d in LEAVES:
        if first not in facts or d["refused"] or not d["main"]:
            continue
        second = route.route(TABLE, {first: facts[first]}, REHEARSALS)
        shown = {first} | {q["key"] for q in second["questions"]} | {i["key"] for q in second["questions"]
                                                                      for i in q.get("items", [])}
        assert set(facts) - {first} <= shown, (facts, shown)
        reply = {first: facts[first], "fatti": [k for k, v in facts.items() if v is True]}
        reply |= {k: v for k, v in facts.items() if T["facts"][k]["type"] != "yes_no"}
        r = route.route(TABLE, reply, REHEARSALS)
        direct = route.route(TABLE, facts, REHEARSALS)
        assert (r["pratica"], r["unsupported"]) == (direct["pratica"], direct["unsupported"]), (facts, r)
        gates = {x["key"]: x.get("only_if", []) for q in second["questions"] for x in [q] + q.get("items", [])}
        for k in r["answers"]:
            assert k not in T["facts"] or k in shown, (facts, k)
            # an item under a gate left unticked was never answered: never handed on as a no
            unticked_gate = any(g not in reply["fatti"] for g in gates.get(k, []))
            assert not (k in facts and k not in reply["fatti"] and unticked_gate
                        and T["facts"][k]["type"] == "yes_no" and k not in reply), (facts, k)


def wrong_answers():
    """Asked again with why when the case needs them; malformed ones refused, never a crash."""
    base = {"intervento": "manutenzione_straordinaria", "cambio_uso": "no", "paesaggio": "no", "terre_rocce": "no"}
    r = route.route(TABLE, {**base, "fatti": ["intervento"]}, REHEARSALS)  # not a checklist item
    assert {q["key"]: q for q in r["questions"]}["fatti"]["error"], r
    r = route.route(TABLE, {**base, "fatti": [["x"]]}, REHEARSALS)
    assert {q["key"]: q for q in r["questions"]}["fatti"]["error"], r
    r = route.route(TABLE, {**base, "fatti": [], "strutture": "boh"}, REHEARSALS)  # needed: asked again
    items = {i["key"]: i for q in r["questions"] for i in q.get("items", [])}
    assert not r["routed"] and items["strutture"]["error"], r
    r = route.route(TABLE, {**base, "fatti": [], "demolizione_zona_a": "boh"}, REHEARSALS)  # not needed: dropped
    assert r["pratica"] == "cila-fittizia" and "demolizione_zona_a" not in r["answers"], r
    # Ticked after a wrong answer of its own: the tick is the answer.
    r = route.route(TABLE, {**base, "fatti": ["sanatoria"], "sanatoria": "forse"}, REHEARSALS)
    assert r["pratica"] == "cila-fittizia" and r["asked_again"][0]["fits"] == ["in corso", "realizzato"], r
    r = route.route(TABLE, {"intervento": {"a": 1}}, REHEARSALS)
    assert r["questions"][0]["error"], r
    r = route.route(TABLE, {"fatti": ["strutture"]}, REHEARSALS)  # a checklist before the works: read nothing
    assert r["questions"][0]["key"] == "intervento" and not r["routed"], r
    try:
        route.route(TABLE, [], REHEARSALS)
    except run.StepError:
        pass
    else:
        raise AssertionError("a list was taken for answers")


def gated_items_stay_unknown():
    """An item shown only under another (the bene culturale, under the sanatoria) is never
    taken for a no while that one is unticked: the form reads it (the Soprintendenza's
    tutela), so its pre-flight asks it. Nor an item the checklist didn't show (the sanatoria
    answered no before it)."""
    case = {"intervento": "ristrutturazione", "terre_rocce": "no", "cambio_uso": "no", "paesaggio": "no"}
    second = route.route(TABLE, {"intervento": "ristrutturazione"}, REHEARSALS)
    items = {i["key"]: i for q in second["questions"] for i in q.get("items", [])}
    assert items["bene_culturale"]["only_if"] == ["sanatoria"], items["bene_culturale"]
    r = route.route(TABLE, {**case, "fatti": []}, REHEARSALS)
    assert r["pratica"] == "scia-fittizia" and "bene_culturale" not in r["answers"], r
    r = route.route(TABLE, {**case, "fatti": ["sanatoria"]}, REHEARSALS)
    assert r["answers"].get("bene_culturale") is False or not r["routed"], r
    r = route.route(TABLE, {**case, "sanatoria": False, "fatti": []}, REHEARSALS)
    assert "bene_culturale" not in r["answers"], r


def own_words_kept_only_if_they_agree():
    """cila_stato given by the person is kept when it says what the facts say, else asked
    again with what was given, never overwritten."""
    base = {"intervento": "manutenzione_straordinaria", "cambio_uso": "no", "paesaggio": "no", "terre_rocce": "no"}
    r = route.route(TABLE, {**base, "fatti": ["sanatoria"], "cila_stato": "in corso"}, REHEARSALS)
    assert r["answers"]["cila_stato"] == "in corso" and not r["asked_again"], r
    for given in ("da iniziare", "bogus"):
        r = route.route(TABLE, {**base, "fatti": ["sanatoria"], "cila_stato": given}, REHEARSALS)
        assert "cila_stato" not in r["answers"] and r["asked_again"][0]["given"] == given, r


def missing_answers_file():
    import subprocess
    p = subprocess.run([sys.executable, "-I", str(HERE.parent / "route.py"), "--table", TABLE, "--answers",
                        "/nonexistent/facts.json"], capture_output=True, text=True)
    assert p.returncode == 1 and p.stderr.startswith("stopped:"), p.stderr


def cila_reads_sanatoria_its_way():
    """The CILA reads `sanatoria` from cila_stato: one option fits "no", two fit "yes"."""
    base = {"intervento": "manutenzione_straordinaria", "terre_rocce": "no", "cambio_uso": "no", "paesaggio": "no", "fatti": []}
    r = route.route(TABLE, base, REHEARSALS)
    assert r["pratica"] == "cila-fittizia" and r["answers"]["cila_stato"] == "da iniziare", r
    assert "sanatoria" not in r["answers"]
    r = route.route(TABLE, {**base, "fatti": ["sanatoria"]}, REHEARSALS)
    assert r["pratica"] == "cila-fittizia", r
    assert r["asked_again"] == [{"fact": "sanatoria", "ask": "cila_stato", "fits": ["in corso", "realizzato"]}], r


def sanatoria_in_tutela():
    """Works that needed the permesso, done without it in a protected area (2026-11-02): no
    alteration is the plain permesso in sanatoria; a new volume can't have its compatibility found
    (art. 167 c. 4); otherwise the permesso with the accertamento, whose landscape quadro the
    portal can't state (pdc-36-paesaggio)."""
    base = {"intervento": "ristrutturazione_pesante", "terre_rocce": "no", "cambio_uso": "no", "paesaggio": "ordinaria",
            "fatti": ["sanatoria", "paesaggio_eseguiti"]}
    r = route.route(TABLE, {**base, "paesaggio": "senza_autorizzazione", "fatti": ["sanatoria"]}, REHEARSALS)
    assert r["pratica"] == "pdc-sanatoria-fittizio", r
    r = route.route(TABLE, {**base, "fatti": base["fatti"] + ["paesaggio_volumi"]}, REHEARSALS)
    assert not r["routed"] and "art. 167 c. 4" in r["unsupported"][0], r
    r = route.route(TABLE, base, REHEARSALS)
    assert r["pratica"] == "pdc-sanatoria-accertamento-fittizio", r
    r = route.route(TABLE, {**base, "fatti": ["sanatoria"]}, REHEARSALS)
    assert not r["routed"] and "dopo la sanatoria" in r["unsupported"][0], r


def sanatoria_cambio_uso():
    """A change of use done without a title (2026-11-02) is legalized by the title it needed: one
    unit's by the SCIA in sanatoria (art. 36-bis c. 1), a whole building's by the permesso in
    sanatoria (art. 36 names the SCIA alternativa); without works between compatible categories
    it is free, and a use the PRG doesn't allow is refused."""
    base = {"intervento": "manutenzione_straordinaria", "terre_rocce": "no", "cambio_uso": "stessa_categoria", "paesaggio": "no",
            "fatti": ["sanatoria", "uso_ammesso_prg"]}
    r = route.route(TABLE, base, REHEARSALS)
    assert r["pratica"] == "scia-sanatoria-fittizia", r
    r = route.route(TABLE, {**base, "cambio_uso": "intero_tra_categorie"}, REHEARSALS)
    assert r["pratica"] == "pdc-sanatoria-fittizio", r
    r = route.route(TABLE, {**base, "intervento": "nessuna_opera", "cambio_uso": "tra_categorie"}, REHEARSALS)
    assert not r["routed"] and r["unsupported"][0].startswith("Per questo caso non serve alcuna pratica"), r
    r = route.route(TABLE, {**base, "fatti": ["sanatoria"]}, REHEARSALS)
    assert not r["routed"] and "PRG" in r["unsupported"][0], r


def sanatoria_zona_a():
    """A demolition and reconstruction in zona A, done without a title (2026-11-02): it needed the
    permesso in Naples, so the permesso in sanatoria (art. 36); in a protected area the same
    landscape rules as any permesso in sanatoria."""
    base = {"intervento": "ristrutturazione", "terre_rocce": "no", "cambio_uso": "no", "paesaggio": "no", "fatti": ["sanatoria", "demolizione_zona_a"]}
    r = route.route(TABLE, base, REHEARSALS)
    assert r["pratica"] == "pdc-sanatoria-fittizio", r
    r = route.route(TABLE, {**base, "paesaggio": "ordinaria", "fatti": base["fatti"] + ["paesaggio_eseguiti"]}, REHEARSALS)
    assert r["pratica"] == "pdc-sanatoria-accertamento-fittizio", r
    r = route.route(TABLE, {**base, "intervento": "ristrutturazione_pesante"}, REHEARSALS)
    assert r["pratica"] == "pdc-sanatoria-fittizio", r


def sanatoria_titoli():
    """The last sanatorie (2026-11-02): an urban restructuring needed the permesso, so the permesso
    in sanatoria; a variant to a SCIA, never filed, is works in difformità from the SCIA, so the
    SCIA in sanatoria; temporary works have no sanatoria in the law, and say why."""
    base = {"terre_rocce": "no", "cambio_uso": "no", "paesaggio": "no", "fatti": ["sanatoria"]}
    r = route.route(TABLE, {**base, "intervento": "ristrutturazione_urbanistica"}, REHEARSALS)
    assert r["pratica"] == "pdc-sanatoria-fittizio", r
    r = route.route(TABLE, {**base, "intervento": "variante_scia"}, REHEARSALS)
    assert r["pratica"] == "scia-sanatoria-fittizia", r
    r = route.route(TABLE, {**base, "intervento": "opere_temporanee"}, REHEARSALS)
    assert not r["routed"] and "180 giorni" in r["unsupported"][0], r


def cambio_uso_fuori_23ter():
    """A change of use art. 23-ter doesn't give a title for (one unit on the ground floor, or
    outside zones A, B and C: 2026-11-03) takes Campania's, as a whole building's does: free
    without works, else the SCIA alternativa; done without it, the permesso in sanatoria. The
    a.1 to a.2 change in the centro storico stays the SUE's, saying what it lacks."""
    base = {"intervento": "manutenzione_straordinaria", "terre_rocce": "no", "cambio_uso": "piano_terra", "paesaggio": "no",
            "fatti": ["uso_ammesso_prg"]}
    r = route.route(TABLE, base, REHEARSALS)
    assert r["pratica"] == "scia-alternativa-fittizia", r
    r = route.route(TABLE, {**base, "cambio_uso": "altro"}, REHEARSALS)
    assert r["pratica"] == "scia-alternativa-fittizia", r
    r = route.route(TABLE, {**base, "intervento": "nessuna_opera", "cambio_uso": "altro"}, REHEARSALS)
    assert not r["routed"] and r["unsupported"][0].startswith("Per questo caso non serve alcuna pratica"), r
    r = route.route(TABLE, {**base, "fatti": ["uso_ammesso_prg", "sanatoria"]}, REHEARSALS)
    assert r["pratica"] == "pdc-sanatoria-fittizio", r
    r = route.route(TABLE, {**base, "cambio_uso": "stessa_categoria", "fatti": ["uso_ammesso_prg", "verso_a2_tavola_7a"]}, REHEARSALS)
    assert not r["routed"] and "Giunta" in r["unsupported"][0], r


def rehearsal_cases_come_home(table=TABLE, least=30):
    """Each rehearsal's answers files, read as its steps file reads the facts, route back to it
    (a case its own rules refuse is left out: it tests the refusal)."""
    n = 0
    for name, path, steps in route.index(table, REHEARSALS).values():
        for f in sorted(path.parent.glob("answers*.json")):
            a = json.loads(f.read_text())
            v = run.Values(a, fields={}, asks=steps["asks"])
            out, waiting = run.ruled(steps, v)
            if out or waiting:
                continue
            facts = {k: x for k, t in steps["rules"]["facts"].items() if (x := v.render(t)) is not None}
            r = route.route(table, facts, REHEARSALS)
            assert r["pratica"] == name, (name, f.name, r["unsupported"] or r["questions"])
            n += 1
    assert n >= least, n
    print(f"  {table}: {n} rehearsal cases routed back")


def asks_as_the_table_asks():
    """One message: the works first, then every fact some kind of works needs, each one not
    every kind needs saying for which (`only_for`); yes/no ones as one checklist, the seismic
    choice only under the structures; a wrong answer asked again with why."""
    r = route.route(TABLE, {}, REHEARSALS)
    qs = {q["key"]: q for q in r["questions"]}
    assert r["questions"][0]["key"] == "intervento" and not r["routed"] and {"paesaggio", "fatti"} <= set(qs), list(qs)
    items = {i["key"]: i for i in qs["fatti"]["items"]}
    assert items["prospetti"]["only_for"] == {"intervento": ["manutenzione_straordinaria"]}, items["prospetti"]
    assert "only_for" not in qs["paesaggio"], qs["paesaggio"]  # every kind of works asks it
    assert "altro" not in str([q.get("only_for") for q in r["questions"]]), "a kind the table refuses needs nothing more"
    r = route.route(TABLE, {"intervento": "manutenzione_straordinaria"}, REHEARSALS)
    qs = {q["key"]: q for q in r["questions"]}
    assert set(qs) == {"sismica", "cambio_uso", "paesaggio", "terre_rocce", "fatti"}, set(qs)
    assert qs["sismica"]["only_if"] == ["strutture"]
    assert "strutture" in [i["key"] for i in qs["fatti"]["items"]]
    assert qs["fatti"]["question"] == route.CHECKLIST
    r = route.route(TABLE, {"intervento": "rifare il bagno"}, REHEARSALS)
    assert r["questions"][0]["key"] == "intervento" and "error" in r["questions"][0]
    r = route.route(TABLE, {"intervento": "manutenzione_straordinaria", "fatti": "nessuna"}, REHEARSALS)
    assert "error" in {q["key"]: q for q in r["questions"]}["fatti"]
    # The options as a recipe words them ("senza autorizzazione") are the table's values.
    r = route.route(TABLE, {"intervento": "manutenzione straordinaria", "terre_rocce": "no", "cambio_uso": "no",
                            "paesaggio": "senza autorizzazione", "fatti": []}, REHEARSALS)
    assert r["pratica"] == "cila-fittizia", r


def refusals_say_why():
    r = route.route(TABLE, {"intervento": "edilizia_libera", "cambio_uso": "no", "paesaggio": "no", "terre_rocce": "no",
                            "fatti": []}, REHEARSALS)
    assert not r["routed"] and r["unsupported"][0].startswith("Per questo caso non serve alcuna pratica"), r
    r = route.route(TABLE, {"intervento": "altro"}, REHEARSALS)
    assert not r["routed"] and "proroghe" in r["unsupported"][0] and FOLLOW in r["unsupported"][0], r
    # Every combination has a steps file since 2026-10-31: one left out shows the message.
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copytree(REHEARSALS / "cila-fittizia", Path(tmp) / "cila-fittizia")
        r = route.route(TABLE, {"intervento": "manutenzione_straordinaria", "terre_rocce": "no", "cambio_uso": "no", "paesaggio": "ordinaria",
                                "fatti": []}, Path(tmp))
    assert r["unsupported"] == [f"Non ancora prevista: {run.procedure_name('napoli/comune/cila-lavori-edilizi')}, insieme a "
                                f"{run.procedure_name('napoli/comune/autorizzazione-paesaggistica-ordinaria')}."], r
    assert "napoli/" not in r["message"], r["message"]


def apart_is_the_persons():
    """Works on the structures: the seismic filing at the Genio Civile is filed apart."""
    for facts, d in LEAVES:
        if d["apart"] and d["main"] and not d["refused"]:
            r = route.route(TABLE, facts, REHEARSALS)
            if r["routed"]:
                assert r["apart"] and r["apart"][0].startswith("Da presentare a parte"), r
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


def landscape_kept_in_force():
    """A title whose works already have a landscape authorization (2026-11-04): extended (art.
    10-septies) or renewed (art. 7 D.P.R. 31/2017) in the title's pratica; works with no title
    take it alone. Done without the permesso they needed, the table refuses it (the accertamento
    is the way), and a SCIA in sanatoria with it is still to map."""
    base = {"terre_rocce": "no", "cambio_uso": "no", "fatti": []}
    cila = {**base, "intervento": "manutenzione_straordinaria"}
    assert route.route(TABLE, {**cila, "paesaggio": "proroga"}, REHEARSALS)["pratica"] == "cila-proroga-paesaggistica-fittizia"
    assert route.route(TABLE, {**cila, "paesaggio": "rinnovo", "terre_rocce": "dichiarazione"},
                       REHEARSALS)["pratica"] == "cila-rinnovo-paesaggistica-terre-rocce-fittizia"
    pdc = {**base, "intervento": "nuova_costruzione", "fatti": [], "paesaggio": "rinnovo"}
    r = route.route(TABLE, pdc, REHEARSALS)
    assert r["pratica"] == "pdc-rinnovo-paesaggistica-fittizio", r
    libera = {**base, "intervento": "edilizia_libera"}
    assert route.route(TABLE, {**libera, "paesaggio": "proroga"}, REHEARSALS)["pratica"] == "proroga-paesaggistica-fittizia"
    assert route.route(TABLE, {**libera, "paesaggio": "rinnovo"}, REHEARSALS)["pratica"] == "rinnovo-paesaggistica-fittizia"
    r = route.route(TABLE, {**pdc, "fatti": ["sanatoria"]}, REHEARSALS)
    assert not r["routed"] and "permesso in sanatoria" in r["unsupported"][0], r
    r = route.route(TABLE, {**base, "intervento": "ristrutturazione", "paesaggio": "proroga", "fatti": ["sanatoria"]}, REHEARSALS)
    assert r["unsupported"][0].startswith("Not mapped yet: napoli/comune/scia-in-sanatoria"), r


def edilizia_libera_that_digs():
    """Works with no title whose soil leaves the site (2026-11-04): the dichiarazione di utilizzo
    is their pratica, or goes with their landscape procedure; the piano goes to the VIA authority
    and the SUE has nothing; after landscape works already done, never (the dichiarazione comes first)."""
    libera = {"intervento": "edilizia_libera", "cambio_uso": "no", "fatti": [], "terre_rocce": "dichiarazione"}
    assert route.route(TABLE, {**libera, "paesaggio": "no"}, REHEARSALS)["pratica"] == "scavo-fuori-sito-fittizio"
    for paesaggio, name in (("semplificata", "paesaggistica-semplificata-terre-rocce-fittizia"),
                            ("ordinaria", "paesaggistica-ordinaria-terre-rocce-fittizia"),
                            ("proroga", "proroga-paesaggistica-terre-rocce-fittizia"),
                            ("rinnovo", "rinnovo-paesaggistica-terre-rocce-fittizia")):
        r = route.route(TABLE, {**libera, "paesaggio": paesaggio}, REHEARSALS)
        assert r["pratica"] == name and any("avvenuto" in a for a in r["apart"]), r
    r = route.route(TABLE, {**libera, "paesaggio": "no", "terre_rocce": "piano"}, REHEARSALS)
    assert not r["routed"] and "piano di utilizzo" in r["unsupported"][0], r
    r = route.route(TABLE, {**libera, "paesaggio": "semplificata", "fatti": ["paesaggio_eseguiti"]}, REHEARSALS)
    assert r["pratica"] == "accertamento-paesaggistico-fittizio", r
    # Already dug (2026-11-05 review): neither the dichiarazione nor the piano is filed any more.
    for terre in ("dichiarazione", "piano"):
        r = route.route(TABLE, {**libera, "paesaggio": "no", "terre_rocce": terre, "fatti": ["sanatoria"]}, REHEARSALS)
        assert not r["routed"] and "già fatti" in r["unsupported"][0], r
    # A change of use free without works keeps saying so, never "the permesso in sanatoria".
    r = route.route(TABLE, {"intervento": "nessuna_opera", "cambio_uso": "intero_tra_categorie", "paesaggio": "proroga",
                            "fatti": ["sanatoria", "uso_ammesso_prg"]}, REHEARSALS)
    assert r["unsupported"][0].startswith("This case needs no pratica"), r


def follow_ups_routed():
    """What is filed on a title held (2026-11-04): every case of sue-napoli-adempimenti reaches
    its steps file or is refused with why, every one of those steps files is reached, and each
    rehearsal's own cases come back to it."""
    every_case_routed_or_refused(FOLLOW)
    assert not route.coverage(FOLLOW, REHEARSALS)["unmapped"]
    reached = {route.route(FOLLOW, f, REHEARSALS)["pratica"] for f, d in CASES[FOLLOW] if d["main"]}
    names = {n for n, _, _ in route.index(FOLLOW, REHEARSALS).values()}
    assert names == reached - {None} and len(names) >= 37, sorted(names ^ reached)
    answers_carry_into_preflight(FOLLOW)
    rehearsal_cases_come_home(FOLLOW, least=20)
    r = route.route(FOLLOW, {}, REHEARSALS)
    assert [q["key"] for q in r["questions"]] == ["adempimento"], r
    # The checklist is about the works, as the new works' is, never gen.py's default for a shop
    # ("valgono per l'attività": the recipes named no question, 2026-11-05).
    r = route.route(FOLLOW, {"adempimento": "fine_lavori"}, REHEARSALS)
    assert {q["key"]: q for q in r["questions"]}["fatti"]["question"] == route.CHECKLIST, r
    for name, _, steps in route.index(FOLLOW, REHEARSALS).values():
        assert steps.get("groups", {}).get("fatti", {}).get("question", route.CHECKLIST) == route.CHECKLIST, name
    # Asked as a person answers: the filing alone, then one reply with the checklist ticked.
    global TABLE, T, LEAVES
    saved = TABLE, T, LEAVES
    TABLE, T, LEAVES = FOLLOW, rules.table(FOLLOW), CASES[FOLLOW]
    try:
        as_a_conversation()
    finally:
        TABLE, T, LEAVES = saved


def follow_ups_as_the_law_reads_them():
    """The title decides the filing: a voltura for a permesso, a cambio d'intestazione for a
    CILA or a SCIA; the ordinary extension is the permesso's, the 10-septies one the permesso's
    and the SCIA's; the first 10-septies communication of the start has no operation of its own."""
    go = lambda **a: route.route(FOLLOW, a, REHEARSALS)
    assert go(adempimento="intestatario", titolo_tipo="permesso di costruire")["pratica"] == "voltura-pdc-fittizia"
    assert go(adempimento="intestatario", titolo_tipo="SCIA")["pratica"] == "cambio-intestazione-fittizio"
    assert go(adempimento="proroga_fine", proroga="straordinaria", titolo_tipo="SCIA",
              paesaggistica="no")["pratica"] == "proroga-ultimazione-fittizia"
    r = go(adempimento="proroga_fine", proroga="ordinaria", titolo_tipo="SCIA")
    assert not r["routed"] and "art. 15 c. 2" in r["unsupported"][0], r
    r = go(adempimento="proroga_inizio", proroga="straordinaria")
    assert not r["routed"] and "va chiesto al SUE" in r["unsupported"][0], r
    r = go(adempimento="proroga_inizio", proroga="ordinaria", titolo_tipo="permesso di costruire", paesaggistica="rinnovo")
    assert r["pratica"] == "proroga-inizio-rinnovo-paesaggistica-fittizia", r
    r = go(adempimento="fine_lavori", fatti=["dau"])
    assert r["pratica"] == "fine-lavori-dau-fittizia", r
    r = go(adempimento="inizio_lavori", titolo_tipo="permesso di costruire", fatti=["dichiarazione_utilizzo"])
    assert r["pratica"] == "inizio-lavori-terre-rocce-fittizia" and r["apart"], r
    r = go(adempimento="inizio_lavori", titolo_tipo="CILA")
    assert not r["routed"] and "art. 15" in r["unsupported"][0], r


def main():
    tests = [every_case_routed_or_refused, every_recipe_reached, answers_carry_into_preflight, as_a_conversation,
             wrong_answers, gated_items_stay_unknown, own_words_kept_only_if_they_agree, missing_answers_file,
             cila_reads_sanatoria_its_way, sanatoria_in_tutela, sanatoria_cambio_uso, sanatoria_zona_a, sanatoria_titoli, cambio_uso_fuori_23ter,
             rehearsal_cases_come_home, asks_as_the_table_asks, refusals_say_why, apart_is_the_persons,
             one_steps_file_per_combination, plugin_layout, landscape_kept_in_force, edilizia_libera_that_digs,
             follow_ups_routed, follow_ups_as_the_law_reads_them]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"{len(tests)}/{len(tests)} passed")


if __name__ == "__main__":
    main()
