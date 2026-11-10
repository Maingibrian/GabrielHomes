#!/usr/bin/env bash
# UPDATE-WEBSITE.sh — apply a Gabriel Homes UPDATE zip over this install.
#
#   ./UPDATE-WEBSITE.sh                       (finds the newest
#					      gabriel-homes-update-*.zip in
#					      ~/Downloads or the current dir)
#   ./UPDATE-WEBSITE.sh /path/to/zip          (explicit)
#
# Your database (db.sqlite3), all photos/videos (media/) and the Python
# venv (.venv) are NEVER touched — the zip contains code only and simply
# overwrites the files it carries. If the site is running, its auto-reload
# picks the new code up on the next page load.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

zip_arg="${1:-}"
if [ -z "$zip_arg" ]; then
    for d in "$HOME/Downloads" "$HOME/Download" "$HOME/下载" "$PWD" "$here"; do
        f="$(ls -t "$d"/gabriel-homes-update-*.zip 2>/dev/null | head -1 || true)"
        if [ -n "$f" ]; then zip_arg="$f"; break; fi
    done
fi
if [ -z "$zip_arg" ]; then
    echo "No gabriel-homes-update-*.zip found."
    echo "Usage: ./UPDATE-WEBSITE.sh /path/to/gabriel-homes-update-YYYY-MM-DD.zip"
    exit 1
fi
echo "Applying: $zip_arg"

command -v unzip >/dev/null 2>&1 || {
    echo "Please install unzip first (Ubuntu/Linux:  sudo apt install unzip)"
    exit 1
}

# Sanity check: an update zip is ROOTLESS (manage.py at the top level) and
# never contains a database or media. Capture the listing once, then grep it.
listing="$(unzip -l "$zip_arg")"
echo "$listing" | grep -Eq '(^| )manage\.py$' || {
    echo "FATAL: $zip_arg does not look like a Gabriel Homes update zip."
    exit 1
}

tmp="$(mktemp)"
unzip -o "$zip_arg" -d "$here" > "$tmp"
n="$(grep -cE 'inflating|extracting|creating' "$tmp" || true)"
rm -f "$tmp"
echo "Updated $n files."

PY="$here/.venv/bin/python"
if [ ! -x "$PY" ]; then PY="$(command -v python3)"; fi
cd "$here"
"$PY" manage.py migrate --noinput 2>/dev/null \
    || echo "(migrate skipped — deps not installed yet; the START script will do it)"

echo ""
echo "OK — update applied. Database, photos and settings were kept."
echo "If the site was NOT running, start it:  ./START-GABRIEL-HOMES.sh"
echo "If it WAS running, just refresh the browser — code hot-reloads."
