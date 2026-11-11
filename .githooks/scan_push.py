#!/usr/bin/env python3
"""pre-push: scan what the push adds for the maintainer's private terms.

Git feeds stdin one line per ref: `<local ref> <local sha> <remote ref> <remote sha>`. For each ref
the commits the remote lacks are read as patches (every added line of every commit, so a term added
and removed in the same push is still found). Output names a file and a line, never the term: it
may end up in a log. No list on this machine: the push goes through, with a note.
"""
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plugin"))
import private_terms  # noqa: E402

ZERO = "0" * 40


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, errors="replace").stdout


def added(range_args):
    """(commit, file, line, text) for every line the commits add."""
    out = git("log", "-p", "--unified=0", "--no-color", "--format=commit %h", *range_args)
    commit = path = None
    line = 0
    for l in out.splitlines():
        if l.startswith("commit "):
            commit, path = l[7:], None
        elif l.startswith("+++ "):
            path = l[6:] if l.startswith("+++ b/") else None
        elif l.startswith("@@"):
            m = re.match(r"@@ -\S+ \+(\d+)", l)
            line = int(m.group(1)) if m else 0
        elif l.startswith("+") and path:
            yield commit, path, line, l[1:]
            line += 1
    # A file's name is text too.
    for l in git("log", "--name-only", "--no-color", "--format=commit %h", *range_args).splitlines():
        if l.startswith("commit "):
            commit = l[7:]
        elif l.strip():
            yield commit, l, 0, l


def main():
    terms = private_terms.load()
    if not terms:
        print("pre-push: no private-terms list on this machine (see plugin/private_terms.py): not scanned", file=sys.stderr)
        return 0
    # A short number (a civico, a pixel coordinate in a layout) is told from data by no scan of lines:
    # the build's whole-file check keeps those terms; this hook skips digit-only ones under 6 digits.
    keep = [i for i, t in enumerate(terms) if not (t.isdigit() and len(t) < 6)]
    pats = private_terms.patterns(terms)
    found = set()
    for ref in sys.stdin.read().splitlines():
        parts = ref.split()
        if len(parts) != 4 or parts[1] == ZERO:  # a deletion carries nothing
            continue
        _, local, _, remote = parts
        if remote == ZERO:  # a new branch: what origin's branches lack
            rng = [local, "--not", "--remotes=" + (sys.argv[1] if len(sys.argv) > 1 else "origin")]
        else:
            rng = [f"{remote}..{local}"]
        for commit, path, line, text in added(rng):
            for n in private_terms.hits(text, terms, pats):
                if n - 1 in keep:
                    found.add((commit, path, line, n))
    if found:
        print("pre-push: private terms in what this push adds (line numbers in the private list):", file=sys.stderr)
        for commit, path, line, n in sorted(found):
            print(f"  {commit} {path}:{line}  (list line {n})", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
