#!/usr/bin/env python3
"""The skill's Python launcher (plugin/impresa-in-due-minuti/skills/pratiche/py), offline, in both builds of
plugin/build.yaml's python_download: which Python it picks; off, that nothing fetches anything and
it says how to install one; on, that it never runs a download whose SHA-256 isn't the pinned one.

  python3 plugin/test_py.py      (PyYAML, as build.py: the builds are made by its keep())

Each case runs the launcher with PATH holding only fake commands (and the few system tools it
calls), so nothing is downloaded and no real Python is started.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import build  # noqa: E402

PY = HERE / "impresa-in-due-minuti" / "skills" / "pratiche" / "py"
TOOLS = ["sh", "uname", "mkdir", "mktemp", "rm", "mv", "cat", "cut", "tar", "shasum", "sha256sum"]
SHA_ARM_MAC = "9866e11cf2ae9caa1e671383786f248859a52dd8bfb702fb4c0dc2c65f1d36de"


def fake(bin_, name, body):
    p = bin_ / name
    p.write_text("#!/bin/sh\n" + body + "\n")
    p.chmod(0o755)


def run(launcher, bin_, home, *args, env=None):
    # Only the fakes and the system tools the launcher calls: no real python3, curl or xcode-select.
    for t in TOOLS:
        src = shutil.which(t)
        if src and not (bin_ / t).exists():
            (bin_ / t).symlink_to(src)
    e = {"PATH": str(bin_), "HOME": str(home)}
    e.update(env or {})
    return subprocess.run(["/bin/sh", str(launcher), *args], env=e, capture_output=True, text=True)


def main():
    failed = 0

    def check(name, ok, r=None):
        nonlocal failed
        print(("ok   " if ok else "FAIL ") + name)
        if not ok:
            failed += 1
            if r is not None:
                print(f"  exit {r.returncode}\n  out: {r.stdout!r}\n  err: {r.stderr!r}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        src = PY.read_text()
        builds = {on: tmp / f"py-{'on' if on else 'off'}" for on in (True, False)}
        for on, f in builds.items():
            f.write_text(build.keep(src, on, "download", build.DOWNLOAD_SH, "py"))
        n = 0

        def fresh():
            nonlocal n
            n += 1
            b, h = tmp / str(n) / "bin", tmp / str(n) / "home"
            b.mkdir(parents=True)
            h.mkdir()
            return b, h

        for name, f in [("on", builds[True]), ("off", builds[False]), ("repo", PY)]:
            r = subprocess.run(["/bin/sh", "-n", str(f)], capture_output=True, text=True)
            check(f"{name}: valid sh", r.returncode == 0, r)
            if shutil.which("dash"):
                r = subprocess.run(["dash", "-n", str(f)], capture_output=True, text=True)
                check(f"{name}: valid for dash too", r.returncode == 0, r)
        off = builds[False].read_text()
        code = "\n".join(l for l in off.splitlines() if not l.lstrip().startswith("#"))
        shipped = [w for w in ("curl", "python-build-standalone", "sha_of", "bundled", "download", "25 MB") if w in code]
        check(f"off: no download code shipped {shipped or ''}", not shipped)
        check("on: the download code and no marker line", "python-build-standalone" in builds[True].read_text()
              and "# <" not in builds[True].read_text())

        # Both builds: an installed Python 3.9+ is used, the arguments reach it; one too old is passed over.
        for on, f in builds.items():
            tag = "on" if on else "off"
            b, h = fresh()
            fake(b, "python3", 'case "$1" in -c) exit 0 ;; esac; echo "ran: $*"')
            r = run(f, b, h, "x.py", "--flag")
            check(f"{tag}: an installed python3 runs the script", r.returncode == 0 and r.stdout.strip() == "ran: x.py --flag", r)
            b, h = fresh()
            fake(b, "python3", 'case "$1" in -c) exit 1 ;; esac; echo "old ran"')
            fake(b, "python", 'case "$1" in -c) exit 0 ;; esac; echo "python ran"')
            r = run(f, b, h, "x.py")
            check(f"{tag}: a python3 older than 3.9 is passed over", r.stdout.strip() == "python ran", r)
            b, h = fresh()
            fake(b, "mine", 'echo "mine: $*"')
            r = run(f, b, h, "x.py", env={"IMPRESA_IN_DUE_MINUTI_PYTHON": str(b / "mine")})
            check(f"{tag}: IMPRESA_IN_DUE_MINUTI_PYTHON is used as named", r.stdout.strip() == "mine: x.py", r)

        # Off (and the repo's file, which behaves as off): no Python means a message, never a fetch.
        for tag, f in [("off", builds[False]), ("repo", PY)]:
            b, h = fresh()
            log = tmp / f"{tag}-curl.log"
            fake(b, "uname", 'case "$1" in -m) echo x86_64 ;; *) echo Linux ;; esac')
            fake(b, "curl", f'echo "$@" >> "{log}"; exit 0')
            r = run(f, b, h, "x.py")
            check(f"{tag}: no Python on Linux: how to install it, and nothing fetched",
                  r.returncode != 0 and "manca Python 3" in r.stderr and not log.exists() and "scarico" not in r.stderr, r)
            b, h = fresh()
            xlog = tmp / f"{tag}-xcode.log"
            fake(b, "uname", 'case "$1" in -m) echo arm64 ;; *) echo Darwin ;; esac')
            fake(b, "xcode-select", f'echo "$@" >> "{xlog}"; exit 1')
            fake(b, "curl", f'echo "$@" >> "{log}"; exit 0')
            r = run(f, b, h, "x.py")
            check(f"{tag}: no Python on a Mac: Apple's installer opens, and nothing fetched",
                  r.returncode != 0 and "strumenti per sviluppatori" in r.stderr
                  and xlog.exists() and "--install" in xlog.read_text() and not log.exists(), r)
            b, h = fresh()
            fake(b, "uname", 'case "$1" in -m) echo x86_64 ;; -s) echo MINGW64_NT-10.0 ;; esac')
            r = run(f, b, h, "x.py")
            check(f"{tag}: no Python on Windows: python.org", r.returncode != 0 and "python.org" in r.stderr, r)

        on = builds[True]
        # On: a download whose bytes aren't the pinned ones is refused, never unpacked or run.
        b, h = fresh()
        fake(b, "curl", 'while [ $# -gt 0 ]; do [ "$1" = -o ] && { echo evil > "$2"; }; shift; done; exit 0')
        r = run(on, b, h, "x.py")
        cache = h / ".cache" / "impresa-in-due-minuti"
        check("on: a download with another SHA-256 is refused", r.returncode != 0 and "non è quello atteso" in r.stderr
              and "scarico Python" in r.stderr and not list(cache.glob("python-*")) and not list(cache.glob(".dl.*")), r)
        b, h = fresh()
        fake(b, "curl", "exit 6")
        r = run(on, b, h, "x.py")
        check("on: no network: a plain message", r.returncode != 0 and "non riesco a scaricare" in r.stderr, r)
        b, h = fresh()
        fake(b, "uname", 'case "$1" in -m) echo riscv64 ;; *) echo Linux ;; esac')
        fake(b, "curl", "echo should-not-run >&2; exit 1")
        r = run(on, b, h, "x.py")
        check("on: an unknown machine is said, nothing downloaded",
              r.returncode != 0 and "non è tra quelli previsti" in r.stderr and "should-not-run" not in r.stderr, r)
        # A cache marked with another hash is not trusted; with the pinned one it runs, no download.
        b, h = fresh()
        fake(b, "curl", "exit 6")
        fake(b, "uname", 'case "$1" in -m) echo arm64 ;; *) echo Darwin ;; esac')
        d = h / ".cache" / "impresa-in-due-minuti" / "python-3.12.15-20261013"
        (d / "python" / "bin").mkdir(parents=True)
        fake(d / "python" / "bin", "python3", 'case "$1" in -c) exit 0 ;; esac; echo "cached ran"')
        (d / ".sha256").write_text("0" * 64 + "\n")
        r = run(on, b, h, "x.py", env={"IMPRESA_IN_DUE_MINUTI_PYTHON": "download"})
        check("on: a cache with the wrong hash isn't run", "cached ran" not in r.stdout and r.returncode != 0, r)
        (d / ".sha256").write_text(SHA_ARM_MAC + "\n")
        r = run(on, b, h, "x.py", env={"IMPRESA_IN_DUE_MINUTI_PYTHON": "download"})
        check("on: a cache with the pinned hash runs without a download",
              r.stdout.strip() == "cached ran" and "scarico" not in r.stderr, r)

    print(f"{failed} failed" if failed else "all passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
