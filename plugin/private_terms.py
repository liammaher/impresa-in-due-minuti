"""The maintainer's private terms: the list, and how a text is held to it.

Standard library only: plugin/build.py (the plugin's files), .githooks/pre-push (what a push carries)
and anything else that must never carry the maintainer's own details share this one reading.
The list is the maintainer's, outside every repo (0600), one term per line, # for comments. Output
names a file and a line, never a term: it may end up in a log.
"""
import os
import re
from pathlib import Path

# The variable and the folder the list is looked for under, newest name first; the earlier names of
# the plugin (Portali, Impresa in due minuti, Portale SUE) are where it may still be.
ENV = ("IMPRESA_IN_UN_MINUTO_PRIVATE_TERMS", "PORTALI_PRIVATE_TERMS")
FOLDERS = ("impresa-in-un-minuto", "portali", "impresa-in-due-minuti", "portale-sue")


def list_path():
    for name in ENV:
        if os.environ.get(name):
            return Path(os.environ[name])
    config = Path.home() / ".config"
    return next((p for p in (config / f / "private-terms.txt" for f in FOLDERS) if p.is_file()),
                config / FOLDERS[0] / "private-terms.txt")


def load():
    """The terms, one per line (empty when there is no list)."""
    path = list_path()
    if not path.is_file():
        return []
    lines = (l.strip() for l in path.read_text().splitlines())
    return [l for l in lines if l and not l.startswith("#")]


def patterns(terms):
    """A term as a whole word (a number inside a hash doesn't count)."""
    return [re.compile(r"(?<![0-9A-Za-z])" + re.escape(t) + r"(?![0-9A-Za-z])", re.I) for t in terms]


def hits(text, terms, pats):
    """The 1-based line numbers of the list whose term is in text: as a whole word, or, for a long
    one, spaced out as a form prints a codice fiscale."""
    flat = re.sub(r"\s+", "", text)
    return [i + 1 for i, p in enumerate(pats) if p.search(text) or (len(terms[i]) >= 9 and p.search(flat))]
