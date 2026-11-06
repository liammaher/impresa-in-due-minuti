#!/usr/bin/env python3
"""Writes .claude-plugin/marketplace.json for one release: the marketplace people add
(in the Claude app, or `claude plugin marketplace add liammaher/portale-sue`) and the one entry in
it, the Portale SUE plugin, as the release's commit on the `plugin` branch (publish_plugin.py),
tagged plugin-v<version> and pinned by its commit SHA, so a moved tag installs nothing else.

  pin_marketplace.py --version 0.4.1 --commit <40 hex of plugin-v0.4.1's commit> [--out FILE]

A git source, not the release's zip (`archive`, Claude Code only): the Claude app (chat, Cowork)
syncs only `github`, `url`, `git-subdir` and `./` sources (claude.com/docs/plugins/org-sync); with
the `archive` source, "Add marketplace" failed in the app (2026-11-06). The release workflow
(.github/workflows/release.yml) runs it after publishing the plugin and opens a pull request.
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO = "liammaher/portale-sue"
HERE = Path(__file__).resolve().parent


def vault():
    """build.yaml's `vault`: whether the release's plugin ships the archive (the listing says so)."""
    sys.path.insert(0, str(HERE))
    import build
    return build.vault_default()


def marketplace(version, commit, repo=REPO, vault=True):
    return {
        "name": "portale-sue",
        "description": "Portale SUE: Claude prepares your pratiche on Italian government portals up to the steps only "
                       "you can take (SPID login, declarations, signature, payment, sending).",
        "owner": {"name": "Liam Maher"},
        "plugins": [{
            "name": "portale-sue",
            "description": "Prepares pratiche on the portals, today the Comune di Napoli's SUE (on "
                           f"impresainungiorno), from your documents{' or your private vault' if vault else ''}, "
                           "with the pratiche-napoli library of rules.",
            "source": {
                "source": "github",
                "repo": repo,
                "ref": f"plugin-v{version}",
                "sha": commit,
            },
        }],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--version", required=True)
    ap.add_argument("--commit", required=True, help="the plugin branch's commit for this version")
    ap.add_argument("--out", type=Path, default=HERE.parent / ".claude-plugin" / "marketplace.json")
    a = ap.parse_args()
    if not re.fullmatch(r"\d+\.\d+\.\d+([-+][0-9A-Za-z.-]+)?", a.version):
        ap.error(f"--version {a.version!r} isn't a version like 0.1.0")
    if not re.fullmatch(r"[0-9a-f]{40}", a.commit):
        ap.error("--commit must be a full commit SHA, 40 lower-case hex characters")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(marketplace(a.version, a.commit, vault=vault()), indent=2, ensure_ascii=False) + "\n")
    print(a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
