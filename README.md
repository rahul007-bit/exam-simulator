# Kubernetes and CKA Question Engine (`labctl` & `examctl`)

`cka-labs` is an offline, multi-cluster exam simulator and 111-question curriculum engine for Certified Kubernetes Administrator (CKA) preparation and high-pressure production incident triage.

---

## Key Features

- **111 Scenario-Based Questions**: Covering troubleshooting, workloads, storage, cluster architecture, and security across 4 difficulty tiers (easy, medium, hard, crazy).
- **18 Predefined Presets**: Including 6 full 17-question CKA mock exams, 4 foundational easy drills, 4 intermediate medium drills, and 4 multi-domain mix drills.
- **PSI / Killer.sh Style Web Simulator**:
  - Split-screen browser UI: Task instructions, countdown timer, question navigator, and one-click code copy on the left; embedded xterm.js terminal or full remote desktop on the right.
  - Native TigerVNC / noVNC remote desktop with XFCE4, native Mozilla Firefox, and bidirectional clipboard synchronization.
  - Enforced candidate mode (`?candidate=1`) with full-screen anti-cheat lock overlay.
- **Dual-CLI Architecture**:
  - **`labctl` (Admin/Proctor CLI)**: Full control over question deployment, grading, solution guides, and cluster resets. Restricted to `root`.
  - **`examctl` (Candidate CLI)**: Safe student-facing interface for task navigation (`task`, `status`, `next`, `prev`, `jump`, `flag`, `unflag`) with granular sudoers lockdown.
- **Hybrid Multi-Node Topologies**:
  - Local containerized k3d cluster (`k3d-cka`: 1 server + 2 agents) for rapid namespace-scoped tasks.
  - Remote multi-node Kubeadm cluster (`kubeadm-vms`: `node1` control-plane and `node2` worker) running native **CRI-O on RHEL 9** for realistic baremetal/VM operations.
- **Universal Dynamic Deployability (Phase 2 Objective)**:
  - Zero hardcoded IPs or host usernames. Configured entirely via `.env` with dynamic discovery.

---

## Architecture & Privilege Model

```
+-------------------------------------------------------------------------------+
| Jumphost / Platform Host (Linux VM)                                           |
|                                                                               |
|  [ root User ] (Admin / Proctor)                                              |
|   └── /root/cka-labs/labctl ─── Full engine, deployment, grading, solutions   |
|                                                                               |
|  [ exam User ] (Candidate Sandbox)                                            |
|   └── /usr/local/bin/examctl ── Sudoers whitelist: task, status, next, prev   |
|   └── Host sudo restricted ──── `sudo ls /` fails with security rejection     |
|   └── ~/.bashrc ─────────────── Shortcuts: k, $dr, $now, banner guide         |
|   └── ~/.ssh/config ─────────── Passwordless node access: ssh node1, node2    |
+---------------------------------------┬---------------------------------------+
                                        │
        ┌───────────────────────────────┴───────────────────────────────┐
        ▼                                                               ▼
+───────────────────────────────+               +───────────────────────────────+
| k3d Cluster (k3d-cka)         |               | Kubeadm Cluster (kubeadm-vms) |
| - k3d-cka-server-0 (CP)       |               | - node1 (CP, v1.36.4, RHEL 9) |
| - k3d-cka-agent-0  (W1)       |               | - node2 (W1, v1.36.3, RHEL 9) |
| - k3d-cka-agent-1  (W2)       |               | Runtime: Native CRI-O v1.35.5 |
+───────────────────────────────+               +───────────────────────────────+
```

---

## Quick Start & Setup

### 1. Configure Environment Variables
Copy `.env.example` and set your node IPs and settings:
```bash
cp .env.example .env
nano .env
```
Example `.env`:
```ini
SSH_USER=root
SSH_KEY=~/.ssh/id_rsa
NODE_1=192.168.1.57
NODE_2=192.168.1.56
K3D_CLUSTER_NAME=cka
```

### 2. Bootstrap Hybrid Infrastructure
```bash
# 1. Provision Platform Host (VNC, noVNC, Web UI, Firefox, examctl)
sudo ./tools/setup-platform.sh

# 2. Bootstrap Local k3d Cluster with warmed image cache
./tools/bootstrap-k3d.sh

# 3. Bootstrap Remote Kubeadm Multi-Node Cluster
./tools/bootstrap-kubeadm.sh

# 4. Link SSH and Kubeconfigs across Platform and Nodes
./tools/link-exam-nodes.sh
```

---

## Web Simulator & Desktop Deployment

The web simulator runs on port `3000`, backed by TigerVNC (`:1` on `5901`) and noVNC (`6080`):

```bash
# Start background systemd services
sudo systemctl restart k8s-web.service      # Web Simulator (FastAPI on :3000)
sudo systemctl restart exam-vnc.service      # TigerVNC XFCE desktop (:5901)
sudo systemctl restart exam-novnc.service    # WebSockify noVNC bridge (:6080)
```

### Candidate Mode vs. Proctor Mode

By default, navigating to `http://<platform-ip>:3000/` strictly defaults to **Candidate Mode**.

