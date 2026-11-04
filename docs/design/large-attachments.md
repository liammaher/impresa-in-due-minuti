# Large attachments in the browser pane: the options (2026-11-04)

**Decided 2026-11-04: A.** Liam: one file pick at the start of the run is among the person's
steps. Built the same day (`askFiles` in inpage.js, `picked` in run.py, portal/README.md "Large
files: the person picks them"), tested offline on the fake portal, and run on the real portal the same day: a made-up CILA with a
5 MB and a 2 MB file, its folder picked once, filled in 127 s (`rehearsals/cila-fittizia` README).

North-star open question 7, written up for a decision. An architect's SUE pratica attaches its
drawings and relazioni: 1-5 MB a file is usual, and the portal takes up to 9.77 MB a file
(`run.py` `SLOT_MAX_BYTES`). In the Claude browser pane `run.js` is one tool call's text, so all of a
run's files may come to 256 KB (`PAGE_FILES_LIMIT`): a receipt or a small scan, never a planimetria.
Until this is settled, a real case with real drawings can't run all-or-nothing in the pane.

What the pane allows was tested on 2026-10-28 and 2026-11-01 (north-star-2026-10-27.md, question 7;
portal/README.md, Checking them all): its form tool can't set a file box; the portal's page can't
fetch or frame `localhost` (`net::ERR_BLOCKED_BY_CLIENT`, the app's own block); `window.open`
replaces the tab; a normal `https` fetch with CORS works; and **a file the person picks in a box on
the page is read by the page** (`pick.js`, every batch since 2026-11-01, an 848 KB bundle today,
checked by sha256 before it is used).

## The options

| | Option | Size | Client's files leave the computer? | Through the conversation? | Person's extra step | State |
|---|---|---|---|---|---|---|
| A | **The person picks the job's files once, in a box the runner shows** | any (the portal's 9.77 MB a file) | no | no: run.js carries names, sizes, sha256 | one pick, like typing the run's code | not built; its parts are (below) |
| B | The Playwright window (`run.py run`) | any | no | no | a second browser and a second SPID login | built, used by the first rehearsals |
| C | Cowork's own file tool, if it can fill a page's file box | any | no | no | none | untested (packaging.md, test 2) |
| D | A short-lived `https` URL per file (`--file-urls`) | any | **yes**, to whatever serves it | no | none | proven with a public gist (2026-10-29), then **removed** (2026-11-04): the client's files would leave the computer, and a host of ours is out (north-star "What doesn't bend" 1) |
| E | The architect attaches the big files by hand | any | no | no | every big slot, mid-run | possible today; breaks all-or-nothing |
| F | The bytes through the conversation in pieces | 256 KB a call | no | **yes**, and 5 MB is about 7 million base64 characters | none | not viable |

### A. The person picks the files (recommended)

How it would work: pre-flight already lists every file of the case with its path, size and type
(`files`, `pane_ok`). `run.py page` would put each large file in run.js as `{name, size, sha256,
picked: true}` instead of its bytes. When the run reaches its first such file, the runner opens a box
over the page, as it does for the code (`askCode`): "Choose these files from the job's folder", the
list of names, one `<input type=file multiple>` (or `webkitdirectory` for the whole folder). The page
reads each chosen file, keeps those whose name, size and sha256 match the list, says which are
missing or different, and `attach()` uploads them as it does the fetched ones (`fetched` already
checks size and sha256). Nothing leaves the computer except to the portal, Claude never sees a byte,
and nothing is stored.

Why it fits: it is the one way into the page the pane already proved, today, with a file larger than
the limit; the person's step is a pick, in the same window, at the start of the run, like the code
they type for a sealed run; and the sealed run's code box gives the same place to ask. The rule it
bends: "everything between login and the person's sign/send is automatic". A pick isn't a judgment,
and the runner checks every byte, but it is a step. That is the decision below.

What it takes: an `askFiles` beside `askCode` in inpage.js; `picked` entries in `page_files` and
pre-flight (files over the pane's limit are no longer `pane_ok: false` but "picked at the start");
the skill's wording; a test on the fake portal (`bench/test_inpage.py`: a 3 MB file picked through
Playwright's `set_input_files`, a wrong file refused, a missing one named); then one rehearsal on the
real portal with made-up drawings of real size (5 MB, several files). Roughly a day of work. Open: a
`.p7m` picked is checked by pre-flight first (who signed it), as now; a folder pick (`webkitdirectory`)
needs one check in the pane, where the app may limit it.

### B. The Playwright window

Works today for any size, from the same steps file, and it is what one-command runs of known
pratiche used from 2026-10-28. Against it for the product: it is a second browser beside the app,
with its own SPID login, while the product runs in the app's own browser (the Code tab's pane,
Cowork's). Keep it as the fallback the skill already names.

### C. Cowork's file tool

If Cowork's browser can put a file from the job's folder into the page's file box, it beats A: no
step at all. It is the second of packaging.md's Cowork tests, not run yet. It only helps in Cowork,
not in the Code tab's pane.

### D, E, F

D is proven but puts the client's drawings on a server, which the product's rules exclude; the
architect's own cloud share link is the same leak with less control (and the vault never stores a
sharing link). E is what the skill refuses today, because a half-automatic flow is worse than a
manual one. F can't carry a planimetria at all.

## The decision

1. Is one file pick at the start of the run, in the page, acceptable among the person's steps? If
   yes: build A, keep B as the fallback, run C when Cowork is tested and switch to it there if it
   passes.
2. If no: C first (untested), with B as the only all-automatic route meanwhile, and the skill keeps
   refusing a case whose files don't fit the pane.
