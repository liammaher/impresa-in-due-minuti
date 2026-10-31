#!/usr/bin/env python3
"""Clean reruns of many rehearsals in the Claude browser pane, one after another, nothing
touched between them: the check after a change to the runner, the dictionary or gen.py.

  ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/rerun.py \\
      --values VALUES.json --out DIR [REHEARSAL ...]

Each rehearsal (rehearsals/<name>: its portal-steps.generated.yaml, else portal-steps.yaml,
and its answers file) goes through run.py's page_files, as `run.py page` would. DIR gets:

  check.js      which of runner.js and steps/<name>.js the pane's storage lacks (byte for
                byte), so only those are sent; run it first, on the portal's origin
  runner.js     inpage.js, as install.js stores it
  steps/*.js    each rehearsal's steps (no personal data)
  queue-N.js    the runs' values, in pieces of at most 40 KB (a message the pane takes in one call):
                a procedure's first run whole, each later one as what differs from it (the
                sections it changes, its wizard), so six cases of one pratica cost one and a bit
  loop.js       starts the runs in order and returns at once; each result is kept in the tab
                (sessionStorage pv-batch), so running loop.js again carries on where it stopped
  results.js    the results so far, one line each (`fresh.js` clears them for a new batch)
  record.js     every run's name and result, as JSON (small, no values): `rerun.py --record -` reads
                it pasted on stdin (or --record FILE) and adds each run to its rehearsal's runs.json
                (what schema_branches.py counts as filled)
  pick.js       with --bundle FILE: everything above in FILE, and a box on the page where the
                person picks it once (checked by sha256): no big script copied through the conversation

The pane cuts a call off at 45 s: poll results.js. The values file is what `pvault get`
prints, or a fixture as it is (rehearsals/cila-fittizia/fixture-p6.json: its "fields" are read, so a
person added to it is in the next batch).
No rehearsal named: every one with a generated steps file and the answers file. A rehearsal
named `NAME:ANSWERS.json` runs with that answers file instead (one pratica, several cases: each
its own run, `NAME/ANSWERS` in the results).
"""

import argparse
from datetime import date
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True
import run  # noqa: E402
import yaml  # noqa: E402

REHEARSALS = HERE.parents[4] / "rehearsals"
CHUNK = 40_000


def values_of(run_js, proc):
    """The values run.js starts its run with."""
    line = run_js.splitlines()[1]
    head = f"__pv.start({json.dumps(proc)}, "
    assert line.startswith(head) and line.endswith(")"), "run.js changed shape"
    return line[len(head):-1]


def write_bundle(out, path):
    """runner.js, the steps, the queue and loop.js as one file, and pick.js: a box on the page where
    the person picks that file. Copying a big script into the pane through the conversation can
    garble it (2026-10-30: 24,770 characters arrived for 24,000); a picked file arrives as it is.
    The box clears leftover frames that would cover it (a crawl's), checks the file by sha256,
    and loads it once: a second pick would start a second batch (loop.js refuses that too). A
    bundle is a new batch: it clears the tab's results first (fresh.js), or loop.js skips a run
    whose name an earlier batch left there (2026-10-30: a permesso run skipped, unreported)."""
    import hashlib
    parts = [out / "runner.js"] + sorted((out / "steps").glob("*.js")) + sorted(out.glob("queue-*.js")) + \
        [out / "fresh.js", out / "loop.js"]
    text = "\n;\n".join(p.read_text() for p in parts)
    path.write_text(text)
    sha = hashlib.sha256(text.encode()).hexdigest()
    (out / "pick.js").write_text(f"""if (window.pvBatchBusy) throw new Error("a batch is running in this tab: wait for it, or reload the page to stop it");
document.querySelectorAll("iframe, #pv-pick").forEach((x) => x.remove());
const box = document.createElement("div"); box.id = "pv-pick";
box.style.cssText = "position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:2147483647;background:#fff;border:3px solid #1a4fd6;padding:16px 20px;font:16px sans-serif;box-shadow:0 4px 18px rgba(0,0,0,.3);border-radius:8px;max-width:520px";
box.innerHTML = '<b>Choose <code>{path.name}</code> (once)</b><br><input type="file" accept=".js" style="margin-top:10px"><div style="margin-top:8px;color:#444"></div>';
document.body.appendChild(box);
const [input, msg] = [box.querySelector("input"), box.querySelector("div")];
input.addEventListener("change", async () => {{
  if (window.pvBundleLoaded) {{ msg.textContent = "Already loaded: nothing done."; return; }}
  window.pvBundleLoaded = true; input.disabled = true;
  const text = await input.files[0].text();
  const got = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text)))).map((b) => b.toString(16).padStart(2, "0")).join("");
  if (got !== "{sha}") {{ window.pvBundleLoaded = false; input.disabled = false; msg.textContent = "Not that file (its sha256 differs): nothing loaded."; return; }}
  try {{ window.pvBundle = String((0, eval)(text)); msg.textContent = "Loaded: " + window.pvBundle; setTimeout(() => box.remove(), 4000); }}
  catch (e) {{ window.pvBundle = "error " + e.message; msg.textContent = window.pvBundle; }}
}});
"box shown: pick the file once, then poll results.js"
""")


