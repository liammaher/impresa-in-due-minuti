#!/usr/bin/env python3
"""Municipia's citizen portals for Napoli, read from the public files a browser loads.

What this reads: the page's HTML, its JavaScript and its translation files, the same bytes a visitor's
browser downloads, in one pass, with no login. What it never does: call a backend endpoint, sign in, guess
a URL, or read a value of a person. The endpoint names it lists are strings found in the code, kept so
the screens can be understood and tested, not to be called.

  python3 claude/skills/pratica/portal/municipia/extract.py run [--out DIR] [--only NAME]
  python3 claude/skills/pratica/portal/municipia/extract.py check [--dir DIR]

`run` writes one JSON per app (default: catalogue/napoli/). `check` compares the file names the portals
serve now with those the catalogue was made from (a build's files carry a content hash in their names),
and exits 1 when a build changed: the catalogue then needs a new run and a look at what moved.
"""

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DIR = HERE / "catalogue" / "napoli"
UA = "pratica-catalogue/0.1 (reads the public files a browser loads, one pass)"
PAUSE = 0.3  # seconds between requests: one visitor's pace

# The citizen portal and the gestori's own app. portaletributi.* answers with the same build as cizrm.*.
TARGETS = {
    "multiservizi": {"url": "https://cizrm.municipia.eng.it/",
                     "aliases": ["https://portaletributi.comune.napoli.it/"]},
    "geis": {"url": "https://geis-web-portal.municipia.eng.it/"},
}
FRAMEWORK_MODULES = {"HttpClientModule", "FormsModule", "ReactiveFormsModule", "CommonModule", "BrowserModule"}


# ---- parsers: pure functions on text, held to bench/test_municipia.py ----------------------------------

def script_srcs(html):
    """The script files an index page loads, in order, as written (relative or absolute)."""
    out = re.findall(r'<script[^>]+\bsrc="([^"]+)"', html)
    out += re.findall(r'<link[^>]+rel="modulepreload"[^>]+href="([^"]+)"', html)
    return list(dict.fromkeys(out))


def chunk_map(runtime):
    """Webpack's lazy chunks from the runtime file: {id: file name}. Empty if the runtime has none."""
    hashes = re.search(r'\+"-es2015\."\+\{([^}]*)\}\[e\]', runtime)
    if not hashes:
        return {}
    names = re.search(r'\(\{([^}]*)\}\[e\]\|\|e\)', runtime)
    nm = dict(re.findall(r'(\d+):"([^"]+)"', names.group(1))) if names else {}
    return {i: f"{nm.get(i, i)}-es2015.{h}.js" for i, h in re.findall(r'(\d+):"([0-9a-f]+)"', hashes.group(1))}


def _unescape(s):
    s = re.sub(r"\\x([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16)), s)
    s = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)
    return s.replace("\\'", "'").replace('\\"', '"').replace("\\n", " ").replace("\\r", " ").replace("\\t", " ")


def routes(js):
    """Routes written as {path:"/...", title:"...", roles:[...]} (the menu), in either key order."""
    out, seen = [], set()
    for m in re.finditer(r'path:"(/[^"]+)"', js):
        if m.group(1) in seen:
            continue
        seen.add(m.group(1))
        lo = js.rfind("{", 0, m.start())
        ends = [x for x in (js.find("{", m.end()), js.find("}", m.end())) if x != -1]
        seg = js[lo:min(ends) if ends else len(js)]
        title = re.search(r'title:"([^"]*)"', seg)
        roles = re.search(r'roles:\[([^\]]*)\]', seg)
        out.append({"path": m.group(1), "title": title.group(1) if title else "",
                    "roles": re.findall(r'"([^"]+)"', roles.group(1)) if roles else []})
    return out


def route_segments(js):
    """Router paths without a leading slash (the lazy modules' own: "geis", "genericpage/:page")."""
    segs = re.findall(r'path:"([^"/][^"]*)"', js)
    return [s for s in dict.fromkeys(segs) if re.fullmatch(r"[\w:/.\-]+", s)]


def selectors(js):
    """Angular components' selectors: one per screen."""
    return list(dict.fromkeys(re.findall(r'selectors:\[\["([^"]+)"\]\]', js)))


def modules(js):
    found = re.findall(r"\b([A-Z][A-Za-z0-9]+Module)\b", js)
    return sorted(m for m in set(found) if m not in FRAMEWORK_MODULES)


MAX_LABEL = 100  # a label, not a paragraph of the portal's help text


