# CKA-LABS PROJECT HANDOVER & OPERATIONAL RUNBOOK

**Document Version:** 2.0.0  
**Status:** Phase 1 Complete — Transitioning to Phase 2 (Universal Dynamic Deployment)  
**Author:** AI Pair Programming & Infrastructure Engineering Team  
**Date:** September 5, 2026  

---

## 1. Executive Summary

**CKA-Labs** is an offline, multi-cluster Kubernetes training engine, self-grading exam simulator, and 111-question interactive curriculum platform built to replicate the exact environment, difficulty, and pressure of the Linux Foundation Certified Kubernetes Administrator (CKA) exam and production SRE incident triage.

Over the initial phase, the project evolved from a command-line question runner into a full-scale web simulator (PSI/Killer.sh style) featuring:
- A split-screen browser interface with embedded xterm.js terminal and native TigerVNC/noVNC remote desktop.
- Complete separation of privileges between candidate (`exam` user) and proctor/administrator (`root` user).
- A hybrid multi-cluster architecture combining disposable local `k3d` nodes with a live, pure Kubeadm multi-node cluster on RHEL 9 with CRI-O.
- 111 standardized, modular question packages and 18 structured mock presets.

This document serves as the master engineering handover, detailing architecture, cluster topologies, security policies, operations, known gotchas, and the primary objective for the next phase: **Universal Dynamic Deployability (Zero Hardcoded Values)**.

---

## 2. System Architecture & Topology

### 2.1 High-Level Architecture

```
                                  +-------------------------------------------------------------+
                                  |                     CANDIDATE BROWSER                       |
                                  |                   http://<PLATFORM_IP>:3000                 |
                                  +------------------------------+------------------------------+
                                                                 |
                                       +-------------------------+-------------------------+
                                       |                                                   |
                                       v                                                   v
                         +-----------------------------+                     +-----------------------------+
                         |    Split-Screen Left Pane   |                     |   Split-Screen Right Pane   |
                         |  - Active Task Instructions |                     |  - xterm.js Web Terminal    |
                         |  - Exam Timer & Scorecard   |                     |            OR               |
                         |  - One-Click Code Copy      |                     |  - noVNC Desktop (Port 6080)|
                         +-----------------------------+                     +-----------------------------+
                                       |                                                   |
+-----------------------------------------------------------------------------------------------------------------------+
| PLATFORM HOST (Linux VM / Jumphost)                                                                                   |
|                                                                                                                       |
|  [ root ] Admin / Proctor                                  [ exam ] Candidate Sandbox                                |
|   ├── /root/cka-labs/labctl (Engine Core)                   ├── /usr/local/bin/examctl (Restricted Navigation CLI)    |
|   ├── Systemd Services:                                     ├── Sudoers Lockdown: Only labctl tasks/status/nav       |
|   │    ├─ k8s-web.service      (FastAPI :3000)              ├── ~/.bashrc: Shortcuts (k, $dr, $now), auto-banner      |
|   │    ├─ exam-vnc.service     (TigerVNC :1 on :5901)       └── ~/.ssh/config: Transparent access to node1, node2     |
|   │    └─ exam-novnc.service   (WebSockets :6080)                                                                     |
|   └── Native Firefox 155 (Mozilla APT repository)                                                                     |
+-------------------------------------------------+---------------------------------------------------------------------+
                                                  |
                         +------------------------+------------------------+
                         |                                                 |
                         v                                                 v
+-------------------------------------------------+     +---------------------------------------------------------------+
| LOCAL CONTAINERIZED CLUSTER                     |     | REMOTE MULTI-NODE KUBEADM CLUSTER                             |
| Context: `k3d-cka`                              |     | Context: `kubeadm-vms`                                        |
| Engine: Docker + k3d / k3s                      |     | OS / Runtime: RHEL 9.8 / CRI-O (cri-o://1.35.5)              |
|                                                 |     |                                                               |
| • k3d-cka-server-0 (Control Plane)              |     | • node1 (Control-Plane, Kubeadm v1.36.4, IP: ${NODE_1})       |
| • k3d-cka-agent-0  (Worker Node 1)              |     | • node2 (Worker Node, Kubeadm v1.36.3, IP: ${NODE_2})         |
| • k3d-cka-agent-1  (Worker Node 2)              |     |                                                               |
| Used for: 85%+ of namespace & workload drills   |     | Used for: Host drills (kubeadm upgrade, etcd, static pods,    |
|                                                 |     |           systemd kubelet troubleshooting, cert renewal)      |
+-------------------------------------------------+     +---------------------------------------------------------------+
```

