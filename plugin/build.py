#!/usr/bin/env python3
"""Build the Portali plugin for Cowork: plugin/portali plus the runner, the rehearsals'
steps files and the pratiche-napoli library, as one installable file.

  build.py [--library DIR] [--out DIR] [--connector URL] [--vault on|off] [--python-download on|off]
           [--cowork-test] [--evals]

Writes OUT/portali/ (default plugin/dist) and OUT/portali.plugin (the same, zipped), then
pre-flights the test fixture with the built plugin through its launcher (sh py, which picks this
computer's python3), as the skill runs it. --library is a pratiche-napoli checkout (default
$PRATICHE_NAPOLI_DIR). Needs PyYAML (the pratica venv's Python): the plugin itself needs no
packages, because every YAML file
the runner reads goes in as JSON (rules.load reads it). --connector adds the Portali
connector (connector/, serving this same build) as the plugin's .mcp.json. --vault overrides
build.yaml's `vault` for this build: off, the plugin carries no setup skill and its texts keep
only their no-vault parts. --python-download overrides build.yaml's `python_download`: off, the
skill's launcher (py) and its texts keep only their no-download parts, so nothing in the plugin
fetches a Python. --cowork-test keeps the Cowork test skill, for whoever runs those tests:
a release leaves it out (its made-up case and 3 MB PDF are for the build's self-check and the test).
--evals adds plugin/evals/ (how Claude follows the skill, for `claude plugin eval`), with that
made-up case as their job (evals/_job/); a release leaves them out too.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PRATICA = REPO / "claude" / "skills" / "pratica"
REHEARSALS = REPO / "rehearsals"
sys.path.insert(0, str(PRATICA / "portal"))
sys.dont_write_bytecode = True  # no __pycache__ in the skill's folder
import gen  # noqa: E402  (the steps files, built; a combination's recipe, resolved)
# The library's parts a Cowork session reads: its tools, reports backend and layouts
# (PDF filling, which needs PyMuPDF) stay out of this version.
LIBRARY_PARTS = ["procedures", "rules", "offices", "situations", "contract/signing.json",
                 "README.md", "LICENSE", "LICENSE-CONTENT.md"]
# What coverage.json can't derive: comuni, who files each sportello's pratiche, what's coming.
COVERAGE = yaml.safe_load((HERE / "coverage.yaml").read_text())
# The fixture the test skill runs: the CILA rehearsal's P6 case, made-up people.
TEST_CASE = "cila-fittizia"
# The archive switch: whether the plugin ships pvault (build.yaml says what each means).
SETUP_SKILL = "portali-setup"
TEST_SKILL = "portali-cowork-test"
MARKER = re.compile(r"^<!-- (/?)(vault|no-vault) -->$")
# The second switch, python_download: its parts in the texts, and in the launcher (a shell
# script, so its marker lines are comments: `# <download>` ... `# </download>`).
DOWNLOAD = re.compile(r"^<!-- (/?)(download|no-download) -->$")
DOWNLOAD_SH = re.compile(r"^# <(/?)(download|no-download)>$")
LAUNCHER = "skills/portali-pratica/py"


def switch(key):
    on = yaml.safe_load((HERE / "build.yaml").read_text()).get(key)
    if not isinstance(on, bool):
        sys.exit(f"plugin/build.yaml: `{key}` must be true or false")
    return on


def vault_default():
    return switch("vault")


def keep(text, on, part, marker, name):
    """text with only the parts for this build: a marker line opening `part` starts a part kept
    when `on`, one opening `no-<part>` a part kept when not, and its closing line ends it. Parts of
    one switch don't nest (another switch's markers are plain lines here, so its parts may sit
    inside); the marker lines themselves go."""
    out, open_ = [], None
    for n, line in enumerate(text.splitlines(keepends=True), 1):
        m = marker.match(line.strip())
        if not m:
            if open_ is None or (open_ == part) == on:
                out.append(line)
            continue
        closing, got = m.groups()
        if closing and open_ != got or not closing and open_ is not None:
            sys.exit(f"{name}:{n}: {line.strip()} with {open_ or 'no part'} open")
        open_ = None if closing else got
    if open_:
        sys.exit(f"{name}: {open_} never closed")
    return "".join(out)


def keep_parts(text, vault, name):
    """text with only the archive switch's parts for this build: `<!-- vault -->` ...
    `<!-- /vault -->` kept when the plugin ships the archive, `<!-- no-vault -->` ... when not."""
    return keep(text, vault, "vault", MARKER, name)


def select_vault(plugin, vault):
    """The hand-written plugin texts for this build. Without the archive: no setup skill (nor its
    installers), and nothing left in a text that names it."""
    if not vault:
        shutil.rmtree(plugin / "skills" / SETUP_SKILL)
    for f in sorted(plugin.rglob("*.md")):
        text = keep_parts(f.read_text(), vault, f.relative_to(plugin))
        if not vault:
            said = re.search(r"pvault|" + SETUP_SKILL, text)
            if said:
                sys.exit(f"{f.relative_to(plugin)}: says {said.group(0)!r} outside a <!-- vault --> part")
        f.write_text(text)


def select_download(plugin, download):
    """The launcher and the texts for the python_download switch. Off: nothing left that fetches a
    Python, or says the plugin does."""
    py = plugin / LAUNCHER
    files = sorted(plugin.rglob("*.md")) + [py]
    for f in files:
        text = keep(f.read_text(), download, "download", DOWNLOAD_SH if f == py else DOWNLOAD, f.relative_to(plugin))
        if not download:
            said = re.search(r"python-build-standalone|curl\b|scarico Python|25 MB", text)
            if said:
                sys.exit(f"{f.relative_to(plugin)}: says {said.group(0)!r} outside a download part")
        f.write_text(text)


_built = {}


def steps_file(d):
    """A rehearsal's steps file, as bench/rerun.py picks it: the generated one first. That one is
    built here from its recipe (never committed), and must be the one rehearsals/steps.lock names:
    a lock that isn't stops the build, as the plugin would ship steps no one has reviewed."""
    if (d / "recipe.yaml").is_file():
        if d not in _built:
            text = gen.dump(gen.generate(gen.load_yaml(d / "recipe.yaml")))
            if gen.sha256(text) != gen.read_lock().get(d.name):
                sys.exit(f"{d.name}: its steps file isn't the one rehearsals/steps.lock names: "
                         "run claude/skills/pratica/portal/bench/regen.py and commit the lock")
            f = d / gen.STEPS
            if not f.is_file() or f.read_text() != text:
                f.write_text(text)  # the self-check pre-flights it with the repo's runner
            _built[d] = f
        return _built[d]
    return d / "portal-steps.yaml" if (d / "portal-steps.yaml").is_file() else None