def labels(js):
    """The static text of the templates, in the order the code holds it, up to MAX_LABEL characters."""
    pat = r'(?:\\u0275\\u0275|\u0275\u0275)text(?:"\])?\(\d+,\s*"((?:[^"\\]|\\.)*)"\)'
    out = [_unescape(m).strip() for m in re.findall(pat, js)]
    return list(dict.fromkeys(t for t in out if 2 <= len(t) <= MAX_LABEL))


def rest_paths(js):
    """Backend paths named in the code: /rest/... in GEIS, ms-*/pargopa/cms/conf in the citizen portal."""
    pat = r'"(/?(?:rest|ms-[\w\-]+|pargopa|cms|conf)/[A-Za-z0-9_/\-{}.?=&]{2,100})"'
    return sorted(set(re.findall(pat, js)))


def messages(js):
    """What the code tells the user through alert() and confirm()."""
    out = [_unescape(m).strip() for m in re.findall(r'(?:alert|confirm)\("((?:[^"\\]|\\.)*)"', js)]
    return list(dict.fromkeys(t for t in out if len(t) >= 10))


def imports(js):
    """Files an ES module imports or loads lazily, as written ("./chunk-X.js")."""
    return list(dict.fromkeys(re.findall(r'(?:from|import)\s*\(?\s*["\'](\.{1,2}/[^"\']+\.js)["\']', js)))


def roles_of(route_list):
    return sorted({r for x in route_list for r in x["roles"]})


def flatten(d, prefix=""):
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out |= flatten(v, key + ".")
        else:
            out[key] = v
    return out


# ---- fetching ------------------------------------------------------------------------------------------

class Fetcher:
    def __init__(self, pause=PAUSE):
        self.pause, self.last, self.cache = pause, 0.0, {}

    def get(self, url):
        if url in self.cache:
            return self.cache[url]
        wait = self.last + self.pause - time.time()
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
        self.last = time.time()
        self.cache[url] = body
        return body

    def text(self, url):
        return self.get(url).decode("utf-8", "replace")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def abs_url(base, ref):
    return urllib.request.urljoin(base, ref)


def _scripts(base, html, prefix):
    return [abs_url(base, s) for s in script_srcs(html) if Path(s.split("?")[0]).name.startswith(prefix)]


MAX_FILES = 400  # a build's own code, not the whole library behind it


def crawl(starts, f, seen=None):
    """Every file reachable from `starts` by import, breadth first, up to MAX_FILES: {url: bytes}."""
    seen = {} if seen is None else seen
    queue = list(starts)
    while queue and len(seen) < MAX_FILES:
        url = queue.pop(0)
        if url in seen:
            continue
        seen[url] = f.get(url)
        queue += [abs_url(url, r) for r in imports(seen[url].decode("utf-8", "replace"))]
    return seen


def shared_libs(base, f):
    """The in-house libraries the citizen portal's shell shares with its remotes (its own _argo_* files)."""
    try:
        spec = json.loads(f.text(abs_url(base, "remoteEntry.json")))
    except Exception:  # noqa: BLE001  the shell's list is a bonus, not a precondition
        return []
    names = {s.get("outFileName", "") for s in spec.get("shared", [])}
    return sorted(n for n in names if n.startswith("_argo_") and n.endswith(".js"))


def records(files):
    per_file = {}
    for url, body in files.items():
        if not url.endswith(".js"):
            continue
        js = body.decode("utf-8", "replace")
        rec = {"modules": modules(js), "screens": selectors(js), "labels": labels(js),
               "rest": rest_paths(js), "messages": messages(js)}
        if any(rec.values()):
            per_file[Path(url).name] = rec
    return per_file


def build_record(roots, files):
    return {"roots": sorted(roots), "names": sorted(Path(u).name for u in files),
            "sha256": {Path(u).name: sha(b) for u, b in files.items()}}


# ---- the two apps ----------------------------------------------------------------------------------------

def geis(base, f):
    """geis-web-portal: Angular with lazy chunks. Roots: index's main and runtime, and each chunk."""
    html = f.text(base)
    main = _scripts(base, html, "main-es2015")[0]
    runtime = _scripts(base, html, "runtime-es2015")[0]
    files = {main: f.get(main), runtime: f.get(runtime)}
    for name in chunk_map(f.text(runtime)).values():
        files[abs_url(base, name)] = f.get(abs_url(base, name))
    main_js = files[main].decode("utf-8", "replace")
    menu = routes(main_js)
    return {
        "app": "geis-web-portal", "url": base,
        "build": build_record([Path(u).name for u in files], files),
        "routes": menu, "route_segments": route_segments(main_js), "roles": roles_of(menu),
        "files": records(files),
    }


