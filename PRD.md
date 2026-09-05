# Product Requirement Document (PRD)
# Kubernetes & CKA Interactive Lab Engine, Web Simulator & Question Bank (`labctl` & `examctl`)

**Document Version:** 2.0.0  
**Status:** Approved  
**Author:** AI Pair Programming & Platform Engineering Team  
**Date:** September 5, 2026  
**Target Release:** v2.0-GA  

---

## 1. Executive Summary

The **Kubernetes & CKA Interactive Lab Platform (`cka-labs`)** is an open, modular, hands-on training, troubleshooting, and exam simulation environment. It bridges the gap between basic Kubernetes tutorials and high-stakes production incident triage / Linux Foundation Certified Kubernetes Administrator (CKA) certification exams.

The platform provides:
1. An **Interactive Web Simulator** (PSI / Killer.sh style) with a split-screen layout: task instructions, live timer, and question navigator on the left; embedded xterm.js terminal and native TigerVNC/noVNC remote desktop on the right.
2. A **Dual-CLI Architecture**:
   - `labctl` (Admin/Proctor CLI): Full engine control, question seeding, grading, solutions, and environment management (restricted to `root`).
   - `examctl` (Candidate CLI): Safe student-facing interface for task navigation (`task`, `status`, `next`, `prev`, `jump`, `flag`, `unflag`) with granular sudoers lockdown.
3. A **Catalog of 111 Standardized, Modular Questions** across five CKA domains and four difficulty tiers (**Easy**, **Medium**, **Hard**, and **Crazy/Chaos**), bundled into **18 structured presets** (including 6 full 17-question CKA mock exams).
4. A **Hybrid Infrastructure Topology**:
   - Local disposable containerized cluster (`k3d-cka`, 1 server + 2 agents) for rapid namespace-scoped drills.
   - Live multi-node Kubeadm cluster (`kubeadm-vms`) running native **CRI-O on RHEL 9** for realistic baremetal/VM operations (etcd backup/restore, kubeadm upgrades, static pod debugging, systemd kubelet repair).
5. **Universal Dynamic Deployability (Strategic Objective for Phase 2)**:
   - Complete elimination of hardcoded IPs, hostnames, and usernames across all scripts, tools, and question modules.
   - Dynamic environment configuration via `.env`, intelligent discovery, and portable cross-platform execution.

---

## 2. Problem Statement & Strategic Goals

### 2.1 The Current Industry Gaps
1. **Static & Predictable Mock Exams**: Traditional platforms offer 2–3 static exam sessions. Once attempted, students memorize specific question orders and bug locations, destroying replay value.
2. **Superficial Syntax Testing**: Most practice tools test simple resource creation (e.g. `kubectl run ...`) rather than complex, realistic failure modes (e.g. CoreDNS loop crashes, cgroup driver mismatches, admission webhook deadlocks, multi-taint anti-affinity traps, kubelet cert expirations).
3. **Lack of True Exam Realism**: Candidates struggle during the real CKA exam because standard web consoles differ significantly from the dual-cluster, SSH-heavy, terminal-and-browser Linux Foundation PSI testing interface.
4. **Hardcoded, Brittle Deployment Scripts**: Legacy lab platforms hardcode private IP addresses and usernames, making them impossible to run on new laptops, cloud VMs, or custom homelabs without rewriting scripts.

### 2.2 Core Product Objectives
- **Realistic Exam & SRE Simulation**: Match the real CKA exam interface, scoring threshold (66%), time limits (2 hours), and multi-context workflows.
- **Extreme Troubleshooting Focus**: Over 60% of the question bank centers on real-world diagnostics, node failures, network partitions, storage binding deadlocks, and control-plane recovery.
- **Pure Kubeadm & CRI-O Realism**: Real multi-node Kubeadm cluster with native CRI-O runtime—zero KIND/k3d emulation on host nodes.
- **Universal Dynamic Deployability**: Allow anyone to clone the repo, specify their node IPs in `.env`, and immediately deploy the full platform on any system without touching source code.

---

## 3. User Personas & Permissions Model

### 3.1 Personas
| Persona | Context | Key Needs & Permissions |
| :--- | :--- | :--- |
| **Alex — CKA Candidate** | Taking mock exams to prepare for CKA certification | Operates in sandboxed Web Simulator or candidate shell (`exam` user). Can navigate tasks, view instructions, edit manifests, and SSH to remote nodes. **Strictly blocked** from host sudo, viewing solutions, or premature self-grading. |
| **Priya — Platform / SRE Engineer** | Drilling high-stakes production incident triage | Runs "Crazy Mode" chaos gauntlet. Requires authentic node-level failure modes (iptables drops, etcd quorum loss, broken admission webhooks). |
| **Sam — Kubernetes Trainer / Proctor** | Conducting training workshops or proctoring exams | Uses `labctl` (as `root` / admin). Deploys presets, inspects grader results, resets broken states, and monitors student progression. |

