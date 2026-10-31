#!/usr/bin/env python3
"""The portal catalogue's bookkeeping, around crawl.js's batch (`__crawl.batch`).

    catalogue.py ops sue|suap [--sectors N,M] [--common]   the batch's `ops`, as JSON
    catalogue.py ops sue --combo NAME MAIN OTHER           two operations in one pratica, with the procura
                                                           scelta and its attachments screen (crawl.js `also`)
    catalogue.py known                                     fingerprints of the stored crawls
    catalogue.py import EXPORT.json|-                      a batch's results into sections/ (export.js's
                                                           file, or print.js's text: its sha256 checked)
    catalogue.py count                                     distinct sections and their uses
    catalogue.py drift EXPORT.json                         a check batch against the stored crawls
    catalogue.py pane DIR                                  the pane's scripts: install.js stores wizard.js
                                                           and crawl.js in localStorage, load.js runs them
                                                           (an op with `like`: against that pratica, into same.json)
    catalogue.py pane DIR --bundle FILE --ops OPS.json     a batch as one file the person picks (pick.js),
        [--draft NAME] [--depth 3] [--fresh]               status.js to poll, export.js to save the results
                                                           (print.js prints a small batch's, sha256 first)

A section's fingerprint is what it shows before any choice (ids, kinds, labels, lengths,
short lists), hashed as crawl.js does: the same fingerprint is the same section, whatever
pratica it sits in, and a different one for a stored section means the portal changed it.
"""
import argparse
import collections
import datetime
import hashlib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAT = HERE / "catalogue" / "F839"
SECTIONS = CAT / "sections"
# Operations a check found to be another sector's pratica, unchanged ({"same": {name: like}}),
# and those that differ and need a crawl of their own ("different").
SAME = CAT / "same.json"
DECLARATIONS = re.compile(r"consapevolezza|informativa sulla privacy|requisiti di o|altre dichiarazioni|"
                          r"dichiarazioni ai sensi dell'art\. 6|rispetto sulle tasse|art\. ?75", re.I)
# The SUE's pratiche crawled one by one before the batch, by the names recipes use.
SUE_NAMES = {
    "Comunicazione di Inizio Lavori per opere temporanee (C.I.L.)": "cil",
    "Comunicazione Inizio Lavoro Asseverata (C.I.L.A.)": "cila",
    "Segnalazione Certificata di Inizio Attività Edilizia (S.C.I.A.)": "scia",
    "Comunicazione inizio lavori": "inizio-lavori",
    "Comunicazione di fine lavori": "fine-lavori",
    "Segnalazione Certificata per l'Agibilità": "agibilita",
}


def sportello(name):
    """A crawl's sportello, by its name: the batch's start with it, the first ones are SUE's
    but for the hairdresser's."""
    return "suap" if name.startswith("suap") or name == "acconciatore" else "sue"


def fingerprint(fields):
    basis = [[f["id"], f["kind"], f["label"], f.get("context") or "", f.get("max") or 0,
              f["options"] if isinstance(f.get("options"), list) else []]
             for f in fields if f["kind"] != "message"]
    raw = json.dumps(basis, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def slug(s, n=48):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\([^)]*\)", "", s)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:n].strip("-")


def crawls():
    return {p.stem: json.loads(p.read_text()) for p in sorted(SECTIONS.glob("*.json"))}


def resolve(ref, cache=None, sections=None):
    """`pratica#section` to that crawled section, following a reference to a reference."""
    cache = cache if cache is not None else {}
    for _ in range(10):
        name, _, section = ref.partition("#")
        if name not in cache:
            cache[name] = json.loads(((sections or SECTIONS) / f"{name}.json").read_text())
        s = next(s for s in cache[name]["sections"] if s["section"] == section and not s.get("scelta")) \
            if any(s["section"] == section and not s.get("scelta") for s in cache[name]["sections"]) \
            else next(s for s in cache[name]["sections"] if s["section"] == section)
        if not s.get("same_as"):
            return s
        ref = s["same_as"]
    raise ValueError(f"{ref}: references go round")


