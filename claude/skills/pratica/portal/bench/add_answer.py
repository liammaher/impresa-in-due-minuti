#!/usr/bin/env python3
"""A new question's answer in every existing case, as text: what the cases did before, so their
plans stay as they were (bench/plan_diff.py) and their recorded runs still stand.

    ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/add_answer.py KEY VALUE [REHEARSAL ...]

VALUE is JSON (false, true, "text"). Every answers*.json of the rehearsals whose generated steps ask
KEY (or those named) gets `"KEY": VALUE` before its closing brace, unless it has KEY: rewriting a file
with json.dump reflows its inline lists, and the diff of 84 files buries the answers (2026-11-01).
A combination's answers-p6.json is its main pratica's changed by its parts (gen.py --answers): this
says which to regenerate, and which main pratica doesn't ask KEY, so its part's `answers` must carry
it (the CIL with its landscape authorization, 2026-11-02).
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True
import gen  # noqa: E402

REHEARSALS = HERE.parents[4] / "rehearsals"


def asks(name):
    f = REHEARSALS / name / "portal-steps.generated.yaml"
    return set((yaml.safe_load(f.read_text()) or {}).get("asks", {})) if f.exists() else set()


def add(path, key, value):
    """The file with the answer added as text, or None when it has one already."""
    text = path.read_text()
    old = json.loads(text)
    if key in old:
        return None
    indent = re.match(r"\{\n([ \t]+)\"", text)
    if not indent:
        sys.exit(f"{path}: not one key per line: add {key} by hand")
    body = text[:text.rstrip().rfind("}")].rstrip()
    new = body + (",\n" if old else "\n") + f"{indent[1]}{json.dumps(key)}: {json.dumps(value, ensure_ascii=False)}\n}}\n"
    assert json.loads(new) == {**old, key: value}, path
    return new


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("key")
    ap.add_argument("value", type=json.loads)
    ap.add_argument("rehearsals", nargs="*")
    a = ap.parse_args()
    names = a.rehearsals or sorted(d.name for d in REHEARSALS.iterdir() if a.key in asks(d.name))
    changed = []
    for name in names:
        for f in sorted((REHEARSALS / name).glob("answers*.json")):
            new = add(f, a.key, a.value)
            if new is not None:
                f.write_text(new)
                changed.append(f)
    print(f"{len(changed)} answers file(s) in {len(names)} rehearsal(s) now answer {a.key}")
    for d in sorted(REHEARSALS.iterdir()):
        recipe = d / "recipe.yaml"
        r = (yaml.safe_load(recipe.read_text()) or {}) if recipe.exists() else {}
        if d.name not in names or not r.get("extends") or not gen.resolved(r).get("answers"):
            continue
        parents = r.get("extends") or []
        main = [p for p in ([parents] if isinstance(parents, str) else parents) if not p.startswith("parts/")]
        lacks = main and a.key not in json.loads((REHEARSALS / main[0] / "answers-p6.json").read_text()) \
            and a.key not in gen.resolved(r)["answers"]
        print(f"  {d.name}: regenerate its answers-p6.json (gen.py --answers)"
              + (f"; its main pratica {main[0]} doesn't answer {a.key}: put it in the part's `answers`" if lacks else ""))


if __name__ == "__main__":
    main()
