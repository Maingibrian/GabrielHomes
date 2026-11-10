#!/usr/bin/env bash
# Restore drill: load the newest backup into a scratch database and check it.
# Never touches the live database. Run this at least monthly.
#
# Usage:
#   DATABASE_URL=mysql://user:pass@host:3306/gabriel_homes ./scripts/restore-drill.sh
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL must be set}"
eval "$(python3 "$(dirname "$0")/_db_url.py" "$DATABASE_URL")"

DIR="${BACKUP_DIR:-./backups}"
NEWEST=$(ls -1t "$DIR"/"${DB_NAME}"-*.sql.gz 2>/dev/null | head -n1 || true)
[ -n "$NEWEST" ] || { echo "restore-drill: no backup found in $DIR" >&2; exit 1; }

SCRATCH="${DB_NAME}_restore_drill"
CNF=$(mktemp)
trap 'rm -f "$CNF"' EXIT
printf '[client]\nuser=%s\npassword=%s\nhost=%s\nport=%s\n' \
  "$DB_USER" "$DB_PASS" "$DB_HOST" "$DB_PORT" > "$CNF"

mariadb --defaults-extra-file="$CNF" -e "DROP DATABASE IF EXISTS \`$SCRATCH\`; CREATE DATABASE \`$SCRATCH\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
gunzip -c "$NEWEST" | mariadb --defaults-extra-file="$CNF" "$SCRATCH"

TABLES=$(mariadb --defaults-extra-file="$CNF" -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$SCRATCH';")
echo "restore-drill: restored $(basename "$NEWEST") into $SCRATCH ($TABLES tables)"
[ "$TABLES" -gt 0 ] || { echo "restore-drill: FAILED, no tables restored" >&2; exit 1; }

mariadb --defaults-extra-file="$CNF" -e "DROP DATABASE \`$SCRATCH\`;"
echo "restore-drill: OK, scratch database removed"
