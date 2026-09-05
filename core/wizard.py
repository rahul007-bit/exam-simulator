import os
import sys
from typing import Optional, Dict, Any, List
from core.models import Difficulty, Domain, Question
from core.loader import QuestionLoader
from core.selector import QuestionSelector
from core.deployer import LabDeployer
from core.grader import LabGrader


class QuestionnaireWizard:
    def __init__(self, loader: QuestionLoader, deployer: LabDeployer, grader: LabGrader):
        self.loader = loader
        self.selector = QuestionSelector(loader)
        self.deployer = deployer
        self.grader = grader

    def run_main_menu(self) -> None:
        try:
            import questionary
            from rich.console import Console
            console = Console()
        except ImportError:
            print("[Error] questionary or rich is not installed. Run: pip install -r requirements.txt")
            return

        while True:
            console.print("\n[bold cyan]Kubernetes and CKA Lab Engine (labctl)[/bold cyan]")
            console.print("[dim]Select an option:[/dim]\n")

            action = questionary.select(
                "Action:",
                choices=[
                    "Start predefined mock exam (mock-01 to mock-06)",
                    "Deploy all 111 questions sequentially",
                    "Deploy selected question(s)",
                    "Generate random 17-question mock exam",
                    "Start custom practice drill",
                    "Start crazy mode (5 hard/chaos questions)",
                    "Grade active session",
                    "View active tasks",
                    "View solutions",
                    "Reset active session",
                    "Run preflight environment check",
                    "Exit",
                ],
            ).ask()

            if not action or action == "Exit":
                break

            if "Start predefined mock exam" in action:
                self._flow_preset_mock()
            elif "Deploy all 111 questions" in action:
                self._flow_deploy_all()
            elif "Deploy selected question" in action:
                self._flow_deploy_selected()
            elif "Generate random 17-question" in action:
                self._flow_random_mock()
            elif "Start custom practice drill" in action:
                self._flow_custom_drill()
            elif "Start crazy mode" in action:
                self._flow_crazy_gauntlet()
            elif "Grade active session" in action:
                self._flow_grade()
            elif "View active tasks" in action:
                self._flow_view_tasks()
            elif "View solutions" in action:
                self._flow_view_solutions()
            elif "Reset active session" in action:
                self._flow_reset()
            elif "Run preflight" in action:
                self._flow_preflight()

    def _flow_preset_mock(self) -> None:
        import questionary
        presets = self.selector.list_presets()
        if not presets:
            print("[Warning] No preset mock exams found in presets/ directory.")
            return

        choices = [f"{p['filename']} - {p.get('name', p['filename'])}" for p in presets]
        selected_choice = questionary.select("Select a mock exam preset:", choices=choices).ask()
        if not selected_choice:
            return

        preset_file = selected_choice.split(" - ")[0]
        data = self.selector.load_preset(preset_file)
        if not data:
            print(f"[Error] Failed to load preset {preset_file}.")
            return

        questions = self.selector.select_preset(data.get("questions", []))
        if not questions:
            print(f"[Error] No valid questions found in preset {preset_file}.")
            return

        confirm = questionary.confirm(
            f"Deploy '{data.get('name')}' ({len(questions)} tasks)?",
            default=True,
        ).ask()
        if confirm:
            session = self.deployer.deploy_sequential(
                questions,
                session_name=data.get("name", preset_file),
                time_limit_minutes=data.get("time_limit_minutes", 120),
            )
            self._render_tasks_instructions([session.questions[0]], start_idx=1)

    def _flow_deploy_all(self) -> None:
        import questionary
        questions = self.loader.get_all()
        if not questions:
            print("[Error] No questions found in catalog.")
            return

        confirm = questionary.confirm(
            f"Deploy all {len(questions)} curriculum questions sequentially?",
            default=True,
        ).ask()
        if confirm:
            session = self.deployer.deploy_sequential(
                questions,
                session_name=f"Full CKA Curriculum ({len(questions)} Tasks)",
                time_limit_minutes=None,
            )
            self._render_tasks_instructions([session.questions[0]], start_idx=1)

    def _flow_deploy_selected(self) -> None:
        import questionary
        all_q = self.loader.get_all()
        if not all_q:
            print("[Error] No questions found in catalog.")
            return

        choices = [
            questionary.Choice(
                title=f"[{q.id}] [{q.difficulty.value.upper()}] [{q.domain.value}] {q.title} ({q.target_context})",
                value=q.id,
            )
            for q in all_q
        ]

        selected_ids = questionary.checkbox(
            "Select questions to deploy (Space to select, Enter to confirm):",
            choices=choices,
        ).ask()

        if not selected_ids:
            return

        questions = [self.loader.get(qid) for qid in selected_ids if self.loader.get(qid) is not None]
        session_title = f"Task {questions[0].id}" if len(questions) == 1 else f"Selected Tasks ({len(questions)} Questions)"
        session = self.deployer.deploy_sequential(
            questions,
            session_name=session_title,
            time_limit_minutes=None,
        )
        self._render_tasks_instructions([session.questions[0]], start_idx=1)

    def _flow_random_mock(self) -> None:
        import questionary
        questions = self.selector.select_mock_exam(target_count=17)
        if not questions:
            print("[Error] No questions found in catalog to build mock exam.")
            return

        confirm = questionary.confirm(
            f"Deploy random mock exam ({len(questions)} tasks)?",
            default=True,
        ).ask()
        if confirm:
            self.deployer.deploy(questions, session_name="Random CKA Mock Exam (17 Tasks)", time_limit_minutes=120)
            self._render_tasks_instructions(questions)

    def _flow_custom_drill(self) -> None:
        import questionary

        # 1. Difficulty
        diff_choices = [
            {"name": "Easy", "value": Difficulty.EASY, "checked": True},
            {"name": "Medium", "value": Difficulty.MEDIUM, "checked": True},
            {"name": "Hard", "value": Difficulty.HARD, "checked": False},
            {"name": "Crazy", "value": Difficulty.CRAZY, "checked": False},
        ]
        selected_diffs = questionary.checkbox("Select difficulty level:", choices=diff_choices).ask()
        if not selected_diffs:
            selected_diffs = [Difficulty.EASY, Difficulty.MEDIUM]

        # 2. Domains
        domain_choices = [
            {"name": "Troubleshooting", "value": Domain.TROUBLESHOOTING, "checked": True},
            {"name": "Storage", "value": Domain.STORAGE, "checked": True},
            {"name": "Workloads and Scheduling", "value": Domain.WORKLOADS, "checked": True},
            {"name": "Cluster Architecture and Networking", "value": Domain.CLUSTER_ARCH, "checked": True},
            {"name": "Security", "value": Domain.SECURITY, "checked": True},
        ]
        selected_domains = questionary.checkbox("Select domains:", choices=domain_choices).ask()
        if not selected_domains:
            selected_domains = list(Domain)

        # 3. Cluster target
        cluster_target = questionary.select(
            "Target cluster:",
            choices=[
                "k3d (local cluster)",
                "kubeadm (remote nodes)",
                "Both",
            ],
        ).ask()
        target_contexts = ["k3d-cka"] if "k3d" in cluster_target else (["kubeadm-vms"] if "kubeadm" in cluster_target else None)

        # 4. Count
        count_choice = questionary.select(
            "Question count:",
            choices=["3 questions", "5 questions", "10 questions", "17 questions"],
        ).ask()
        count_map = {"3": 3, "5": 5, "10": 10, "17": 17}
        count = next((v for k, v in count_map.items() if k in count_choice), 5)

        questions = self.selector.select_custom(
            difficulties=selected_diffs,
            domains=selected_domains,
            target_contexts=target_contexts,
            count=count,
        )
        if not questions:
            print("[Warning] No matching questions found for the selected criteria.")
            return

        confirm = questionary.confirm(
            f"Found {len(questions)} question(s). Deploy now?",
            default=True,
        ).ask()
        if confirm:
            self.deployer.deploy(questions, session_name=f"Custom Drill ({count} Tasks)")
            self._render_tasks_instructions(questions)

    def _flow_crazy_gauntlet(self) -> None:
        import questionary
        questions = self.selector.select_crazy_gauntlet(count=5)
        if not questions:
            print("[Warning] No crazy/hard questions found in catalog.")
            return
        confirm = questionary.confirm(
            f"Deploy {len(questions)} crazy mode scenarios?",
            default=True,
        ).ask()
        if confirm:
            self.deployer.deploy(questions, session_name="Crazy Mode (5 Tasks)")
            self._render_tasks_instructions(questions)

    def _flow_grade(self) -> None:
        session = self.deployer.load_active_session(self.loader)
        if not session or not session.questions:
            print("\n[Warning] No active exam session found. Start one first.")
            return
        print(f"\nEvaluating {len(session.questions)} task(s) for '{session.name}'...")
        summaries = self.grader.grade_session(session)
        self.grader.render_scorecard(summaries)

    def _flow_view_tasks(self) -> None:
        session = self.deployer.load_active_session(self.loader)
        if not session or not session.questions:
            print("\n[Warning] No active session found.")
            return
        self._render_tasks_instructions(session.questions)

    def _flow_view_solutions(self) -> None:
        import questionary
        from rich.console import Console
        from rich.markdown import Markdown
        console = Console()

        all_q = self.loader.all()
        if not all_q:
            print("[Warning] No questions in catalog.")
            return

        choices = [f"{q.id} - {q.title} ({q.difficulty.value}, {q.domain.value})" for q in all_q]
        selected_str = questionary.select("Select a question to view solution:", choices=choices).ask()
        if not selected_str:
            return

        q_id = selected_str.split(" - ")[0]
        q = self.loader.get(q_id)
        if q and q.solution_file and q.solution_file.exists():
            with open(q.solution_file, "r", encoding="utf-8") as f:
                content = f.read()
            console.print(Markdown(content))
        else:
            print(f"Solution file not found for {q_id}.")

    def _flow_reset(self) -> None:
        import questionary
        confirm = questionary.confirm(
            "Clear active session state and delete test namespaces?",
            default=True,
        ).ask()
        if confirm:
            self.deployer.clear_session()
            print("Session cleared.")

    def _flow_preflight(self) -> None:
        import subprocess
        from pathlib import Path
        script = Path(__file__).parent.parent / "tools" / "preflight.sh"
        if script.exists():
            subprocess.run(["bash", str(script)])
        else:
            print("[Error] tools/preflight.sh not found.")

    def _render_tasks_instructions(self, questions: List[Question], start_idx: int = 1) -> None:
        try:
            from rich.console import Console
            from rich.panel import Panel
            console = Console()
            session = self.deployer.load_active_session(self.loader)
            flagged_ids = set(session.flagged) if session else set()

            heading = "[bold green]Active task[/bold green]" if len(questions) == 1 else "[bold green]Active tasks[/bold green]"
            console.print(f"\n{heading}\n")
            for idx, q in enumerate(questions, start_idx):
                diff_str = f"[bold yellow]{q.difficulty.value.upper()}[/bold yellow]"
                context_badge = f"[bold cyan]context: {q.target_context}[/bold cyan]"
                ns_badge = f"[magenta]ns: {q.namespace}[/magenta]" if q.namespace else "[dim]ns: default[/dim]"
                flag_badge = " [bold red][🚩 FLAGGED FOR REVIEW][/bold red]" if q.id in flagged_ids else ""

                header = f"Task {idx} [{diff_str}] ({q.points} pts) [{context_badge}] [{ns_badge}]{flag_badge}"
                body = f"[bold]{q.title}[/bold]\n\n{q.description}"

                console.print(Panel(body, title=header, border_style="blue"))
            prog = os.environ.get("EXAMCTL_PROG", "examctl")
            console.print(f"\n[dim]Navigate tasks with '{prog} next', '{prog} prev', '{prog} flag', or '{prog} jump <num>'.[/dim]")
            console.print("[dim]Task sheet exported to: sets/active_exam.md[/dim]\n")
        except Exception:
            for idx, q in enumerate(questions, start_idx):
                print(f"\nTask {idx} [{q.difficulty.value.upper()}] ({q.points} pts) [context: {q.target_context}]")
                print(f"Title: {q.title}")
                print(q.description)