### 2.2 Active Cluster Topologies

| Cluster Context | Infrastructure Type | Topology | Runtime / OS | Primary Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **`k3d-cka`** | Local Docker containers | 1 Server + 2 Agents | containerd (k3s v1.30.2) | Fast, isolated namespace tasks (deployments, ingresses, storage, network policies). Reset in seconds. |
| **`kubeadm-vms`** | Dedicated RHEL 9 VMs | 1 CP (`node1`) + 1 Worker (`node2`) | CRI-O v1.35.5 on Linux 5.14 | Baremetal/VM tasks: control plane upgrade, worker upgrade, etcd snapshot backup/restore, kubelet systemd repair, static pod fixes. |

> [!IMPORTANT]
> **Pure Kubeadm Guarantee**: `node1` and `node2` run native **CRI-O** container runtime and upstream **kubeadm**. Zero KIND or k3d wrappers are used on these nodes to ensure 100% CKA exam realism.

---

## 3. Access, Security & Privilege Model

### 3.1 Proctor vs. Candidate Separation

| Feature | Proctor / Admin (`root`) | Candidate (`exam`) |
| :--- | :--- | :--- |
| **Working Directory** | `/root/cka-labs` (`chmod 700`) | `/home/exam` |
| **CLI Tooling** | `labctl` (full control: grading, seeding, resetting, solutions) | `examctl` (candidate interface: next, prev, jump, task, status, flag) |
| **Host Sudo Rights** | `ALL=(ALL) NOPASSWD:ALL` | **Blocked**: `sudo ls /` fails with `sudo: I'm sorry exam. I'm afraid I can't do that` |
| **Sudo Whitelist** | Unrestricted | Strictly whitelisted in `/etc/sudoers.d/examctl` for `/root/cka-labs/labctl` commands |
| **Remote Node Access** | Passwordless root SSH to `node1` & `node2` | Passwordless root SSH to `node1` & `node2` via pre-seeded keys |
| **Web Interface** | Access to all presets, grading modals, and admin actions | Enforced Candidate Mode (`?candidate=1`), anti-cheat overlay, locked preset |

### 3.2 Candidate CLI (`examctl`) Specification

Candidates interact with the exam exclusively via `/usr/local/bin/examctl`:
- `examctl task`: Displays current active question description, context, and requirements.
- `examctl status`: Displays the live ASCII exam progress table, showing points, current step, and flagged questions.
- `examctl next`: Completes current step and automatically deploys the subsequent task.
- `examctl prev`: Returns to the previous question.
- `examctl jump <N>`: Jumps directly to question number `N`.
- `examctl flag [N]` / `examctl unflag [N]`: Marks or unmarks questions for review.

---

## 4. Web Simulator & Desktop Subsystem

The web interface is served by **FastAPI** (`web/server.py`) and backed by modern Vanilla JavaScript (`web/static/js/app.js`):

1. **Split-Screen Interface**:
   - Left side: Task instructions, timer, question navigator, and copyable commands.
   - Right side: Embedded xterm.js terminal OR noVNC remote desktop.
2. **TigerVNC & noVNC Remote Desktop**:
   - TigerVNC server runs display `:1` on port `5901` (`exam-vnc.service`).
   - WebSockify bridges VNC traffic to WebSocket on port `6080` (`exam-novnc.service`).
   - Desktop environment is **XFCE4** configured with Mozilla Firefox, terminal shortcuts, and an unslop desktop theme.