def compact(queue):
    """Each procedure's first run whole ({"base": values}); each later one as what differs: its
    other keys (the wizard) and the sections it changes ({"set": [[index, section]]})."""
    bases, out = {}, []
    for name, proc, v in queue:
        b = bases.get(proc)
        if b is None or set(v) != set(b) or len(v.get("sections", [])) != len(b.get("sections", [])):
            bases[proc] = v
            out.append([name, proc, {"base": v}])
            continue
        d = {k: x for k, x in v.items() if k != "sections" and x != b[k]}
        d["set"] = [[i, s] for i, (r, s) in enumerate(zip(b["sections"], v["sections"])) if r != s]
        out.append([name, proc, d])
    return out


def record(done, default, day):
    """Each run of a batch (record.js: "pdc-fittizio/answers-deroga", or a rehearsal alone for its
    default answers file) into rehearsals/<name>/runs.json, once per date, case and result."""
    for d in done:
        name, _, stem = d["name"].partition("/")
        f = REHEARSALS / name / "runs.json"
        runs = json.loads(f.read_text()) if f.is_file() else []
        entry = {"date": day, "answers": f"{stem}.json" if stem else default, "result": d["result"],
                 **({"seconds": d["total_seconds"]} if d.get("total_seconds") else {})}
        if not any(all(r.get(k) == entry[k] for k in ("date", "answers", "result")) for r in runs):
            runs.append(entry)
            f.write_text(json.dumps(runs, indent=1) + "\n")
        print(f"{name}: {entry['answers']} {entry['result']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("rehearsals", nargs="*")
    ap.add_argument("--values", type=Path)
    ap.add_argument("--answers", default="answers-p6.json", help="each rehearsal's answers file")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--record", type=Path, help="record.js's output: add each run to its rehearsal's runs.json, and stop")
    ap.add_argument("--date", default=date.today().isoformat(), help="--record: the batch's date")
    ap.add_argument("--file-urls", type=Path, help="JSON {path: https URL}: files the page fetches by link")
    ap.add_argument("--bundle", type=Path, help="also write everything the pane needs as one file here (pick.js loads it)")
    a = ap.parse_args()
    if a.record:
        return record(json.loads(sys.stdin.read() if str(a.record) == "-" else a.record.read_text()), a.answers, a.date)
    if not (a.values and a.out):
        ap.error("--values and --out are required to build a batch")
    names = a.rehearsals or sorted(d.name for d in REHEARSALS.iterdir()
                                   if (d / "portal-steps.generated.yaml").exists() and (d / a.answers).exists())
    fields = json.loads(a.values.read_text())
    if isinstance(fields, dict) and isinstance(fields.get("fields"), list):
        fields = dict(fields["fields"])  # a fixture
    urls = json.loads(a.file_urls.read_text()) if a.file_urls else None
    (a.out / "steps").mkdir(parents=True, exist_ok=True)
    stored, sources, origin, queue, failed = {}, {}, None, [], []
    for item in names:
        name, _, answers = item.partition(":")
        answers = answers or a.answers
        label = f"{name}/{Path(answers).stem}" if answers != a.answers else name
        d = REHEARSALS / name
        steps_file = d / "portal-steps.generated.yaml"
        if not steps_file.exists():
            steps_file = d / "portal-steps.yaml"
        steps = yaml.safe_load(steps_file.read_text())
        values = run.Values(json.loads((d / answers).read_text()), fields=fields, asks=steps.get("asks"))
        try:
            files, parts = run.page_bundle(steps, values, urls=urls)
        except run.StepError as e:
            failed.append(f"{label}: {e}")
            continue
        proc = steps["procedure"]
        (a.out / "runner.js").write_text(files["runner.js"])
        (a.out / "steps" / f"{name}.js").write_text(files["steps.js"] + "'installed'\n")
        stored |= parts
        sources |= {"pv-runner": "runner.js", f"pv-steps:{proc}": f"steps/{name}.js"}
        origin = origin or run.re.match(r"https?://[^/]+", steps["logged_in"])[0]
        queue.append([label, proc, json.loads(values_of(files["run.js"], proc))])
    if failed:
        sys.exit("rerun.py: not written:\n  " + "\n  ".join(failed))
    (a.out / "check.js").write_text(run.check_script(stored, origin, sources, then="the queue files, then loop.js"))
    queue = [json.dumps(q, ensure_ascii=False, separators=(",", ":")) for q in compact(queue)]
    chunks, cur = [], []
    for q in queue:
        if cur and sum(map(len, cur)) + len(q) > CHUNK:
            chunks.append(cur)
            cur = []
        cur.append(q)
    chunks.append(cur)
    for i, c in enumerate(chunks):
        (a.out / f"queue-{i}.js").write_text(
            ("window.pvBatch = [];\n" if i == 0 else "")
            + "window.pvBatch = window.pvBatch.concat([" + ",".join(c) + "]);\nwindow.pvBatch.length\n")
    (a.out / "loop.js").write_text("""if (!window.__pv) (0, eval)(localStorage.getItem('pv-runner'));
// A run's values: whole ({base}), or what differs from its procedure's first run.
if (window.pvBatch && window.pvBatch.some(([, , d]) => d.base || d.set)) {
  const bases = {};
  window.pvBatch = window.pvBatch.map(([n, p, d]) => {
    if (d.base) { bases[p] = d.base; return [n, p, d.base]; }
    const v = JSON.parse(JSON.stringify(bases[p]));
    for (const [i, s] of d.set || []) v.sections[i] = s;
    for (const k of Object.keys(d)) if (k !== "set") v[k] = d[k];
    return [n, p, v];
  });
}
// One loop per tab: a second one would drive the same runner and file its runs' results under
// its own names (2026-10-30, a bundle loaded twice). Running loop.js again while one runs is a no-op.
var pvAlready = !!window.pvBatchBusy;  // var: a second run of this script redeclares it
if (!pvAlready) window.pvBatchRun = (async () => {
  window.pvBatchBusy = true;
  const done = JSON.parse(sessionStorage.getItem("pv-batch") || "[]");
  for (const [name, proc, values] of window.pvBatch || []) {
    if (done.some((d) => d.name === name)) continue;
    __pv.start(proc, values);
    let r; do { r = await __pv.wait(30000); } while (r.result === "running");
    // moved and loose: the ids that named another box, the labels worth a look (what a gen.py
    // change is checked by). gaps: a stopped run's empty boxes the portal wants (labels only,
    // from its snapshot, which holds no value), so the stop names them without opening the draft.
    const gaps = ((r.snapshot && r.snapshot.boxes) || []).filter((b) => b.required && b.state !== "filled"
      && b.state !== "checked").map((b) => `${b.kind} ${b.label || b.id}`);
    done.push({ name, result: r.result, error: r.error || null, at: r.at, sections: r.sections.length,
      verify_seconds: r.verify_seconds ?? null, total_seconds: r.total_seconds, url: r.url,
      moved: r.moved || [], loose: r.loose || [], retries: (r.retries || []).length, ...(gaps.length ? { gaps } : {}) });
    sessionStorage.setItem("pv-batch", JSON.stringify(done));
  }
  // Each filled run drew the person's review over the portal: nobody reads it in a batch, and it
  // covers what the next click needs (2026-10-31).
  document.querySelectorAll('[data-pv="review"], iframe[data-pv="runner"]').forEach((e) => e.remove());
  return "done";
})().finally(() => { window.pvBatchBusy = false; });
pvAlready ? "a batch is already running in this tab: nothing started" : `started: ${(window.pvBatch || []).length} queued`
""")
    (a.out / "results.js").write_text("""await new Promise((r) => setTimeout(r, 35000));  // the pane cuts a call at 45 s
const done = JSON.parse(sessionStorage.getItem("pv-batch") || "[]");
JSON.stringify({ done: done.length, of: (window.pvBatch || []).length, running: !!window.pvBatchBusy,
  filled: done.filter((d) => d.result === "filled").length,
  stopped: done.filter((d) => d.result !== "filled").map((d) => [d.name, d.error, d.at && d.at.section, d.gaps || []]),
  moved: done.filter((d) => (d.moved || []).length).map((d) => [d.name, d.moved]),
  loose: done.filter((d) => (d.loose || []).length).map((d) => [d.name, d.loose]) })
""")
    (a.out / "record.js").write_text('JSON.stringify(JSON.parse(sessionStorage.getItem("pv-batch") || "[]")'
                                      '.map((d) => ({ name: d.name, result: d.result, total_seconds: d.total_seconds })))\n')
    (a.out / "fresh.js").write_text('sessionStorage.removeItem("pv-batch"); "cleared"\n')
    if a.bundle:
        write_bundle(a.out, a.bundle)
    print(f"{a.out}: {len(names)} rehearsals, {len(chunks)} queue file(s). In the pane, on {origin}: "
          "check.js, then the files it names, then the queue files, loop.js, and results.js until done.")


if __name__ == "__main__":
    main()
