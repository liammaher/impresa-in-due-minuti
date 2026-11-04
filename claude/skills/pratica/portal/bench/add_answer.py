#!/usr/bin/env python3
"""A new question's answer in every existing case, as text: what the cases did before, so their
plans stay as they were (bench/plan_diff.py) and their recorded runs still stand.

    ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/add_answer.py KEY VALUE [REHEARSAL ...]

VALUE is JSON (false, true, "text"). Every answers*.json of the rehearsals whose generated steps ask
KEY (or those named) gets `"KEY": VALUE` before its closing brace, unless it has KEY: rewriting a file
with json.dump reflows its inline lists, and the diff of 84 files buries the answers (2026-11-01).
A combination's answers-p6.json is its main pratica's changed by its parts: where the main pratica
doesn't answer KEY, its part's `answers` gets it (the CIL with its landscape authorization, 2026-11-02,
and the bollo exemption on ten combinations), then each combination's answers are written again
(regen.py).
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))  # regen.py: -I leaves the script's folder off the path (2026-11-03)
sys.dont_write_bytecode = True
import gen  # noqa: E402
import regen  # noqa: E402

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
    combos = []
    for d in sorted(REHEARSALS.iterdir()):
        recipe = d / "recipe.yaml"
        r = (yaml.safe_load(recipe.read_text()) or {}) if recipe.exists() else {}
        if d.name not in names or not r.get("extends") or not gen.resolved(r).get("answers"):
            continue
        combos.append(d.name)
        parents = r.get("extends") or []
        parents = [parents] if isinstance(parents, str) else parents
        main = [p for p in parents if not p.startswith("parts/")]
        if main and a.key not in json.loads((REHEARSALS / main[0] / "answers-p6.json").read_text()) \
                and a.key not in gen.resolved(r)["answers"]:
            for part in (p for p in parents if p.startswith("parts/")):
                if add_to_part(HERE.parent / f"{part}.yaml", a.key, a.value):
                    print(f"  {part}: answers {a.key} (its main pratica {main[0]} doesn't)")
    if combos:
        written, refused = regen.regenerate(combos)
        for name, why in refused.items():
            print(f"  {name}: gen.py refuses it: {why}")
        print(f"  {len(written)} combination file(s) written again")


def add_to_part(path, key, value):
    """KEY at the end of a part's `answers:` block, as text; False when the part has it already."""
    lines = path.read_text().split("\n")
    start = lines.index("answers:")
    if key in (yaml.safe_load("\n".join(lines)).get("answers") or {}):
        return False
    end = start + 1
    while end < len(lines) and (lines[end].startswith(" ") or lines[end].startswith("#")):
        end += 1
    while lines[end - 1].strip() == "" or lines[end - 1].lstrip().startswith("#"):
        end -= 1
    lines.insert(end, f"  {key}: {json.dumps(value, ensure_ascii=False)}")
    path.write_text("\n".join(lines))
    assert yaml.safe_load(path.read_text())["answers"][key] == value, path
    return True

if __name__ == "__main__":
    main()