def cmd_ops(args):
    ops, seen = ops_of(args), collections.Counter()
    for o in ops:  # two labels can slug alike
        seen[o["name"]] += 1
        if seen[o["name"]] > 1:
            o["name"] += f"-{seen[o['name']]}"
    return ops


PROCURA = "IL PRESENTATORE DELLA DOMANDA È UN PROFESSIONISTA / ALTRO SOGGETTO MUNITO DI PROCURA SPECIALE"


def sue_name(label):
    """A SUE operation's crawl, by the name recipes use."""
    return SUE_NAMES.get(label) or "sue-" + slug(label, 72)


def ops_of(args):
    if args.sportello == "sue" and args.combo:
        # Two operations in one pratica (a building pratica with its landscape authorization):
        # only the scelte a recipe takes (the procura) are tried, and the attachments screen is
        # read on the way, so the combination is one batch (2026-10-31: by hand before). --combo
        # repeats: several combinations in one batch (2026-10-31: two outputs joined by hand).
        w = json.loads((CAT / "sue-wizard.json").read_text())
        by = {o["label"]: o for o in w["operations"]}
        path = lambda l: f"{by[l]['group']} › {l}"
        ops = []
        for name, *labels in args.combo:
            missing = [l for l in labels if l not in by]
            if missing or len(labels) < 2:
                sys.exit(f"--combo {name}: " + (f"not an operation of the SUE's wizard: {missing}" if missing else "give its operations, the main one first"))
            ops.append({"name": name, "sector": w["sector"], "path": path(labels[0]), "also": [path(l) for l in labels[1:]],
                        "scelte": args.scelta or [PROCURA], "slots": True})
        return ops
    if args.sportello == "sue":
        w = json.loads((CAT / "sue-wizard.json").read_text())
        have = {p.stem for p in SECTIONS.glob("*.json")}
        ops = []
        for o in w["operations"]:
            name = sue_name(o["label"])
            if name in have and not args.all:
                continue
            ops.append({"name": name, "sector": w["sector"], "path": f"{o['group']} › {o['label']}"})
        return ops
    w = json.loads((CAT / "suap-wizard.json").read_text())
    sectors = w["sectors"]
    nth = collections.Counter()
    for s in sectors:
        s["nth"] = nth[s["sector"]]
        nth[s["sector"]] += 1
    pick = [int(x) for x in args.sectors.split(",")] if args.sectors else range(len(sectors))
    ops = []
    if args.common:
        # The operations most sectors offer, once each, under the first sector given.
        s = sectors[pick[0]]
        for o in w["common"]:
            ops.append({"name": "suap-common-" + slug(o.split(" › ", 1)[-1], 60), "sector": s["sector"],
                        "sector_nth": s["nth"], "path": o})
        return ops
    for i in pick:
        s = sectors[i]
        for o in s["operations"]:
            ops.append({"name": f"suap-{i:03d}-" + slug(o.split(": ", 1)[1].split(" › ")[-1], 50),
                        "sector": s["sector"], "sector_nth": s["nth"], "path": o})
    return ops


def cmd_known(_):
    known = {}
    for name, c in crawls().items():
        for s in c["sections"]:
            if s.get("fields") and not s.get("error") and not s.get("same_as"):
                known.setdefault(fingerprint(s["fields"]), f"{name}#{s['section']}")
    return known