3. **Clipboard Synchronization**:
   - Integrated via `autocutsel` (monitoring both `CLIPBOARD` and `PRIMARY` selections) and `vncconfig -nowin`.
   - Clicking code snippets in the Web UI instantly copies them to the system clipboard and syncs directly into the VNC desktop session and xterm terminal.
4. **Candidate Mode & Anti-Cheat**:
   - Accessing `http://<IP>:3000/` automatically applies `?candidate=1`.
   - Starts directly into the assigned exam preset.
   - Triggers fullscreen mode on start; leaving fullscreen displays an anti-cheat lock overlay.

---

## 5. Question Catalog & Presets

### 5.1 Catalog Breakdown (111 Questions)

| Domain | Total Questions | Easy | Medium | Hard | Crazy / Chaos |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. Troubleshooting (`questions/troubleshooting/`)** | 50 | 10 | 20 | 12 | 8 |
| **2. Workloads & Scheduling (`questions/workloads/`)** | 15 | 4 | 7 | 3 | 1 |
| **3. Storage (`questions/storage/`)** | 15 | 3 | 7 | 3 | 2 |
| **4. Cluster Architecture & Networking (`questions/cluster-arch/`)** | 18 | 4 | 8 | 4 | 2 |
| **5. Security & Hardening (`questions/security/`)** | 13 | 3 | 5 | 3 | 2 |
| **Total** | **111** | **24** | **47** | **25** | **15** |

### 5.2 Preset Mock Exams (18 Presets in `presets/`)

1. **Foundational & Essentials**: `easy-01-foundation.yaml`, `easy-02-essentials.yaml`, `easy-03-confidence.yaml`, `easy-04-speedrun.yaml`.
2. **Intermediate Skill Drills**: `medium-01-cluster-storage.yaml`, `medium-02-security-workloads.yaml`, `medium-03-troubleshooting.yaml`, `medium-04-advanced-mix.yaml`.
3. **Domain Deep-Dives**: `mix-01-networking-cluster.yaml`, `mix-02-storage-security.yaml`, `mix-03-workloads-scheduling.yaml`, `mix-04-troubleshooting-ops.yaml`.
4. **Full 17-Question CKA Mock Simulations**:
   - `mock-01-acme.yaml`: ACME Corp Onboarding (Balanced CKA mix).
   - `mock-02-globex.yaml`: Globex Systems Outage (Heavy troubleshooting focus).
   - `mock-03-initech-kubeadm.yaml`: Initech Migration (Heavy Kubeadm & Host cluster focus).
   - `mock-04-umbrella.yaml`: Umbrella Corp Chaos Day (Complex multi-component failures).
   - `mock-05-wonka.yaml`: Wonka Final Mock (Advanced scheduling and security).
   - `mock-06-apex.yaml`: Apex Systems Infrastructure (Production-grade realistic challenge).

### 5.3 Standard Question Framing Specification (Candidate UI Contract)

To match the exact look, feel, and cognitive challenge of the real Linux Foundation CKA exam and production SRE drills, every question's `description` field in `question.yaml` must adhere to the following **Question Framing Anatomy**:

```markdown
[Context: <target_context>]

Set configuration context:
$ kubectl config use-context <target_context>

<Realistic Incident / Enterprise Context>

Task Requirements:
1. <Objective 1 with exact resource type and name>
2. <Objective 2 with exact namespace, ports, image tags, or mount paths>
3. <Operational constraint or preservation rule>

Node Access (if applicable):
$ ssh <node-alias>
$ sudo -i (if root privileges are required)
Return to the base terminal upon completion.
```

#### Core Framing Principles & Anti-Giveaway Rules:
1. **Context Directive Header**:
   - Every single task must begin with the active cluster context switch command:
     `[Context: k3d-cka]` or `[Context: kubeadm-vms]`.
   - Candidates must be conditioned to verify their context before running commands.
