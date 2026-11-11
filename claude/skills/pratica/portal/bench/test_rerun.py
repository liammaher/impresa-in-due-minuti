#!/usr/bin/env python3
"""rerun.py offline: what a batch for the pane holds, and what it refuses before anyone picks a file.

  ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/test_rerun.py

No browser, vault or network. Each case was learned on the real portal (2026-11-11, the procura variants):

  - two steps files of one procedure (a pratica and its procura variant) in one batch are keyed apart in the
    pane (run.py page_bundle: the procedure and a hash of what it fills); until that key, the last one's steps
    ran for both (2026-11-11);
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
    batch.out = out
    q = out / "queue-0.js"
    batch.steps = sorted(p.name for p in (out / "steps").glob("*.js")) if (out / "steps").is_dir() else []
    return msg, q.read_text() if q.exists() else None


@case("two steps files of one procedure in one batch are keyed apart: each runs on its own steps")
def _():
    own = lambda n: f"{n}:answers.json:rehearsals/{n}/fixture.json"
    msg, q = batch("ristorante-fittizio", own(OWN))
    assert msg is None and q, msg
    assert len(batch.steps) == 2 and len(set(batch.steps)) == 2, batch.steps  # two steps files, two keys
    msg, q = batch(own("subingresso-ristorante-procura-fittizio"), own("subingresso-negozio-procura-fittizio"))
    assert msg is None and len(batch.steps) == 2, (msg, batch.steps)


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


@case("loop.js refuses a pane whose stored runner isn't the one the batch was built for (2026-11-11: the pane held another checkout's, 86,595 characters against 80,592)")
def _():
    import re
    import subprocess
    msg, q = batch("ristorante-fittizio")
    assert msg is None, msg
    loop = (batch.out / "loop.js").read_text()
    # the sha check.js holds for the stored runner (runner.js is the script that stores it)
    want = re.search(r'"pv-runner": "([0-9a-f]{64})"', (batch.out / "check.js").read_text())[1]
    assert want in loop and "__RUNNER_SHA__" not in loop, "loop.js doesn't name the runner it was built for"
    if not shutil.which("node"):
        return
    # loop.js in node with a stub page whose stored runner is another: it must not start a run.
    harness = (
        "global.window = {pvBatch: [['x', 'p', {}]]}; global.document = {querySelectorAll: () => []};\n"
        "const store = {'pv-runner': 'window.__pv = {start() { window.started = true; }, wait: async () => ({result: \"filled\"})};'};\n"
        "global.localStorage = {getItem: (k) => store[k] ?? null}; const ss = {}; global.sessionStorage = {getItem: (k) => ss[k] ?? null, setItem: (k, v) => { ss[k] = v; }};\n"
        "global.window.__pv = null; (0, eval)(" + json.dumps(loop) + ");\n"
        "window.pvBatchRun.then((r) => console.log(JSON.stringify({r, started: !!window.started, halted: window.pvBatchHalted})));\n"
    )
    out = subprocess.run(["node", "-e", harness], capture_output=True, text=True, timeout=30)
    got = json.loads(out.stdout.strip().splitlines()[-1]) if out.stdout.strip() else out.stderr
    assert got == {"r": "refused", "started": False, "halted": got["halted"]} and "runner" in got["halted"], got


print(f"{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
