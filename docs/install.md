# Installing

**Status:** the marketplace installs the release its file pins (the latest is on the
[releases page](https://github.com/liammaher/portale-sue/releases)). Since 0.3.0 the plugin ships
without the archive (`plugin/build.yaml` `vault: false`: the release builds no pvault); 0.2.0
(2026-10-29) shipped it. From 0.4.0 it is Portale SUE, the SUE's pratiche only; whoever has Portali
0.3.0 installs `portale-sue` once and removes `portali`. Installed in an isolated Claude config; not
yet on a clean Mac or Windows (*What is not done*).

Without the archive, Claude reads the job's documents and checks the draft against them, so the
client's details pass through the conversation (the plugin's README says so to the tecnico).

## What you do

1. **Add the plugin**, on a paid plan (Anthropic lists plugins for Pro, Max, Team and
   Enterprise). In the Claude app, with no terminal: **Customize → Plugins → Add → Add marketplace**,
   choose **Add from a repository**, type `liammaher/portale-sue`, pick it in the list, **Sync**, then
   **Add** on Portale SUE. Updates (how a remapped pratica or a portal-drift refusal reaches the
   tecnico) come by **Add → Manage marketplaces → ⋯ → Check for updates**, which works with no GitHub
   account (tried 2026-11-07: "Updated to 55ae7a9"). **Sync automatically** does not: on claude.ai it
   needs the person to grant Claude's GitHub app access («Concedi accesso»), stays off without it, and
   for personal marketplaces it does not fire even then (anthropics/claude-code#93825). It is saved to the account, so it is in chat,
   Cowork and Claude Code too. On a Team or Enterprise plan an owner can install it for everyone (or
   require it) instead. In Claude Code the same is
   `/plugin install portale-sue --marketplace liammaher/portale-sue`.

   One way only: there is no separate skill to upload. An uploaded skill has no update channel, so it
   would go stale the first time the portal changed.
2. **Open the folder of jobs** in the app, one subfolder per job. That is all today's plugin needs.

Only a build with the archive (`vault: true`, not today's releases) adds two steps: say "set me up"
(Claude asks before it downloads anything), then choose a password and keep the recovery key on the
page `pvault setup` opens in the browser, and turn on Touch ID there; neither is ever typed or shown
in the conversation. The rest of this page up to *Python* is about that archive.

## What happens, and what is checked

```
.claude-plugin/marketplace.json  --pinned by commit-->  plugin-v<version>  (the plugin branch)
the plugin  contains  pvault-checksums.txt  (SHA-256 of each pvault archive of that release)
install-pvault.sh | .ps1  downloads  pvault_<version>_<os>_<arch>  and refuses it unless it matches
```

- The marketplace file is pinned to one release's commit of the `plugin` branch (the built plugin,
  tagged `plugin-v<version>`), so a moved tag installs nothing else. A pull request moves the pin at
  each release (`plugin/pin_marketplace.py`). A git source because the Claude app takes only
  `github`, `url`, `git-subdir` and `./` sources: with the release zip (`archive`, which only
  Claude Code reads) "Add marketplace" failed in the app. The zip is still on each release, for
  **Upload plugin**.
- The plugin carries the checksums of the `pvault` downloads, so a swapped binary is refused even if the
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
- **Python.** The skill runs its scripts through `sh py` (`plugin/portale-sue/skills/portale-sue-pratica/py`):
  the computer's own Python 3.9+ if there is one. Where there is none, `plugin/build.yaml`'s
  `python_download` decides: off (the default), it says how to install one (on a Mac it opens Apple's
  installer of the developer tools) and stops, and the plugin downloads nothing; on, it downloads
  python-build-standalone 3.12 (release 20261013) once into `~/.cache/portale-sue` and runs it only if its
  SHA-256 is the one pinned there. `plugin/test_py.py` tests both builds offline. Untried: the download
  on a clean Mac, and anything on Windows (Git Bash's `sh`, `curl` and `tar`).
- **A listing in Anthropic's directory** (stage four) would make step 1 a single "Add".

## Releasing (maintainers)

1. Bump `version` in `plugin/portale-sue/.claude-plugin/plugin.json` (in a pull request, merged); the
   release workflow refuses a tag that differs from it.
2. On GitHub, **Actions → Release → Run workflow** on `main`: it tags `v<that version>` itself and runs
   the release (it refuses a version released already). Pushing a tag `vX.Y.Z` by hand does the
   same. The workflow runs the tests, builds the six `pvault` archives and
   `checksums.txt` (goreleaser), builds the plugin with them and attaches it as `portale-sue-X.Y.Z.zip`, commits the same build
   to the `plugin` branch as `plugin-vX.Y.Z` (`plugin/publish_plugin.py`), then opens a pull request
   that pins `.claude-plugin/marketplace.json` to that commit.
3. Merge that pull request (a bot's pull request gets no CI run, so it takes an admin merge). Until
   then the marketplace still installs the previous release.
4. On a clean Mac and a clean Windows machine: add the marketplace, install, and run one pratica's
   pre-flight; with the archive, also say "set me up" and check `pvault version`. (The installer's
   tests run against a fake release in CI: `plugin/test_install.py`.)
5. The private-terms check (`plugin/build.py`) runs only where the maintainer's list is, never in
   CI: build the released zip's tag locally, or unzip the release and run `check_private` on it. The
   `plugin` branch holds the same files, so a term found there means deleting the release and the
   `plugin-vX.Y.Z` tag and force-pushing `plugin` back to the commit before it.
