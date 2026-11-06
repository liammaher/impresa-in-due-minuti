#!/usr/bin/env bash
# The made-up CILA job after a compilation that stopped and wasn't recovered: its report in run/,
# and the job's values beside it, as the skill leaves them. The folder bears the client's surname,
# as a tecnico's folders often do.
set -euo pipefail
job="$(cd "$(dirname "${BASH_SOURCE[0]}")/../_job" && pwd)"
cp "$job/studio.json" studio.json
mkdir -p Fittizio/run
cp -R "$job/files" Fittizio/files
cp "$job/values.json" Fittizio/values.json
cp "$job/answers.json" Fittizio/answers.json
python3 - "$job/studio.json" "$job/values.json" Fittizio/run/values.json <<'PY'
import json, sys
merged = json.load(open(sys.argv[1])) | json.load(open(sys.argv[2]))
json.dump(merged, open(sys.argv[3], "w"), ensure_ascii=False, indent=1)
PY
cat > Fittizio/run/report.json <<'JSON'
{"result": "stopped", "pratica": "cila", "error": "0 fields with this label: Foglio (block: Dati catastali dell'immobile)", "at": {"section": 6, "title": "Dati catastali", "field": 2, "label": "Foglio"}, "fixes_tried": 2, "draft": "CILA-2026-11-06-0912"}
JSON