| Persona | URL | Features & Restrictions |
| :--- | :--- | :--- |
| **Candidate (Default)** | `http://<ip>:3000/`<br>*(or `?candidate=1`)* | • **Locked Preset**: Starts directly on assigned mock exam<br>• **Enforced Fullscreen**: Auto-enters fullscreen on *Start Exam*<br>• **Anti-Cheat Overlay**: Triggered if candidate exits fullscreen<br>• **Clean Workspace**: Admin controls, solutions, and score diagnostics hidden |
| **Admin / Proctor** | `http://<ip>:3000/?admin=1` | • **⚙️ Preset Selector**: Choose from all 18 mock presets or custom drills<br>• **⛔ End Exam**: Force-submits active session and computes scorecard in <1s<br>• **🔄 Reset Exam**: Purges cluster namespaces, active sessions, and resets to start screen<br>• Full visibility into scoring diagnostics |

---

## Available Exam Presets (18 Presets)

All presets contain 17 tasks evaluated sequentially against `k3d-cka` and `kubeadm-vms` clusters with a standard 120-minute timer:

#### 1. Full-Length Standard Mocks
- `mock-01-acme`: ACME Corp Onboarding (Balanced standard curriculum mix)
- `mock-02-globex`: Globex Production Incidents (Troubleshooting and storage focus)
- `mock-03-initech-kubeadm`: Initech Kubeadm Operations (Cluster-arch and node management)
- `mock-04-umbrella`: Umbrella Corp Hardening (Security contexts, RBAC, network policies)
- `mock-05-wonka`: Wonka Edge Cases & Chaos (Advanced scheduling, webhooks, cgroups)
- `mock-06-apex`: Apex Final Mock (Comprehensive dress rehearsal)

#### 2. All-Easy Presets (17 Easy Questions)
- `easy-01-foundation`: Core Kubernetes fundamentals across all domains
- `easy-02-essentials`: Core essentials practice run
- `easy-03-confidence`: Confidence builder run
- `easy-04-speedrun`: Timed 60-minute speed drill

#### 3. All-Medium Presets (17 Medium Questions)
- `medium-01-cluster-storage`: Cluster architecture, networking, and persistent storage
- `medium-02-security-workloads`: RBAC, security contexts, and workload management
- `medium-03-troubleshooting`: Cluster and workload troubleshooting deep dive
- `medium-04-advanced-mix`: Mixed domains covering advanced medium scenarios

#### 4. Easy + Medium Mix Presets (4-5 Easy + 12-13 Medium)
- `mix-01-networking-cluster`: Networking, ingress, services, and cluster operations
- `mix-02-storage-security`: Volumes, PVCs, StorageClasses, and RBAC
- `mix-03-workloads-scheduling`: Deployments, DaemonSets, affinities, and probes
- `mix-04-troubleshooting-ops`: Day-2 operations, rollout debugging, and node taints

---

## Admin CLI Usage (`labctl`)

Run as `root` from `/root/cka-labs`:

```bash
# Interactive terminal wizard
./labctl

# Deploy specific question or preset
./labctl deploy TR-001
./labctl exam mock-01-acme

# Run functional grading on active session
./labctl grade

# View reference solution
./labctl solution TR-001

# Reset and purge active exam namespaces
./labctl reset
```

---

## Candidate CLI Usage (`examctl`)

Run as user `exam` from any directory:

```bash
# View current question requirements
examctl task

# View live exam progress table
examctl status

# Advance to next task (automatically cleans prior task and deploys next)
examctl next

# Return to previous task
examctl prev

# Jump directly to task N
examctl jump 5

# Flag or unflag task for review
examctl flag 3
examctl unflag 3
```

---

## Candidate Shell Environment & Shortcuts

| Shortcut | Target / Expansion | Purpose |
| :--- | :--- | :--- |
| `k` | `kubectl` | CLI alias |
| `$dr` | `--dry-run=client -o yaml` | Generate manifest templates |
| `$now` | `--force --grace-period=0` | Immediate pod deletion |
| `k config get-contexts` | Lists `k3d-cka` and `kubeadm-vms` | View available clusters |
| `ssh node1` | `${SSH_USER}@${NODE_1}` | Control-plane node access |
| `ssh node2` | `${SSH_USER}@${NODE_2}` | Worker node access |

---

## Documentation Links

- [HANDOVER.md](file:///home/amazinrahul/Projects/4-sep-test/cka-labs/HANDOVER.md): Comprehensive system handover, runbooks, and Phase 2 dynamic architecture.
- [PRD.md](file:///home/amazinrahul/Projects/4-sep-test/cka-labs/PRD.md): Product Requirements Document (v2.0.0).
- [PLATFORM_SETUP.md](file:///home/amazinrahul/Projects/4-sep-test/cka-labs/PLATFORM_SETUP.md): Detailed host provisioning and cluster bootstrap guide.
- [STATUS.md](file:///home/amazinrahul/Projects/4-sep-test/cka-labs/STATUS.md): Current engineering status and milestones.

---

## License

MIT
