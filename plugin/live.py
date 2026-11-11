#!/usr/bin/env python3
"""The one way to try the plugin as a tecnico gets it: build it when it is stale, then say what to load.

  ~/.cache/pratica-portal/venv/bin/python plugin/live.py [--check]

A test of how Impresa in un minuto behaves (the Prova, a demo, a UX change) is run through the built
plugin's own skill, in the Claude app's browser pane, from a fresh folder, saying what a tecnico says
("fammi vedere una prova"). Never through the repo's scripts (run.py, rerun.py, a Playwright window,
the CILA fixture): they are the same engine in another wrapper, and what they show can differ from
what the plugin shows. The build refuses a plugin whose runner files differ from the repo's
(plugin/build.py, RUNNER_FILES) or whose Prova card differs from the repo runner's.

dist/build.json records a digest of everything a build is made from (build.sources_digest). This
rebuilds, with the evals, when it differs or the file is missing; --check only reports (exit 1 if stale).
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import build  # noqa: E402

DIST = HERE / "dist"


def WANTED():
    """The options live.py builds with: build.yaml's defaults, and the evals."""
    return {"vault": build.vault_default(), "python_download": build.switch("python_download"), "evals": True,
            "cowork_test": False, "connector": None, "pvault": None}


def stale():
    """Why dist is not this checkout's plugin, or None."""
    f = DIST / "build.json"
    if not (DIST / "impresa-in-un-minuto").is_dir() or not f.is_file():
        return "no build in plugin/dist"
    done = json.loads(f.read_text())
    if done.get("sources") != build.sources_digest():
        return "plugin/dist was built from other files than this checkout's"
    if done.get("flags") != WANTED():
        return "plugin/dist was built with other options than live.py's (the defaults, with the evals)"
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="only say whether dist is current (exit 1 if not)")
    a = ap.parse_args()
    why = stale()
    if a.check:
        print(why or "current")
        return 1 if why else 0
    if why:
        print(f"rebuilding: {why}", file=sys.stderr)
        r = subprocess.run([sys.executable, str(HERE / "build.py"), "--evals"])
        if r.returncode:
            return r.returncode
    plugin = DIST / "impresa-in-un-minuto"
    print(f"""The plugin as a tecnico gets it (built from {build.git_head() or 'this checkout'}):
  {plugin}
  {DIST / 'impresa-in-un-minuto.plugin'}   (install from file in Cowork)

To test it: load that folder (`claude --plugin-dir {plugin}`, or install the .plugin file), open a new
session in an empty folder, and write what a tecnico writes: «fammi vedere una prova». The portal
steps are theirs too: SPID login in the app's browser pane, then watch. Delete the draft
«PROVA NON INVIARE - CILA di prova» from Pratiche in bozza afterwards.""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
