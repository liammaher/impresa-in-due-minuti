#!/usr/bin/env python3
"""What a dictionary, gen.py or recipe change does to each case: its fill plan before and after.

    ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/plan_diff.py [--since REF] [rehearsal ...]

A steps file's diff is noisy (ids that go by label, conditions reworded); a case's plan is what
the run types and ticks for its answers (run.py plan, on the P6 fixture). For every answers file
of the rehearsals whose steps file changed since REF (default HEAD), or those named, this prints
the plan's lines that differ, and a case that is new or no longer plans. A new question answered
as the case did before leaves its plan unchanged: that is how existing cases keep their recorded
runs (2026-11-01: 119 cases, only a box those forms don't have dropped). No browser, no network.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RUN = HERE.parent / "run.py"
FIXTURE = "rehearsals/cila-fittizia/fixture-p6.json"


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def plan(steps, answers):
    """run.py plan's lines, or its error as one line."""
    r = subprocess.run([sys.executable, str(RUN), "plan", "--steps", steps, "--answers", answers,
                        "--values", FIXTURE, "--made-up"], cwd=ROOT, capture_output=True, text=True)
    return r.stdout.splitlines() if r.returncode == 0 else [f"(no plan: {(r.stderr or r.stdout).strip().splitlines()[-1:]})"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", default="HEAD")
    ap.add_argument("rehearsals", nargs="*")
    a = ap.parse_args()
    names = a.rehearsals or sorted({Path(p).parent.name for p in git(
        "diff", "--name-only", a.since, "--", "rehearsals/*/portal-steps.generated.yaml").stdout.split()})
    changed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for name in names:
            steps = f"rehearsals/{name}/portal-steps.generated.yaml"
            old_steps = Path(tmp, "steps.yaml")
            old = git("show", f"{a.since}:{steps}")
            old_steps.write_text(old.stdout if old.returncode == 0 else "")
            for answers in sorted((ROOT / "rehearsals" / name).glob("answers*.json")):
                rel = os.path.relpath(answers, ROOT)
                was = git("show", f"{a.since}:{rel}")
                after = plan(steps, rel)
                if was.returncode != 0 or old.returncode != 0:
                    print(f"== {rel}: new" + ("" if not after[0].startswith("(no plan") else f" {after[0]}"))
                    continue
                old_answers = Path(tmp, "answers.json")
                old_answers.write_text(was.stdout)
                before = plan(str(old_steps), str(old_answers))
                if before != after:
                    changed += 1
                    gone = [x for x in before if x not in after]
                    came = [x for x in after if x not in before]
                    print(f"== {rel}")
                    print("\n".join([f"  - {x}" for x in gone] + [f"  + {x}" for x in came]))
    print(f"{changed} case(s) plan differently since {a.since}")


if __name__ == "__main__":
    main()
