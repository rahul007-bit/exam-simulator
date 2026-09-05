import importlib.util
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.models import ExamSession, Question, GradeResult, TaskGradeSummary
from core.graderlib import KubernetesContext


class LabGrader:
    def __init__(self):
        self._contexts: Dict[str, KubernetesContext] = {}

    def get_context(self, context_name: str) -> KubernetesContext:
        if context_name not in self._contexts:
            self._contexts[context_name] = KubernetesContext(context_name=context_name)
        return self._contexts[context_name]

    def grade_question(self, question: Question) -> GradeResult:
        if not question.grader_script or not question.grader_script.exists():
            return GradeResult(
                passed=False,
                score=0,
                max_score=question.points,
                message="No grader.py found for this task",
            )

        ctx = self.get_context(question.target_context)
        try:
            spec = importlib.util.spec_from_file_location(
                f"grader_{question.id}", str(question.grader_script)
            )
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[f"grader_{question.id}"] = mod
                spec.loader.exec_module(mod)
                if hasattr(mod, "grade"):
                    res = mod.grade(ctx)
                    if isinstance(res, GradeResult):
                        return res
                    elif isinstance(res, tuple) and len(res) >= 4:
                        return GradeResult(
                            passed=bool(res[0]),
                            score=int(res[1]),
                            max_score=int(res[2]),
                            message=str(res[3]),
                        )
                    elif isinstance(res, bool):
                        return GradeResult(
                            passed=res,
                            score=question.points if res else 0,
                            max_score=question.points,
                            message="Passed" if res else "Assertion failed",
                        )
            return GradeResult(
                passed=False,
                score=0,
                max_score=question.points,
                message="Grader module did not export valid grade() function",
            )
        except Exception as e:
            return GradeResult(
                passed=False,
                score=0,
                max_score=question.points,
                message=f"Grader execution error: {e}",
            )

    def grade_session(self, session: ExamSession) -> List[TaskGradeSummary]:
        summaries: List[TaskGradeSummary] = []
        if session.mode == "sequential":
            for idx, q in enumerate(session.questions, 1):
                if q.id in session.scores:
                    sc = session.scores[q.id]
                    msg = sc.get("message", "Evaluated in step mode")
                    is_flagged = str(msg).startswith("Flagged for review") or q.id in getattr(session, "flagged", [])
                    if is_flagged and not sc.get("passed", False):
                        try:
                            res = self.grade_question(q)
                            session.scores[q.id] = {
                                "passed": res.passed,
                                "score": res.score,
                                "max_score": res.max_score,
                                "message": res.message,
                            }
                        except Exception:
                            res = GradeResult(
                                passed=sc.get("passed", False),
                                score=sc.get("score", 0),
                                max_score=sc.get("max_score", q.points),
                                message="Validation failed",
                            )
                    else:
                        res = GradeResult(
                            passed=sc.get("passed", False),
                            score=sc.get("score", 0),
                            max_score=sc.get("max_score", q.points),
                            message=msg,
                        )
                else:
                    res = GradeResult(
                        passed=False,
                        score=0,
                        max_score=q.points,
                        message="Not attempted",
                    )
                summaries.append(TaskGradeSummary(task_num=idx, question=q, result=res))
        else:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                results = list(executor.map(self.grade_question, session.questions))
            for idx, (q, res) in enumerate(zip(session.questions, results), 1):
                summaries.append(TaskGradeSummary(task_num=idx, question=q, result=res))
        return summaries

    def render_scorecard(self, summaries: List[TaskGradeSummary]) -> None:
        try:
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel

            console = Console()
            table = Table(title="Exam Scorecard", header_style="bold cyan")
            table.add_column("Task #", justify="center", style="bold")
            table.add_column("ID", style="dim")
            table.add_column("Domain", style="magenta")
            table.add_column("Diff", justify="center")
            table.add_column("Context", style="blue")
            table.add_column("Score", justify="center")
            table.add_column("Status", justify="center")
            table.add_column("Diagnostics / Message")

            total_score = 0
            max_total = 0

            for item in summaries:
                q = item.question
                res = item.result
                total_score += res.score
                max_total += res.max_score

                status_str = "[green]PASS[/green]" if res.passed else "[red]FAIL[/red]"
                if res.skipped:
                    status_str = "[yellow]SKIPPED[/yellow]"

                diff_badge = f"[yellow]{q.difficulty.value}[/yellow]"
                if q.difficulty.value == "crazy":
                    diff_badge = "[bold red]CRAZY[/bold red]"
                elif q.difficulty.value == "hard":
                    diff_badge = "[red]HARD[/red]"

                table.add_row(
                    str(item.task_num),
                    q.id,
                    q.domain.value,
                    diff_badge,
                    q.target_context,
                    f"{res.score}/{res.max_score}",
                    status_str,
                    res.message,
                )

            console.print("\n")
            console.print(table)

            percentage = (total_score / max_total * 100) if max_total > 0 else 0
            is_pass = percentage >= 66

            summary_text = (
                f"[bold]Total Score:[/bold] {total_score} / {max_total} pts ([bold]{percentage:.1f}%[/bold])\n"
                f"[bold]Result:[/bold] "
                + ("[bold green]PASSED (>= 66%)[/bold green]" if is_pass else "[bold red]FAILED (< 66%)[/bold red]")
            )
            console.print(Panel(summary_text, title="Summary", border_style="green" if is_pass else "red"))
            console.print("\n")

        except ImportError:
            print("\nScorecard:")
            print(f"{'Task':<6}{'ID':<10}{'Domain':<16}{'Score':<8}{'Status':<10}{'Message'}")
            print("-" * 75)
            total_score = sum(s.result.score for s in summaries)
            max_total = sum(s.result.max_score for s in summaries)
            for item in summaries:
                status = "PASS" if item.result.passed else "FAIL"
                print(f"#{item.task_num:<5}{item.question.id:<10}{item.question.domain.value:<16}{item.result.score}/{item.result.max_score:<5}{status:<10}{item.result.message}")
            print("-" * 75)
            pct = (total_score / max_total * 100) if max_total > 0 else 0
            print(f"Total: {total_score}/{max_total} ({pct:.1f}%), {'PASSED' if pct >= 66 else 'FAILED'}\n")