2. **Authentic Scenario Narrative (Zero Clue Leaks)**:
   - Frame problems as enterprise production issues or architecture requests (e.g. *"The checkout service is reporting downtime during canary rollout"* or *"An internal security audit flagged unprivileged containers running as root"*).
   - **Anti-Giveaway Rule (Unslop Framing)**: Never state the root cause or giveaway fix in the prompt.
     - ❌ *Incorrect (Giveaway)*: "Fix the typo in line 14 of the configmap where database_url has a typo."
     - ✅ *Correct (Authentic)*: "Pod `order-api` in namespace `sales` is stuck in `CreateContainerConfigError`. Investigate pod events and dependent configurations, resolve the issue, and ensure the pod reaches `1/1 Running`."
3. **Precise Deliverables & Explicit Constraints**:
   - Always specify exact resource names (e.g. Pod `web-app`, Deployment `api-gateway`, Secret `db-tls`).
   - Always state the target namespace explicitly (e.g. `namespace: payments`), or explicitly declare the `default` namespace.
   - Define strict boundaries: e.g. *"Do not delete or recreate the existing PersistentVolume"*, *"Ensure changes persist across node reboots"*, *"Do not modify other containers in the pod"*.
4. **Host & Node Directives**:
   - When a task requires node access (e.g. kubeadm upgrades, static pods, etcd snapshots, cgroup troubleshooting), state the target node clearly (`ssh node1` or `ssh node2`).
   - Explicitly state privilege requirements: *"Elevate to root via `sudo -i` if required"*.
   - Include a clear instruction to return to the base jumphost terminal upon completion.

### 5.4 Question Package Engineering Standards

Every question resides in `questions/<domain>/<question-id>/` with 5 mandatory components:

```
questions/<domain>/<question-id>/
├── question.yaml    # Schema metadata, points, context, tags, framed description
├── setup.sh         # Idempotent defect injection & setup (<10s runtime)
├── manifests/       # Clean Kubernetes YAML definitions
├── grader.py        # Functional Python 3 assertions (GradeResult output)
└── solution.md      # Diagnostic guide, root cause, command-by-command fix
```

#### Engineering Rules for Question Assets:
- **`setup.sh`**:
  - Must be fully idempotent (safe to run repeatedly without breaking).
  - Must create its dedicated namespace if namespace-scoped.
  - Must dynamically resolve node IPs/aliases (`${NODE_1}`, `node1`) instead of hardcoding IP addresses.
  - Must complete in under 10 seconds and return exit code `0`.
- **`grader.py`**:
  - Must implement `grade(ctx: KubernetesContext) -> GradeResult`.
  - Must be **non-destructive**: graders inspect and assert, but never mutate or fix cluster resources.
  - Must perform a reachability probe first (`ctx.is_reachable()` or SSH ping), returning `SKIPPED` if infrastructure is offline.
  - Must support partial credit where multiple sub-tasks are evaluated.
- **`solution.md`**:
  - Must contain: (1) Diagnosis (`kubectl describe`, `kubectl logs`, `journalctl`), (2) Root Cause explanation, (3) Exact fix commands, and (4) Verification command.

### 5.5 Step Teardown & Question Cleanup Architecture

To ensure questions do not interfere with subsequent tasks (port collisions, resource exhaustion, stuck webhooks), the engine implements a multi-tier teardown model:

1. **Automated Namespace Purging**:
   - When advancing via `examctl next`, `prev`, or `jump`, the engine identifies the leaving task's namespace.
   - If the task is **not flagged**, the engine issues an asynchronous namespace deletion:
     `kubectl --context <ctx> delete namespace <ns> --wait=false --ignore-not-found`
   - Using asynchronous non-blocking deletion ensures step transitions occur instantly (< 1 second) without waiting for pod termination grace periods.
2. **Custom Question Teardown (`cleanup.sh`)**:
   - For tasks that touch cluster-scoped or host-level resources (e.g. etcd restore paths, static pod manifests, node taints, storage classes), a `cleanup.sh` script is placed in the question package:
     `questions/<domain>/<question-id>/cleanup.sh`
   - The deployer executes `cleanup.sh` automatically when leaving the unflagged task and during full exam resets (`./labctl reset`).
   - `cleanup.sh` must be idempotent and safe to run even if the target resources were never created.
