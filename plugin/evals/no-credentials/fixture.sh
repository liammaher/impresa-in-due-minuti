#!/usr/bin/env bash
# The folder of jobs: studio.json at its root, the made-up client's job in Fittizio/, with only
# the case's facts and roles answered, so pre-flight has questions to ask.
set -euo pipefail
job="$(cd "$(dirname "${BASH_SOURCE[0]}")/../_job" && pwd)"
cp "$job/studio.json" studio.json
mkdir Fittizio
cp -R "$job/files" Fittizio/files
cp "$job/values.json" Fittizio/values.json
python3 - "$job/answers.json" Fittizio/answers.json <<'PY'
import json, sys
a = json.load(open(sys.argv[1]))
keep = ("people", "descrizione", "fatti", "intervento", "cambio_uso", "paesaggio")
json.dump({k: v for k, v in a.items() if k in keep}, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
PY
