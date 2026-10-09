#!/usr/bin/env python3
"""H6 — DEPLOY.md doc-lint (stdlib only).

Parses gabriel_homes/DEPLOY.md and asserts:
  1. every `manage.py <command>` names a command that `manage.py help
     --commands` lists (ground truth from Django itself)
  2. every environment variable USED in DEPLOY.md (assignments like
     `VAR=...` / `export VAR=...`, shell refs like `$VAR` / `${VAR}`)
     appears in .env.example
  3. every `scripts/*.sh|py` path DEPLOY.md mentions exists in the repo
  4. angle-bracket placeholders (<REPO_URL>, <your-domain>) are listed
     explicitly as ALLOWED PLACEHOLDERS — visible, never silently ignored

Run:  python3 scripts/tests_deploy_doc.py    (exit 0 = GREEN)
"""
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GH = REPO / "gabriel_homes"
DEPLOY = GH / "DEPLOY.md"
ENV_EXAMPLE = GH / ".env.example"

# tokens that look like env vars in assignment/shell contexts but are not
NON_ENV = {
    "URL", "IP", "TCP", "SSH", "HTTP", "HTTPS", "API", "JSON", "SQL", "EOF",
    "PID", "CPU", "RAM", "MD5", "UUID", "ISO", "STDIN", "STDOUT", "STDERR",
}


def real_manage_py_commands() -> set:
    venv_py = GH / ".venv" / "bin" / "python"
    py = str(venv_py) if venv_py.exists() else sys.executable
    out = subprocess.run(
        [py, str(GH / "manage.py"), "help", "--commands"],
        cwd=GH, capture_output=True, text=True, timeout=60,
    )
    if out.returncode != 0:
        sys.exit(f"FAIL: could not list manage.py commands: {out.stderr[:400]}")
    return {line.strip() for line in out.stdout.splitlines() if line.strip()}


def main() -> int:
    if not DEPLOY.exists():
        print(f"FAIL: {DEPLOY} does not exist")
        return 1
    text = DEPLOY.read_text()

    valid = real_manage_py_commands()
    failures = []

    # ------------------------------------------------ 1. manage.py commands
    used_cmds = re.findall(r"manage\.py\s+([a-z][a-z0-9_]*)", text)
    bad_cmds = sorted({c for c in used_cmds if c not in valid})
    if bad_cmds:
        failures.append(f"manage.py commands not offered by manage.py help: {bad_cmds}")
    print(f"manage.py commands referenced: {sorted(set(used_cmds))}")

    # ------------------------------------------------ 2. environment vars
    env_names = set(re.findall(r"(?m)(?:^|\s)(?:export\s+)?([A-Z][A-Z0-9_]{2,})=", text))
    env_names |= set(re.findall(r"\$(?:\{)?([A-Z][A-Z0-9_]{2,})(?:\})?", text))
    env_names -= NON_ENV
    env_text = ENV_EXAMPLE.read_text() if ENV_EXAMPLE.exists() else ""
    bad_env = sorted(n for n in env_names if not re.search(rf"\b{re.escape(n)}\b", env_text))
    if bad_env:
        failures.append(f"env vars used in DEPLOY.md but absent from .env.example: {bad_env}")
    print(f"env vars referenced: {sorted(env_names)}")

    # ------------------------------------------------ 3. script paths
    # no lookbehind on purpose: "$SRC/scripts/x.sh" and "gabriel_homes/scripts/x.sh"
    # must also be caught; trailing prose punctuation is stripped before checking
    script_refs = {p.rstrip(".") for p in re.findall(r"(scripts/[A-Za-z0-9_./-]+\.(?:sh|py))", text)}
    bad_paths = sorted(p for p in script_refs
                       if not (GH / p).is_file() and not (REPO / p).is_file())
    if bad_paths:
        failures.append(f"script paths mentioned in DEPLOY.md that do not exist: {bad_paths}")
    print(f"script paths referenced: {sorted(script_refs)}")

    # ------------------------------------------------ 4. placeholders (listed, not hidden)
    placeholders = sorted(set(re.findall(r"<[^<>\n]{2,40}>", text)))
    print(f"ALLOWED PLACEHOLDERS (must stay placeholders, never real values): {placeholders}")

    print("----")
    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        print("H6 TEST: RED")
        return 1
    print("H6 TEST: GREEN — DEPLOY.md commands, env vars and script paths all check out")
    return 0


if __name__ == "__main__":
    sys.exit(main())
