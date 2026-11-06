#!/usr/bin/env python3
"""Copy the Prova (the made-up CILA beside this script) into a new folder, for prova.md.

  prova.py [DEST]
  prova.py --files DIR

DEST defaults to portale-sue-prova in the current folder; when that exists, portale-sue-prova-2,
-3 and so on. Prints the folder it made. --files copies only the Prova's made-up PDFs into DIR
(made if missing, a file there already kept), for a test of the tecnico's own case, and prints
each one's path. Never writes into the plugin's own folder: the copy is
made by this script, so the only path a command names is the new folder (a `cp` from the plugin's
folder can be refused by a session's permission rules).
"""

import shutil
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parent / "prova"


def target(base):
    dest, n = base, 1
    while dest.exists():
        n += 1
        dest = base.with_name(f"{base.name}-{n}")
    return dest


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--files":
        out = Path(sys.argv[2]).resolve()
        out.mkdir(parents=True, exist_ok=True)
        for f in sorted((CASE / "files").glob("*.pdf")):
            if not (out / f.name).exists():
                shutil.copy2(f, out / f.name)
            print(out / f.name)
        return 0
    if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1].startswith("-")):
        sys.exit("usage: prova.py [DEST] | prova.py --files DIR")
    dest = target(Path(sys.argv[1] if len(sys.argv) == 2 else "portale-sue-prova").resolve())
    shutil.copytree(CASE, dest)
    (dest / "run").mkdir(exist_ok=True)
    print(dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
