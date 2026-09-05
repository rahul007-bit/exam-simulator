# Project Status: CKA-Labs Platform & Question Engine

**Snapshot Date:** September 5, 2026  
**Current Milestone:** Phase 1 Complete — Phase 2 (Universal Dynamic Deployability) Active  
**Engine Version:** v2.0.0  

---

## 1. Executive Summary

`cka-labs` has achieved full operational readiness across its core engine, 111-question curriculum, web simulator, remote desktop subsystem, and hybrid multi-cluster infrastructure.

All 111 question modules across 5 CKA domains and 4 difficulty tiers are implemented with idempotent setup scripts, raw manifests, and live functional Python graders. The hybrid infrastructure is operational with local `k3d-cka` (1 server + 2 agents) and remote live Kubeadm nodes (`node1` control-plane and `node2` worker running native **CRI-O on RHEL 9**). The web simulator delivers a split-screen experience with xterm.js terminal and native TigerVNC/noVNC remote desktop with bidirectional clipboard synchronization.

With Phase 1 objectives fully validated, the project is officially embarking on **Phase 2: Universal Dynamic Deployability**, eliminating all hardcoded IPs, subnets, and hostnames to ensure seamless deployment on any laptop, homelab, or cloud environment.

---

## 2. Completed Milestones (Phase 1)

### 2.1 Question Catalog & Presets
- **111 Standardized Question Packages**:
  - Troubleshooting: 50 scenarios (CrashLoopBackOff, CoreDNS syntax, ingress routing, webhook deadlocks, cgroup driver mismatches, etcd WAL disk space).
  - Workloads & Scheduling: 15 scenarios (sidecars, initContainers, rolling updates, HPA, affinities, topology spread).
  - Storage: 15 scenarios (local PV/PVC binding, dynamic StorageClasses with Retain, volume expansions, subpaths).
  - Cluster Architecture & Networking: 18 scenarios (kubeadm CP & worker upgrades, etcd backup/restore, static pod repair, cert renewal).
  - Security & Hardening: 13 scenarios (RBAC ServiceAccounts, ClusterRoles, security contexts non-root/readonly, TLS secrets).
- **18 Presets Configured**:
  - 6 Full 17-question CKA mock exams (`mock-01` to `mock-06`).
  - 4 Foundational Easy drills (`easy-01` to `easy-04`).
  - 4 Intermediate Medium drills (`medium-01` to `medium-04`).
  - 4 Multi-Domain Mix drills (`mix-01` to `mix-04`).

### 2.2 Web Simulator & Desktop Subsystem
- **Split-Screen Web Interface (Port 3000)**:
  - Left pane: Markdown question instructions, countdown timer, question progress table, and one-click copyable code snippets.
  - Right pane: Embedded xterm.js terminal or full remote desktop toggle.
- **TigerVNC & noVNC Stack**:
  - TigerVNC server running on display `:1` (port `5901`) with lightweight XFCE4 desktop.
  - WebSockify noVNC bridge running on port `6080`.
  - Native Mozilla Firefox (installed via official Mozilla APT repository to avoid Ubuntu Snap confinement issues).
- **Bidirectional Clipboard Sync**:
  - Full clipboard integration via `autocutsel` (`CLIPBOARD` and `PRIMARY` selections) and `vncconfig -nowin`.
  - Copying code snippets from task instructions automatically syncs into the candidate's terminal and VNC clipboard.
- **Candidate Persona & Anti-Cheat**:
  - Default URL (`http://<ip>:3000/`) automatically locks into Candidate Mode (`?candidate=1`).
  - Fullscreen mode enforced on exam start; exiting fullscreen triggers an anti-cheat security overlay.
  - Admin/Proctor controls (`?admin=1`) enable preset switching, instant exam termination, and cluster resets.

### 2.3 Access Security & Candidate Privilege Separation
- **Host User Separation**:
  - Proctor / Admin: `root` user with full access in `/root/cka-labs`.
  - Candidate: `exam` user in `/home/exam`.