def notes(text):
    """The comment block a steps file starts with: who its roles are, what it fills."""
    lines = []
    for line in text.splitlines():
        if not line.startswith("#"):
            break
        lines.append(line[1:].strip())
    return " ".join(lines).strip()


def as_json(data):
    # A YAML date (2026-10-28 unquoted) goes in as the text it was, which the runner reads.
    return json.dumps(data, ensure_ascii=False, indent=1, default=str)


def lines_json(entries):
    """A JSON list one entry a line, so Claude searches it (grep) instead of reading it whole."""
    return "[\n" + ",\n".join(json.dumps(e, ensure_ascii=False, default=str) for e in entries) + "\n]"


def copy_library(library, skill):
    for part in LIBRARY_PARTS:
        src, dst = library / part, skill / "library" / part
        if not src.exists():
            sys.exit(f"{src}: missing from the library checkout")
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".*"))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def copy_runner(skill):
    portal = skill / "portal"
    portal.mkdir(parents=True)
    # rules.py's drifted(): pre-flight refuses a pratica the last drift check found changed on
    # the portal, so a plugin update carries the refusal (drift.json, not the crawls).
    (skill / "intake").mkdir()
    shutil.copy2(PRATICA / "intake" / "intake.py", skill / "intake" / "intake.py")  # reads the job's documents
    for name in ("run.py", "rules.py", "route.py", "inpage.js"):
        shutil.copy2(PRATICA / "portal" / name, portal / name)
    (portal / "catalogue" / "F839").mkdir(parents=True)
    shutil.copy2(PRATICA / "portal" / "catalogue" / "F839" / "drift.json", portal / "catalogue" / "F839" / "drift.json")
    (portal / "rules").mkdir()
    for table in sorted((PRATICA / "portal" / "rules").glob("*.yaml")):
        # BaseLoader, as rules.py reads it: every scalar stays a string.
        (portal / "rules" / f"{table.stem}.json").write_text(as_json(yaml.load(table.read_text(), Loader=yaml.BaseLoader)))
    (skill / "fill").mkdir()
    shutil.copy2(PRATICA / "fill" / "fill.py", skill / "fill" / "fill.py")  # run.py imports it
    shutil.copy2(PRATICA / "review.py", skill / "review.py")
    (skill / "reference").mkdir()
    shutil.copy2(REPO / "schema.json", skill / "reference" / "schema.json")


