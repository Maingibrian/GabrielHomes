#!/usr/bin/env bash
# r102 push-safety sweep — MANDATORY before every push (see .agents/memory/lessons.md).
# Usage:
#   scripts/push_safety_check.sh              # generic pre-push sweep (run before ANY push)
#   scripts/push_safety_check.sh --audit-pat  # + PAT-incident audit (r102 one-off)
#   scripts/push_safety_check.sh --verify-clean  # post-push verification (r102 one-off)
# Exits 1 if a secret pattern is found where it must not be.
# NEVER prints secret values — only file names, counts and HTTP status codes.
set -u
cd "$(git rev-parse --show-toplevel)"

PATTERNS='github_pat_[A-Za-z0-9_]+|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|ghs_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|xox[bap]-[A-Za-z0-9-]{10,}'
FAIL=0

echo "== push range (what would go up) =="
git fetch origin main >/dev/null 2>&1 || true
git log --oneline origin/main..HEAD 2>/dev/null | sed 's/^/  /' || true
[ -z "$(git log origin/main..HEAD 2>/dev/null)" ] && echo "  (nothing ahead of origin/main)"

echo "== [1] secret-pattern sweep over HEAD tree =="
hits=$(git grep -lE "$PATTERNS" HEAD -- . 2>/dev/null || true)
if [ -n "$hits" ]; then echo "  FAIL:"; printf '%s\n' "$hits" | sed 's/^/    /'; FAIL=1; else echo "  clean"; fi

echo "== [2] tracked token-shaped files under upload/ =="
tok=$(git ls-files -- 'upload/*pat*.txt' 'upload/*.pem' 'upload/*.key' 'upload/*token*' 2>/dev/null || true)
if [ -n "$tok" ]; then echo "  FAIL:"; printf '%s\n' "$tok" | sed 's/^/    /'; FAIL=1; else echo "  clean"; fi

echo "== [3] local git config / credential stores =="
for f in "$HOME/.git-credentials" "$HOME/.gitconfig" ".git/config"; do
  if [ -f "$f" ]; then
    if grep -qE "$PATTERNS" "$f" 2>/dev/null; then echo "  FAIL: token present in $f"; FAIL=1
    else echo "  $f: clean"; fi
  fi
done
echo "  credential.helper: $(git config --get credential.helper || echo '(none)')"

if [ "${1:-}" = "--audit-pat" ]; then
  echo "== [audit] PAT incident specifics =="
  INTRO=15a2e2d2
  echo "  commits touching 'upload/gabriels pat.txt':"
  git log --oneline -- "upload/gabriels pat.txt" | sed 's/^/    /'
  for ref in a81fc9fb c7db02cf origin/main; do
    if git merge-base --is-ancestor "$INTRO" "$ref" 2>/dev/null; then
      echo "  $INTRO IS reachable from $ref"
    else
      echo "  $INTRO NOT reachable from $ref"
    fi
  done
  git show -s --format='  introduced: %h %ci' "$INTRO"
  echo "  remote tip: $(GIT_TERMINAL_PROMPT=0 git ls-remote origin main 2>/dev/null || echo '(ls-remote failed)')"
  echo "  local HEAD: $(git rev-parse HEAD)"
  SHA=$(git rev-parse "$INTRO")
  curl -s -o /dev/null -w "  raw@${INTRO} 'gabriels pat.txt' -> %{http_code}\n" --max-time 20 \
    "https://raw.githubusercontent.com/Maingibrian/GabrielHomes/${SHA}/upload/gabriels%20pat.txt"
  curl -s --max-time 20 https://api.github.com/repos/Maingibrian/GabrielHomes | python3 -c \
    "import json,sys; d=json.load(sys.stdin); print('  GitHub API: private=%s visibility=%s' % (d.get('private'), d.get('visibility', d.get('message','?'))))"
  if command -v tesseract >/dev/null 2>&1; then
    n=$(tesseract "upload/pasted_image_1794546026489.png" stdout 2>/dev/null | grep -cE "$PATTERNS" || true)
    echo "  screenshot OCR secret hits: ${n:-0}"
  else
    echo "  screenshot OCR: tesseract absent — cannot read pasted_image_1794546026489.png"
  fi
fi

if [ "${1:-}" = "--verify-clean" ]; then
  echo "== post-push verification =="
  git fetch origin main >/dev/null 2>&1 || true
  echo "  origin/main: $(git rev-parse origin/main 2>/dev/null)"
  echo "  HEAD:        $(git rev-parse HEAD)"
  hits=$(git grep -lE "$PATTERNS" origin/main -- . 2>/dev/null || true)
  if [ -n "$hits" ]; then echo "  FAIL: secrets still in origin/main tree:"; printf '%s\n' "$hits" | sed 's/^/    /'; FAIL=1
  else echo "  origin/main tree: clean"; fi
  H=$(git rev-parse HEAD)
  curl -s -o /dev/null -w "  raw@HEAD(${H:0:8}) 'gabriels pat.txt' -> %{http_code} (want 404)\n" --max-time 20 \
    "https://raw.githubusercontent.com/Maingibrian/GabrielHomes/${H}/upload/gabriels%20pat.txt"
  O=$(git rev-parse 15a2e2d2)
  curl -s -o /dev/null -w "  raw@15a2e2d2 'gabriels pat.txt' -> %{http_code} (history retains it until rewrite/GC)\n" --max-time 20 \
    "https://raw.githubusercontent.com/Maingibrian/GabrielHomes/${O}/upload/gabriels%20pat.txt"
  [ -f "upload/gabriels pat.txt" ] && echo "  owner's file still on disk: yes" || echo "  owner's file on disk: MISSING"
fi

echo "== result: $([ $FAIL -eq 0 ] && echo SAFE || echo UNSAFE) =="
exit $FAIL
