## 2026-09-07T18:02:38Z
You are the SWE Orchestrator (teamwork_preview_swe).

Working directory for your metadata (BRIEFING.md, progress.md, etc.):
C:/Users/HP/Projects/4-sep-test/cka-labs/.agents/teamwork_preview_swe_1

Project workspace directory:
C:/Users/HP/Projects/4-sep-test/cka-labs

Original user request is recorded at:
C:/Users/HP/Projects/4-sep-test/cka-labs/.agents/ORIGINAL_REQUEST.md

Mission:
Implement and stabilize a dynamic, fast Incus node provisioning engine for CKA multi-node cluster scenarios, supporting sub-15s local copy-on-write snapshot launching and dynamically scaling across multiple remote VM hosts when available.

Key Requirements:
- R1. Dynamic Incus Engine with Fast CoW Snapshot Provisioning: Dynamic inspection of Incus remotes/hosts, fast CoW instance creation from pre-cached golden images (<20s per local node), automatic discovery/distribution of workers across remote VM hosts when present, graceful fallback to local system containers when remotes are absent. Security profile nesting=true, CPU/memory limits.
- R2. Resilient Kubeadm Bootstrap, Worker Join, & Kubeconfig Distribution: Automate control-plane init or worker join sequence across provisioned Incus instances. Sanitize and sync kubeconfig into Redis, host, and active candidate container cka-desktop-{session_id} with context name kubeadm-vms. Non-blocking node readiness polling. All nodes transition to Ready in k8s.
- R3. Safe Lifecycle Teardown & Resource Isolation: Complete teardown stopping and deleting ephemeral Incus instances, attached networks, and storage volumes upon session termination/reset. Idempotent, robust against partial failures, zero orphan instances or stale contexts.
- Programmatic end-to-end verification test script passing with exit code 0.

Relevant codebase files:
- core/incus_manager.py
- core/sandbox_orchestrator.py
- core/desktop_manager.py

Maintain progress.md and BRIEFING.md in your working directory C:/Users/HP/Projects/4-sep-test/cka-labs/.agents/teamwork_preview_swe_1.
Report completion back when all requirements and acceptance criteria are implemented and verified.
