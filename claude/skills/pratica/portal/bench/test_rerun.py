#!/usr/bin/env python3
"""rerun.py offline: what a batch for the pane holds, and what it refuses before anyone picks a file.

  ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/test_rerun.py

No browser, vault or network. Each case was learned on the real portal (2026-11-11, the procura variants):

  - the pane keeps steps under the procedure's key alone, so two steps files of one procedure in one batch
    share it and the last wins for every run of that procedure: refused, run them in batches of their own;
  - a SUAP rehearsal answers in answers.json (the SUE's in answers-p6.json): named alone it is found, and
    recorded under its own file;
  - values that are the rehearsal's own fixture.json are what its run is recorded on (no "@" in the name);
  - a client company with a REA can't pass the portal's check with made-up data: refused, not sent.
"""
import io
import json
import os
import shutil
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import rerun  # noqa: E402

ROOT = HERE.parents[4]
REH = ROOT / "rehearsals"
OWN = "ristorante-procura-fittizio"
results = []


def case(name):
    def deco(fn):
        try:
            fn()
            print(f"ok    {name}")
            results.append(True)
        except Exception as e:  # noqa: BLE001
            print(f"FAIL  {name}: {type(e).__name__}: {e}")
            results.append(False)
    return deco


def batch(*args, values=None):
    """rerun.py's main with these arguments: (exit message or None, the queue file's text)."""
    out = Path(tempfile.mkdtemp())
    argv = ["rerun.py", "--values", str(values or REH / "pizzeria-fittizia" / "fixture.json"), "--out", str(out), *args]
    old, here = sys.argv, os.getcwd()
    sys.argv = argv
    os.chdir(ROOT)
    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            try:
                rerun.main()
                msg = None
            except SystemExit as e:
                msg = str(e.code) if e.code not in (0, None) else None
    finally:
        sys.argv = old
        os.chdir(here)
    q = out / "queue-0.js"
    return msg, q.read_text() if q.exists() else None


@case("two steps files of one procedure in one batch are refused: they share the pane's one key")
def _():
    own = lambda n: f"{n}:answers.json:rehearsals/{n}/fixture.json"
    msg, _q = batch("ristorante-fittizio", own(OWN))
    assert msg and "separate batches" in msg and "scia-somministrazione" in msg, msg
    msg, _q = batch(own("subingresso-ristorante-procura-fittizio"), own("subingresso-negozio-procura-fittizio"))
    assert msg and "separate batches" in msg, msg


@case("each of them alone builds")
def _():
    msg, q = batch("ristorante-fittizio")
    assert msg is None and q, msg
    for n in (OWN, "subingresso-negozio-procura-fittizio"):
        msg, q = batch(f"{n}:answers.json:rehearsals/{n}/fixture.json")
        assert msg is None and q, (n, msg)


@case("a SUAP rehearsal is found by its answers.json, and its own fixture keeps its name for the record")
def _():
    msg, q = batch(f"{OWN}:answers.json:rehearsals/{OWN}/fixture.json", values=REH / OWN / "fixture.json")
    assert msg is None and q, msg
    assert f"{OWN}/answers" in q and "@fixture" not in q, q[:200]  # recorded: not "...answers@fixture"
    # other values than the rehearsal's own are another case: named by them, and not recorded
    other = Path(tempfile.mkdtemp()) / "other.json"
    shutil.copy(REH / OWN / "fixture.json", other)
    msg, q = batch(f"{OWN}:answers.json:{other}", values=REH / OWN / "fixture.json")
    assert msg is None and "@other" in q, msg


@case("a client company with a REA can't pass the portal with made-up data: refused before a file is picked")
def _():
    fixture = json.loads((REH / OWN / "fixture.json").read_text())
    fixture["fields"] += [["trattoria:business.rea", "NA-1234567"], ["trattoria:business.cciaa", "NA"]]
    tmp = Path(tempfile.mkdtemp()) / "fixture.json"
    tmp.write_text(json.dumps(fixture))
    msg, q = batch(OWN, values=tmp)
    assert msg and "made-up data can't pass" in msg and q is None, msg


@case("record: a SUAP rehearsal's run is filed under its own answers file, once")
def _():
    real = rerun.REHEARSALS
    tmp = Path(tempfile.mkdtemp())
    (tmp / "suap-x").mkdir()
    (tmp / "suap-x" / "answers.json").write_text("{}")
    (tmp / "sue-x").mkdir()
    (tmp / "sue-x" / "answers-p6.json").write_text("{}")
    rerun.REHEARSALS = tmp
    try:
        with redirect_stdout(io.StringIO()):
            for _ in range(2):
                rerun.record([{"name": "suap-x", "result": "filled", "total_seconds": 5.0},
                              {"name": "sue-x", "result": "filled", "total_seconds": 6.0},
                              {"name": "suap-x/answers@fixture", "result": "filled"}], "answers-p6.json", "2026-11-11")
        suap = json.loads((tmp / "suap-x" / "runs.json").read_text())
        sue = json.loads((tmp / "sue-x" / "runs.json").read_text())
        assert [r["answers"] for r in suap] == ["answers.json"] and [r["answers"] for r in sue] == ["answers-p6.json"], (suap, sue)
    finally:
        rerun.REHEARSALS = real
        shutil.rmtree(tmp, ignore_errors=True)


print(f"{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