3. **CoreDNS & Node Cordon Cleanup Guards**:
   - Built into `core/deployer.py`:
     - When leaving CoreDNS tasks (`CA-010`, `TR-005`), custom ConfigMaps (`coredns-custom`) are automatically purged from `kube-system`.
     - When leaving node taint/drain tasks (`TR-008`, `TR-014`, `CA-004`, `CA-005`), worker nodes on both `k3d-cka` and `kubeadm-vms` are automatically uncordoned to prevent scheduling deadlocks on future tasks.

### 5.6 Flagged Task Lifecycle & Work Preservation Engine

In high-stakes exams, candidates frequently skip difficult questions and revisit them before final submission. The engine features an intelligent work preservation engine for flagged tasks:

1. **Flagging a Question**:
   - Via CLI: `examctl flag` (flags active task) or `examctl flag <N>` (flags task number N).
   - Via Web UI: Clicking the **🚩 Flag Question** button in the top action bar.
   - Status indicators: Displays `[🚩 FLAGGED FOR REVIEW]` in the terminal banner, `FLAGGED` in the status table, and a persistent red flag badge on the question pill in the web navigator.
2. **Preservation of Candidate Work (Skip Teardown)**:
   - When a candidate navigates away from a flagged question to another task:
     - **Namespace deletion is bypassed**: The candidate's namespace, modified deployments, and PVCs remain active in the cluster.
     - **Custom `cleanup.sh` is bypassed**: Remote VM host edits and cluster objects are preserved.
     - **Grading is deferred**: The task is marked as `"Flagged for review (Pending submission)"` rather than being marked as a failure.
3. **Redeployment Bypass on Return**:
   - When the candidate later navigates back to the flagged task (`examctl jump <N>` or clicking the task card in Web UI):
     - The deployer detects that the task is in `session.flagged` and prints `[PRESERVED FLAGGED WORK]`.
     - **`setup.sh` is NOT re-run**: The engine intentionally skips defect re-injection so the candidate's partial fixes, created resources, and manifest files are not overwritten.
     - The candidate can inspect their previous work and continue troubleshooting uninterrupted.
4. **Final Exam Submission & Warning**:
   - Flagged questions are fully eligible for points. During final exam submission (`labctl grade --all` or Web UI "Submit Exam"), all tasks—including flagged ones—are evaluated against their live cluster state.
   - Before submission, the Web UI and CLI alert the student if flagged tasks remain, prompting confirmation before finalizing the scorecard.

---

## 6. Operational Runbooks

### 6.1 Service Management on Platform Host

Check status of all simulator services:
```bash
systemctl status k8s-web.service exam-vnc.service exam-novnc.service --no-pager
```

Restart simulator stack:
```bash
sudo systemctl restart k8s-web.service exam-vnc.service exam-novnc.service
```

View live simulator logs:
```bash
journalctl -u k8s-web.service -f
```

### 6.2 Bootstrapping Infrastructure

1. **Bootstrap Local k3d Cluster**:
   ```bash
   cd /root/cka-labs
   ./tools/bootstrap-k3d.sh
   ```
   *Creates 1 server + 2 agents and pre-pulls all question images into the local container cache.*

2. **Bootstrap Remote Kubeadm Multi-Node Cluster**:
   ```bash
   cd /root/cka-labs
   ./tools/bootstrap-kubeadm.sh
   ```
   *Resets `node1` and `node2`, initializes Kubeadm, deploys Flannel CNI, joins `node2`, and upgrades `node1` to v1.36.4 while keeping `node2` at v1.36.3 for worker upgrade exercises.*

3. **Link Platform Host to Kubeadm Nodes**:
   ```bash
   cd /root/cka-labs
   ./tools/link-exam-nodes.sh
   ```
   *Generates SSH keys, propagates authorization across all nodes, configures `~/.ssh/config` aliases (`ssh node1`, `ssh node2`), fetches `admin.conf`, and configures the candidate `kubeadm-vms` context.*

---

## 7. Known Issues & Troubleshooting Gotchas

