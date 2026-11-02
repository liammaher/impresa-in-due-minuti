#!/usr/bin/env python3
"""Every rehearsal's generated steps file, and each combination's answers-p6.json, written again
from the dictionary, the recipes and the crawls: what README step 3 asks after any change to them.

    ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/regen.py [--check] [REHEARSAL ...]

It prints the files it changed and every rehearsal gen.py refuses (with gen.py's reasons), and
exits 1 if any is refused. --check writes nothing and exits 1 if a file would change. A
combination's answers come from its main pratica's, so the main pratiche go first. Look at the diff
after: an unrelated steps file that changes is a regression until shown otherwise (plan_diff.py).
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True
import gen  # noqa: E402

REHEARSALS = HERE.parents[4] / "rehearsals"


def regenerate(names=None, check=False):
    """(changed paths, {rehearsal: gen.py's refusal})."""
    dirs = [d for d in sorted(REHEARSALS.iterdir()) if (d / "recipe.yaml").exists()
            and (d / "portal-steps.generated.yaml").exists() and (not names or d.name in names)]
    recipes = {d: gen.load_yaml(d / "recipe.yaml") for d in dirs}
    changed, refused = [], {}
    for d in sorted(dirs, key=lambda d: bool(recipes[d].get("extends"))):
        try:
            files = {d / "portal-steps.generated.yaml": gen.dump(gen.generate(recipes[d]))}
            answers = gen.combo_answers(recipes[d]) if recipes[d].get("extends") else None
        except gen.GenError as e:
            refused[d.name] = str(e)
            continue
        if answers is not None:
            files[d / "answers-p6.json"] = gen.dump_answers(answers)
        for path, text in files.items():
            if path.read_text() != text:
                changed.append(path)
                if not check:
                    path.write_text(text)
    return changed, refused


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if a file would change")
    ap.add_argument("rehearsals", nargs="*")
    a = ap.parse_args()
    changed, refused = regenerate(a.rehearsals, a.check)
    for name, why in refused.items():
        print(f"refused {name}:\n  " + why.replace("\n", "\n  "))
    for p in changed:
        print(("would change " if a.check else "wrote ") + str(p.relative_to(REHEARSALS.parent)))
    print(f"{len(changed)} file(s) {'to change' if a.check else 'changed'}, {len(refused)} refused")
    sys.exit(1 if refused or (a.check and changed) else 0)


if __name__ == "__main__":
    main()
