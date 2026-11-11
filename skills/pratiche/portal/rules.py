"""The library's rules tables (library/rules/*.yaml): from a few facts about a case to the
pratiche the law asks for.

decide() reads a table as the library's tools/lib/rules.ts does (the library validates
the tables: every combination of facts decided once, every rule citing a verified claim).
bench/test_rules.py holds the two to the same answers.
"""

import json
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _tables_dir():
    """Where the tables are: next to this file in the plugin (JSON, built from the library); in
    the repository the library's own rules/, $PRATICHE_NAPOLI_DIR to try another checkout."""
    if (HERE / "rules").is_dir():
        return HERE / "rules"
    return library_dir() / "rules"


def library_dir():
    """The library checkout the tools read: $PRATICHE_NAPOLI_DIR, else this repository's library/."""
    lib = os.environ.get("PRATICHE_NAPOLI_DIR")
    return Path(lib) if lib else (HERE.parents[3] if len(HERE.parents) > 3 else HERE) / "library"


TABLES = _tables_dir()
# What the last drift check (catalogue.py drift) found changed on the portal, per pratica.
DRIFT = HERE / "catalogue" / "F839" / "drift.json"
_tables = {}


def drifted(name):
    """The differences the last drift check found in a pratica's crawl, or []: pre-flight
    refuses such a pratica (run.py portal_changed). Here so the runtime imports no authoring
    code: the plugin ships rules.py and drift.json, not catalogue.py."""
    if not DRIFT.exists():
        return []
    return json.loads(DRIFT.read_text())["pratiche"].get(name, {}).get("differences", [])


def load(path, strings=False):
    """A steps file or a rules table: JSON as the plugin ships them (it runs with no packages),
    else the repo's YAML. strings: every scalar a string, as a rules table is read."""
    path = Path(path)
    if path.suffix == ".json":
        return json.loads(path.read_text())
    import yaml  # the repo's files only
    return yaml.load(path.read_text(), Loader=yaml.BaseLoader) if strings else yaml.safe_load(path.read_text())


def table(name):
    if name not in _tables:
        path = next((p for p in (TABLES / f"{name}.json", TABLES / f"{name}.yaml") if p.is_file()), None)
        if not path:
            raise ValueError(f"no rules table {name} in {TABLES}")
        _tables[name] = load(path, strings=True)  # strings: "true" stays a word
        for r in _tables[name]["rules"]:
            r["when"] = {k: _condition(v) for k, v in r["when"].items()}
    return _tables[name]


def _condition(c):
    """A condition as read with every scalar a string: a list, a yes/no, or a bound."""
    if isinstance(c, list):
        return c
    if isinstance(c, dict):
        return {k: float(v) for k, v in c.items()}
    return c == "true"


def _holds(cond, value):
    if value is None:
        return None
    if isinstance(cond, list):
        return str(value) in cond
    if isinstance(cond, bool):
        return value is cond
    return ("over" not in cond or value > cond["over"]) and ("upto" not in cond or value <= cond["upto"])


def fact_value(fact, v):
    """An answer as the table compares it (a bool, a number, a value's key), or None when
    it isn't one."""
    s = str(v).strip().lower()
    if fact["type"] == "yes_no":
        return {"true": True, "false": False, "yes": True, "no": False, "si": True, "sì": True}.get(s)
    if fact["type"] == "number":
        try:
            return float(s.replace(",", "."))
        except ValueError:
            return None
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")  # an ask's "tra categorie" is the value tra_categorie
    return s if s in fact["values"] else None


def decide(t, facts):
    """What the table says of a case: the facts some rule still waits on (`ask`, in the
    table's order), the case's `main` pratica (or `none`, no pratica needed) once none is
    missing, the others it adds with it (`also`) or on their own elsewhere (`apart`), the
    rules that refuse it (`refused`) and main rules that disagree."""
    ask, fired = set(), []
    for rule in t["rules"]:
        held = [_holds(c, facts.get(name)) for name, c in rule["when"].items()]
        if False in held:
            continue
        if None in held:
            ask |= {name for name in rule["when"] if facts.get(name) is None}
            continue
        fired.append(rule)
    d = {"ask": [f for f in t["facts"] if f in ask], "main": None, "none": None, "also": [], "apart": [], "refused": [],
         "conflict": []}
    mains, nones = [], []
    for rule in fired:
        then = rule["then"]
        if rule["status"] != "verified":
            d["refused"].append({"rule": rule["id"], "reason": rule["note"]})
        elif "refuse" in then:
            d["refused"].append({"rule": rule["id"], "reason": then["refuse"]})
        elif "none" in then:
            nones.append({"rule": rule["id"], "reason": then["none"]})
        else:
            o = {"rule": rule["id"], "procedure": then["procedure"], "regime": then["regime"]}
            if "portal" in then:
                o["portal"] = then["portal"]
            if then["role"] == "main":
                mains.append(o)
            elif not any(a["procedure"] == o["procedure"] for a in d[then["role"]]):
                d[then["role"]].append(o)
    # A main pratica and "none needed" disagree as two different mains do.
    if len({(m["procedure"], m["regime"]) for m in mains}) + bool(nones) > 1:
        d["conflict"] = [m["rule"] for m in mains] + [n["rule"] for n in nones]
    elif not d["ask"]:
        d["main"] = mains[0] if mains else None
        d["none"] = nones[0] if nones else None
    d["also"] = [a for a in d["also"] if not d["main"] or a["procedure"] != d["main"]["procedure"]]
    return d
