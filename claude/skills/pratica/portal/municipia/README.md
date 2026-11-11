# Municipia's portals for Napoli: the catalogue

What the Comune di Napoli's other citizen portals are made of, read by program from the public files a
browser loads, so a screen can be understood before anyone signs in. The analogue of `../catalogue/` for
impresainungiorno; the dictionary and steps files that follow from it are not written yet.

## The two apps

| App | Hosts | What it is |
|---|---|---|
| Portale Multiservizi (`fe-cittadino`) | `cizrm.municipia.eng.it`, `portaletributi.comune.napoli.it` | One build under two names (`same_main_file_as` in `multiservizi.json`). Angular with module federation (shared, smart, tax, urban). Pagamenti, Domande Online, Documenti, deleghe, tax pages. |
| GEIS Portal | `geis-web-portal.municipia.eng.it` | The gestori's imposta di soggiorno app. Older Angular with lazy chunks and a JSON backend under `/rest/`. Named by the first app's configuration (`urlPortaleGeis`); the login carries over. |

Menus are gated by role in the code (`GESTORE_STRUTTURA`, `DELEGATO_STRUTTURA`, `CITTADINO`,
`Internal/INTERMEDIARIO`, `Internal/DELEGATO`, ...): a plain citizen account sees no GEIS menu until the
Comune approves "Nuovo gestore struttura".

## Files

- `extract.py run`: one pass over the public files, no login; writes `catalogue/napoli/<app>.json`: the build's
  files with their sha256 (`build`), the menu's routes with titles and roles, the lazy modules' router segments,
  and per file the screens (component selectors), labels (up to 100 characters: labels, not help prose), backend
  paths named in the code and the messages the code shows. `multiservizi.json` also holds the two translation
  files and the remotes' exposed features.
- `extract.py check`: compares the file names served now with the catalogue's `build.roots` (a build's file
  names carry a content hash); exit 1 means a build changed and the catalogue needs a new run and a look.
- `catalogue/napoli/domande-online/models.json`: the Domande Online models the portal lists, by area.
- `catalogue/napoli/domande-online/GESTORE.json`: the "Nuovo gestore struttura" form's fields (Formly code, type,
  required, label, options, step), read from the rendered page in the browser pane while signed in as an ordinary
  citizen. Nothing was entered, saved or sent, and no value was read.

## Rules

- Read-only and public: the page's HTML, JavaScript and translations, at one visitor's pace. Never a backend
  call, a sign-in, a guessed URL or a person's value. The backend paths in the catalogue are strings found in
  the code, to understand a screen and to write tests, not to call.
- A model or screen the account is not offered is not opened by another route (the three NAPG models, the GEIS
  menu): mapping those needs the role, through the page.
- The person's own acts stay theirs: the SPID login, the privacy consent, Send, payment, a signature.
- The catalogue holds nothing of a person: `bench/test_municipia.py` checks the form's file for a value, and the
  repo's private-terms scan covers the rest.

## Not mapped yet

- The gestore's screens' live behaviour: the declaration's rows for a structure, the draft state in practice,
  what the guest-file import (Tracciato Ospiti) saves, delegate login. Needs a gestore or delegate session.
- The three NAPG forms, the Persona giuridica set of the registration form, its address search.
- The citizen portal's Pagamenti and tax screens beyond their code (`/personale/pagamenti/*`,
  `/personale/domandeonline/dichiarazioneimutari`), the `INTERMEDIARIO` and `DELEGATO` roles' pages.
- Other comuni on the same platform: the build is shared, the configuration is not.
- Each portal's terms on automation (`NOTICE.md`: not checked).

## Tests

`python3 claude/skills/pratica/portal/bench/test_municipia.py`: the parsers on text shaped like the portals' code
(no network) and the committed catalogue.
