#!/usr/bin/env bash
# Backup the MariaDB database to a timestamped, gzipped dump in ./backups/.
# Keeps the newest 30 days by default.
#
# Usage:
#   DATABASE_URL=mysql://user:pass@host:3306/gabriel_homes ./scripts/backup-db.sh
#   ./scripts/backup-db.sh --keep-days 14
#
# Needs the MariaDB client tools (mariadb-dump) on the PATH.
set -euo pipefail

KEEP_DAYS=30
if [[ "${1:-}" == "--keep-days" ]]; then KEEP_DAYS="${2:?days}"; fi
: "${DATABASE_URL:?DATABASE_URL must be set, e.g. mysql://user:pass@host:3306/gabriel_homes}"

eval "$(python3 "$(dirname "$0")/_db_url.py" "$DATABASE_URL")"

DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$DIR"
STAMP=$(date +%Y%m%d-%H%M%S)
TARGET="$DIR/${DB_NAME}-${STAMP}.sql.gz"

# Password goes through an option file so it never appears in the process list.
CNF=$(mktemp)
trap 'rm -f "$CNF"' EXIT
printf '[client]\nuser=%s\npassword=%s\nhost=%s\nport=%s\n' \
  "$DB_USER" "$DB_PASS" "$DB_HOST" "$DB_PORT" > "$CNF"

mariadb-dump --defaults-extra-file="$CNF" --single-transaction --routines --triggers \
  --default-character-set=utf8mb4 "$DB_NAME" | gzip > "$TARGET"

echo "backup-db: wrote $TARGET ($(du -h "$TARGET" | cut -f1))"
find "$DIR" -name "${DB_NAME}-*.sql.gz" -mtime +"$KEEP_DAYS" -print -delete