- **Candidate Sudo Lockdown**:
  - Removed `exam` from `sudo` group.
  - Removed unrestricted sudoers rules.
  - Configured granular rule in `/etc/sudoers.d/examctl` whitelisting only `labctl tasks`, `status`, `next`, `prev`, `jump`, `flag`, and `unflag`.
  - Attempting arbitrary sudo (e.g. `sudo ls /`) correctly triggers security rejection: `sudo: I'm sorry exam. I'm afraid I can't do that`.
- **Candidate CLI (`examctl`)**:
  - Installed in `/usr/local/bin/examctl`.
  - Enables safe task navigation without solution leaks or unearned grading hints.

### 2.4 Hybrid Infrastructure & Pure Kubeadm Cluster
- **Local k3d Cluster (`k3d-cka`)**:
  - 1 server + 2 agents provisioned via `tools/bootstrap-k3d.sh`.
  - Pre-warmed image cache for all 9 application images and 3 system images to enable instant offline execution.
- **Remote Kubeadm Multi-Node Cluster (`kubeadm-vms`)**:
  - Running on dedicated Linux VMs (RHEL 9.8).
  - Native **CRI-O** container runtime (`cri-o://1.35.5`)—zero KIND or k3d wrappers on remote nodes.
  - Flannel CNI deployed.
  - Multi-version topology: Control-plane `node1` upgraded to **`v1.36.4`** while worker `node2` remains at **`v1.36.3`**, creating the authentic state needed for worker node upgrade drills (`CA-004-kubeadm-worker-upgrade`).
  - Automated deployment and reset scripted in `tools/bootstrap-kubeadm.sh`.
  - Key distribution and transparent SSH aliases (`ssh node1`, `ssh node2`) configured via `tools/link-exam-nodes.sh`.

### 2.5 Tooling & Codebase Hygiene
- Removed 8 obsolete/redundant generator and seeding scripts from `tools/`.
- Deleted obsolete `PLAN.md` and temporary test set markdown files.
- Upgraded `PRD.md` to v2.0.0.
- Published comprehensive master `HANDOVER.md`.

---

## 3. Active Phase 2 Objective: Universal Dynamic Deployability

### 3.1 Problem Statement
Certain setup scripts, tools, and question modules contain legacy fallback IP addresses (e.g. `192.168.1.x`, `192.168.50.x`) and assume specific host usernames (`rahul`). This introduces friction when deploying on arbitrary laptops, cloud VMs, Vagrant setups, or homelabs.

### 3.2 Phase 2 Target Deliverables
1. **Dynamic Environment Source (`.env`)**: Ensure all scripts, tools, and questions strictly read environment parameters from `.env` (using `.env.example` as the canonical schema).
2. **Dynamic Node Discovery in Graders**: Update host-targeting graders to discover node names via the live Kubernetes API (`kubectl get nodes`) rather than assuming static node names.
3. **Interactive Onboarding CLI (`./labctl configure`)**: Build a guided CLI command to prompt new users for their network topology, validate SSH keys, and auto-generate `.env`.
4. **Automated End-to-End Test Suite**: Continuous integration pipeline verifying clean deployment and grading across disposable test clusters.

---

## 4. Operational Health & Service Status

| Service | Port / Target | Status | Notes |
| :--- | :--- | :--- | :--- |
| `k8s-web.service` | TCP `3000` | Active (running) | FastAPI Web Simulator |
| `exam-vnc.service` | TCP `5901` | Active (running) | TigerVNC XFCE desktop (:1) |
| `exam-novnc.service` | TCP `6080` | Active (running) | WebSockify noVNC proxy |
| `k3d-cka` | Context | Active (3 nodes Ready) | Local Docker k3d cluster |
| `kubeadm-vms` | Context | Active (2 nodes Ready) | Remote CRI-O Kubeadm cluster |
| `examctl` | `/usr/local/bin/examctl` | Verified | Granular sudoers navigation |