### 3.2 Privilege Separation Matrix
```
+---------------------------------------------------------------------------------------+
| JUMPHOST / PLATFORM HOST                                                              |
|                                                                                       |
|  [ Admin / Proctor: root ]                                                            |
|   ├── Directory: /root/cka-labs (chmod 700)                                           |
|   ├── Tool: labctl (deploy, grade, reset, solution, preflight, web)                   |
|   └── Sudoers: Full NOPASSWD:ALL                                                      |
|                                                                                       |
|  [ Candidate: exam ]                                                                  |
|   ├── Directory: /home/exam (unprivileged user)                                       |
|   ├── Tool: /usr/local/bin/examctl (task, status, next, prev, jump, flag, unflag)      |
|   ├── Sudoers: Whitelisted ONLY for /root/cka-labs/labctl navigation commands         |
|   │   └── Unauthorized sudo (e.g. `sudo ls /`) returns:                               |
|   │       "sudo: I'm sorry exam. I'm afraid I can't do that"                          |
|   ├── Shell: ~/.bashrc with kubectl aliases (k, $dr, $now) and exam guide banner      |
|   └── SSH: Transparent key-based access to remote nodes (`ssh node1`, `ssh node2`)    |
+---------------------------------------------------------------------------------------+
```

---

## 4. System Architecture & Components

```
+---------------------------------------------------------------------------------------+
|                                    CLIENT BROWSER                                     |
|                              http://<PLATFORM_HOST>:3000                              |
|                                                                                       |
|  +------------------------------------+--------------------------------------------+  |
|  | LEFT PANE: Task & Exam Navigator   | RIGHT PANE: Interactive Workspace          |  |
|  | - Question Markdown Instructions   | - xterm.js Web Terminal                    |  |
|  | - Active 2-Hour Timer              |              OR                            |  |
|  | - Task Flagging & Status Table     | - noVNC Remote Desktop (Port 6080)         |  |
|  | - One-Click Code Snippet Copy      |   (XFCE4 Desktop + Native Firefox 155)     |  |
|  +------------------------------------+--------------------------------------------+  |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
| PLATFORM ENGINE (`core/` & `web/`)                                                    |
|                                                                                       |
|  +-------------------+  +-------------------+  +-------------------+                  |
|  | web/server.py     |  | core/deployer.py  |  | core/grader.py    |                  |
|  | (FastAPI + Websock)| | (Setup & Ordering)|  | (Evaluations)    |                  |
|  +-------------------+  +-------------------+  +-------------------+                  |
|  +-------------------+  +-------------------+  +-------------------+                  |
|  | core/loader.py    |  | core/selector.py  |  | core/graderlib.py |                  |
|  | (Question Parser) |  | (Preset Resolver) |  | (Kubectl/SSH APIs)|                  |
|  +-------------------+  +-------------------+  +-------------------+                  |
+---------------------+-------------------------------------+---------------------------+
                      |                                     |
                      v                                     v
+---------------------------------------+ +---------------------------------------------+
| LOCAL CONTAINERIZED CLUSTER           | | REMOTE MULTI-NODE KUBEADM CLUSTER           |
| Context: `k3d-cka`                    | | Context: `kubeadm-vms`                      |
| Host: Local Docker daemon             | | Host: Dedicated Linux VMs (RHEL 9.8 / CRI-O)|
|                                       | |                                             |
| • k3d-cka-server-0 (Control Plane)    | | • node1: Control Plane (Kubeadm v1.36.4)    |
| • k3d-cka-agent-0  (Worker 1)         | | • node2: Worker Node   (Kubeadm v1.36.3)    |
| • k3d-cka-agent-1  (Worker 2)         | |                                             |
| Pre-warmed image cache on all nodes   | | Authentic host failure modes & upgrades     |
+---------------------------------------+ +---------------------------------------------+
```

---

## 5. Functional Requirements (FR)

### 5.1 Web Simulator & Interface
- **FR-01 (Split-Screen Layout)**: The web UI must present instructions, timers, and navigation on the left; and xterm.js terminal or noVNC desktop on the right.
- **FR-02 (Candidate Mode Enforcement)**: Accessing the web UI without admin credentials defaults to Candidate Mode (`?candidate=1`), hiding solution guides, admin controls, and preset pickers.
- **FR-03 (Anti-Cheat Fullscreen)**: When a candidate starts the exam, the UI requests full screen. Exiting full screen triggers a prominent anti-cheat security overlay.
- **FR-04 (Bidirectional Clipboard Sync)**: Code blocks in task instructions must have a one-click copy button that immediately synchronizes to both the xterm.js terminal and the TigerVNC/noVNC desktop via `autocutsel`.

