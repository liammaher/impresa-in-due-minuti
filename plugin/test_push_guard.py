#!/usr/bin/env python3
"""The pre-push guard (.githooks/scan_push.py): a push that adds a private term is refused, naming
the commit, file and the list's line, never the term; one that doesn't is let through.

    python3 plugin/test_push_guard.py
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / ".githooks" / "scan_push.py"
TERM = "zzqq-not-a-real-term-123"


def run(repo, terms, local, remote):
    env = {**os.environ, "PORTALI_PRIVATE_TERMS": str(terms), "IMPRESA_IN_UN_MINUTO_PRIVATE_TERMS": str(terms)}
    return subprocess.run([sys.executable, str(HOOK), "origin"], input=f"refs/heads/main {local} refs/heads/main {remote}\n",
                          cwd=repo, env=env, capture_output=True, text=True)


def git(repo, *a):
    return subprocess.run(["git", *a], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


with tempfile.TemporaryDirectory() as t:
    repo, terms = Path(t) / "r", Path(t) / "terms.txt"
    repo.mkdir()
    terms.write_text(f"# a comment\n{TERM}\n")
    git(repo, "init", "-q", ".")
    git(repo, "config", "user.email", "a@b.c")
    git(repo, "config", "user.name", "t")
    (repo / "a.txt").write_text("base\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "base")
    base = git(repo, "rev-parse", "HEAD")
    (repo / "b.txt").write_text(f"x\n{TERM}\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "adds it")
    bad = git(repo, "rev-parse", "HEAD")
    r = run(repo, terms, bad, base)
    assert r.returncode == 1 and "b.txt:2" in r.stderr and "list line 1" in r.stderr, r.stderr
    assert TERM not in r.stderr, "the term must never be printed"
    (repo / "b.txt").write_text("x\n")
    git(repo, "commit", "-qam", "removes it")
    r = run(repo, terms, git(repo, "rev-parse", "HEAD"), base)
    assert r.returncode == 1, "a term added and removed in one push is still found"
    assert run(repo, terms, base, base).returncode == 0, "nothing added"
    r = run(repo, Path(t) / "none.txt", bad, base)
    assert r.returncode == 0 and "not scanned" in r.stderr, r.stderr
    # A short number is data (a coordinate), not scanned line by line.
    terms.write_text("714\n")
    (repo / "c.json").write_text("  714,\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "coordinate")
    assert run(repo, terms, git(repo, "rev-parse", "HEAD"), base).returncode == 0
print("5/5 passed")
