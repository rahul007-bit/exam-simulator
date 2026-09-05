import os
import argparse
import sys
from pathlib import Path
from core.loader import QuestionLoader
from core.deployer import LabDeployer
from core.grader import LabGrader
from core.wizard import QuestionnaireWizard
from core.models import Difficulty, Domain


def main():
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

    # Preflight
    subparsers.add_parser("preflight", help="Run preflight environment verification")

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

        if args.id:
            target_q = next((q for q in session.questions if q.id == args.id), None)
            if not target_q:
                print(f"[Error] Question {args.id} is not in current active session.")
                sys.exit(1)
            res = grader.grade_question(target_q)
            session.scores[target_q.id] = {"passed": res.passed, "score": res.score, "max_score": res.max_score, "message": res.message}
            deployer.save_session(session)
            print(f"[{'PASS' if res.passed else 'FAIL'}] {args.id} ({res.score}/{res.max_score} pts): {res.message}")
        elif session.mode == "sequential" and not args.all:
            cur_q = session.current_question
            if cur_q:
                res = grader.grade_question(cur_q)
                session.scores[cur_q.id] = {"passed": res.passed, "score": res.score, "max_score": res.max_score, "message": res.message}
                deployer.save_session(session)
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