### 5.2 Question & Preset Engine
- **FR-05 (111 Question Modules)**: Support 111 modular question packages across Troubleshooting (50), Workloads (15), Storage (15), Cluster Architecture (18), and Security (13).
- **FR-06 (18 Presets)**: Provide 4 Easy presets, 4 Medium presets, 4 Mix presets, and 6 Full Mock Exams (ACME, Globex, Initech, Umbrella, Wonka, Apex).
- **FR-07 (Sequential Step Lifecycle & Auto-Tear-Down)**: When navigating via `next`, `prev`, or `jump`, the engine automatically cleans up namespaces, admission webhooks, and host artifacts from prior steps before deploying the new question.
- **FR-07b (Question Cleanup Standard)**: Tasks mutating cluster-scoped or host-level resources must provide an idempotent `cleanup.sh` executed automatically upon step transition and during full resets.
- **FR-07c (Flagged Task State Preservation)**: When a candidate flags a task (`examctl flag` or UI button) and navigates away, the engine must preserve the live namespace, skip `cleanup.sh`, and defer grading. When returning to a flagged task, the engine must skip `setup.sh` to preserve candidate work in progress (`[PRESERVED FLAGGED WORK]`).
- **FR-08 (Topological Deployment Ordering)**: Breaking mutations (validating webhooks, broken CoreDNS configs, node cordons) deploy strictly after application resources.
- **FR-08b (Standard Question Framing & Anti-Giveaway Rules)**: All questions presented in the UI and candidate CLI must follow a standardized format: (1) Context directive header (`[Context: <name>]`), (2) Authentic enterprise scenario narrative without giveaway clues or artificial stage labels, (3) Explicit requirements and constraints with exact resource names and namespaces, and (4) Clear node access and privilege escalation directives where applicable.

### 5.3 Grading & Assessment
- **FR-09 (Automated Grading Engine)**: Evaluate live cluster and host state via functional assertions in `< 3 seconds`.
- **FR-10 (Partial Credit & Passing Threshold)**: Support multi-criteria scoring per task with an aggregate pass threshold of 66%.
- **FR-11 (Reachability Guard)**: If a target cluster context or SSH host is offline, graders must return an explicit `SKIPPED` state rather than false failures.

### 5.4 Candidate CLI (`examctl`)
- **FR-12 (Non-Privileged Candidate CLI)**: Install `examctl` in `/usr/local/bin/examctl` for candidates to execute `task`, `status`, `next`, `prev`, `jump`, `flag`, and `unflag`.
- **FR-13 (Sudoers Lockdown)**: The `exam` user must be restricted from arbitrary sudo commands (`sudo ls /` fails), while allowing passwordless execution strictly for whitelisted `labctl` navigation commands.

---

## 6. Strategic Requirements for Phase 2: Universal Dynamic Deployability

### 6.1 Zero Hardcoding Principles
- **FR-14 (Dynamic Environment Contract)**: All scripts, tools, and question modules must read configuration from a single `.env` file (based on `.env.example`). No hardcoded IPs, subnets, or usernames are permitted in source code.
- **FR-15 (Configurable Node Endpoints)**: Control-plane and worker node IPs or hostnames must be supplied dynamically via `${NODE_1}`, `${NODE_2}`, and `${NODE_3}`.
- **FR-16 (Dynamic Node Aliasing)**: The platform must automatically generate `/etc/hosts` or `~/.ssh/config` entries mapping `node1`, `node2`, `node3` to target IPs, enabling scripts and students to use transparent `ssh node1` commands regardless of the underlying network.
- **FR-17 (Parameterizable User Identities)**:
  - Candidate user must be parameterizable via `${EXAM_USER:-exam}`.
  - Platform administrator must be parameterizable via `${ADMIN_USER:-${SUDO_USER:-$USER}}`.
  - Remote SSH user must be parameterizable via `${SSH_USER:-root}`.
- **FR-18 (Dynamic Node Discovery in Graders)**: Graders targeting Kubernetes nodes must query the API dynamically (`kubectl get nodes -o jsonpath='...'`) rather than assuming static node names.
- **FR-19 (Interactive Onboarding CLI)**: Provide an interactive command (`./labctl configure`) to prompt new users for their environment details and auto-generate a valid `.env` file with preflight validation.

---

## 7. Non-Functional Requirements (NFR)

- **NFR-01 (Performance)**: Step transitions and question deployments must complete within 10 seconds. Scorecard evaluations must complete within 3 seconds.
- **NFR-02 (Idempotency)**: Setup and cleanup scripts must be completely idempotent and safe to re-run multiple times.
- **NFR-03 (Offline / Air-Gapped Operation)**: All container images required for questions must be pre-pulled into the local Docker/k3d cache to ensure exams run without internet access.
- **NFR-04 (Exam Realism)**: The remote Kubeadm cluster must run native CRI-O on standard Linux distributions without mock emulation.

---

## 8. Success Metrics & Roadmap

| Metric | Target | Current Status |
| :--- | :--- | :--- |
| Question Catalog Coverage | 100+ CKA questions | 111 questions completed & validated |
| Preset Availability | ≥ 5 Mock exams | 18 presets completed (6 full mocks, 12 drills) |
| Multi-Cluster Execution | Local k3d + Remote Kubeadm | Operational (k3d-cka + kubeadm-vms) |
| Candidate Security Lockdown | Restricted sudoers sandbox | Verified (`sudo: I'm sorry exam...`) |
| Dynamic Deployability | Zero hardcoded IPs / users | **Phase 2 In Progress** |
