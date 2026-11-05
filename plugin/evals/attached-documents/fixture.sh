#!/usr/bin/env bash
# The folder of jobs with the studio only, and the made-up client's documents where an upload
# leaves them (caricati/), outside any job's subfolder.
set -euo pipefail
job="$(cd "$(dirname "${BASH_SOURCE[0]}")/../_job" && pwd)"
cp "$job/studio.json" studio.json
mkdir caricati
cp "$job"/files/*.pdf caricati/
