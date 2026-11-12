#!/usr/bin/env python3
"""Every rehearsal's steps file, the steps lock, and each combination's answers-p6.json, written
again from the dictionary, the recipes and the crawls: what README step 3 asks after any change
to them.

    ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/regen.py [--check] [REHEARSAL ...]

The steps files (rehearsals/*/portal-steps.generated.yaml) are build outputs, never committed:
rehearsals/steps.lock is, one sha256 per steps file, so the lock's diff names the pratiche a
change touches and `bench/plan_diff.py` shows what it does to each case. It prints the lock
lines and answers files it changed and every rehearsal gen.py refuses (with gen.py's reasons),
and exits 1 if any is refused. --check writes nothing and exits 1 if the lock or an answers file
would change (test_gen runs it). A combination's answers come from its main pratica's, so the
main pratiche go first. An unrelated pratica whose hash changes is a regression until shown
otherwise (plan_diff.py).
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
    """(changed: the rehearsals whose lock line or answers file changed, {rehearsal: refusal})."""
    dirs = [d for d in sorted(REHEARSALS.iterdir()) if (d / "recipe.yaml").exists() and (not names or d.name in names)]
    recipes = {d: gen.load_yaml(d / "recipe.yaml") for d in dirs}
    lock = gen.read_lock(REHEARSALS / gen.LOCK.name)
    new_lock = dict(lock) if names else {}
    changed, refused = [], {}
    for d in sorted(dirs, key=lambda d: bool(recipes[d].get("extends"))):
        try:
            steps = gen.dump(gen.generate(recipes[d]))
            answers = gen.combo_answers(recipes[d]) if recipes[d].get("extends") else None
        except gen.GenError as e:
            refused[d.name] = str(e)
            new_lock.pop(d.name, None) if d.name not in lock else new_lock.__setitem__(d.name, lock[d.name])
            continue
        new_lock[d.name] = gen.sha256(steps)
        if new_lock[d.name] != lock.get(d.name):
            changed.append(f"{d.name}/{gen.STEPS} (steps.lock)")
        if not check:
            f = d / gen.STEPS
            if not f.is_file() or f.read_text() != steps:
                f.write_text(steps)
        if answers is not None:
            f, text = d / "answers-p6.json", gen.dump_answers(answers)
            if f.read_text() != text:
                changed.append(f"{d.name}/answers-p6.json")
                if not check:
                    f.write_text(text)
    gone = [n for n in lock if n not in new_lock]
    changed += [f"{n}/{gen.STEPS} (no recipe: out of steps.lock)" for n in gone]
    if not check and (changed or not (REHEARSALS / gen.LOCK.name).is_file()):
        (REHEARSALS / gen.LOCK.name).write_text(gen.lock_text(new_lock))
    return changed, refused


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if the lock or an answers file would change")
    ap.add_argument("rehearsals", nargs="*")
    a = ap.parse_args()
    # A name that is no rehearsal used to do nothing and say "0 file(s) changed" (2026-11-12: zsh doesn't split an unquoted
    # $NAMES, so one long "name" matched nothing and a renamed ask went unregenerated).
    unknown = [n for n in a.rehearsals if not (REHEARSALS / n / "recipe.yaml").exists()]
    if unknown:
        sys.exit("regen.py: no rehearsal named " + ", ".join(repr(n) for n in unknown) + " (in zsh, expand a list of names with ${=NAMES})")
    changed, refused = regenerate(a.rehearsals, a.check)
    for name, why in refused.items():
        print(f"refused {name}:\n  " + why.replace("\n", "\n  "))
    for p in changed:
        print(("would change " if a.check else "wrote ") + p)
    print(f"{len(changed)} file(s) {'to change' if a.check else 'changed'}, {len(refused)} refused")
    sys.exit(1 if refused or (a.check and changed) else 0)


if __name__ == "__main__":
    main()
