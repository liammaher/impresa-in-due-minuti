#!/usr/bin/env python3
"""catalogue/F839/sue-pairs.yaml against the wizard and the rehearsals, offline.

  ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/test_pairs.py

With PRATICHE_NAPOLI_DIR set, each reason's cites are checked against the library's entries.
Prints the combinations a case files together that have no steps file yet (to map).
"""

import json
import os
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
PORTAL = HERE.parent
sys.path.insert(0, str(PORTAL))
sys.dont_write_bytecode = True
import gen  # noqa: E402  (a combination's operations, resolved)
ROOT = PORTAL.parents[3]
WIZARD = json.loads((PORTAL / "catalogue/F839/sue-wizard.json").read_text())
PAIRS = yaml.safe_load((PORTAL / "catalogue/F839/sue-pairs.yaml").read_text())
VERDICTS = {"together", "apart", "never", "refused", "rules", "each_alone"}

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


def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


SLUG = {norm(v): k for k, v in PAIRS["ops"].items()}
KEY = {o["key"]: SLUG.get(norm(o["label"])) for o in WIZARD["operations"]}


def recipe_ops():
    """Each rehearsal's operations, as slugs (a frozenset)."""
    out = {}
    for f in sorted((ROOT / "rehearsals").glob("*/recipe.yaml")):
        op = gen.resolved(gen.load_yaml(f)).get("operation")  # a combination's follow from its extends
        if op is None:
            continue
        ops = [op] if isinstance(op, str) else op
        slugs = [SLUG.get(norm(x)) for x in ops]
        if None in slugs:  # a SUAP recipe
            continue
        out[f.parent.name] = frozenset(slugs)
    return out


RECIPES = recipe_ops()
assert RECIPES, f"no rehearsals under {ROOT}"
ENTRIES = [("pair", e) for e in PAIRS["pairs"]] + [("triple", e) for e in PAIRS["triples"]]


@case("every operation of the wizard has a slug, and every slug is one of the wizard's")
def _():
    assert None not in KEY.values(), [k for k, v in KEY.items() if v is None]
    assert set(KEY.values()) == set(PAIRS["ops"]), set(PAIRS["ops"]) ^ set(KEY.values())


@case("every pair the wizard accepts is here once, and nothing else")
def _():
    accepted = {frozenset(KEY[k] for k in p["keys"]) for p in WIZARD["pairs"] if p.get("accepted")}
    here = [frozenset(e["ops"]) for e in PAIRS["pairs"]]
    assert len(here) == len(set(here)), "a pair twice"
    assert set(here) == accepted, f"missing {[sorted(p) for p in accepted - set(here)][:3]}, extra {[sorted(p) for p in set(here) - accepted][:3]}"


@case("a triple takes one operation of each group the wizard pairs (a title, a landscape procedure, a terre e rocce box)")
def _():
    accepted = {frozenset(KEY[k] for k in p["keys"]) for p in WIZARD["pairs"] if p.get("accepted")}
    for e in PAIRS["triples"]:
        ops = e["ops"]
        assert len(set(ops)) == 3, ops
        for i in range(3):
            for j in range(i + 1, 3):
                assert frozenset((ops[i], ops[j])) in accepted, f"{ops}: the wizard never took {ops[i]} with {ops[j]}"


@case("each entry's reason exists, with a known verdict, a status and cites")
def _():
    for name, r in PAIRS["reasons"].items():
        assert r["verdict"] in VERDICTS, name
        assert r["status"] in ("verified", "reading"), name
        assert r["cites"] and r["why"], name
    for kind, e in ENTRIES:
        assert e["reason"] in PAIRS["reasons"], f"{kind} {e['ops']}: no reason {e['reason']}"


@case("only a together entry lists rehearsals, and each selects exactly its operations")
def _():
    for kind, e in ENTRIES:
        together = PAIRS["reasons"][e["reason"]]["verdict"] == "together"
        assert together == ("rehearsals" in e), f"{kind} {e['ops']}"
        for name in e.get("rehearsals") or []:
            assert name in RECIPES, f"{e['ops']}: no rehearsal {name}"
            assert RECIPES[name] == frozenset(e["ops"]), f"{name} selects {sorted(RECIPES[name])}, not {e['ops']}"


@case("every rehearsal of several operations is listed under its combination, which files them together")
def _():
    listed = {n for _, e in ENTRIES for n in e.get("rehearsals") or []}
    combos = {n for n, ops in RECIPES.items() if len(ops) > 1}
    assert combos <= listed, f"not listed: {sorted(combos - listed)}"


@case("each operation alone has a rehearsal: a pair that isn't filed together needs nothing more")
def _():
    alone = {next(iter(ops)) for ops in RECIPES.values() if len(ops) == 1}
    assert alone == set(PAIRS["ops"]), f"no rehearsal of {sorted(set(PAIRS['ops']) - alone)} alone"


@case("the cites name the library's sources (library/)")
def _():
    import rules
    lib = rules.library_dir()
    for name, r in PAIRS["reasons"].items():
        for c in r["cites"]:
            f = Path(lib) / "procedures" / f"{c['procedure']}.yaml"
            assert f.is_file(), f"{name}: no library entry {c['procedure']}"
            ids = {s.get("id") for s in yaml.safe_load(f.read_text()).get("sources") or []}
            assert c["source"] in ids, f"{name}: {c['procedure']} has no source {c['source']}"


todo = [(kind, e["ops"]) for kind, e in ENTRIES if e.get("rehearsals") == []]
print(f"\nTo map ({len(todo)}): combinations a case files together with no steps file yet")
for kind, ops in todo:
    print(f"  {' + '.join(ops)}")
print(f"\n{sum(results)} of {len(results)} passed")
sys.exit(0 if all(results) else 1)
