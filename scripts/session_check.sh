#!/usr/bin/env bash
# SESSION TRIPWIRE — run FIRST in every session (rule 1 of WORK.md).
#
# Detects a sandbox disk rollback by comparing the LAST_COMMIT recorded in
# WORK.md against real git history.
#
# Why not exact-hash equality? A commit cannot contain its own hash (writing
# the hash into WORK.md changes the commit, changing the hash). So the check
# is: the recorded commit must EXIST and be an ANCESTOR of HEAD.
#   - normal new work  -> recorded commit stays an ancestor -> OK, no noise
#   - sandbox rollback -> recorded commit missing / not an ancestor -> FAIL
#
# Exit codes: 0 = OK, 1 = ROLLBACK DETECTED, 2 = baseline not set yet.
set -u
cd "$(dirname "$0")/.."

rec=$(grep -m1 '^LAST_COMMIT:' WORK.md | awk '{print $2}')
if [ -z "$rec" ] || [ "$rec" = "PENDING" ]; then
  echo "WARN: WORK.md has no LAST_COMMIT baseline yet (fresh repo?)."
  echo "It gets set right after the first commit of a session."
  exit 2
fi

if ! git cat-file -e "${rec}^{commit}" 2>/dev/null; then
  echo "ROLLBACK DETECTED: recorded commit $rec does not exist in this repo."
  echo "The sandbox disk is OLDER than the last recorded session."
  echo "STOP. Tell the user. Restore per REBUILD.md step 1 (git bundle)."
  exit 1
fi
if ! git merge-base --is-ancestor "$rec" HEAD 2>/dev/null; then
  echo "ROLLBACK DETECTED: HEAD is NOT a descendant of recorded $rec."
  echo "History diverged or was rolled back. STOP. Tell the user."
  echo "Restore per REBUILD.md step 1."
  exit 1
fi

echo "OK: history contains recorded commit $rec (LAST_COMMIT)."
git log -3 --format='  %h %ad %s' --date=format:'%Y-%m-%d %H:%M'
