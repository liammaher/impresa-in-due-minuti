---
name: portali-setup
description: Configura Portali su questo computer - installa l'archivio cifrato (pvault, verificato con il checksum che il plugin porta con sé), lo crea o lo apre in una pagina del browser e attiva Touch ID o Windows Hello, senza terminale. Use when the user says "configura Portali", "set me up", asks to set up, install, open or update the archive (vault, pvault), or when a pratica needs the archive and it isn't installed, created, open or confirmable.
---

# Configurare Portali

The archive (pvault) keeps the tecnico's, the studio's and the clients' details on their own
computer, encrypted, so a portal is filled from it without the details passing through this
conversation. This skill installs it, has the tecnico create it (or open it) in a page of their
browser, and turns on Touch ID (Mac) or Windows Hello (Windows). It needs a shell on their own
computer (the Claude desktop app's Code tab); in a sandbox with no access to it (Cowork's) say so
in one line and stop: `portali-pratica` then works from a folder.

Speak Italian to the tecnico, as Lei, with no software words: "l'archivio", "la pagina", "la
password", "la chiave di recupero", "Touch ID". Never "vault", "pvault", "server", "checksum",
"PATH", "token".

## 1. Is it installed?

Run `pvault version`; if it isn't found, `~/.local/bin/pvault version` (macOS, Linux) or
`%LOCALAPPDATA%\Programs\pvault\pvault.exe version` (Windows). If it prints the version in
`pvault.version` next to this file, go to step 3 (a `dev` version is a build from source: leave it
alone). On a Mac, `pvault touchid status` saying the helper isn't installed also means step 2.

## 2. Install it, with their yes

A download needs their explicit yes. Ask once, in Italian, saying what it is:

> Scarico il programma dell'archivio (pvault <version>, per <Mac / Windows / Linux>) dalla pagina
> ufficiale del progetto su GitHub: qualche decina di MB. Prima di installarlo controllo che sia
> identico a quello atteso, poi lo metto nella sua cartella utente. Non servono permessi di
> amministratore e non cambia nient'altro sul computer. Procedo?

On yes, run the script next to this file, as it is:

- macOS, Linux: `sh install-pvault.sh` (on a Mac it also installs the Touch ID helper)
- Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File install-pvault.ps1`

Its last line is `PVAULT_PATH=<where it is>`: use that path from here on if `pvault` isn't on the
PATH. Don't edit the PATH or a shell profile unless they ask.

If it says `checksum mismatch`, **stop**: tell them plainly that the download wasn't the expected
one and nothing was installed. Don't retry from elsewhere, don't skip the check, don't download by
hand. If it says there is no release to install from, this copy was built from source: say so.

## 3. Create or open it, in their browser

Run `pvault setup --impresa` (a studio's archive: the studio, the tecnico and the clients). It
opens a page in their default browser and waits until they finish there (at most 15 minutes), so
run it in the background and tell them first:

> Si è aperta una pagina nel suo browser. Lì sceglie la password dell'archivio (o la scrive, se
> l'archivio c'è già), conserva la chiave di recupero e attiva Touch ID. Quando la pagina dice
> «Fatto», torni qui.

- Never open that page in the Claude browser pane, never read it, and never ask them to type the
  password, the key or anything from that page into this conversation.
- When it ends it prints `Vault: created`, `Open: true` and whether Touch ID (or Windows Hello)
  is `on`: nothing secret. If it closed with the archive still closed or Touch ID off, run it
  again once they're ready.
- A closed archive later (it closes itself after 30 minutes unused): on a Mac with Touch ID,
  `pvault unlock` opens it with their fingerprint; on Windows, `pvault setup` again, where they
  type the password.

## 4. Their details

The studio's details (denominazione, partita IVA, sede, PEC) and the tecnico's (dati anagrafici,
albo, residenza) go in once. Run `pvault ui`: it opens the archive's page in their browser, where
they type them (it asks the password once more). You see nothing of it; `pvault list` then shows
which fields exist, not their values. Or leave it: the first pratica's pre-flight lists what's
missing, and they can fill it then.

## 5. Say what's next

One line, in Italian: the archive is ready, each pratica will ask Touch ID once to read what it
needs, and you will only ever see which details exist, never what they are.
