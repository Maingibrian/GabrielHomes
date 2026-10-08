#!/usr/bin/env bash
# restore-drill.sh — prove that backups actually restore (PLAN D5)
#
# A backup that has never been restored is a hope, not a plan. This drill:
#   1. takes the newest backup from backups/
#   2. restores it into a scratch database gabriel_restore_test
#   3. points Django at the scratch DB and runs manage.py check + showmigrations
#   4. drops the scratch database
#
# Needs a reachable PostgreSQL (the same instance used for PLAN D2).
# Usage:  DATABASE_URL=postgres://user:pass@host:5432/gabriel_homes ./scripts/restore-drill.sh
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL must be set, e.g. postgres://user:pass@host:5432/gabriel_homes}"

DB_USER=$(echo "$DATABASE_URL" | sed -n 's|^postgres://\([^:]*\):[^@]*@.*|\1|p')
DB_PASS=$(echo "$DATABASE_URL" | sed -n 's|^postgres://[^:]*:\([^@]*\)@.*|\1|p')
DB_HOST=$(echo "$DATABASE_URL" | sed -n 's|^postgres://[^@]*@\([^:/]*\).*|\1|p')
DB_PORT=$(echo "$DATABASE_URL" | sed -n 's|^postgres://[^@]*@[^:/]*:\([0-9]*\).*|\1|p')
DB_NAME=$(echo "$DATABASE_URL" | sed -n 's|^postgres://[^@]*/\([A-Za-z0-9_.-]*\)$|\1|p')

SCRATCH="gabriel_restore_test"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$REPO_DIR/backups"

NEWEST=$(ls -1t "$BACKUP_DIR"/gabriel-homes-*.sql.gz 2>/dev/null | head -n 1 || true)
[ -n "$NEWEST" ] || { echo "restore-drill: no backup found in $BACKUP_DIR — run scripts/backup-db.sh first." >&2; exit 1; }
echo "restore-drill: using $NEWEST"

export PGPASSWORD="${DB_PASS:-}"
PSQL_OPTS=(-w -v ON_ERROR_STOP=1)
[ -n "$DB_USER" ] && PSQL_OPTS+=(-U "$DB_USER")
[ -n "$DB_HOST" ] && PSQL_OPTS+=(-h "$DB_HOST")
[ -n "$DB_PORT" ] && PSQL_OPTS+=(-p "$DB_PORT")

cleanup() {
  echo "restore-drill: dropping scratch database $SCRATCH"
  psql "${PSQL_OPTS[@]}" -d postgres -c "DROP DATABASE IF EXISTS $SCRATCH;" >/dev/null || true
}
trap cleanup EXIT

cleanup
echo "restore-drill: creating scratch database $SCRATCH"
psql "${PSQL_OPTS[@]}" -d postgres -c "CREATE DATABASE $SCRATCH;"

echo "restore-drill: restoring backup"
gunzip -c "$NEWEST" | psql "${PSQL_OPTS[@]}" -d "$SCRATCH" >/dev/null

echo "restore-drill: running Django checks against the restored copy"
export GABRIEL_RESTORE_DB="$SCRATCH"
( cd "$REPO_DIR" && \
  DATABASE_URL="postgres://${DB_USER}:${DB_PASS:-}@${DB_HOST:-localhost}:${DB_PORT:-5432}/$SCRATCH" \
  DJANGO_SETTINGS_MODULE=config.settings.prod \
  SECRET_KEY="${SECRET_KEY:-drill-only-not-a-real-key-0123456789abcdef}" \
  ALLOWED_HOSTS=localhost \
  .venv/bin/python manage.py check && \
  .venv/bin/python manage.py showmigrations --list >/dev/null && \
  echo "restore-drill: check + showmigrations OK" )

echo "restore-drill: SUCCESS — backup is restorable."