def copy_pratiche(skill, library):
    """Each rehearsal's steps file as pratiche/<name>.json, and catalog.json listing them."""
    (skill / "pratiche").mkdir()
    catalog = []
    for d in sorted(p for p in REHEARSALS.iterdir() if p.is_dir()):
        src = steps_file(d)
        if not src:
            continue
        text = src.read_text()
        steps = yaml.safe_load(text)
        out = skill / "pratiche" / f"{d.name}.json"
        out.write_text(as_json(steps))
        # Resolved: a combination takes its comune and sportello from its main pratica.
        recipe = gen.resolved(gen.load_yaml(d / "recipe.yaml")) if (d / "recipe.yaml").is_file() else {}
        proc = steps["procedure"]
        catalog.append({
            "name": d.name,
            "procedure": proc,
            "title": steps.get("title") or recipe.get("title"),
            "comune": recipe.get("comune") or COVERAGE["default_comune"],
            "sportello": recipe.get("sportello") or COVERAGE["sportello"].get(d.name),
            "library": f"library/procedures/{proc}.yaml" if (library / "procedures" / f"{proc}.yaml").is_file() else None,
            "notes": notes(text),
            # The connector serves the same hash: a different one means this copy is stale.
            "steps_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        })
    # The cases each refuses stay in its steps file: pre-flight reports them, and the connector
    # reads them there.
    (skill / "catalog.json").write_text(lines_json(catalog))
    return catalog


def last_run(d):
    """The latest date in a rehearsal README's runs table (`| 2026-10-28 | ...`): the last
    time it was run on the real portal, whatever that run's result."""
    readme = d / "README.md"
    dates = re.findall(r"^\| *(\d{4}-\d{2}-\d{2}) *\|", readme.read_text(), re.M) if readme.is_file() else []
    return max(dates, default=None)


def write_coverage(skill, catalog, library, version):
    """coverage.json: every pratica's status, from what the repo says rather than by hand.
    available: a steps file run on the real portal (its README's runs table) that the last
    drift check found unchanged; paused: one it found changed (pre-flight refuses it);
    mapped: a steps file with no recorded run yet, shown as coming soon; guide: a library
    procedure with no steps file, where Claude can say what it needs but not fill it;
    coming: coverage.yaml's list."""
    drift = json.loads((PRATICA / "portal" / "catalogue" / "F839" / "drift.json").read_text())["pratiche"]
    entries, filled = [], set()
    for e in catalog:
        steps = json.loads((skill / "pratiche" / f"{e['name']}.json").read_text())
        crawl = re.match(r"gen\.py from (\S+) ", steps.get("generated", ""))
        changed = drift.get(crawl.group(1), {}).get("differences", []) if crawl else []
        run = last_run(REHEARSALS / e["name"])
        entries.append({k: e[k] for k in ("name", "procedure", "title", "comune", "sportello", "steps_sha256")}
                       | {"status": "paused" if changed else "available" if run else "mapped", "changed": changed,
                          "avatars": COVERAGE["avatars"].get(e["sportello"], []),
                          "last_run": run, "library": bool(e["library"])})
        filled.add(e["procedure"])
    for f in sorted((library / "procedures").rglob("*.yaml")):
        proc = str(f.relative_to(library / "procedures").with_suffix(""))
        if proc in filled:
            continue
        # Only the title: the library parses its YAML with the yaml package, which takes a few
        # files PyYAML refuses.
        title = re.search(r"^title: *(.+)$", f.read_text(), re.M)
        entries.append({"name": None, "procedure": proc, "title": title and title.group(1).strip().strip('"'),
                        "comune": "F839" if proc.startswith("napoli/") else "IT", "sportello": None,
                        "status": "guide", "avatars": [], "library": True})
    entries += [c | {"name": None, "status": "coming"} for c in COVERAGE["coming"]]
    head = {"plugin_version": version, "built": dt.date.today().isoformat(), "comuni": COVERAGE["comuni"] | {"IT": "nazionale"}}
    (skill / "coverage.json").write_text(json.dumps(head, ensure_ascii=False)[:-1] + ', "pratiche": ' + lines_json(entries) + "}\n")
    return entries


def make_test_case(test):
    """The CILA rehearsal's P6 fixture, split as an architect's folder holds it: the studio
    and the architect in studio.json, the job's people in values.json."""
    d = REHEARSALS / TEST_CASE
    fixture = json.loads((d / "fixture-p6.json").read_text())
    fields = dict(fixture["fields"])
    ruolo = {k.split(":")[0]: v for k, v in fields.items() if k.endswith(":ruolo.tipo")}
    studio_people = {s for s, v in ruolo.items() if "titolare" in v.split(",")}
    studio = {k: v for k, v in fields.items() if ":" not in k or k.split(":")[0] in studio_people}
    job = {k: v for k, v in fields.items() if k not in studio}
    case = test / "cila"
    (case / "files").mkdir(parents=True)
    for f in (d / "files").glob("*.pdf"):
        shutil.copy2(f, case / "files" / f.name)
    answers = json.loads((d / "answers-p6.json").read_text())
    for k, v in answers.items():
        if isinstance(v, str) and v.startswith(f"rehearsals/{TEST_CASE}/files/"):
            answers[k] = "files/" + Path(v).name
    answers["descrizione"] = "PROVA NON INVIARE - CILA Cowork test"
    for name, data in (("studio.json", studio), ("values.json", job), ("answers.json", answers)):
        (case / name).write_text(json.dumps(data, indent=1, ensure_ascii=False))
    make_pdf(test / "planimetria-3mb.pdf", 3 * 1024 * 1024)


def make_pdf(path, size):
    """A valid one-page PDF of about `size` bytes: the padding is an unreferenced stream of
    random bytes (seeded, so each build is the same), which no compressor shrinks."""
    page = b"BT /F1 24 Tf 72 720 Td (Planimetria di prova - PROVA NON INVIARE) Tj ET"
    pad = random.Random(0).randbytes(size)
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
            b"/Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length %d >>\nstream\n" % len(page) + page + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Length %d >>\nstream\n" % len(pad) + pad + b"\nendstream"]
    out, offsets = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"), []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    path.write_bytes(bytes(out))


def self_check(plugin):
    """The test case through check.py and pre-flight, run as the skill runs them: through its
    py launcher (sh py), which picks this computer's python3."""
    skill = plugin / "skills" / "portali-pratica"
    case = plugin / "skills" / TEST_SKILL / "cila"
    py = ["sh", str(skill / "py")]
    with tempfile.TemporaryDirectory() as tmp:
        values = Path(tmp) / "values.json"
        r = subprocess.run([*py, skill / "check.py", "studio.json", "values.json", "--out", values],
                           cwd=case, capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"check.py refused the test case:\n{r.stdout}{r.stderr}")
        r = subprocess.run([*py, skill / "portal" / "run.py", "preflight", "--steps",
                            skill / "pratiche" / f"{TEST_CASE}.json", "--answers", "answers.json",
                            "--values", values, "--made-up"], cwd=case, capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"pre-flight of the test case isn't ready:\n{r.stdout}{r.stderr}")
        # A first pratica in a new folder of jobs, as the skill starts it: studio.json holds only
        # the tecnico's role, and pre-flight must then list the tecnico's details to ask for.
        first = Path(tmp) / "first"
        first.mkdir()
        (first / "studio.json").write_text('{"tecnico:ruolo.tipo": "titolare"}')
        (first / "values.json").write_text("{}")
        subprocess.run([*py, skill / "check.py", "studio.json", "values.json", "--out", "values-merged.json"],
                       cwd=first, check=True, capture_output=True)
        r = subprocess.run([*py, skill / "portal" / "run.py", "preflight", "--steps",
                            skill / "pratiche" / f"{TEST_CASE}.json", "--answers", case / "answers.json",
                            "--values", "values-merged.json", "--made-up"], cwd=first, capture_output=True, text=True)
        missing = [m["field"] for m in json.loads(r.stdout or "{}").get("missing", [])]
        if not any(f.startswith("tecnico:identity.") for f in missing) or "*:ruolo.tipo" in missing:
            sys.exit(f"a new folder's first pre-flight doesn't list the tecnico's details:\n{r.stdout}{r.stderr}")
        # Every pratica's JSON must read as its YAML did: pre-flight prints the same, from
        # the plugin under python3 and from the repo's runner with PyYAML.
        for steps in sorted((skill / "pratiche").glob("*.json")):
            d = REHEARSALS / steps.stem
            answers = next(iter(sorted(d.glob("answers*.json"))), None)
            tail = (["--answers", answers] if answers else []) + ["--values", values]
            ours = subprocess.run([*py, skill / "portal" / "run.py", "preflight", "--steps", steps] + tail,
                                  cwd=REPO, capture_output=True, text=True)
            theirs = subprocess.run([sys.executable, PRATICA / "portal" / "run.py", "preflight", "--steps",
                                     steps_file(d)] + tail, cwd=REPO, capture_output=True, text=True)
            if (ours.returncode, ours.stdout, ours.stderr) != (theirs.returncode, theirs.stdout, theirs.stderr):
                sys.exit(f"{steps.name}: pre-flight differs from {steps_file(d).relative_to(REPO)}'s")


PVAULT_TARGETS = [("darwin", "amd64", "tar.gz"), ("darwin", "arm64", "tar.gz"), ("linux", "amd64", "tar.gz"),
                  ("linux", "arm64", "tar.gz"), ("windows", "amd64", "zip"), ("windows", "arm64", "zip")]
# The Touch ID helper, built on macOS by release.yml (one universal binary): installed next to
# pvault on a Mac, so Touch ID needs no `make build`.
TOUCHID_ASSET = "pvault-touchid_{version}_darwin_universal.tar.gz"


def write_pvault_release(setup, version, checksums):
    """The release the setup skill installs: its version and the SHA-256 of each of its six
    archives and the Touch ID helper's (goreleaser's checksums.txt), shipped in the plugin so the
    installer checks a download against what the plugin says, not against what the download says."""
    if not re.fullmatch(r"\d+\.\d+\.\d+([-+][0-9A-Za-z.-]+)?", version):
        sys.exit(f"--pvault-version {version!r} isn't a version like 0.1.0")
    wanted = {f"pvault_{version}_{os_}_{arch}.{ext}" for os_, arch, ext in PVAULT_TARGETS}
    wanted.add(TOUCHID_ASSET.format(version=version))
    lines = {}
    for line in checksums.read_text().splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] in wanted:
            if not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
                sys.exit(f"{checksums}: {parts[1]} has no SHA-256")
            lines[parts[1]] = parts[0]
    if set(lines) != wanted:
        sys.exit(f"{checksums} lacks {sorted(wanted - set(lines))}")
    (setup / "pvault.version").write_text(version + "\n")
    (setup / "pvault-checksums.txt").write_text("".join(f"{lines[n]}  {n}\n" for n in sorted(lines)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--library", type=Path, default=os.environ.get("PRATICHE_NAPOLI_DIR"))
    ap.add_argument("--out", type=Path, default=HERE / "dist")
    ap.add_argument("--pvault-version", help="the pvault release the setup skill installs, e.g. 0.1.0 (with --pvault-checksums)")
    ap.add_argument("--pvault-checksums", type=Path, help="that release's checksums.txt")
    ap.add_argument("--connector", help="the Portali connector's https URL (connector/): the plugin brings it")
    ap.add_argument("--vault", choices=("on", "off"), help="ship the archive or not, for this build (default: build.yaml's)")
    ap.add_argument("--python-download", choices=("on", "off"),
                    help="let the skill's launcher fetch a Python where there is none, for this build (default: build.yaml's)")
    ap.add_argument("--cowork-test", action="store_true", help="keep the Cowork test skill (a release leaves it out)")
    ap.add_argument("--evals", action="store_true", help="add plugin/evals/ for `claude plugin eval` (a release leaves them out)")
    a = ap.parse_args()
    vault = vault_default() if a.vault is None else a.vault == "on"
    download = switch("python_download") if a.python_download is None else a.python_download == "on"
    if a.connector and not re.fullmatch(r"https://[^\s/]+(/\S*)?", a.connector):
        ap.error("--connector must be an https URL")
    if bool(a.pvault_version) != bool(a.pvault_checksums):
        ap.error("--pvault-version and --pvault-checksums go together")
    if a.pvault_version and not vault:
        ap.error("--pvault-version: this build ships no archive (vault off in plugin/build.yaml or --vault off)")
    if not a.library:
        ap.error("--library or $PRATICHE_NAPOLI_DIR: a pratiche-napoli checkout")
    # The repo's runner names a procedure by its library title from here, as the plugin's does
    # from its own library/ (run.procedure_name): the self-check compares their pre-flights.
    os.environ["PRATICHE_NAPOLI_DIR"] = str(Path(a.library).resolve())
    plugin = a.out / "portali"
    if plugin.exists():
        shutil.rmtree(plugin)
    shutil.copytree(HERE / "portali", plugin, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"))
    select_vault(plugin, vault)  # before anything else goes in: only the hand-written texts
    select_download(plugin, download)
    # The licence and notices travel with the plugin: it bundles the library's CC BY-SA texts.
    for name in ("LICENSE", "NOTICE.md"):
        shutil.copy2(REPO / name, plugin / name)
    if a.connector:  # without one the skill uses coverage.json, as of the build
        (plugin / ".mcp.json").write_text(as_json({"mcpServers": {"portali": {"type": "http", "url": a.connector}}}))
    if a.pvault_version:  # without one the setup skill says there is no release to install from
        write_pvault_release(plugin / "skills" / SETUP_SKILL, a.pvault_version, a.pvault_checksums)
    skill = plugin / "skills" / "portali-pratica"
    copy_runner(skill)
    catalog = copy_pratiche(skill, a.library)
    copy_library(a.library, skill)
    manifest = json.loads((plugin / ".claude-plugin" / "plugin.json").read_text())
    coverage = write_coverage(skill, catalog, a.library, manifest["version"])
    make_test_case(plugin / "skills" / TEST_SKILL)
    self_check(plugin)
    if a.evals:
        shutil.copytree(HERE / "evals", plugin / "evals", ignore=shutil.ignore_patterns(".DS_Store", "results"))
        shutil.copytree(plugin / "skills" / TEST_SKILL / "cila", plugin / "evals" / "_job")
    if not a.cowork_test:  # the self-check's case, never the customer's
        shutil.rmtree(plugin / "skills" / TEST_SKILL)
    if not re.fullmatch(r"[a-z0-9-]+", manifest["name"]):
        sys.exit(f"plugin name {manifest['name']!r} isn't kebab-case")
    zipped = a.out / f"{manifest['name']}.plugin"
    with zipfile.ZipFile(zipped, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(plugin.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts and f.name != ".DS_Store":
                z.write(f, f.relative_to(plugin))
    counts = {s: sum(e["status"] == s for e in coverage) for s in ("available", "paused", "mapped", "guide", "coming")}
    print(f"{zipped}: {manifest['name']} {manifest['version']}, {'with' if vault else 'no'} archive, {'with' if download else 'no'} Python download{', Cowork test' if a.cowork_test else ''}{', evals' if a.evals else ''}, {len(catalog)} pratiche, "
          f"{zipped.stat().st_size // 1024} KB; coverage {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