def cmd_import(args):
    """Each pratica of an export (localStorage `crawl:op:*`) to sections/<name>.json."""
    text = sys.stdin.read() if args.export == "-" else Path(args.export).read_text()
    # print.js's text: its sha256 first, so a copy that arrived changed is refused. Its JSON never
    # ends in a newline, but a heredoc or a paste adds one (2026-10-31: a good copy refused).
    head, _, rest = text.partition("\n")
    rest = rest.rstrip("\r\n")
    if re.fullmatch(r"[0-9a-f]{64}", head.strip()):
        if hashlib.sha256(rest.encode()).hexdigest() != head.strip():
            sys.exit("not the text print.js printed (its sha256 differs): nothing imported")
        text = rest
    data = json.loads(text)
    out = []
    for key, r in sorted(data.items()):
        if not key.startswith("crawl:op:"):
            continue
        r = r if isinstance(r, dict) else json.loads(r)
        if r.get("error"):
            out.append(f"{r['name']}: not imported ({r['error']})")
            continue
        # The login's name and CF must never be in a crawl (crawl.js stores only that a box was
        # prefilled): CATALOGUE_PRIVATE is a pattern for them, kept out of the repo.
        private = os.environ.get("CATALOGUE_PRIVATE")
        if private and re.search(private, json.dumps(r, ensure_ascii=False), re.I):
            sys.exit(f"{r['name']}: holds the login's name or CF, not imported")
        depth = r.get("depth") or args.depth or 2
        doc = {"crawled": r["crawled"], "by": f"crawl.js batch, depth {depth}",
               "pratica": f"{sportello(r['name']).upper()}: {r['operation']}"
                          + (f" (sector {r['sector']})" if r.get("sector") else ""),
               "seconds": r.get("seconds")}
        if r.get("also"):
            ops = [o.split(" › ")[-1] for o in [r["operation"], *r["also"]]]
            doc["pratica"] = (f"{sportello(r['name']).upper()}: {len(ops)} operations in one pratica: " + " + ".join(ops)
                              + "".join(f", with the scelta {v['option']}" for v in r.get("variants", [])))
            doc["note"] = ("Every section is one of the operations' own, the same fingerprint: the combination is "
                           "their union, in this order. A recipe names every operation and extends the main one's.")
            doc["also"] = r["also"]
        for k in ("refused", "pratica", "screens", "variants"):
            if k in r:
                doc["generated" if k == "pratica" else k] = r[k]
        doc["sections"] = r["sections"]
        if r.get("slots"):
            # Read on an empty draft: the slots its answers add are missing, so the main
            # operation's own (read on its filled drafts) are added, as a run would meet them.
            main = SECTIONS / f"{sue_name(r['operation'].split(' › ')[-1])}.json"
            own = json.loads(main.read_text()).get("slots", {}).get("Gestione degli allegati", []) if r.get("also") and main.exists() else []
            have = {x["title"] for x in r["slots"]}
            added = [{k: v for k, v in x.items() if k != "id"} for x in own if x["title"] not in have]
            doc["slots"] = {"Gestione degli allegati": r["slots"] + added}
            doc["slots_note"] = (f"read {r['crawled'][:10]} on the empty draft (crawl.js `slots`)"
                                 + (f", plus the {len(added)} its answers add from {main.stem}'s own screen" if added else ""))
        if r.get("slots_error"):
            out.append(f"{r['name']}: the attachments screen wasn't read ({r['slots_error']}): read it again")
        old = SECTIONS / f"{r['name']}.json"
        if old.exists():  # a crawl again keeps the attachments slots read on their screen
            prev = json.loads(old.read_text())
            doc.update({k: prev[k] for k in ("slots", "slots_note") if k in prev and k not in doc})
        (SECTIONS / f"{r['name']}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        drift = CAT / "drift.json"  # a new crawl settles what the last check found
        if drift.exists():
            d = json.loads(drift.read_text())
            if d["pratiche"].pop(r["name"], None) is not None:
                drift.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
        new = sum(1 for s in r["sections"] if s.get("fields"))
        out.append(f"{r['name']}: {len(r['sections'])} sections, {new} new")
    return out


def covered(section, dictionary):
    """Whether the dictionary fills every box of this crawled section (gen.py's own test),
    for the person or for the business declaring."""
    import gen
    if DECLARATIONS.search(section["section"]):
        return True
    for subject in (None, "impresa"):
        for entry, as_name in gen.dictionary_entries(dictionary["sections"], section["section"]):
            if entry.get("subject", subject) != subject:
                continue
            if entry.get("omit"):
                return True
            _, problems, _ = gen.fill(entry, as_name, section, {"subject": subject} if subject else {}, section["section"])
            if not problems:
                return True
    return False


def cmd_count(args):
    """Each distinct section (by fingerprint), how many pratiche use it, and whether the
    dictionary fills it."""
    import gen
    dictionary = gen.load_yaml(HERE / "dictionary" / "fnsuap.yaml")
    uses, names, where, cache = collections.Counter(), collections.defaultdict(set), {}, {}
    pratiche, by = collections.defaultdict(set), collections.defaultdict(collections.Counter)
    by_name = collections.defaultdict(collections.Counter)
    stored = crawls()
    alias = json.loads(SAME.read_text())["same"] if SAME.exists() else {}
    for name, c in list(stored.items()) + [(n, stored[l]) for n, l in alias.items() if l in stored]:
        cache.setdefault(name, c)
        sp = sportello(name)
        for s in c["sections"]:
            if s.get("skipped") or s.get("error"):
                continue
            if s.get("same_as"):
                fp = s.get("fingerprint") or fingerprint(resolve(s["same_as"], cache)["fields"])
            else:
                fp = s.get("fingerprint") or fingerprint(s["fields"])
                where.setdefault(fp, f"{name}#{s['section']}")
            uses[fp] += 1
            by[fp][sp] += 1
            names[fp].add(s["section"])
            by_name[fp][(sp, s["section"])] += 1
            pratiche[fp].add(sp)
    rows = []
    for fp, n in uses.most_common():
        sec = resolve(where[fp], cache) if fp in where else None
        # The dictionary finds a section by its name: the same boxes under another title (the
        # bakery's "indirizzo dell'attività") are filled only if that name has an entry too.
        missing = sorted(nm for nm in names[fp] if not (sec and covered({**sec, "section": nm}, dictionary)))
        rows.append({"fingerprint": fp, "uses": n, "by": dict(by[fp]), "names": sorted(names[fp]), "crawl": where.get(fp),
                     "sportelli": sorted(pratiche[fp]), "covered": bool(sec) and not missing,
                     **({"names_missing": missing} if sec and missing and len(missing) < len(names[fp]) else {}),
                     "filled": {sp: sum(k for (p, nm), k in by_name[fp].items() if p == sp and sec and nm not in missing)
                                for sp in by[fp]}})
    if not args.summary:
        return rows
    out = []
    for sp in ("sue", "suap"):
        r = [x for x in rows if sp in x["sportelli"]]
        if not r:
            continue
        done = [x for x in r if x["covered"]]
        u = lambda xs: sum(x["by"][sp] for x in xs)
        filled = sum(x["filled"][sp] for x in r)
        n = len({p for p in list(stored) + list(alias) if sportello(p) == sp})
        out.append(f"{sp.upper()}: {n} pratiche, {len(r)} distinct sections, {len(done)} in the dictionary; "
                   f"{filled} of {u(r)} uses ({100 * filled // max(1, u(r))}%)")
    return out


def stored_fingerprints(name, cache=None):
    """Each section of a stored crawl and its fingerprint."""
    cache = cache if cache is not None else {}
    out = {}
    for s in json.loads((SECTIONS / f"{name}.json").read_text())["sections"]:
        if s.get("skipped") or s.get("error"):
            continue
        if s.get("same_as"):
            out[s["section"]] = s.get("fingerprint") or fingerprint(resolve(s["same_as"], cache)["fields"])
        else:
            out[s["section"]] = s.get("fingerprint") or fingerprint(s["fields"])
    return out


def cmd_drift(args):
    """A check batch (`crawl:check:*` keys) against the stored crawls, into drift.json: the
    pratiche whose sections changed, which gen.py and run.py then refuse."""
    data = json.loads(Path(args.export).read_text())
    path = CAT / "drift.json"
    drift = json.loads(path.read_text()) if path.exists() else {"pratiche": {}}
    same = json.loads(SAME.read_text()) if SAME.exists() else {"same": {}, "different": {}}
    out, cache = [], {}
    for key, r in sorted(data.items()):
        if not key.startswith("crawl:check:"):
            continue
        r = r if isinstance(r, dict) else json.loads(r)
        name, like = r["name"], r.get("like")
        if r.get("error"):
            out.append(f"{name}: not checked ({r['error']})")
            continue
        if not (SECTIONS / f"{like or name}.json").exists():
            out.append(f"{name}: no stored crawl of {like or name} to compare")
            continue
        old = stored_fingerprints(like or name, cache)
        now = {s["section"]: s.get("fingerprint") for s in r["sections"] if not s.get("skipped") and not s.get("error")}
        diff = sorted(f"gone: {n}" for n in old if n not in now) + sorted(f"new: {n}" for n in now if n not in old)
        diff += sorted(f"changed: {n}" for n in now if n in old and now[n] != old[n])
        if like:
            # The same operation in another sector: the same pratica, or one to crawl itself.
            same["same" if not diff else "different"][name] = like if not diff else {"like": like, "differences": diff}
            (same["different" if not diff else "same"]).pop(name, None)
            out.append(f"{name}: " + (f"same pratica as {like}" if not diff else f"differs from {like}, crawl it: " + "; ".join(diff)))
            continue
        drift["pratiche"][name] = {"checked": r["crawled"][:10], "differences": diff}
        out.append(f"{name}: " + ("same as the stored crawl" if not diff else "; ".join(diff)))
    path.write_text(json.dumps(drift, ensure_ascii=False, indent=1) + "\n")
    SAME.write_text(json.dumps(same, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    return out


def drifted(name):
    """The differences the last check found in a pratica's crawl, or []."""
    path = CAT / "drift.json"
    if not path.exists():
        return []
    return json.loads(path.read_text())["pratiche"].get(name, {}).get("differences", [])


def cmd_pane(args):
    """wizard.js and crawl.js for the pane, kept in its localStorage (pv-wizard, pv-crawl) so a
    page that navigates doesn't lose them: install.js (gzip, base64: a third of the size) checks
    each by sha256 before storing it, load.js runs the stored copies, and says if they're stale."""
    import base64, gzip
    out = Path(args.dir)
    out.mkdir(parents=True, exist_ok=True)
    srcs = {k: (HERE / f).read_text() for k, f in (("pv-wizard", "wizard.js"), ("pv-crawl", "crawl.js"))}
    sha = {k: hashlib.sha256(v.encode()).hexdigest() for k, v in srcs.items()}
    gz = {k: base64.b64encode(gzip.compress(v.encode(), 9, mtime=0)).decode() for k, v in srcs.items()}
    common = ("const sha = async (s) => Array.from(new Uint8Array(await crypto.subtle.digest(\"SHA-256\", "
              "new TextEncoder().encode(s)))).map((b) => b.toString(16).padStart(2, \"0\")).join(\"\");\n"
              f"const want = {json.dumps(sha)};\n")
    (out / "install.js").write_text(
        "const gunzip = async (b) => new Response(new Blob([Uint8Array.from(atob(b), (c) => c.charCodeAt(0))])"
        ".stream().pipeThrough(new DecompressionStream(\"gzip\"))).text();\n" + common +
        f"const gz = {json.dumps(gz)};\nconst done = [];\n"
        "for (const [k, b] of Object.entries(gz)) { const s = await gunzip(b);\n"
        "  if (await sha(s) !== want[k]) throw new Error(k + \": not the file sent\");\n"
        "  localStorage.setItem(k, s); done.push(k); }\n"
        "(0, eval)(localStorage.getItem(\"pv-wizard\")); (0, eval)(localStorage.getItem(\"pv-crawl\"));\n"
        "`installed ${done.join(\", \")}`\n")
    (out / "load.js").write_text(common +
        "const stale = []; for (const k of Object.keys(want)) if (await sha(localStorage.getItem(k) || \"\") !== want[k]) stale.push(k);\n"
        "if (!stale.length) { (0, eval)(localStorage.getItem(\"pv-wizard\")); (0, eval)(localStorage.getItem(\"pv-crawl\")); }\n"
        "stale.length ? `stale: ${stale.join(\", \")}: run install.js` : \"loaded\"\n")
    if not args.bundle:
        return [f"{out}/install.js ({(out / 'install.js').stat().st_size // 1024} KB), {out}/load.js: "
                "on the portal's origin, load.js first; install.js only if it says stale"]
    return bundle(out, Path(args.bundle).expanduser(), srcs, json.loads(Path(args.ops).read_text()), args)


def bundle(out, path, srcs, ops, args):
    """A batch as one file the person picks once in the pane (2026-10-31: a big script copied
    through the conversation can arrive garbled), checked by sha256: it stores and runs wizard.js
    and crawl.js, with --fresh clears what makes the batch skip a pratica or a section it has
    seen (the crawls are in the repo; known fingerprints and scelte are backed up), and starts.
    status.js polls it; export.js saves the results as the export `import` reads, those the
    pane's storage couldn't keep included."""
    names = [o["name"] for o in ops]
    opts = {"draft": args.draft, "depth": args.depth, "variants": True, "ops": ops}
    stamp = "backup-" + datetime.date.today().strftime("%Y%m%d")
    # Busy only while a batch runs: one that ended doesn't hold the tab (2026-10-31: a second
    # bundle in the tab was refused).
    text = (f"(() => {{\n  if (window.__crawlBusy && !(window.__crawl && (window.__crawl.report() || {{}}).done)) return \"a batch already runs in this tab\";\n"
            f"  const src = {json.dumps(srcs)};\n"
            "  for (const [k, v] of Object.entries(src)) localStorage.setItem(k, v);\n"
            "  (0, eval)(src[\"pv-wizard\"]); (0, eval)(src[\"pv-crawl\"]);\n"
            f"  const opts = {json.dumps(opts, ensure_ascii=False)};\n"
            "  localStorage.setItem(\"crawl:batch\", JSON.stringify(opts));\n"
            + (f"  for (const k of [\"crawl:known\", \"crawl:scelte\"]) {{ const v = localStorage.getItem(k); if (v !== null) localStorage.setItem(k + \":{stamp}\", v); }}\n"
               "  localStorage.setItem(\"crawl:known\", \"{}\"); localStorage.removeItem(\"crawl:scelte\");\n"
               "  for (const o of opts.ops) localStorage.removeItem(\"crawl:op:\" + o.name);\n" if args.fresh else "")
            + "  window.__crawlBusy = true;\n  window.__crawl.batch(opts);\n"
            f"  return `started: ${{opts.ops.length}} pratiche, depth ${{opts.depth}}{' (fresh)' if args.fresh else ''}`;\n}})()\n")
    path.write_text(text)
    sha = hashlib.sha256(text.encode()).hexdigest()
    (out / "pick.js").write_text(f"""document.querySelectorAll("iframe, #pv-pick").forEach((x) => x.remove());
const box = document.createElement("div"); box.id = "pv-pick";
box.style.cssText = "position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:2147483647;background:#fff;border:3px solid #1a4fd6;padding:16px 20px;font:16px sans-serif;box-shadow:0 4px 18px rgba(0,0,0,.3);border-radius:8px;max-width:520px";
box.innerHTML = '<b>Choose <code>{path.name}</code> (once)</b><br><input type="file" accept=".js" style="margin-top:10px"><div style="margin-top:8px;color:#444"></div>';
document.body.appendChild(box);
const [input, msg] = [box.querySelector("input"), box.querySelector("div")];
input.addEventListener("change", async () => {{
  const text = await input.files[0].text();
  const got = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text)))).map((b) => b.toString(16).padStart(2, "0")).join("");
  if (got !== "{sha}") {{ msg.textContent = "Not that file (its sha256 differs): nothing loaded."; return; }}
  input.disabled = true;
  try {{ window.pvBundle = String((0, eval)(text)); msg.textContent = window.pvBundle; setTimeout(() => box.remove(), 5000); }}
  catch (e) {{ window.pvBundle = "error " + e.message; msg.textContent = window.pvBundle; }}
}});
"box shown: pick the file once, then poll status.js"
""")
    (out / "status.js").write_text("""await new Promise((r) => setTimeout(r, 38000));  // the pane cuts a call at 45 s
const r = window.__crawl ? await window.__crawl.wait(300) : null;
JSON.stringify(r ? { done: r.done, done_ops: r.done_ops, of: JSON.parse(localStorage.getItem("crawl:batch")).ops.length,
  current: r.current, tried: r.tried, errors: r.errors, stopped: r.stopped, error: r.error, storage: r.storage } : "no crawl in this tab")
""")
    name = "crawl-batch-" + path.stem.removeprefix("pv-") + ".json"
    (out / "export.js").write_text(f"""// Saves the batch's results to the person's Downloads (ask them first): what `catalogue.py
// import` reads, with what the pane's storage couldn't keep.
const opts = JSON.parse(localStorage.getItem("crawl:batch")), unsaved = window.__crawlUnsaved || {{}};
const out = {{}};
for (const o of opts.ops) {{ const k = "crawl:op:" + o.name, v = unsaved[k] || localStorage.getItem(k); if (v) out[k] = JSON.parse(v); }}
const blob = new Blob([JSON.stringify(out)], {{ type: "application/json" }});
const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = {json.dumps(name)};
document.body.appendChild(a); a.click(); a.remove();
({{ file: {json.dumps(name)}, pratiche: Object.keys(out).length, of: opts.ops.length, bytes: blob.size }})
""")
    (out / "print.js").write_text("""// A small batch's results as text (a combination, its sections all known): sha256 first, for
// `catalogue.py import -`, which refuses a copy that arrived changed. A big one: export.js.
const opts = JSON.parse(localStorage.getItem("crawl:batch")), unsaved = window.__crawlUnsaved || {};
const out = {};
for (const o of opts.ops) { const k = "crawl:op:" + o.name, v = unsaved[k] || localStorage.getItem(k); if (v) out[k] = JSON.parse(v); }
const text = JSON.stringify(out);
const sha = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text)))).map((b) => b.toString(16).padStart(2, "0")).join("");
text.length > 40000 ? `${text.length} characters: too big to print, save it with export.js` : sha + "\\n" + text
""")
    return [f"{path} ({path.stat().st_size // 1024} KB, {len(names)} pratiche) and, in {out}: pick.js (the box "
            f"where the person picks it), status.js (poll), export.js (saves {name}, once they agree), "
            f"print.js (a small batch's results as text)"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("ops")
    p.add_argument("sportello", choices=["sue", "suap"])
    p.add_argument("--sectors", help="SUAP sector indices in suap-wizard.json, comma-separated")
    p.add_argument("--common", action="store_true", help="the common operations, under the first sector")
    p.add_argument("--all", action="store_true", help="also the pratiche already crawled")
    p.add_argument("--combo", nargs="+", action="append", metavar="NAME MAIN OTHER",
                   help="sue: a combination's crawl name, then its operations' labels, the main one first; repeat it for several")
    p.add_argument("--scelta", action="append", help="--combo: a scelta to try (default: the procura)")
    sub.add_parser("known")
    p = sub.add_parser("import")
    p.add_argument("export")
    p.add_argument("--depth", type=int, help="the batch's depth, for one that didn't record it (before 2026-10-30: 2)")
    p = sub.add_parser("count")
    p.add_argument("--summary", action="store_true")
    p = sub.add_parser("drift")
    p.add_argument("export")
    p = sub.add_parser("pane")
    p.add_argument("dir")
    p.add_argument("--bundle", help="also a batch as one file the person picks (with --ops)")
    p.add_argument("--ops", help="--bundle: the batch's ops (catalogue.py ops' JSON)")
    p.add_argument("--draft", default="PROVA NON INVIARE - catalogo sue", help="--bundle: the scratch draft")
    p.add_argument("--depth", type=int, default=3)
    p.add_argument("--fresh", action="store_true", help="--bundle: crawl the ops again, though stored")
    args = ap.parse_args()
    res = globals()["cmd_" + args.cmd](args)
    if isinstance(res, list) and res and isinstance(res[0], str):
        print("\n".join(res))
    else:
        print(json.dumps(res, ensure_ascii=False, indent=1 if args.cmd == "count" else None))


if __name__ == "__main__":
    main()
