#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python3"
LOG_DIR="$ROOT_DIR/data/logs"
OUT_JSON="$ROOT_DIR/data/yc_jobs_latest.json"
OUT_SUMMARY="$ROOT_DIR/data/yc_jobs_summary.txt"

mkdir -p "$LOG_DIR"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Missing virtualenv python at $PYTHON_BIN" >&2
  exit 1
fi

if [[ -f "$ROOT_DIR/.env" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
fi

if [[ -z "${TELEGRAM_CHAT_ID:-}" ]]; then
  echo "Missing TELEGRAM_CHAT_ID in $ROOT_DIR/.env" >&2
  exit 1
fi

if ! command -v openclaw >/dev/null 2>&1; then
  echo "openclaw CLI is required for Telegram send." >&2
  exit 1
fi

TS="$(date '+%Y-%m-%d_%H-%M-%S')"
LOG_FILE="$LOG_DIR/scrape_$TS.log"

SCRAPE_OUTPUT="$(
{
  echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Starting weekly scrape"
  "$PYTHON_BIN" "$ROOT_DIR/src/scrapers/yc_scraper.py" \
    --nyc-or-remote \
    --out "$OUT_JSON"
  echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Scrape complete"
} 2>&1
)"

echo "$SCRAPE_OUTPUT" | tee "$LOG_FILE"

"$PYTHON_BIN" "$ROOT_DIR/src/summarize_jobs.py" \
  --input "$OUT_JSON" \
  --out "$OUT_SUMMARY" \
  --max-jobs 5 >>"$LOG_FILE" 2>&1

SUMMARY_TEXT="$(cat "$OUT_SUMMARY")"
MESSAGE="Weekly YC scrape (NYC + Remote)

${SUMMARY_TEXT}"

openclaw message send \
  --channel telegram \
  --target "${TELEGRAM_CHAT_ID}" \
  --message "${MESSAGE}" >>"$LOG_FILE" 2>&1

echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Telegram send complete" | tee -a "$LOG_FILE"