def multiservizi(base, aliases, f):
    """cizrm.municipia.eng.it (also portaletributi.*): Angular, module federation. Roots: main, the
    remotes' entries and the features they expose, the shell's own _argo_* libraries; the code they
    import is followed (MAX_FILES)."""
    html = f.text(base)
    main = _scripts(base, html, "main-")[0]
    manifest = json.loads(f.text(abs_url(base, "assets/federation.manifest.json")))
    roots, remotes = {main}, {}
    for name, entry in manifest.items():
        entry_url = abs_url(base, entry)
        spec = json.loads(f.text(entry_url))
        folder = entry_url.rsplit("/", 1)[0] + "/"
        remotes[name] = {"entry": entry, "shared": len(spec.get("shared", [])),
                         "exposes": {e["key"]: e["outFileName"] for e in spec.get("exposes", [])}}
        roots |= {entry_url} | {folder + o for o in remotes[name]["exposes"].values()}
    roots |= {abs_url(base, n) for n in shared_libs(base, f)} | {abs_url(base, "remoteEntry.json")}
    files = {}
    for r in sorted(roots):
        crawl([r], f, files)
    main_js = files[main].decode("utf-8", "replace")
    # the shell's routes sit in the chunks main imports, not in main itself
    menu = routes("\n".join(b.decode("utf-8", "replace") for u, b in files.items()
                            if u.startswith(base) and "/remotes/" not in u and u.endswith(".js")))
    i18n = {}
    for rel in ("assets/i18n/shell/ita.json", "assets/i18n/shared-components/ita.json"):
        try:
            i18n[rel] = flatten(json.loads(f.text(abs_url(base, rel))))
        except Exception as e:  # noqa: BLE001  a missing translation file is not a failed catalogue
            i18n[rel] = f"not read: {e}"
    same = {}
    for a in aliases:
        am = _scripts(a, f.text(a), "main-")
        same[a] = bool(am) and Path(am[0]).name == Path(main).name
    return {
        "app": "multiservizi (fe-cittadino)", "url": base, "same_main_file_as": same,
        "build": build_record([Path(u).name for u in roots], files),
        "remotes": remotes, "routes": menu, "route_segments": route_segments(main_js), "roles": roles_of(menu),
        "files": records(files), "i18n": i18n,
    }


def roots_now(name, f):
    """The build's root file names as served now, for `check`: only the index, the runtime or manifest
    and the entries are read (a root's name carries its content hash, and imports change it)."""
    t = TARGETS[name]
    base = t["url"]
    html = f.text(base)
    if name == "geis":
        main = _scripts(base, html, "main-es2015")[0]
        runtime = _scripts(base, html, "runtime-es2015")[0]
        return sorted({Path(main).name, Path(runtime).name, *chunk_map(f.text(runtime)).values()})
    out = {Path(_scripts(base, html, "main-")[0]).name}
    for entry in json.loads(f.text(abs_url(base, "assets/federation.manifest.json"))).values():
        entry_url = abs_url(base, entry)
        out.add(Path(entry_url).name)
        out |= {e["outFileName"] for e in json.loads(f.text(entry_url)).get("exposes", [])}
    out |= set(shared_libs(base, f)) | {"remoteEntry.json"}
    return sorted(out)


def run(out_dir, only=None):
    f = Fetcher()
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, t in TARGETS.items():
        if only and name != only:
            continue
        cat = geis(t["url"], f) if name == "geis" else multiservizi(t["url"], t.get("aliases", []), f)
        path = out_dir / f"{name}.json"
        path.write_text(json.dumps(cat, ensure_ascii=False, indent=1, sort_keys=False) + "\n", encoding="utf-8")
        print(f"{name}: {len(cat['build']['names'])} files, {len(cat['routes'])} routes, {len(cat['roles'])} roles, {path.name}")


def check(dir_):
    f = Fetcher()
    changed = False
    for name in TARGETS:
        path = dir_ / f"{name}.json"
        if not path.is_file():
            print(f"{name}: no catalogue at {path}")
            changed = True
            continue
        had = set(json.loads(path.read_text(encoding="utf-8"))["build"]["roots"])
        now = set(roots_now(name, f))
        if had == now:
            print(f"{name}: unchanged ({len(now)} files)")
        else:
            changed = True
            print(f"{name}: CHANGED, new {sorted(now - had)}, gone {sorted(had - now)}")
    return 1 if changed else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--out", type=Path, default=DEFAULT_DIR)
    r.add_argument("--only", choices=sorted(TARGETS))
    c = sub.add_parser("check")
    c.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    a = ap.parse_args(argv)
    if a.cmd == "run":
        run(a.out, a.only)
        return 0
    return check(a.dir)


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    sys.exit(main())
