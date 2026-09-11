import json
import subprocess
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any
from core.models import Question, ExamSession
from core.loader import QuestionLoader
from core.recorder import recorder

SYSTEM_NAMESPACES = {"default", "kube-system", "kube-public", "kube-node-lease", "metallb-system", "local-path-storage"}


class LabDeployer:
    def __init__(self, session_file: Optional[Path] = None, sets_dir: Optional[Path] = None):
        self.session_file = session_file or (Path(__file__).parent.parent / "var" / "session.json")
        self.sets_dir = sets_dir or (Path(__file__).parent.parent / "sets")
        self.sets_dir.mkdir(parents=True, exist_ok=True)

    def _read_legacy_session(self) -> Optional[Dict[str, Any]]:
        """One-time read of a legacy session file, renamed to .migrated afterwards."""
        if not self.session_file or not self.session_file.exists():
            return None
        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[Warning] Failed to parse active session: {e}")
            return None
        try:
            migrated = self.session_file.with_name(self.session_file.name + ".migrated")
            self.session_file.rename(migrated)
        except Exception:
            pass
        try:
            session_id = data.get("session_id")
            if session_id:
                from core.redis_bus import bus as redis_bus
                redis_bus.set_session_state(session_id, data)
        except Exception:
            pass
        return data

    def _session_from_state(self, data: Optional[Dict[str, Any]], loader: QuestionLoader) -> Optional[ExamSession]:
        if not data:
            return None
        # Do not return completed or archived sessions as active
        if data.get("status") in ("completed", "submitted", "terminated", "replaced"):
            return None
        try:
            q_ids = data.get("question_ids", [])
            questions = [loader.get(qid) for qid in q_ids if loader.get(qid) is not None]
            return ExamSession(
                session_id=data.get("session_id", "default"),

                created_at=data.get("created_at", ""),
                name=data.get("name", "Active Practice Session"),
                questions=questions,
                target_contexts=data.get("target_contexts", []),
                time_limit_minutes=data.get("time_limit_minutes"),
                mode=data.get("mode", "batch"),
                current_index=data.get("current_index", 0),
                scores=data.get("scores", {}),
                flagged=data.get("flagged", []),
                scorecard=data.get("scorecard"),
                status=data.get("status", "active"),
                last_active_at=data.get("last_active_at"),
                candidate_token=data.get("candidate_token"),
                owner_username=data.get("owner_username"),
                assigned_by=data.get("assigned_by"),
            )
        except Exception as e:
            print(f"[Warning] Failed to parse active session: {e}")
            return None

    def load_session(self, loader: QuestionLoader, session_id: str) -> Optional[ExamSession]:
        """Loads a specific session by id (FS-003b: per-session resolution)."""
        if not session_id:
            return None
        try:
            from core.redis_bus import bus as redis_bus
            data = redis_bus.get_session_state(session_id)
        except Exception:
            data = None
        return self._session_from_state(data, loader)

    def load_active_session(self, loader: QuestionLoader) -> Optional[ExamSession]:
        """Legacy: the most-recent global session (pointer). Prefer
        `load_session` / contextual resolution for concurrent sessions."""
        data = None
        try:
            from core.redis_bus import bus as redis_bus
            data = redis_bus.get_session_state()
        except Exception:
            data = None

        if data is None:
            data = self._read_legacy_session()
        return self._session_from_state(data, loader)

    def save_session(self, session: ExamSession) -> None:
        data = session.to_dict()
        try:
            from core.redis_bus import bus as redis_bus
            redis_bus.set_session_state(session.session_id, data)
        except Exception:
            pass

    def clear_active_session(self, session_id: Optional[str] = None) -> None:
        try:
            from core.redis_bus import bus as redis_bus
            redis_bus.clear_session_state(session_id)
        except Exception:
            pass
        try:
            if self.session_file and self.session_file.exists():
                self.session_file.unlink(missing_ok=True)
        except Exception:
            pass


    def export_tasks_markdown(self, session: ExamSession) -> Path:
        """Exports the active exam questions as a clean Markdown task sheet in sets/."""
        slug = re.sub(r"[^a-zA-Z0-9_\-]+", "-", session.name.lower()).strip("-")
        md_file = self.sets_dir / f"{slug}.md"
        active_file = self.sets_dir / "active_exam.md"

        total_pts = sum(q.points for q in session.questions)
        time_limit = f"{session.time_limit_minutes} minutes" if session.time_limit_minutes else "Untimed"

        lines = [
            f"# {session.name}",
            "",
            f"- **Session ID:** `{session.session_id}`",
            f"- **Total Tasks:** {len(session.questions)}",
            f"- **Total Points:** {total_pts} pts",
            f"- **Time Limit:** {time_limit}",
            f"- **Pass Threshold:** 66%",
            f"- **Mode:** `{session.mode}`",
            "",
            "To navigate tasks during the exam:",
            f"- Run `{os.environ.get('EXAMCTL_PROG', 'examctl')} task` to view the current active task",
            f"- Run `{os.environ.get('EXAMCTL_PROG', 'examctl')} next` to deploy and advance to the next task",
            f"- Run `{os.environ.get('EXAMCTL_PROG', 'examctl')} prev` to return to the previous task",
            f"- Run `{os.environ.get('EXAMCTL_PROG', 'examctl')} jump <num>` to jump directly to a task",
            f"- Run `{os.environ.get('EXAMCTL_PROG', 'examctl')} status` to view overall exam progress",
            "",
            "---",
            "",
        ]

        for idx, q in enumerate(session.questions, 1):
            ns_str = q.namespace if q.namespace else "default"
            status_indicator = ""
            if session.mode == "sequential":
                if idx - 1 == session.current_index:
                    status_indicator = " (CURRENT ACTIVE TASK)"
                elif q.id in session.scores:
                    passed = session.scores[q.id].get("passed", False)
                    status_indicator = f" ({'PASSED' if passed else 'FAILED'})"

            lines.extend([
                f"### Task {idx}: {q.title} [{q.difficulty.value.upper()}] ({q.points} pts){status_indicator}",
                f"- **ID:** `{q.id}`",
                f"- **Context:** `{q.target_context}`",
                f"- **Namespace:** `{ns_str}`",
                "",
                "#### Description",
                q.description.strip(),
                "",
                "---",
                "",
            ])

        content = "\n".join(lines).strip() + "\n"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(content)
        with open(active_file, "w", encoding="utf-8") as f:
            f.write(content)

        # Store task sheet in Redis for candidate container injection (zero host /home/exam pollution)
        try:
            from core.redis_bus import bus as redis_bus
            client = redis_bus.get_sync_client()
            if client:
                client.setex(f"session:{session.session_id}:exam_md", 86400, content)
                client.setex("k8s:active_exam_md", 86400, content)
        except Exception:
            pass

        return md_file

    def clear_session(self, cleanup_cluster: bool = True) -> None:
        active_sid = None
        try:
            from core.redis_bus import bus as redis_bus
            active_sid = redis_bus.get_active_session_id()
            if active_sid:
                from core.desktop_manager import desktop_mgr
                desktop_mgr.stop_desktop(active_sid)
        except Exception:
            active_sid = None

        if active_sid:
            try:
                recorder.log_event("SESSION_RESET", {"cleanup_cluster": cleanup_cluster})
                recorder.close()
            except Exception:
                pass
            if cleanup_cluster:
                self._cleanup_cluster_resources()

        try:
            from core.redis_bus import bus as redis_bus
            redis_bus.clear_session_state()
        except Exception:
            pass

        try:
            if self.session_file and self.session_file.exists():
                self.session_file.unlink()
        except Exception:
            pass

        active_file = self.sets_dir / "active_exam.md"
        if active_file.exists():
            try:
                active_file.unlink()
            except Exception:
                pass

    def _cleanup_cluster_resources(self, questions: Optional[List[Question]] = None, exclude_namespace: Optional[str] = None) -> None:
        """Purges test-created namespaces, webhooks, and iptables rules from target contexts."""
        data = None
        try:
            from core.redis_bus import bus as redis_bus
            data = redis_bus.get_session_state()
        except Exception:
            data = None

        SYSTEM_NAMESPACES = {"default", "kube-system", "kube-public", "kube-node-lease", "metallb-system", "local-path-storage"}
        loader = QuestionLoader()
        namespaces = set()
        if questions:
            for q in questions:
                if q and q.namespace and q.namespace not in SYSTEM_NAMESPACES:
                    namespaces.add(q.namespace)
        if data:
            for qid in data.get("question_ids", []):
                q = loader.get(qid)
                if q and q.namespace and q.namespace not in SYSTEM_NAMESPACES:
                    namespaces.add(q.namespace)

        contexts = [c for c in (data.get("target_contexts") or []) if c] if data else []
        if questions:
            target_ctxs = {q.target_context for q in questions if q.target_context}
            if target_ctxs:
                contexts = list(target_ctxs)
        if not contexts:
            contexts = ["k3d-cka"]

        available = set()
        res = subprocess.run(
            ["kubectl", "config", "get-contexts", "-o", "name"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=3,
        )
        if res.returncode == 0:
            available = {line.strip() for line in res.stdout.splitlines() if line.strip()}

        for ctx_name in contexts:
            if ctx_name not in available:
                continue

            # Fast reachability check (2 second timeout)
            try:
                probe = subprocess.run(
                    ["kubectl", "--context", ctx_name, "--request-timeout=2s", "get", "nodes", "--no-headers"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3,
                )
                if probe.returncode != 0:
                    continue
            except Exception:
                continue

            try:
                # Query all non-system namespaces live on the cluster
                ns_res = subprocess.run(
                    ["kubectl", "--context", ctx_name, "--request-timeout=3s", "get", "ns", "-o", "jsonpath={.items[*].metadata.name}"],
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=5,
                )
                live_ns = set()
                if ns_res.returncode == 0 and ns_res.stdout.strip():
                    for n in ns_res.stdout.strip().split():
                        if n not in SYSTEM_NAMESPACES:
                            live_ns.add(n)

                all_to_delete = sorted((namespaces | live_ns) - {exclude_namespace} if exclude_namespace else (namespaces | live_ns))
                if all_to_delete:
                    for del_ns in all_to_delete:
                        subprocess.run(
                            ["kubectl", "--context", ctx_name, "--request-timeout=3s", "delete", "pods", "--all", "-n", del_ns, "--force", "--grace-period=0"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5,
                        )
                        subprocess.run(
                            ["kubectl", "--context", ctx_name, "--request-timeout=3s", "delete", "namespace", del_ns, "--wait=false", "--ignore-not-found"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5,
                        )
                subprocess.run(
                    ["kubectl", "--context", ctx_name, "--request-timeout=3s", "delete",
                     "validatingwebhookconfiguration,mutatingwebhookconfiguration",
                     "strict-policy-enforcer", "admission-hook", "audit-injector", "--ignore-not-found"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5,
                )
                try:
                    if questions is None:
                        subprocess.run(
                            ["kubectl", "--context", ctx_name, "--request-timeout=3s", "delete", "pv", "--all", "--wait=false"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5,
                        )
                    else:
                        subprocess.run(
                            ["kubectl", "--context", ctx_name, "--request-timeout=3s", "delete", "pv",
                             "--field-selector=status.phase=Released", "--wait=false"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5,
                        )
                except Exception:
                    pass
            except Exception:
                pass

            if ctx_name.startswith("k3d-"):
                try:
                    subprocess.run(
                        ["kubectl", "--context", ctx_name, "--request-timeout=3s", "taint", "nodes", "--all", "node-role.kubernetes.io/control-plane:NoSchedule-", "maintenance-"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5,
                    )
                    cluster = ctx_name[len("k3d-"):]
                    for node in (f"k3d-{cluster}-server-0", f"k3d-{cluster}-agent-0", f"k3d-{cluster}-agent-1"):
                        if subprocess.run(["docker", "inspect", node],
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                            subprocess.run(
                                ["docker", "exec", node, "iptables", "-t", "mangle", "-D",
                                 "PREROUTING", "-d", "10.43.0.0/16", "-j", "DROP"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5,
                            )
                except Exception:
                    pass

            if ctx_name in ("kubeadm-vms", "kubernetes"):
                try:
                    node1_target = os.getenv("NODE_1_IP", os.getenv("NODE_1", "node1"))
                    ssh_user = os.getenv("SSH_USER", "root")
                    ssh_key = os.getenv("SSH_KEY_PATH", os.getenv("SSH_KEY", os.path.expanduser("~/.ssh/id_rsa")))
                    ssh_cmd_args = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=2"]
                    if os.path.exists(ssh_key):
                        ssh_cmd_args.extend(["-i", ssh_key])
                    # If target is already configured in ~/.ssh/config (e.g. Host node1), ssh node1 works directly
                    ssh_dest = f"{ssh_user}@{node1_target}" if "@" not in node1_target else node1_target
                    subprocess.run(
                        [*ssh_cmd_args, ssh_dest,
                         "rm -rf /opt/backup /var/lib/etcd-restore /etc/kubernetes/manifests/node-monitor.yaml 2>/dev/null || true"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5,
                    )
                except Exception:
                    pass

        # Execute custom cleanup/teardown scripts for questions
        cleanup_qs = list(questions or [])
        if data:
            for qid in data.get("question_ids", []):
                q = loader.get(qid)
                if q:
                    cleanup_qs.append(q)
        for q in cleanup_qs:
            if getattr(q, "cleanup_script", None) and q.cleanup_script.exists():
                try:
                    subprocess.run(
                        ["bash", str(q.cleanup_script)],
                        cwd=str(q.path),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=10,
                    )
                except Exception:
                    pass


    def deploy(
        self,
        questions: List[Question],
        session_name: str = "Practice Session",
        time_limit_minutes: Optional[int] = 120,
    ) -> ExamSession:
        if not questions:
            raise ValueError("No questions provided for deployment.")

        print(f"\nDeploying {len(questions)} scenario(s) for '{session_name}'...")
        target_contexts = list({q.target_context for q in questions})

        def _deploy_priority(q: Question) -> int:
            if q.breaking:
                return 2
            if q.cluster_scoped:
                return 1
            return 0

        ordered = sorted(questions, key=_deploy_priority)

        deployed_q: List[Question] = []
        for idx, q in enumerate(ordered, 1):
            print(f"  [{idx}/{len(questions)}] Deploying {q.id} ({q.title})...", end="", flush=True)
            if q.setup_script and q.setup_script.exists():
                try:
                    res = subprocess.run(
                        ["bash", str(q.setup_script)],
                        cwd=str(q.path),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=30,
                    )
                    if res.returncode == 0:
                        print(" [OK]")
                        deployed_q.append(q)
                    else:
                        print(f" [FAILED] {res.stderr.strip()[:100]}")
                except Exception as ex:
                    print(f" [ERROR] {ex}")
            else:
                print(" [READY]")
                deployed_q.append(q)

        session = ExamSession(
            session_id=f"session-{int(time.time())}",
            created_at=datetime.now(timezone.utc).isoformat(),
            name=session_name,
            questions=deployed_q,
            target_contexts=target_contexts,
            time_limit_minutes=time_limit_minutes,
            mode="batch",
            current_index=0,
            scores={},
        )
        self.save_session(session)
        try:
            recorder.start_session(
                session_id=session.session_id,
                name=session.name,
                total_tasks=len(session.questions),
                time_limit_minutes=time_limit_minutes,
                target_contexts=target_contexts,
                questions=[{"id": q.id, "title": q.title, "points": q.points, "context": q.target_context} for q in session.questions],
            )
        except Exception:
            pass
        md_path = self.export_tasks_markdown(session)
        print(f"  Exported task sheet to: {md_path.relative_to(self.sets_dir.parent)}")

        return session

    def deploy_sequential(
        self,
        questions: List[Question],
        session_name: str = "Sequential Exam",
        time_limit_minutes: Optional[int] = 120,
    ) -> ExamSession:
        if not questions:
            raise ValueError("No questions provided for deployment.")

        # Clean any existing session and previous leftover test namespaces
        self.clear_session()
        self._cleanup_cluster_resources(questions)

        session = ExamSession(
            session_id=f"session-{int(time.time())}",
            created_at=datetime.now(timezone.utc).isoformat(),
            name=session_name,
            questions=questions,
            target_contexts=list({q.target_context for q in questions}),
            time_limit_minutes=time_limit_minutes,
            mode="sequential",
            current_index=0,
            scores={},
        )
        self.save_session(session)
        try:
            recorder.start_session(
                session_id=session.session_id,
                name=session.name,
                total_tasks=len(session.questions),
                time_limit_minutes=time_limit_minutes,
                target_contexts=session.target_contexts,
                questions=[{"id": q.id, "title": q.title, "points": q.points, "context": q.target_context} for q in questions],
            )
        except Exception:
            pass
        self.export_tasks_markdown(session)
        try:
            res = subprocess.run(["kubectl", "config", "get-contexts", "-o", "name"], capture_output=True, text=True, timeout=2)
            if "k3d-cka" in res.stdout.splitlines():
                self.deploy_step(session, 0)
        except Exception:
            pass
        return session

    def deploy_step(self, session: ExamSession, index: int, force_setup: bool = False, progress_cb: Optional[Any] = None) -> bool:
        if index < 0 or index >= len(session.questions):
            print(f"[Error] Task index {index + 1} out of range (1 to {len(session.questions)}).")
            return False

        try:
            recorder.attach_or_resume(session.session_id, session.name)
        except Exception:
            pass

        leaving_q = None
        is_leaving_flagged = False
        # Silently record score for the task we are leaving before wiping its cluster resources
        if session.current_index is not None and 0 <= session.current_index < len(session.questions) and session.current_index != index:
            leaving_q = session.questions[session.current_index]
            flagged_list = getattr(session, "flagged", []) or []
            is_leaving_flagged = bool(
                leaving_q.id in flagged_list
                or getattr(leaving_q, "is_flagged", False)
            )

            if progress_cb:
                progress_cb("grading", f"Evaluating Task {session.current_index + 1}", 1, 3, f"Evaluating rubric for {leaving_q.title}...")

            if is_leaving_flagged:
                # Do not grade flagged task when switching between tasks
                session.scores[leaving_q.id] = {
                    "passed": False,
                    "score": 0,
                    "max_score": leaving_q.points,
                    "message": "Flagged for review (Pending submission)",
                }
            else:
                try:
                    import concurrent.futures
                    from core.grader import LabGrader
                    evaluator = LabGrader()
                    # Hard 3-second timeout so grading never blocks advancing
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(evaluator.grade_question, leaving_q)
                        res = future.result(timeout=3)

                    session.scores[leaving_q.id] = {
                        "passed": res.passed,
                        "score": res.score,
                        "max_score": res.max_score,
                        "message": res.message,
                    }
                except Exception as e:
                    session.scores[leaving_q.id] = {
                        "passed": False,
                        "score": 0,
                        "max_score": leaving_q.points,
                        "message": "Evaluation timed out or error",
                    }

            try:
                leaving_score = session.scores.get(leaving_q.id, {})
                recorder.log_event("TASK_EVALUATION", {
                    "task_num": session.current_index + 1,
                    "question_id": leaving_q.id,
                    "score": leaving_score.get("score", 0),
                    "max_score": leaving_score.get("max_score", leaving_q.points),
                    "passed": leaving_score.get("passed", False),
                    "message": leaving_score.get("message", ""),
                })
            except Exception:
                pass

        session.current_index = index
        q = session.questions[index]

        if progress_cb:
            progress_cb("cleanup", "Preparing Cluster Environment", 2, 3, "Cleaning ephemeral namespaces and cluster states...")

        # Fast cleanup: Only clean leaving task's specific namespace instead of scanning whole cluster.
        # Preserve namespace for flagged tasks so they can be reviewed and graded upon final exam submission!
        if leaving_q and not is_leaving_flagged and leaving_q.namespace and leaving_q.namespace not in SYSTEM_NAMESPACES and leaving_q.namespace != q.namespace:
            try:
                subprocess.Popen(
                    ["kubectl", "--context", leaving_q.target_context, "--request-timeout=2s",
                     "delete", "namespace", leaving_q.namespace, "--wait=false", "--ignore-not-found"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass

        # Run custom cleanup script for leaving task if defined and not flagged
        if leaving_q and not is_leaving_flagged and getattr(leaving_q, "cleanup_script", None) and leaving_q.cleanup_script.exists():
            try:
                subprocess.Popen(
                    ["bash", str(leaving_q.cleanup_script)],
                    cwd=str(leaving_q.path),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass



        # Clean up DNS overrides when leaving DNS tasks
        if leaving_q and leaving_q.id in ("CA-010", "TR-005"):
            try:
                subprocess.run(["kubectl", "--context", "k3d-cka", "-n", "kube-system", "delete", "configmap", "coredns-custom", "--ignore-not-found"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
            except Exception:
                pass

        # Prevent cordoning from leaking across exam tasks
        k3d_ctx = os.getenv("K3D_CONTEXT", "k3d-cka")
        kubeadm_ctx = os.getenv("KUBEADM_CONTEXT", "kubeadm-vms")
        k3d_cluster = os.getenv("K3D_CLUSTER_NAME", "cka")
        if q.target_context == k3d_ctx and q.id not in ("CA-005", "TR-008", "TR-014"):
            try:
                subprocess.run(["kubectl", "--context", k3d_ctx, "uncordon", f"k3d-{k3d_cluster}-agent-0", f"k3d-{k3d_cluster}-agent-1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
            except Exception:
                pass
        elif q.target_context == kubeadm_ctx and q.id not in ("CA-004", "TR-008", "TR-014"):
            try:
                subprocess.run(["kubectl", "--context", kubeadm_ctx, "uncordon", os.getenv("NODE_2", "node2"), os.getenv("NODE_3", "node3")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
            except Exception:
                pass

        if progress_cb:
            progress_cb("deploying", f"Deploying Task {index + 1}", 3, 3, f"Applying manifests for {q.title}...")

        print(f"\n[Deployer] Deploying Task {index + 1}/{len(session.questions)}: {q.id} ({q.title})...", end="", flush=True)

        is_target_flagged = bool(
            q.id in getattr(session, "flagged", [])
            or getattr(q, "is_flagged", False)
            or (session.scores.get(q.id, {}).get("message", "").startswith("Flagged for review"))
        )

        try:
            recorder.log_event("TASK_DEPLOYED", {
                "task_num": index + 1,
                "question_id": q.id,
                "title": q.title,
                "domain": q.domain.value if hasattr(q.domain, "value") else str(q.domain),
                "difficulty": q.difficulty.value if hasattr(q.difficulty, "value") else str(q.difficulty),
                "context": q.target_context,
                "namespace": q.namespace or "default",
                "points": q.points,
                "is_flagged": is_target_flagged,
            })
        except Exception:
            pass

        should_run_setup = True
        if is_target_flagged and not force_setup:
            # Candidate switched back to an already attempted / flagged task.
            # Do NOT reset or overwrite candidate's existing work!
            should_run_setup = False
            print(" [PRESERVED FLAGGED WORK]")

        if should_run_setup and q.setup_script and q.setup_script.exists():
            if q.target_context:
                try:
                    subprocess.run(
                        ["kubectl", "config", "use-context", q.target_context],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=3,
                    )
                except Exception:
                    pass
            setup_env = os.environ.copy()
            setup_env["KUBECTL_CONTEXT"] = q.target_context or "k3d-cka"
            try:
                res = subprocess.run(
                    ["bash", str(q.setup_script)],
                    env=setup_env,
                    cwd=str(q.path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=35,
                )
                if res.returncode == 0:
                    print(" [OK]")
                else:
                    print(f" [FAILED] {res.stderr.strip()[:100]}")
            except Exception as ex:
                print(f" [ERROR] {ex}")
        elif not should_run_setup:
            pass
        else:
            print(" [READY]")

        if progress_cb:
            progress_cb("ready", f"Task {index + 1} Ready", 3, 3, "Ready for candidate input.")

        self.save_session(session)
        self.export_tasks_markdown(session)
        return True

    def render_session_status(self, session: ExamSession) -> None:
        try:
            from rich.console import Console
            from rich.table import Table
            console = Console()
            table = Table(title=f"Exam Status: {session.name} ({len(session.questions)} Tasks)", header_style="bold cyan")
            table.add_column("Task #", justify="center", style="bold")
            table.add_column("ID", style="dim")
            table.add_column("Title")
            table.add_column("Points", justify="center")
            table.add_column("Context", style="blue")
            table.add_column("Status", justify="center")

            total_earned = 0
            max_points = sum(q.points for q in session.questions)

            for idx, q in enumerate(session.questions, 1):
                cur_tag = " [CURRENT]" if session.mode == "sequential" and idx - 1 == session.current_index else ""
                is_flagged = q.id in session.flagged
                flag_tag = " [bold red]🚩[/bold red]" if is_flagged else ""

                if q.id in session.scores:
                    sc = session.scores[q.id]
                    if sc.get("passed", False):
                        status = f"[green]PASS ({sc.get('score')}/{sc.get('max_score')}){cur_tag}[/green]{flag_tag}"
                    else:
                        status = f"[red]FAIL ({sc.get('score')}/{sc.get('max_score')}){cur_tag}[/red]{flag_tag}"
                    total_earned += sc.get("score", 0)
                elif session.mode == "sequential" and idx - 1 == session.current_index:
                    status = f"[bold yellow]CURRENT[/bold yellow]{flag_tag}"
                elif is_flagged:
                    status = f"[bold yellow]FLAGGED[/bold yellow]{flag_tag}"
                else:
                    status = "[dim]PENDING[/dim]"

                table.add_row(
                    str(idx),
                    q.id,
                    q.title,
                    str(q.points),
                    q.target_context,
                    status,
                )

            console.print("\n")
            console.print(table)
            console.print(f"\n[bold]Current Score:[/bold] {total_earned}/{max_points} pts")
            prog = os.environ.get("EXAMCTL_PROG", "examctl")
            if session.flagged:
                flagged_nums = [str(i) for i, q in enumerate(session.questions, 1) if q.id in session.flagged]
                console.print(f"[bold yellow]🚩 Flagged for review ({len(session.flagged)} tasks):[/bold yellow] Tasks {', '.join(flagged_nums)} (jump with '{prog} jump <num>')")
            console.print(f"[dim]Use '{prog} next', '{prog} prev', '{prog} flag', or '{prog} jump <num>' to navigate tasks.[/dim]\n")
        except Exception:
            print(f"\nExam Status: {session.name} ({len(session.questions)} Tasks)")
            for idx, q in enumerate(session.questions, 1):
                cur = " <= CURRENT" if session.mode == "sequential" and idx - 1 == session.current_index else ""
                fl = " [FLAGGED 🚩]" if q.id in session.flagged else ""
                print(f"  [{idx}/{len(session.questions)}] {q.id} ({q.points} pts): {q.title}{cur}{fl}")
