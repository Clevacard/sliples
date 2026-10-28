#!/usr/bin/env bash
# Notify imperson about a pipeline stage. Never fails the pipeline.
# Usage: notify-imperson.sh <stage> <phase> [status]
#   stage:  build | test | deploy
#   phase:  STARTED | COMPLETED
#   status: SUCCESS | FAILURE | ABORTED   (required with COMPLETED, omitted with STARTED)
# Env: IMPERSON_CI_TOKEN (GitHub secret; skips notification when unset), GITHUB_* (set by Actions)
set -uo pipefail

stage="${1:?stage}"; phase="${2:?phase}"; status="${3:-}"
endpoint="https://imperson.agantis.in/api/v1/webhooks/team/ci"

if [ -z "${IMPERSON_CI_TOKEN:-}" ]; then
  echo "IMPERSON_CI_TOKEN not set; skipping notification"
  exit 0
fi

payload=$(jq -n \
  --arg project "sliples" \
  --arg stage "$stage" \
  --arg phase "$phase" \
  --arg status "$status" \
  --argjson run_number "${GITHUB_RUN_NUMBER:-0}" \
  --argjson run_attempt "${GITHUB_RUN_ATTEMPT:-1}" \
  --arg run_url "${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY:-}/actions/runs/${GITHUB_RUN_ID:-}" \
  --arg sha "${GITHUB_SHA:-}" \
  --arg ref "${GITHUB_REF_NAME:-main}" \
  '{source: "github-actions", project: $project, stage: $stage, phase: $phase,
    run_number: $run_number, run_attempt: $run_attempt,
    run_url: $run_url, sha: $sha, ref: $ref}
    + (if $status != "" then {status: $status} else {} end)')

# Token goes in a header read from stdin so it never appears in the process list.
# Log the response body too: imperson answers 200 for "ignored" as well as "processed".
response=$(printf 'header = "X-CI-Token: %s"\n' "$IMPERSON_CI_TOKEN" \
  | curl -sS -w '\n%{http_code}' --max-time 15 \
      -K - -X POST -H 'Content-Type: application/json' -d "$payload" "$endpoint") \
  || response="curl-failed"
echo "imperson notify sliples-$stage $phase ${status:--} -> ${response//$'\n'/ }"
exit 0
