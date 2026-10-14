#!/usr/bin/env bash
# One-pass history slim-down for /home/z/my-project (2026-10-14):
# purges DELIVERABLE ARTIFACTS from all git history so the session backup
# bundle stays small. Working tree is NOT touched (index-filter only).
#
# Purged from history: download/** (old oneclick zips + archive),
#   gabriel_homes/wheels/ (regenerable via scripts/vendor_wheels.sh),
#   scripts/preview_site/files/*.zip (update zips), scripts/design-audit/.
# Kept: all site media (img/video/fonts), code, docs, page screenshots (png).
set -euo pipefail
cd /home/z/my-project

export FILTER_BRANCH_SQUELCH_WARNING=1

git filter-branch -f --index-filter '
  git rm -r --cached --ignore-unmatch -q download gabriel_homes/wheels scripts/design-audit 2>/dev/null || true
  zips=$(git ls-files -- "scripts/preview_site/files/*.zip" 2>/dev/null || true)
  if [ -n "$zips" ]; then git rm --cached -q --ignore-unmatch $zips; fi
' -- --all

echo "--- verify: no artifact paths left in any commit ---"
fail=0
for p in download gabriel_homes/wheels scripts/design-audit; do
  if git log --all --oneline -- "$p" | head -1 | grep -q .; then
    echo "FAIL: $p still in history"; fail=1
  else
    echo "OK: $p purged"
  fi
done
if git log --all --oneline -- 'scripts/preview_site/files/*.zip' | head -1 | grep -q .; then
  echo "FAIL: preview zips still in history"; fail=1
else
  echo "OK: preview zips purged"
fi
[ "$fail" -eq 0 ] || exit 1

echo "--- tree diff vs backup (expect ONLY deletions of purged paths) ---"
git diff --stat refs/original/refs/heads/master..master | tail -5

echo "--- expire reflog + gc ---"
git reflog expire --expire=now --all
git gc --prune=now --quiet
git count-objects -vH | grep size-pack
echo "SLIM DONE"
