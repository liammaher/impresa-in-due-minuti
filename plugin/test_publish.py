#!/usr/bin/env python3
"""publish_plugin.py and pin_marketplace.py against a local bare repository: each release is one
commit on the `plugin` branch over the one before, tagged plugin-v<version>, with the built files
exactly (modes too); a version is never published twice; the marketplace pins that commit."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pin_marketplace  # noqa: E402
import publish_plugin  # noqa: E402


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def built(root, version):
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": "impresa-in-un-minuto", "version": version}))
    (root / "skills" / "s").mkdir(parents=True)
    (root / "skills" / "s" / "SKILL.md").write_text(f"v{version}\n")
    (root / "skills" / "s" / "py").write_text("#!/bin/sh\n")
    (root / "skills" / "s" / "py").chmod(0o755)
    (root / ".gitignore").write_text("*.md\n")  # shipped as built, never applied
    return root


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
               "GIT_COMMITTER_EMAIL": "t@t", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        os.environ.update(env)
        remote, work = tmp / "remote.git", tmp / "work"
        git("init", "-q", "--bare", str(remote), cwd=tmp)
        git("init", "-q", str(work), cwd=tmp)
        git("remote", "add", "origin", str(remote), cwd=work)
        os.chdir(work)
        # A branch and a tag whose names end the same are not the plugin's (ls-remote matches tails).
        decoy = built(tmp / "decoy", "0.1.0")
        git("init", "-q", cwd=decoy)
        git("add", "-A", "-f", cwd=decoy)
        git("commit", "-q", "-m", "decoy", cwd=decoy)
        git("push", "-q", str(remote), "HEAD:refs/heads/claude/plugin", "HEAD:refs/tags/x/plugin-v0.1.0", cwd=decoy)

        first =publish_plugin.publish("0.1.0", built(tmp / "b1", "0.1.0"), push=True)
        second = publish_plugin.publish("0.1.1", built(tmp / "b2", "0.1.1"), push=True)
        assert git("rev-parse", "plugin", cwd=remote) == second
        assert git("rev-parse", f"{second}^", cwd=remote) == first
        assert git("rev-parse", "plugin-v0.1.0^{commit}", cwd=remote) == first
        files = git("ls-tree", "-r", second, cwd=remote).splitlines()
        assert any(l.startswith("100755") and l.endswith("skills/s/py") for l in files), files
        assert any(l.endswith("skills/s/SKILL.md") for l in files), files  # .gitignore not applied
        assert git("show", f"{second}:skills/s/SKILL.md", cwd=remote) == "v0.1.1"
        assert git("status", "--porcelain", cwd=work) == ""

        for case, args in (("a version published already", ("0.1.1", tmp / "b2")),
                           ("a version its plugin.json doesn't say", ("0.2.0", tmp / "b2"))):
            try:
                publish_plugin.publish(*args, push=True)
            except SystemExit:
                print("ok:", case, "is refused")
            else:
                raise AssertionError(f"published {case}")

        src = pin_marketplace.marketplace("0.1.1", second)["plugins"][0]["source"]
        assert src == {"source": "github", "repo": "liammaher/impresa-in-un-minuto", "ref": "plugin-v0.1.1", "sha": second}, src
    print("ok: publish and pin")


if __name__ == "__main__":
    main()
