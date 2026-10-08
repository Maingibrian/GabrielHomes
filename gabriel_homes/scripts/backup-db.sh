#!/usr/bin/env bash
# backup-db.sh — nightly PostgreSQL backup (PLAN D5)
#
# Reads DATABASE_URL (postgres://user:password@host:port/dbname), writes a
# gzipped pg_dump with a timestamp into ./backups/, keeps the newest 30 days
# of backups and deletes older ones. Exits non-zero on ANY failure so cron
# mail / systemd notices.
#
# Usage:
#   ./scripts/backup-db.sh                    # uses $DATABASE_URL
#   DATABASE_URL=... ./scripts/backup-db.sh --keep-days 14
#
# Cron (DEPLOY.md):
#   15 3 * * *  cd /srv/gabriel-homes && ./scripts/backup-db.sh >> var/backup.log 2>&1
set -euo pipefail

KEEP_DAYS=30
if [ "${1:-}" = "--keep-days" ] && [ -n "${2:-}" ]; then
  KEEP_DAYS="$2"
fi

: "${DATABASE_URL:?DATABASE_URL must be set, e.g. postgres://user:pass@host:5432/gabriel_homes}"

# Parse the URL. No host:port means the local socket defaults apply.
DB_USER=$(echo "$DATABASE_URL" | sed -n 's|^postgres://\([^:]*\):[^@]*@.*|\1|p')
DB_PASS=$(echo "$DATABASE_URL" | sed -n 's|^postgres://[^:]*:\([^@]*\)@.*|\1|p')
DB_HOST=$(echo "$DATABASE_URL" | sed -n 's|^postgres://[^@]*@\([^:/]*\).*|\1|p')
DB_PORT=$(echo "$DATABASE_URL" | sed -n 's|^postgres://[^@]*@[^:/]*:\([0-9]*\).*|\1|p')
DB_NAME=$(echo "$DATABASE_URL" | sed -n 's|^postgres://[^@]*/\([A-Za-z0-9_.-]*\)$|\1|p')

[ -n "$DB_NAME" ] || { echo "backup-db: could not parse DB name from DATABASE_URL" >&2; exit 1; }

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$REPO_DIR/backups"
mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
TARGET="$BACKUP_DIR/gabriel-homes-$STAMP.sql.gz"

export PGPASSWORD="${DB_PASS:-}"

PG_OPTS=(-w)  # never prompt — cron must not hang
[ -n "$DB_USER" ] && PG_OPTS+=(-U "$DB_USER")
[ -n "$DB_HOST" ] && PG_OPTS+=(-h "$DB_HOST")
[ -n "$DB_PORT" ] && PG_OPTS+=(-p "$DB_PORT")

# Dump straight into gzip; a truncated dump fails the pipeline.
pg_dump "${PG_OPTS[@]}" "$DB_NAME" | gzip > "$TARGET"

# Sanity: gzip must be complete and non-trivial in size.
gzip -t "$TARGET"
SIZE=$(stat -c%s "$TARGET" 2>/dev/null || stat -f%z "$TARGET")
if [ "$SIZE" -lt 500 ]; then
  echo "backup-db: dump suspiciously small ($SIZE bytes) — failing." >&2
  exit 1
fi

# Retention: remove backups older than KEEP_DAYS (POSIX-safe).
find "$BACKUP_DIR" -name 'gabriel-homes-*.sql.gz' -type f -mtime +"$KEEP_DAYS" -delete

echo "backup-db: wrote $TARGET ($SIZE bytes), keeping $KEEP_DAYS days."
