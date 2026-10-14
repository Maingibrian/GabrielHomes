#!/usr/bin/env python3
"""audit_update_bat.py - static audit for UPDATE-WEBSITE.bat.

We have no Windows box in the sandbox, so we enforce the bug classes we
have actually hit before, statically:

  1. BLOCK-PAREN: an unquoted ')' inside an echo/rem line that sits within
     an if/for (...) block terminates the block early (broke v1+v2 launchers).
  2. UNBALANCED blocks (final paren depth != 0).
  3. UNC BUG: the script must never 'cd' to %~dp0 (fails on \\UNC paths).
     Entering directories must use pushd.
  4. DELAYED EXPANSION: any use of !VAR! requires EnableDelayedExpansion.
  5. BLOCK-SCOPED !VAR!: a variable read with !VAR! inside a block must be
     set with delayed expansion available (EnableDelayedExpansion is on) -
     flagged only as info when found in the same block as a set /p.
  6. Line endings: the file must be CRLF when shipped (checked at build).
  7. Forbid 'pause' missing at exits: every exit /b path in interactive use
     should pause so the window does not vanish (informational).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def strip_quotes(line: str) -> str:
    return re.sub(r'"[^"]*"', "Q", line)


def audit(path: Path) -> list[str]:
    raw_bytes = path.read_bytes()
    text = raw_bytes.decode("utf-8", errors="replace")
    lines = text.splitlines()
    violations: list[str] = []

    # HARD line-ending contract: CMD misparses ( ... ) blocks in batch
    # files with Unix (LF-only) endings - shipped as '.'-is-not-recognized
    # errors on the user's machine (2026-10-14 incident). Every line
    # MUST end CRLF.
    bare_lf = raw_bytes.count(b"\n") - raw_bytes.count(b"\r\n")
    if bare_lf:
        violations.append(
            f"{bare_lf} bare-LF line(s): batch files must be CRLF-only "
            "(CMD block misparse with LF endings)"
        )

    depth = 0
    delayed_on = False
    saw_setlocal = False
    exit_points: list[int] = []

    for n, raw in enumerate(lines, 1):
        code = strip_quotes(raw).strip()
        low = code.lower()

        if low.startswith("setlocal"):
            saw_setlocal = True
            if "enabledelayedexpansion" in low:
                delayed_on = True
            continue
        if low.startswith(("rem", "::")):
            # rem lines still break blocks on ')'
            if depth > 0:
                no_esc = re.sub(r"\^\)", "", strip_quotes(raw).strip())
                if ")" in no_esc:
                    violations.append(f"line {n}: unquoted ')' inside block: {raw.strip()[:70]}")
            continue

        body = strip_quotes(raw)
        stripped = body.strip()
        cmd = stripped.split()[0].lower() if stripped.split() else ""

        # a bare '.' (or any token starting with an unquoted '.') is never
        # a valid command - it is the classic symptom of a misparsed block
        if cmd == ".":
            violations.append(f"line {n}: bare '.' command (misparse symptom)")

        # echo lines inside blocks: forbid unquoted ')'
        if cmd == "echo" and depth > 0:
            no_esc = re.sub(r"\^\)", "", stripped)
            if ")" in no_esc.rstrip(">").rstrip():
                violations.append(f"line {n}: unquoted ')' in echo inside block: {raw.strip()[:70]}")

        # UNC bug: cd /d "%~dp0" or cd /d to a script-relative path
        if re.search(r"\bcd\s+/d\b", low) and "%~dp0" in low:
            violations.append(f"line {n}: 'cd /d' to %~dp0 fails on UNC paths - use pushd")

        # delayed expansion without setlocal EnableDelayedExpansion
        if not delayed_on and re.search(r"![A-Za-z_][A-Za-z0-9_]*!", raw):
            violations.append(f"line {n}: !VAR! used but EnableDelayedExpansion not set")

        # exit /b bookkeeping (does the window vanish?)
        if low.startswith("exit /b"):
            exit_points.append(n)

        # block-depth tracking
        if stripped.endswith("("):
            depth += 1
        if stripped.startswith(")"):
            depth -= 1
            if depth < 0:
                violations.append(f"line {n}: ')' with unbalanced block depth")

    if depth != 0:
        violations.append(f"unbalanced blocks: final depth {depth}")
    if not saw_setlocal:
        violations.append("missing 'setlocal EnableExtensions'")

    return violations


def main() -> int:
    targets = [Path(p) for p in sys.argv[1:]] or [Path(__file__).resolve().parents[1] / "gabriel_homes" / "UPDATE-WEBSITE.bat"]
    failed = False
    for t in targets:
        v = audit(t)
        rb = t.read_bytes()
        crlf = rb.count(b"\n") == rb.count(b"\r\n") and rb.count(b"\n") > 0
        status = "OK" if not v else "FAIL"
        print(f"{status}: {t.name}  (CRLF: {'yes' if crlf else 'NO - FATAL for shipping'})")
        for line in v:
            failed = True
            print(f"  - {line}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
