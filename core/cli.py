import os
import argparse
import sys
from pathlib import Path
from core.loader import QuestionLoader
from core.deployer import LabDeployer
from core.grader import LabGrader
from core.wizard import QuestionnaireWizard
from core.models import Difficulty, Domain
from core.recorder import recorder


def _load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip())
        except Exception:
            pass


def main():
    _load_env()
    loader = QuestionLoader()
    deployer = LabDeployer()
    grader = LabGrader()
    wizard = QuestionnaireWizard(loader, deployer, grader)

    parser = argparse.ArgumentParser(
        prog="labctl",
        description="Kubernetes and CKA question engine and lab runner",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Wizard / Interactive
    subparsers.add_parser("wizard", help="Launch interactive menu")

    # Start
    start_parser = subparsers.add_parser("start", help="Start a drill or mock exam")
    start_parser.add_argument("--preset", type=str, help="Preset mock exam name (e.g. mock-01-acme, mock-06-apex)")
    start_parser.add_argument("--difficulty", type=str, help="Comma-separated difficulties (easy,medium,hard,crazy)")
    start_parser.add_argument("--domain", type=str, help="Comma-separated domains (troubleshooting,storage,workloads,cluster-arch,security)")
    start_parser.add_argument("--count", type=int, default=5, help="Number of questions")
    start_parser.add_argument("--id", type=str, help="Deploy a single specific question ID")
    start_parser.add_argument("--step", "--sequential", dest="sequential", action="store_true", help="Deploy question-by-question (sequential mode)")

    # Deploy (Deploy specific question or questions by ID)
    deploy_parser = subparsers.add_parser("deploy", help="Deploy specific question(s) by ID (e.g. 'labctl deploy TR-001' or 'labctl deploy TR-001,CA-001')")
    deploy_parser.add_argument("ids", type=str, help="Question ID or comma-separated list of IDs")

    # Exam (shortcut for sequential mock exam)
    exam_parser = subparsers.add_parser("exam", help="Start sequential mock exam")
    exam_parser.add_argument("preset", nargs="?", default="mock-01-acme", help="Preset name (e.g. mock-01-acme, mock-06-apex) or 'all'")
    exam_parser.add_argument("--all", action="store_true", help="Deploy all questions in catalog sequentially")

    # Next / Prev / Jump (sequential mode navigation)
    subparsers.add_parser("next", help="Deploy next question in active exam set")
    subparsers.add_parser("prev", help="Deploy previous question in active exam set")
    jump_parser = subparsers.add_parser("jump", help="Jump to specific question number in active exam set")
    jump_parser.add_argument("num", type=int, help="Task number (1-based)")

    # Flag / Unflag for review
    flag_parser = subparsers.add_parser("flag", help="Flag current active task (or task number) for review")
    flag_parser.add_argument("num", nargs="?", type=int, help="Optional task number to flag (defaults to current active task)")
    unflag_parser = subparsers.add_parser("unflag", help="Unflag current active task (or task number)")
    unflag_parser.add_argument("num", nargs="?", type=int, help="Optional task number to unflag (defaults to current active task)")

    # Status / Tasks
    subparsers.add_parser("status", help="Show all questions in active set and progress")
    tasks_parser = subparsers.add_parser("tasks", help="Display active tasks")
    tasks_parser.add_argument("--all", action="store_true", help="Display all tasks in session")

    # Grade
    grade_parser = subparsers.add_parser("grade", help="Grade active session or specific task")
    grade_parser.add_argument("--id", type=str, help="Grade specific question ID only")
    grade_parser.add_argument("--all", action="store_true", help="Grade all questions in session")

    # Solution
    sol_parser = subparsers.add_parser("solution", help="View solution for a question")
    sol_parser.add_argument("id", type=str, help="Question ID (e.g. TR-001, ST-011)")

    # List
    list_parser = subparsers.add_parser("list", help="List questions in catalog")
    list_parser.add_argument("--domain", type=str, help="Filter by domain")
    list_parser.add_argument("--difficulty", type=str, help="Filter by difficulty")

    # Reset
    subparsers.add_parser("reset", help="Reset active session and clean cluster resources")

    # Recordings, Replay & Review
    recordings_parser = subparsers.add_parser("recordings", help="List recorded candidate exam sessions")
    recordings_parser.add_argument("subcmd", nargs="?", default="list", choices=["list"], help="Subcommand (default: list)")

    review_parser = subparsers.add_parser("review", help="Review candidate session recording and event timeline")
    review_parser.add_argument("session_id", nargs="?", help="Session ID (defaults to latest recorded session)")

    replay_parser = subparsers.add_parser("replay", help="Replay terminal recording in CLI via asciinema")
    replay_parser.add_argument("session_id", nargs="?", help="Session ID (defaults to latest recorded session)")
    replay_parser.add_argument("--speed", type=float, default=1.0, help="Playback speed multiplier (default: 1.0)")

    record_shell_parser = subparsers.add_parser("record-shell", help="Run an interactive recorded shell attached to active session")
    record_shell_parser.add_argument("--session-id", help="Session ID (defaults to active session)")
    record_shell_parser.add_argument("shell_args", nargs=argparse.REMAINDER, help="Optional shell command to run")

    # Preflight & Configuration
    subparsers.add_parser("preflight", help="Run preflight environment verification")
    configure_parser = subparsers.add_parser("configure", help="Interactive environment configuration & preflight setup wizard")
    configure_parser.add_argument("-y", "--yes", action="store_true", help="Non-interactive mode (accept all auto-detected defaults)")
    configure_parser.add_argument("--force", action="store_true", help="Overwrite existing .env without confirmation")

    # Web UI Server
    web_parser = subparsers.add_parser("web", help="Start the CKA Exam Web Simulator server")
    web_parser.add_argument("--port", type=int, default=3000, help="Port to listen on (default: 3000)")
    web_parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface to bind to (default: 0.0.0.0)")
    web_parser.add_argument("--preset", type=str, default="mock-01-acme", help="Pre-selected mock exam preset (default: mock-01-acme)")
    web_parser.add_argument("--admin", action="store_true", help="Enable proctor/admin preset switcher on start screen")

    args = parser.parse_args()

    if not args.command:
        wizard.run_main_menu()
        return

    if args.command == "wizard":
        wizard.run_main_menu()

    elif args.command == "deploy":
        raw_ids = [s.strip() for s in args.ids.split(",") if s.strip()]
        questions = []
        for qid in raw_ids:
            q = loader.get(qid)
            if not q:
                print(f"[Error] Question ID '{qid}' not found in catalog.")
                sys.exit(1)
            questions.append(q)

        session_title = f"Task {questions[0].id} ({questions[0].title})" if len(questions) == 1 else f"Selected Tasks ({len(questions)} Questions)"
        session = deployer.deploy_sequential(
            questions,
            session_name=session_title,
            time_limit_minutes=None,
        )
        prog = os.environ.get("EXAMCTL_PROG", "examctl")
        wizard._render_tasks_instructions([session.questions[0]], start_idx=1)
        print(f"Task sheet exported to: sets/active_exam.md")
        if len(questions) > 1:
            print(f"Navigate tasks using '{prog} next', '{prog} prev', or '{prog} jump <num>'.")

    elif args.command == "exam":
        if getattr(args, "all", False) or (args.preset and args.preset.lower() in ("all", "--all")):
            questions = loader.get_all()
            session = deployer.deploy_sequential(
                questions,
                session_name="Full CKA Curriculum (111 Tasks)",
                time_limit_minutes=None,
            )
        else:
            preset_name = args.preset
            preset_data = wizard.selector.load_preset(preset_name)
            if not preset_data:
                print(f"[Error] Preset '{preset_name}' not found.")
                sys.exit(1)
            q_ids = preset_data.get("questions", [])
            questions = [loader.get(qid) for qid in q_ids if loader.get(qid) is not None]
            session = deployer.deploy_sequential(
                questions,
                session_name=preset_data.get("name", "Mock Exam"),
                time_limit_minutes=preset_data.get("time_limit_minutes", 120),
            )
        prog = os.environ.get("EXAMCTL_PROG", "examctl")
        wizard._render_tasks_instructions([session.questions[0]], start_idx=1)
        print(f"Task sheet exported to: sets/active_exam.md")
        print(f"Navigate tasks using '{prog} next', '{prog} prev', or '{prog} jump <num>'.")

    elif args.command == "next":
        prog = os.environ.get("EXAMCTL_PROG", "examctl")
        session = deployer.load_active_session(loader)
        if not session or not session.questions:
            print(f"[Error] No active exam session. Start one with '{prog} exam <preset>'.")
            sys.exit(1)
        next_idx = session.current_index + 1
        if next_idx >= len(session.questions):
            print(f"Already at final task ({len(session.questions)}/{len(session.questions)}).")
            return
        deployer.deploy_step(session, next_idx)
        wizard._render_tasks_instructions([session.questions[next_idx]], start_idx=next_idx + 1)

    elif args.command == "prev":
        prog = os.environ.get("EXAMCTL_PROG", "examctl")
        session = deployer.load_active_session(loader)
        if not session or not session.questions:
            print(f"[Error] No active exam session. Start one with '{prog} exam <preset>'.")
            sys.exit(1)
        prev_idx = session.current_index - 1
        if prev_idx < 0:
            print("Already at the first task (Task 1).")
            return
        deployer.deploy_step(session, prev_idx)
        wizard._render_tasks_instructions([session.questions[prev_idx]], start_idx=prev_idx + 1)

    elif args.command == "jump":
        prog = os.environ.get("EXAMCTL_PROG", "examctl")
        session = deployer.load_active_session(loader)
        if not session or not session.questions:
            print(f"[Error] No active exam session. Start one with '{prog} exam <preset>'.")
            sys.exit(1)
        target_idx = args.num - 1
        if target_idx < 0 or target_idx >= len(session.questions):
            print(f"[Error] Task number {args.num} out of range (1 to {len(session.questions)}).")
            sys.exit(1)
        deployer.deploy_step(session, target_idx)
        wizard._render_tasks_instructions([session.questions[target_idx]], start_idx=target_idx + 1)

    elif args.command == "flag":
        session = deployer.load_active_session(loader)
        if not session or not session.questions:
            print("[Error] No active exam session found.")
            sys.exit(1)
        idx = (args.num - 1) if args.num is not None else session.current_index
        if idx < 0 or idx >= len(session.questions):
            print(f"[Error] Task number out of range (1 to {len(session.questions)}).")
            sys.exit(1)
        target_q = session.questions[idx]
        if target_q.id not in session.flagged:
            session.flagged.append(target_q.id)
            deployer.save_session(session)
            try:
                recorder.attach_or_resume(session.session_id, session.name)
                recorder.log_event("TASK_FLAGGED", {"task_num": idx + 1, "question_id": target_q.id, "title": target_q.title})
            except Exception:
                pass
        print(f"🚩 Task {idx + 1} ({target_q.id}: {target_q.title}) flagged for review.")

    elif args.command == "unflag":
        session = deployer.load_active_session(loader)
        if not session or not session.questions:
            print("[Error] No active exam session found.")
            sys.exit(1)
        idx = (args.num - 1) if args.num is not None else session.current_index
        if idx < 0 or idx >= len(session.questions):
            print(f"[Error] Task number out of range (1 to {len(session.questions)}).")
            sys.exit(1)
        target_q = session.questions[idx]
        if target_q.id in session.flagged:
            session.flagged.remove(target_q.id)
            deployer.save_session(session)
            try:
                recorder.attach_or_resume(session.session_id, session.name)
                recorder.log_event("TASK_UNFLAGGED", {"task_num": idx + 1, "question_id": target_q.id, "title": target_q.title})
            except Exception:
                pass
        print(f"Task {idx + 1} ({target_q.id}) unflagged.")

    elif args.command == "status":
        session = deployer.load_active_session(loader)
        if not session or not session.questions:
            print("[Error] No active exam session found.")
            sys.exit(1)
        deployer.render_session_status(session)

    elif args.command == "grade":
        prog = os.environ.get("EXAMCTL_PROG", "examctl")
        session = deployer.load_active_session(loader)
        if not session or not session.questions:
            print("[Warning] No active exam session found.")
            sys.exit(1)

        try:
            recorder.attach_or_resume(session.session_id, session.name)
        except Exception:
            pass

        if args.id:
            target_q = next((q for q in session.questions if q.id == args.id), None)
            if not target_q:
                print(f"[Error] Question {args.id} is not in current active session.")
                sys.exit(1)
            res = grader.grade_question(target_q)
            session.scores[target_q.id] = {"passed": res.passed, "score": res.score, "max_score": res.max_score, "message": res.message}
            deployer.save_session(session)
            try:
                recorder.log_event("TASK_EVALUATION", {
                    "question_id": target_q.id,
                    "score": res.score,
                    "max_score": res.max_score,
                    "passed": res.passed,
                    "message": res.message,
                })
            except Exception:
                pass
            print(f"[{'PASS' if res.passed else 'FAIL'}] {args.id} ({res.score}/{res.max_score} pts): {res.message}")
        elif session.mode == "sequential" and not args.all:
            cur_q = session.current_question
            if cur_q:
                res = grader.grade_question(cur_q)
                session.scores[cur_q.id] = {"passed": res.passed, "score": res.score, "max_score": res.max_score, "message": res.message}
                deployer.save_session(session)
                try:
                    recorder.log_event("TASK_EVALUATION", {
                        "task_num": session.current_index + 1,
                        "question_id": cur_q.id,
                        "score": res.score,
                        "max_score": res.max_score,
                        "passed": res.passed,
                        "message": res.message,
                    })
                except Exception:
                    pass
                print(f"\nTask {session.current_index + 1}/{len(session.questions)} Evaluation: [{cur_q.id}] {cur_q.title}")
                print(f"[{'PASS' if res.passed else 'FAIL'}] Score: {res.score}/{res.max_score} pts - {res.message}")
                if session.current_index + 1 < len(session.questions):
                    print(f"Move to next task with: {prog} next")
                else:
                    print(f"Finished last task. Grade overall exam with: {prog} grade --all")
        else:
            if session.mode == "sequential" and session.current_question:
                cur_q = session.current_question
                res = grader.grade_question(cur_q)
                session.scores[cur_q.id] = {
                    "passed": res.passed,
                    "score": res.score,
                    "max_score": res.max_score,
                    "message": res.message,
                }
                deployer.save_session(session)
            summaries = grader.grade_session(session)
            grader.render_scorecard(summaries)
            try:
                tot_earned = sum(s.result.score for s in summaries)
                tot_possible = sum(s.result.max_score for s in summaries)
                pct = (tot_earned / tot_possible * 100) if tot_possible > 0 else 0.0
                recorder.finish_session(
                    session_id=session.session_id,
                    scorecard=[{"task_num": s.task_num, "id": s.question.id, "score": s.result.score, "max_score": s.result.max_score, "passed": s.result.passed} for s in summaries],
                    percentage=round(pct, 1),
                    passed=pct >= 66.0,
                    total_earned=tot_earned,
                    total_possible=tot_possible,
                )
            except Exception:
                pass

    elif args.command == "tasks":
        session = deployer.load_active_session(loader)
        if not session or not session.questions:
            print("[Warning] No active session found.")
            sys.exit(1)
        if args.all:
            wizard._render_tasks_instructions(session.questions, start_idx=1)
        else:
            cur_idx = session.current_index if 0 <= session.current_index < len(session.questions) else 0
            cur_q = session.questions[cur_idx]
            wizard._render_tasks_instructions([cur_q], start_idx=cur_idx + 1)

    elif args.command == "solution":
        q = loader.get(args.id)
        if q and q.solution_file and q.solution_file.exists():
            with open(q.solution_file, "r", encoding="utf-8") as f:
                print(f.read())
        else:
            print(f"[Error] Solution not found for {args.id}.")

    elif args.command == "list":
        questions = loader.all()
        print(f"\nTotal questions in catalog: {len(questions)}")
        print(f"{'ID':<15}{'Domain':<16}{'Difficulty':<12}{'Points':<8}{'Title'}")
        print("-" * 75)
        for q in questions:
            if args.domain and q.domain.value != args.domain:
                continue
            if args.difficulty and q.difficulty.value != args.difficulty:
                continue
            print(f"{q.id:<15}{q.domain.value:<16}{q.difficulty.value:<12}{q.points:<8}{q.title}")
        print()

    elif args.command == "reset":
        deployer.clear_session()
        print("Active session cleared.")

    elif args.command == "recordings":
        recorder.render_recordings_table()

    elif args.command == "review":
        recorder.render_review_report(args.session_id)

    elif args.command == "replay":
        sid = args.session_id
        if not sid:
            recs = recorder.list_recordings()
            if not recs:
                print("\n[Error] No recorded sessions found to replay in recordings/.\n")
                sys.exit(1)
            sid = recs[0]["session_id"]
        recorder.replay_cli(sid, speed=args.speed)

    elif args.command == "record-shell":
        cmd = args.shell_args if args.shell_args else None
        if cmd and cmd[0] == "--":
            cmd = cmd[1:]
        rc = recorder.record_shell(cmd=cmd, session_id=args.session_id)
        sys.exit(rc)

    elif args.command == "start":
        if args.preset:
            preset_data = wizard.selector.load_preset(args.preset)
            if not preset_data:
                print(f"[Error] Preset '{args.preset}' not found.")
                sys.exit(1)
            q_ids = preset_data.get("questions", [])
            questions = [loader.get(qid) for qid in q_ids if loader.get(qid) is not None]
            if args.sequential:
                session = deployer.deploy_sequential(
                    questions,
                    session_name=preset_data.get("name", "Mock Exam"),
                    time_limit_minutes=preset_data.get("time_limit_minutes", 120),
                )
                wizard._render_tasks_instructions([session.questions[0]], start_idx=1)
            else:
                session = deployer.deploy(
                    questions,
                    session_name=preset_data.get("name", "Mock Exam"),
                    time_limit_minutes=preset_data.get("time_limit_minutes", 120),
                )
                wizard._render_tasks_instructions(questions)
        elif args.id:
            q = loader.get(args.id)
            if not q:
                print(f"[Error] Question {args.id} not found in catalog.")
                sys.exit(1)
            deployer.deploy([q], session_name=f"Single Task ({q.id})")
            wizard._render_tasks_instructions([q], start_idx=1)
        else:
            diffs = [Difficulty(d.strip()) for d in args.difficulty.split(",")] if args.difficulty else None
            doms = [Domain(d.strip()) for d in args.domain.split(",")] if args.domain else None
            questions = wizard.selector.select_custom(difficulties=diffs, domains=doms, count=args.count)
            if not questions:
                print("[Error] No matching questions found.")
                sys.exit(1)
            if args.sequential:
                session = deployer.deploy_sequential(questions, session_name=f"Custom Drill ({len(questions)} Tasks)")
                wizard._render_tasks_instructions([session.questions[0]], start_idx=1)
            else:
                deployer.deploy(questions, session_name=f"Custom Drill ({len(questions)} Tasks)")
                wizard._render_tasks_instructions(questions)

    elif args.command == "preflight":
        import subprocess
        preflight_script = Path(__file__).parent.parent / "tools" / "preflight.sh"
        if preflight_script.exists():
            subprocess.run(["bash", str(preflight_script)])
        else:
            print("[Warning] tools/preflight.sh not found.")

    elif args.command == "configure":
        from core.configure import ConfigWizard
        cw = ConfigWizard()
        cw.run(non_interactive=args.yes, force=args.force)

    elif args.command == "web":
        import uvicorn
        from rich.console import Console
        from rich.panel import Panel
        os.environ["EXAM_PRESET"] = args.preset
        os.environ["EXAM_ADMIN"] = "1" if args.admin else "0"
        console = Console()
        console.print(Panel(
            f"[bold green]CKA Exam Web Simulator running![/bold green]\n\n"
            f"• Assigned Preset: [bold yellow]{args.preset}[/bold yellow]\n"
            f"• Mode:            [bold cyan]{'Admin (Full Access)' if args.admin else 'Candidate (Exam Mode)'}[/bold cyan]\n"
            f"• Local URL:       [bold cyan]http://localhost:{args.port}[/bold cyan]\n"
            f"• Network URL:     [bold cyan]http://{args.host}:{args.port}[/bold cyan]\n\n"
            f"[dim]Press Ctrl+C to stop web server.[/dim]",
            title="[bold yellow]CKA EXAM SIMULATOR (WEB UI)[/bold yellow]",
            border_style="cyan"
        ))
        uvicorn.run("web.server:app", host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
