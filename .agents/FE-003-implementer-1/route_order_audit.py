#!/usr/bin/env python3
"""FE-003 route-ordering audit for web/server.py.

web/server.py imports Linux-only modules (pty/fcntl/termios) and live core
services, so it cannot be imported on a non-Linux workstation. This audit
instead parses the source AST and asserts the SPA catch-all is registered LAST
within its own branch, after every /api, /ws and /novnc route. That is exactly
the precedence property FE-003 acceptance #2/#3 requires.

The legacy `app.mount("/", ...)` lives in the mutually-exclusive `else` branch
taken when web/dist is absent, so it is not a conflicting registration.

Exit 0 = ordering OK.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

SERVER = Path(__file__).resolve().parents[2] / "web" / "server.py"

HTTP_DECORATORS = {"get", "post", "put", "patch", "delete", "head", "options"}
WS_DECORATORS = {"websocket"}


def collect(stmts, branch):
    """Collect (lineno, kind, path, branch) for app routes/mounts in source order."""
    regs = []
    for stmt in stmts:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in stmt.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                    owner = getattr(dec.func.value, "id", None)
                    method = dec.func.attr
                    if owner == "app" and method in HTTP_DECORATORS | WS_DECORATORS:
                        if dec.args and isinstance(dec.args[0], ast.Constant):
                            kind = "ws" if method in WS_DECORATORS else "http"
                            regs.append((dec.lineno, kind, dec.args[0].value, branch))
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
            if isinstance(call.func, ast.Attribute) and getattr(call.func.value, "id", None) == "app":
                if call.func.attr == "mount" and call.args and isinstance(call.args[0], ast.Constant):
                    regs.append((stmt.lineno, "mount", call.args[0].value, branch))
        elif isinstance(stmt, ast.If):
            regs += collect(stmt.body, branch + (("if", stmt.lineno),))
            regs += collect(stmt.orelse, branch + (("else", stmt.lineno),))
    return regs


def main() -> int:
    tree = ast.parse(SERVER.read_text(encoding="utf-8"))
    regs = collect(tree.body, ())

    failures: list[str] = []
    notes: list[str] = []

    print("server.py registrations (source order):")
    for lineno, kind, path, branch in regs:
        tag = ""
        if path == "/{full_path:path}":
            tag = "  <-- SPA catch-all"
        elif branch:
            tag = f"  [{branch[-1][0]}@{branch[-1][1]}]"
        print(f"  L{lineno:<5} {kind:<6} {path}{tag}")

    catchalls = [r for r in regs if r[2] == "/{full_path:path}"]
    if len(catchalls) != 1:
        failures.append(f"expected exactly 1 SPA catch-all, found {len(catchalls)}")
    else:
        c_line, _, _, c_branch = catchalls[0]
        # Nothing in the SAME branch may be registered after the catch-all.
        for lineno, kind, path, branch in regs:
            if path == "/{full_path:path}":
                continue
            if branch == c_branch and lineno > c_line:
                failures.append(f"'{path}' (L{lineno}) follows the catch-all (L{c_line}) in the same branch")

    # Acceptance #2: representative /api and /ws routes must precede the catch-all.
    must_precede = {
        "/api/session": "http",
        "/api/start": "http",
        "/api/admin/login": "http",
        "/ws/terminal": "ws",
        "/ws/session/{session_id}": "ws",
        "/ws/desktop": "ws",
    }
    by_path = {p: (ln, kind) for ln, kind, p, _ in regs}
    c_line = catchalls[0][0] if catchalls else None
    for path, kind in must_precede.items():
        if path not in by_path:
            failures.append(f"missing expected route {path}")
            continue
        ln, found_kind = by_path[path]
        if found_kind != kind:
            failures.append(f"{path} registered as {found_kind}, expected {kind}")
        elif c_line is not None and ln > c_line:
            failures.append(f"{path} (L{ln}) is not before the catch-all (L{c_line})")
        else:
            notes.append(f"{path} before catch-all (L{ln} < L{c_line})")

    # Acceptance #3: /novnc mount present and before the catch-all.
    if "/novnc" not in by_path:
        failures.append("missing /novnc mount")
    else:
        ln, _ = by_path["/novnc"]
        if c_line is not None and ln > c_line:
            failures.append(f"/novnc mount (L{ln}) is not before the catch-all")
        else:
            notes.append(f"/novnc mount before catch-all (L{ln})")

    print()
    for n in notes:
        print(f"  OK  {n}")
    if failures:
        print()
        for f in failures:
            print(f"  FAIL  {f}", file=sys.stderr)
        print(f"\nroute-order audit: FAILED ({len(failures)} issues)")
        return 1
    print(f"\nroute-order audit: PASS (catch-all L{c_line} is last of its branch; {len(regs)} registrations checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
