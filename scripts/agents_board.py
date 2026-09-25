#!/usr/bin/env python3
"""Frontend-migration task board: validator + BOARD.md generator.

Canonical data lives in .agents/frontend-migration/tasks.json.
BOARD.md is generated and must not be hand-edited.

Usage:
    python scripts/agents_board.py              # validate, regenerate BOARD.md, print summary
    python scripts/agents_board.py --check       # validate only (non-zero on violations)
    python scripts/agents_board.py --claim ID AGENT
    python scripts/agents_board.py --status ID STATUS
    python scripts/agents_board.py --verify ID   # mark verified (requires evidence)
    python scripts/agents_board.py --set-evidence ID PATH
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROGRAM_DIR = REPO_ROOT / ".agents" / "frontend-migration"
TASKS_FILE = PROGRAM_DIR / "tasks.json"
BOARD_FILE = PROGRAM_DIR / "BOARD.md"

VALID_STATUS = {"todo", "claimed", "in-review", "verified", "blocked", "rejected"}
PHASE_ORDER = [
    "0 - Foundation",
    "1 - UI system",
    "2 - Candidate",
    "3 - Admin",
    "4 - Cutover",
    "Future (FS)",
]


def die(msg: str) -> None:
    print(f"[tasks] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def load() -> dict:
    if not TASKS_FILE.exists():
        die(f"missing {TASKS_FILE}")
    try:
        return json.loads(TASKS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex:
        die(f"tasks.json is not valid JSON: {ex}")


def save(data: dict) -> None:
    TASKS_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def find_task(data: dict, task_id: str) -> dict:
    for t in data["tasks"]:
        if t["id"] == task_id:
            return t
    die(f"unknown task id: {task_id}")


def validate(data: dict) -> list[str]:
    errors: list[str] = []
    tasks = data.get("tasks", [])
    ids = [t.get("id") for t in tasks]

    seen: set[str] = set()
    for tid in ids:
        if not tid:
            errors.append("task missing id")
        elif tid in seen:
            errors.append(f"duplicate id: {tid}")
        seen.add(tid)

    valid_status = set(data.get("status_enum", VALID_STATUS))
    known = set(ids)

    for t in tasks:
        tid = t.get("id", "<no-id>")
        for dep in t.get("depends", []):
            if dep not in known:
                errors.append(f"{tid}: unknown dependency '{dep}'")
        if not t.get("acceptance"):
            errors.append(f"{tid}: missing acceptance criteria")
        status = t.get("status")
        if status not in valid_status and not (
            isinstance(status, str) and status.startswith("claimed:")
        ):
            errors.append(f"{tid}: invalid status '{status}'")
        kind = t.get("kind")
        if kind in ("impl", "verify") and not t.get("tests"):
            errors.append(f"{tid}: missing test cases")
        if kind == "impl" and not t.get("verifier"):
            errors.append(f"{tid}: impl task missing independent verifier")
        if status == "verified" and not t.get("evidence"):
            errors.append(f"{tid}: verified without evidence")
        if status == "rejected" and not t.get("rejection"):
            errors.append(f"{tid}: rejected without a reason")

    # dependency cycles
    graph = {t["id"]: list(t.get("depends", [])) for t in tasks if t.get("id")}
    state: dict[str, int] = {}

    def visit(node: str, stack: list[str]) -> None:
        state[node] = 1
        for dep in graph.get(node, []):
            if state.get(dep, 0) == 1:
                errors.append(f"dependency cycle: {' -> '.join(stack + [dep])}")
            elif state.get(dep, 0) == 0:
                visit(dep, stack + [dep])
        state[node] = 2

    for node in graph:
        if state.get(node, 0) == 0:
            visit(node, [node])

    # milestone gates reference real tasks
    for ms, meta in data.get("milestones", {}).items():
        for tid in meta.get("tasks", []):
            if tid not in known:
                errors.append(f"milestone {ms}: unknown task '{tid}'")
        gate = meta.get("gate")
        if gate and gate not in known:
            errors.append(f"milestone {ms}: unknown gate '{gate}'")

    return errors


def _escape(text: object) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def _deps(t: dict) -> str:
    deps = t.get("depends") or []
    return ", ".join(deps) if deps else "-"


def render_board(data: dict) -> str:
    tasks = data["tasks"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    counts: dict[str, int] = {}
    for t in tasks:
        key = t.get("status", "?")
        if isinstance(key, str) and key.startswith("claimed:"):
            key = "claimed"
        counts[key] = counts.get(key, 0) + 1

    lines: list[str] = []
    lines.append("# BOARD - Frontend Migration")
    lines.append("")
    lines.append("> GENERATED FILE - do not edit by hand.")
    lines.append("> Canonical data: `.agents/frontend-migration/tasks.json`.")
    lines.append(f"> Regenerate with `python scripts/agents_board.py`. Last generated: {now}.")
    lines.append("")
    lines.append(f"**Program:** `{data.get('program')}`  ")
    lines.append(f"**Branch:** `{data.get('branch')}`  ")
    lines.append("")
    lines.append("## Status summary")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("| :--- | ---: |")
    for status in data.get("status_enum", []):
        lines.append(f"| {status} | {counts.get(status, 0)} |")
    lines.append(f"| **total** | **{len(tasks)}** |")
    lines.append("")

    m = data.get("milestones", {})
    if m:
        lines.append("## Milestones")
        lines.append("")
        lines.append("| Milestone | Name | Tasks | Gate |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for key, meta in m.items():
            items = ", ".join(meta.get("tasks", []))
            lines.append(f"| {key} | {meta.get('name', '')} | {items} | {meta.get('gate', '-')} |")
        lines.append("")

    by_phase: dict[str, list[dict]] = {}
    for t in tasks:
        by_phase.setdefault(t.get("phase", "Unphased"), []).append(t)
    ordered = [p for p in PHASE_ORDER if p in by_phase] + [
        p for p in by_phase if p not in PHASE_ORDER
    ]

    lines.append("## Tasks")
    lines.append("")
    for phase in ordered:
        lines.append(f"### {phase}")
        lines.append("")
        lines.append("| ID | Title | Depends | Owner | Status | Verifier | Evidence |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for t in by_phase[phase]:
            lines.append(
                "| `{id}` | {title} | {dep} | {owner} | {status} | {verifier} | {ev} |".format(
                    id=t["id"],
                    title=_escape(t.get("title", "")),
                    dep=_escape(_deps(t)),
                    owner=_escape(t.get("owner") or "-"),
                    status=_escape(t.get("status", "")),
                    verifier=_escape(t.get("verifier") or "-"),
                    ev=_escape(t.get("evidence") or "-"),
                )
            )
        lines.append("")

    lines.append("## Acceptance criteria")
    lines.append("")
    for t in tasks:
        lines.append(f"### {t['id']} - {t.get('title', '')}")
        lines.append("")
        lines.append(f"- **Deliverable:** {_escape(t.get('deliverable', ''))}")
        lines.append(f"- **Depends on:** {_escape(_deps(t))}")
        if t.get("acceptance"):
            lines.append("- **Acceptance:**")
            for a in t["acceptance"]:
                lines.append(f"  - {_escape(a)}")
        if t.get("tests"):
            lines.append("- **Test cases:**")
            for tc in t["tests"]:
                lines.append(
                    f"  - `{_escape(tc.get('id', ''))}` ({_escape(tc.get('type', ''))}) "
                    f"run: {_escape(tc.get('run', ''))} -> expect: {_escape(tc.get('expect', ''))}"
                )
        if t.get("verification"):
            lines.append("- **Verification:**")
            for v in t["verification"]:
                lines.append(f"  - `{_escape(v)}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def cmd_check(data: dict) -> int:
    errors = validate(data)
    if errors:
        print("[tasks] validation FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"[tasks] validation OK ({len(data['tasks'])} tasks)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate only; non-zero on errors")
    parser.add_argument("--claim", nargs=2, metavar=("ID", "AGENT"))
    parser.add_argument("--status", nargs=2, metavar=("ID", "STATUS"))
    parser.add_argument("--verify", metavar="ID")
    parser.add_argument("--set-evidence", nargs=2, metavar=("ID", "PATH"))
    parser.add_argument("--unclaim", metavar="ID")
    parser.add_argument("--reject", nargs=2, metavar=("ID", "REASON"))
    parser.add_argument(
        "--force",
        metavar="REASON",
        help="override the dependency gate on --claim (records dep_override)",
    )
    args = parser.parse_args()

    data = load()

    mutating = (
        args.claim or args.status or args.verify or args.set_evidence or args.unclaim or args.reject
    )
    if args.check and not mutating:
        return cmd_check(data)

    if args.claim:
        tid, agent = args.claim
        t = find_task(data, tid)
        unverified = []
        for dep in t.get("depends", []):
            if find_task(data, dep)["status"] != "verified":
                unverified.append(dep)
        if unverified and not args.force:
            die(
                f"{tid}: dependencies not verified: {', '.join(unverified)}. "
                "Complete/verify them first, or pass --force \"<reason>\" to override."
            )
        if unverified and args.force:
            t["dep_override"] = args.force
            print(f"[tasks] {tid} dependency override: {args.force}")
        t["owner"] = agent
        t["status"] = f"claimed:{agent}"
        t.pop("rejection", None)
        save(data)
        print(f"[tasks] {tid} claimed by {agent}")
    if args.status:
        tid, status = args.status
        if status not in set(data.get("status_enum", VALID_STATUS)) and not status.startswith(
            "claimed:"
        ):
            die(f"invalid status '{status}'")
        t = find_task(data, tid)
        if status == "in-review" and not t.get("evidence"):
            die(f"{tid}: cannot move to in-review without evidence (use --set-evidence)")
        t["status"] = status
        save(data)
        print(f"[tasks] {tid} -> {status}")
    if args.verify:
        t = find_task(data, args.verify)
        if not t.get("evidence"):
            die(f"{args.verify}: cannot verify without evidence (use --set-evidence)")
        t["status"] = "verified"
        t.pop("rejection", None)
        save(data)
        print(f"[tasks] {args.verify} verified")
    if args.unclaim:
        t = find_task(data, args.unclaim)
        t["owner"] = None
        t["status"] = "todo"
        t.pop("dep_override", None)
        t.pop("rejection", None)
        save(data)
        print(f"[tasks] {args.unclaim} unclaimed -> todo")
    if args.reject:
        tid, reason = args.reject
        t = find_task(data, tid)
        t["status"] = "rejected"
        t["rejection"] = reason
        save(data)
        print(f"[tasks] {tid} rejected: {reason}")
    if args.set_evidence:
        tid, path = args.set_evidence
        t = find_task(data, tid)
        t["evidence"] = path
        save(data)
        print(f"[tasks] {tid} evidence -> {path}")

    errors = validate(data)
    if errors:
        print("[tasks] validation FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    BOARD_FILE.write_text(render_board(data), encoding="utf-8")
    counts: dict[str, int] = {}
    for t in data["tasks"]:
        key = t["status"]
        if isinstance(key, str) and key.startswith("claimed:"):
            key = "claimed"
        counts[key] = counts.get(key, 0) + 1
    summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    print(f"[tasks] BOARD.md written ({len(data['tasks'])} tasks: {summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