1. **System Clock Skew on Virtual Machines**:
   - **Symptom**: `apt` or `dnf` fails with `OCSP response has expired` or `InRelease is not valid yet`.
   - **Root Cause**: Virtual machines restoring from snapshots or idling can have drifted system clocks.
   - **Remediation**: Run clock synchronization across all nodes:
     ```bash
     timedatectl set-ntp true
     # Or force manual sync:
     date -s "$(curl -sI https://google.com | grep -i '^Date:' | cut -d' ' -f2-)"
     ```

2. **Mozilla APT Signing Key Format**:
   - **Symptom**: Firefox installation fails on Ubuntu 24.04/26.04 with `unsupported filetype` error.
   - **Root Cause**: Mozilla's signing key is already ASCII armored; piping through `gpg --dearmor` into a `.asc` file corrupts the key format.
   - **Remediation**: In [tools/setup-platform.sh](file:///home/amazinrahul/Projects/4-sep-test/cka-labs/tools/setup-platform.sh), download directly into `/etc/apt/keyrings/packages.mozilla.org.asc`.

3. **TigerVNC Session GID Inheritance**:
   - **Symptom**: User `exam` can execute `sudo` commands even after being removed from the `sudo` group.
   - **Root Cause**: Active desktop sessions inherit supplementary groups at process start time.
   - **Remediation**: Restart `exam-vnc.service` after modifying group memberships so the running session reloads credentials.

---

## 8. Strategic Objective for Phase 2: Universal Dynamic Deployability

### 8.1 The Problem
Historically, setup scripts and some question files defaulted to specific static IP subnets (e.g., `192.168.1.x`, `192.168.50.x`) and assumed specific host usernames (`rahul`). This requires manual editing when deploying on new hardware, cloud environments (AWS/GCP), Vagrant, or different homelab networks.

### 8.2 Phase 2 Architecture Mandate: Zero Hardcoding

Every script, tool, question setup, and grader must adhere to the following principles:

1. **Environment-Driven Configuration (`.env`)**:
   - All host IPs, SSH credentials, cluster names, and usernames must be defined in `.env` (using [.env.example](file:///home/amazinrahul/Projects/4-sep-test/cka-labs/.env.example) as the contract).
   - Scripts must source `.env` automatically:
     ```bash
     SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
     [ -f "${SCRIPT_DIR}/../.env" ] && source "${SCRIPT_DIR}/../.env"
     ```
2. **Zero Hardcoded IPs**:
   - Use dynamic environment variables: `${NODE_1}`, `${NODE_2}`, `${NODE_3}`.
   - Fall back to standard hostname aliases (`node1`, `node2`) configured in `/etc/hosts` or `~/.ssh/config`.
3. **Zero Hardcoded Usernames**:
   - Use `${EXAM_USER:-exam}` for candidate account operations.
   - Use `${ADMIN_USER:-${SUDO_USER:-$USER}}` for host administrative privileges.
   - Use `${SSH_USER:-root}` for remote node management.
4. **Dynamic Node Discovery in Graders**:
   - Graders and questions must query the live Kubernetes API (`kubectl get nodes -o jsonpath='...'`) rather than assuming static node names or IP addresses.
5. **Interactive Onboarding Wizard**:
   - Build `./labctl configure` to guide new users through setting up their environment variables, validating SSH connectivity, and testing cluster contexts automatically.

---

## 9. Next Phase Action Items & Milestones

- [ ] **Milestone 1**: Complete scan of all 111 `questions/*/setup.sh` and `grader.py` files to replace legacy IP fallbacks with dynamic `${NODE_1}` / `node1` aliases.
- [ ] **Milestone 2**: Build `./labctl configure` interactive CLI wizard to automate `.env` generation and cluster preflight checks.
- [ ] **Milestone 3**: Implement candidate session recording (asciinema terminal recording + event logging) for post-exam review.
- [ ] **Milestone 4**: Containerized student sandboxing option (running the platform inside an isolated Docker container with DinD for zero-friction laptop deployment).
