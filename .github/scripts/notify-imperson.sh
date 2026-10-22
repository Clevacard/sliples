#!/usr/bin/env bash
# Notify imperson about a pipeline stage. Never fails the pipeline.
# Usage: notify-imperson.sh <stage> <phase> [status]
#   stage:  build | test | deploy
#   phase:  STARTED | COMPLETED
#   status: SUCCESS | FAILURE | ABORTED   (with COMPLETED)
# Env: IMPERSON_WEBHOOK_URL (full jenkins-webhook URL incl. ?token=...), GITHUB_* (set by Actions)
set -uo pipefail

stage="${1:?stage}"; phase="${2:?phase}"; status="${3:-}"

if [ -z "${IMPERSON_WEBHOOK_URL:-}" ]; then
  echo "IMPERSON_WEBHOOK_URL not set; skipping notification"
  exit 0
fi

# imperson's jenkins webhook takes Notification-plugin JSON; one job per stage.
payload=$(jq -n \
  --arg name "sliples-$stage" \
  --arg url "job/sliples/job/$stage/" \
  --argjson number "${GITHUB_RUN_NUMBER:-0}" \
  --arg phase "$phase" \
  --arg status "$status" \
  --arg full_url "${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY:-}/actions/runs/${GITHUB_RUN_ID:-}" \
  '{name: $name, url: $url,
    build: ({number: $number, phase: $phase, full_url: $full_url}
            + (if $status != "" then {status: $status} else {} end))}')

code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 15 \
  -X POST -H 'Content-Type: application/json' -d "$payload" "$IMPERSON_WEBHOOK_URL") \
  || code="curl-failed"
echo "imperson notify sliples-$stage $phase $status -> $code"
exit 0
