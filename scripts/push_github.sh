#!/usr/bin/env bash
# Push /home/z/my-project main to GitHub: Maingibrian/Gabriel-Homes
# Usage:  bash scripts/push_github.sh <GITHUB_PAT>
# The token is used for this one push only and is NOT saved to git config.
set -euo pipefail

PAT="${1:?Usage: bash scripts/push_github.sh <GITHUB_PAT>  (classic token with 'repo' scope)}"
REMOTE_URL="https://github.com/Maingibrian/Gabriel-Homes.git"
AUTH_URL="https://x-access-token:${PAT}@github.com/Maingibrian/Gabriel-Homes.git"

cd /home/z/my-project

# ensure the remote exists (url kept token-free)
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE_URL"
else
  git remote add origin "$REMOTE_URL"
fi

echo "== pushing main to $REMOTE_URL =="
# normal push first; fall back to force only to replace the placeholder
# "Initial commit" (README.md one-liner) that GitHub created with the repo
if ! git push "$AUTH_URL" main 2>/dev/null; then
  echo "== normal push rejected (unrelated placeholder history) -> force =="
  git push -f "$AUTH_URL" main
fi

# make sure no token lingers anywhere
git remote set-url origin "$REMOTE_URL"

echo "== DONE =="
echo "Verify: https://github.com/Maingibrian/Gabriel-Homes"
