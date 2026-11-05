#!/usr/bin/env python3
"""The skill's Python launcher (plugin/portali/skills/portali-pratica/py), offline: which Python
it picks, and that it never runs a download whose SHA-256 isn't the pinned one.

  python3 plugin/test_py.py      (no packages; no network: curl, python3 and python are fakes)

Each case runs `sh py` with PATH holding only fake commands (and the system's sh tools), so
nothing is downloaded and no real Python is started unless the case says so.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PY = Path(__file__).resolve().parent / "portali" / "skills" / "portali-pratica" / "py"
TOOLS = ["sh", "uname", "mkdir", "mktemp", "rm", "mv", "cat", "cut", "tar", "shasum", "sha256sum", "dirname"]


def fake(bin_, name, body):
    p = bin_ / name
    p.write_text("#!/bin/sh\n" + body + "\n")
    p.chmod(0o755)


def run(bin_, home, *args, env=None):
    # Only the fakes and the few system tools the launcher calls: no real python3 or curl.
    for t in TOOLS:
        src = shutil.which(t)
        if src and not (bin_ / t).exists():
            (bin_ / t).symlink_to(src)
    e = {"PATH": str(bin_), "HOME": str(home)}
    e.update(env or {})
    return subprocess.run(["/bin/sh", str(PY), *args], env=e, capture_output=True, text=True)


def main():
    failed = 0

    def check(name, ok, r):
        nonlocal failed
        print(("ok   " if ok else "FAIL ") + name)
        if not ok:
            failed += 1
            print(f"  exit {r.returncode}\n  out: {r.stdout!r}\n  err: {r.stderr!r}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        def fresh(n):
            b, h = tmp / n / "bin", tmp / n / "home"
            b.mkdir(parents=True)
            h.mkdir()
            return b, h

        # An installed Python 3.9+ is used; the script's arguments reach it.
        b, h = fresh("installed")
        fake(b, "python3", 'case "$1" in -c) exit 0 ;; esac; echo "ran: $*"')
        r = run(b, h, "x.py", "--flag")
        check("an installed python3 runs the script", r.returncode == 0 and r.stdout.strip() == "ran: x.py --flag", r)

        # Too old: python3 refuses the version check, so python is tried.
        b, h = fresh("old")
        fake(b, "python3", 'case "$1" in -c) exit 1 ;; esac; echo "old ran"')
        fake(b, "python", 'case "$1" in -c) exit 0 ;; esac; echo "python ran"')
        r = run(b, h, "x.py")
        check("a python3 older than 3.9 is passed over", r.stdout.strip() == "python ran", r)

        # PORTALI_PYTHON names one.
        b, h = fresh("named")
        fake(b, "mine", 'echo "mine: $*"')
        r = run(b, h, "x.py", env={"PORTALI_PYTHON": str(b / "mine")})
        check("PORTALI_PYTHON is used as named", r.stdout.strip() == "mine: x.py", r)

        # No Python: a download whose bytes aren't the pinned ones is refused, never unpacked or run.
        b, h = fresh("tampered")
        fake(b, "curl", 'while [ $# -gt 0 ]; do [ "$1" = -o ] && { echo evil > "$2"; }; shift; done; exit 0')
        r = run(b, h, "x.py")
        left = list((h / ".cache" / "portali").glob("python-*"))
        check("a download with another SHA-256 is refused", r.returncode != 0 and "non è quello atteso" in r.stderr
              and "scarico Python" in r.stderr and not left and not list((h / ".cache" / "portali").glob(".dl.*")), r)

        # No Python and no network: a plain message, nothing left behind.
        b, h = fresh("offline")
        fake(b, "curl", "exit 6")
        r = run(b, h, "x.py")
        check("no network: a plain message", r.returncode != 0 and "non riesco a scaricare" in r.stderr, r)

        # A machine with no pinned build.
        b, h = fresh("machine")
        fake(b, "uname", 'case "$1" in -m) echo riscv64 ;; *) echo Linux ;; esac')
        fake(b, "curl", "echo should-not-run >&2; exit 1")
        r = run(b, h, "x.py")
        check("an unknown machine is said, nothing downloaded",
              r.returncode != 0 and "non è tra quelli previsti" in r.stderr and "should-not-run" not in r.stderr, r)

        # A cache marked with another hash is not trusted: it downloads again (here: refused).
        b, h = fresh("cache")
        fake(b, "curl", "exit 6")
        d = h / ".cache" / "portali" / "python-3.12.15-20261013"
        (d / "python" / "bin").mkdir(parents=True)
        fake(d / "python" / "bin", "python3", 'case "$1" in -c) exit 0 ;; esac; echo "stale ran"')
        (d / ".sha256").write_text("0" * 64 + "\n")
        r = run(b, h, "x.py", env={"PORTALI_PYTHON": "download"})
        check("a cache with the wrong hash isn't run", "stale ran" not in r.stdout and r.returncode != 0, r)

        # The pinned hash in place (as after a good download): the cached Python runs, no download.
        if os.uname().sysname == "Darwin" and os.uname().machine == "arm64":
            (d / ".sha256").write_text("9866e11cf2ae9caa1e671383786f248859a52dd8bfb702fb4c0dc2c65f1d36de\n")
            r = run(b, h, "x.py", env={"PORTALI_PYTHON": "download"})
            check("a cache with the pinned hash runs without a download",
                  r.stdout.strip() == "stale ran" and "scarico" not in r.stderr, r)

    print(f"{failed} failed" if failed else "all passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
