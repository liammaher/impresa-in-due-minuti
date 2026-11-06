#!/usr/bin/env bash
# A tecnico's first job, as his wife's was on 2026-11-06: a folder of jobs with no studio details
# yet, the client's job with no values and no draft name, only the case's facts and roles
# answered, and no documents. They call it a test, so everything must be invented.
set -euo pipefail
job="$(cd "$(dirname "${BASH_SOURCE[0]}")/../_job" && pwd)"
printf '{"tecnico:ruolo.tipo": "titolare"}\n' > studio.json
mkdir Fittizio
printf '{}\n' > Fittizio/values.json
python3 - "$job/answers.json" Fittizio/answers.json <<'PY'
import json, sys
a = json.load(open(sys.argv[1]))
keep = ("people", "fatti", "intervento", "cambio_uso", "paesaggio")
json.dump({k: v for k, v in a.items() if k in keep}, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
PY
