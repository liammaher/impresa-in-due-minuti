# Installing

**Status: released as [v0.3.0](https://github.com/liammaher/portali/releases/tag/v0.3.0)** (2026-11-05),
without the archive (`plugin/build.yaml` `vault: false`: the release builds no pvault); the
marketplace is pinned to it once the release's pull request is merged. 0.2.0 (2026-10-29) shipped
the archive. Installed in an isolated Claude config; not yet on a clean Mac or Windows (*What is not
done*). Work merged since is in the next release, not in 0.3.0.

## What you do

1. **Add the plugin.** In Claude Code:

   ```
   /plugin install portali --marketplace liammaher/portali
   ```

   (or `claude plugin marketplace add liammaher/portali`, then
   `claude plugin install portali@portali`).
2. **Say "set me up"** if you want the private vault. Claude asks before it downloads anything.
3. **Choose a password and keep the recovery key** on the page `pvault setup` opens in your browser,
   then turn on Touch ID there. This is the one step that is yours alone: neither is ever typed or
   shown in the conversation.

Pratiche that don't use the vault need no step 2 or 3: the folder-and-`values.json` way works as soon as
the plugin is installed.

## What happens, and what is checked

```
.claude-plugin/marketplace.json  --pinned by SHA-256-->  portali-<version>.zip  (a release asset)
portali-<version>.zip  contains  pvault-checksums.txt  (SHA-256 of each pvault archive of that release)
install-pvault.sh | .ps1  downloads  pvault_<version>_<os>_<arch>  and refuses it unless it matches
```

- The marketplace file is pinned to one release's zip, so Claude Code refuses a zip that isn't the one
  the release published. A pull request moves the pin at each release (`plugin/pin_marketplace.py`).
- The zip carries the checksums of the `pvault` downloads, so a swapped binary is refused even if the
  release page were tampered with. The checksum is not fetched with the download.
- The installer needs no admin rights, edits no PATH or shell profile (Windows: only with
  `-AddToPath`), unpacks one named file from the archive, and runs nothing but that `pvault`, to print
  its version.
- It installs to `~/.local/bin` (macOS, Linux) or `%LOCALAPPDATA%\Programs\pvault` (Windows).
  To remove pvault, delete that file; your vault lives in `~/.pvault` and is not touched.

## What is not done

- **Not signed or notarized.** On macOS the installer ad-hoc signs the binary, as `make build` does. A
  file fetched with `curl` is not quarantined, so Gatekeeper should not block it, and this needs no
  Apple developer account; that is **untried on a clean Mac**. On Windows the script is **untried**, and
  SmartScreen behaviour is unknown.
- **Touch ID**: release.yml builds the Swift helper on macOS (one universal binary) and the installer
  puts it next to pvault, checked like the rest and signed ad-hoc on the Mac; **untried from a real
  release** (the installer's test builds the helper itself).
- **No terminal (stage two, built)**: `pvault setup` opens a page in the default browser that creates the
  vault (or opens a locked one), shows the recovery key once and turns on Touch ID or Windows Hello. On
  a Mac with Touch ID a closed vault opens by fingerprint (`pvault unlock`); on Windows it is the page
  again. Creating, opening and the refusals are tested end to end on a Mac (`TestSetup_*`); the Touch ID
  and Windows Hello buttons are untried, since they need a person's fingerprint or face.
- **Python.** The skill runs its scripts through `sh py` (`plugin/portali/skills/portali-pratica/py`):
  the computer's own Python 3.9+ if there is one. Where there is none, `plugin/build.yaml`'s
  `python_download` decides: off (the default), it says how to install one (on a Mac it opens Apple's
  installer of the developer tools) and stops, and the plugin downloads nothing; on, it downloads
  python-build-standalone 3.12 (release 20261013) once into `~/.cache/portali` and runs it only if its
  SHA-256 is the one pinned there. `plugin/test_py.py` tests both builds offline. Untried: the download
  on a clean Mac, and anything on Windows (Git Bash's `sh`, `curl` and `tar`).
- **A listing in Anthropic's directory** (stage four) would make step 1 a single "Add".

## Releasing (maintainers)

1. Bump `version` in `plugin/portali/.claude-plugin/plugin.json`; the release workflow refuses a tag that
   differs from it.
2. Tag `vX.Y.Z` and push the tag. The workflow runs the tests, builds the six `pvault` archives and
   `checksums.txt` (goreleaser), builds the plugin with them and attaches it as `portali-X.Y.Z.zip`, then
   opens a pull request that pins `.claude-plugin/marketplace.json` to it.
3. Merge that pull request. Until then `marketplace add` finds no marketplace.
4. On a clean Mac and a clean Windows machine: add the marketplace, say "set me up", and check
   `pvault version`. (The installer's tests run against a fake release in CI:
   `plugin/test_install.py`.)
