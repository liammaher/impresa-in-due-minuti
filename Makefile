.PHONY: build touchid test schema steps coverage install clean

# On macOS pvault is signed with the hardened runtime too: pvault-touchid sends
# the password only to a vault server running a hardened build, so no library
# can be injected into it through DYLD_* variables.
# pvault.exe on Windows (make from Git Bash or similar).
EXE := $(if $(filter Windows_NT,$(OS)),.exe,)

build:
	go build -o bin/pvault$(EXE) ./cmd/pvault
ifeq ($(shell uname),Darwin)
	codesign -s - -f -o runtime bin/pvault
	@$(MAKE) --no-print-directory touchid
endif

# Touch ID helper (macOS). Ad-hoc signed with the hardened runtime: the
# Keychain only lets this exact build read the saved password, so after
# rebuilding it run 'pvault touchid enable' again (also after moving pvault:
# the helper only trusts the pvault path saved then).
touchid:
	swiftc -O -swift-version 5 cmd/pvault-touchid/main.swift -o bin/pvault-touchid
	codesign -s - -f -o runtime bin/pvault-touchid

test:
	go test -v -race ./...

# schema.json is the recommended schema as 'pvault schema --json' prints it;
# pratiche-napoli's CI compares its copy with the one on main.
schema:
	go run ./cmd/pvault schema --json > schema.json

# The rehearsals' steps files are gen.py's build outputs, never committed: write them all and
# rehearsals/steps.lock (commit the lock). Needs the pratica venv (PyYAML).
steps:
	$(HOME)/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/regen.py

# docs/coverage.md and docs/ready.md (what the released plugin ships), written together from the same counts
# and date so they never drift. Needs the pratica venv (PyYAML); takes a few minutes.
coverage:
	$(HOME)/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/scoreboard.py --write

# Remove before copying: overwriting a signed binary in place can get the
# running copy killed by macOS.
install: build
	rm -f /usr/local/bin/pvault && install -m 755 bin/pvault /usr/local/bin/pvault
ifeq ($(shell uname),Darwin)
	rm -f /usr/local/bin/pvault-touchid && install -m 755 bin/pvault-touchid /usr/local/bin/pvault-touchid
endif

clean:
	rm -rf bin/
