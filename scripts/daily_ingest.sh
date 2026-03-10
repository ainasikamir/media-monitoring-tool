#!/bin/zsh
set -euo pipefail

PROJECT_DIR="/Users/ajnazikamir/media_monitoring_tool"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/daily_ingest.log"

mkdir -p "$LOG_DIR"
cd "$PROJECT_DIR"

# Ensure Python environment is active.
source "$PROJECT_DIR/.venv/bin/activate"

# Start project-local Postgres on 5440 if needed.
if [ -d "$PROJECT_DIR/.pg/data" ]; then
  if ! /Library/PostgreSQL/18/bin/pg_isready -h localhost -p 5440 >/dev/null 2>&1; then
    /Library/PostgreSQL/18/bin/pg_ctl -D "$PROJECT_DIR/.pg/data" -l "$PROJECT_DIR/.pg/postgres.log" -o "-p 5440" start >/dev/null 2>&1 || true
  fi
fi

{
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting daily ingestion"
  python -m media_monitoring.ingest
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Completed daily ingestion"
} >> "$LOG_FILE" 2>&1
