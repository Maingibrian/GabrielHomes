#!/usr/bin/env bash
# One-pass history rewrite for /home/z/my-project (workspace snapshot repo):
#   1) reword bare-UUID commit messages into Task-ID messages (scripts/git_reword_map.txt)
#   2) purge .env (contains DATABASE_URL) from every commit
# Idempotent-ish: run only when refs/original does not exist.
set -euo pipefail

REPO=/home/z/my-project
MAP="$REPO/scripts/git_reword_map.txt"

cd "$REPO"

if git show-ref --verify --quiet refs/original/refs/heads/master; then
  echo "ERROR: refs/original backup already exists — rewrite already ran. Aborting." >&2
  exit 1
fi

export FILTER_BRANCH_SQUELCH_WARNING=1
export MAP

git filter-branch -f \
  --index-filter 'git rm --cached --ignore-unmatch -q .env' \
  --msg-filter '
    msg=$(cat)
    new=$(awk -F"\t" -v h="$GIT_COMMIT" "\$1==h {print \$2}" "$MAP")
    if [ -n "$new" ]; then printf "%s\n" "$new"; else printf "%s" "$msg"; fi
  ' \
  -- --all

echo "--- post-rewrite log ---"
git log --oneline --reverse | head -20

echo "--- verify .env purged from ALL history ---"
if git log --all --oneline -- .env | head -1 | grep -q .; then
  echo "FAIL: .env still referenced in history:"; git log --all --oneline -- .env; exit 1
else
  echo "OK: no commit in any branch touches .env"
fi

echo "--- tree diff vs backup (expect ONLY .env deletion) ---"
git diff --stat refs/original/refs/heads/master..master | tail -3
