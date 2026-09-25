# CKA Concurrent Multi-Node & MicroVM Architecture Plan

**Document Version:** 2.0.0  
**Date:** September 6, 2026  
**Status:** Approved Architectural Blueprint  

---

## 1. Executive Summary

This architecture establishes an automated, high-density, multi-tenant examination engine for CKA testing. Every candidate session receives:
1. **An isolated XFCE / noVNC Desktop Container** (`cka-desktop-{sid}`) with full GUI and browser.
2. **An isolated Ephemeral k3d Cluster** (`k3d-cka-{sid}`) for standard Kubernetes API tasks.
3. **An isolated Multi-Node Kubeadm MicroVM Sandbox** (`node1-{sid}`, `node2-{sid}`, `node3-{sid}`) for bare-metal OS, etcd, systemd, and node lifecycle drills.

The architecture is **location-agnostic**:
- **Distributed Mode**: Distributes desktop containers, k3d clusters, and microVMs across a cluster of compute nodes (`10.8.0.15`, `192.168.50.169`, `192.168.50.188`, `192.168.50.170`).
- **Single Huge Node Mode**: Runs the identical stack on a single high-spec server (e.g. 64GB+ RAM) on `localhost` without code modifications.

---

## 2. Server Fleet & Roles

| Host IP | Role | OS | Spec | Allocated Function |
| :--- | :--- | :--- | :--- | :--- |
| **`10.8.0.15`** | **Management Node** | Ubuntu 26.04 | 8 GB RAM, 49 GB SSD | Web Platform (`k8s-web`), Redis State Bus, WebSocket Multiplexer, Proxy Gateway. |
| **`192.168.50.169`** | **Compute Node 1** | RHEL 9.8 | 15 GB RAM, 49 GB SSD | Ephemeral k3d clusters, candidate desktop containers, and Kubeadm `node1` microVMs. |
| **`192.168.50.188`** | **Compute Node 2** | RHEL 10.2 | 15 GB RAM, 49 GB SSD | Ephemeral k3d clusters, candidate desktop containers, and Kubeadm `node2` microVMs. |
| **`192.168.50.170`** | **Compute Node 3** | RHEL 9.8 | 15 GB RAM, 49 GB SSD | Ephemeral k3d clusters, candidate desktop containers, and Kubeadm `node3` microVMs. |

Total fleet capacity: **53 GB RAM, 196 GB Storage**.

---

## 3. Strict Resource Quotas (Zero Host Exhaustion Guarantee)

Every process, container, and microVM is subject to strict, non-negotiable cgroup and hypervisor resource limits:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        RESOURCE QUOTAS PER SESSION                     │
├────────────────────────────────┬──────────────┬──────────┬─────────────┤
│ Component                      │ Memory Limit │ CPU Cap  │ PID Limit   │
├────────────────────────────────┼──────────────┼──────────┼─────────────┤
│ Desktop (`cka-desktop-{sid}`)  │ 1024 MB      │ 1.5 CPUs │ 500 tasks   │
│ k3d Server (`server-0`)        │ 1024 MB      │ 1.0 CPU  │ 1000 tasks  │
│ k3d Agent (`agent-0`)          │ 768 MB       │ 1.0 CPU  │ 1000 tasks  │
│ Kubeadm MicroVM (`node1`)      │ 2048 MB      │ 2.0 CPUs │ 1500 tasks  │
│ Kubeadm MicroVM (`node2`)      │ 1536 MB      │ 1.5 CPUs │ 1500 tasks  │
│ Kubeadm MicroVM (`node3`)      │ 1536 MB      │ 1.5 CPUs │ 1500 tasks  │
├────────────────────────────────┼──────────────┼──────────┼─────────────┤
│ Total Maximum Footprint        │ ~7.9 GB RAM  │ 8.5 CPUs │             │
└────────────────────────────────┴──────────────┴──────────┴─────────────┘
```

### Safety Headroom:
- Each compute node reserves **3.0 GB RAM minimum** for the host Linux kernel, OS daemons, and storage buffers.
- Host out-of-memory (OOM) killer will never be invoked because limits are enforced at the Docker cgroup and Incus kernel levels.

---

## 4. Workload Division & Lifecycle

```
                       CANDIDATE BROWSER
                              │  HTTPS / WSS (Port 3000)
                              ▼
┌────────────────────────────────────────────────────────────────────────┐
│  MANAGEMENT PLANE (10.8.0.15)                                          │
│                                                                        │
│  • k8s-web (FastAPI, WebTerminal PTY, noVNC HTTP proxy)                │
│  • Redis Bus (Active Sessions, Timer, Heartbeat, Clipboard pub/sub)    │
│  • Node Pool Orchestrator (Selects least-loaded host from pool)        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼ DOCKER_HOST & Incus TLS
┌────────────────────────────────────────────────────────────────────────┐
│  COMPUTE NODES (.169, .188, .170)                                      │
│                                                                        │
│  ┌─────────────────────────┐         ┌───────────────────────────────┐ │
│  │ DOCKER ENGINE           │         │ INCUS MICROVM ENGINE          │ │
│  │                         │         │                               │ │
│  │ • cka-desktop-{sid}     │         │ • node1-{sid} (Control Plane) │ │
│  │ • k3d-cka-{sid}-server  │◄───────►│ • node2-{sid} (Worker Node)   │ │
│  │ • k3d-cka-{sid}-agent   │         │ • node3-{sid} (Unjoined Node) │ │
│  └─────────────────────────┘         └───────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Tier 1: Ephemeral k3d Cluster
* Created on session launch:
  ```bash
  k3d cluster create cka-{sid_short} \
    --image rancher/k3s:v1.30.2-k3s1 \
    --agents 1 \
    --servers-memory 1024m \
    --agents-memory 768m \
    --k3s-arg "--disable=traefik@server:0" \
    --k3s-arg "--kubelet-arg=system-reserved=cpu=100m,memory=150Mi@all" \
    --no-lb \
    --wait
  ```
* Context is exported as `k3d-cka` directly into Redis key `session:{sid}:kubeconfig`.
* Desktop container automatically mounts this kubeconfig on boot.
* On session end / reset: `k3d cluster delete cka-{sid_short}`.

### 4.2 Tier 2: Incus MicroVMs for Kubeadm Multi-Node
* Uses pre-baked golden snapshot templates (`k8s-node1-base`, `k8s-node2-base`, `k8s-node3-base`):
  * Running RHEL 9 / AlmaLinux 9 with native CRI-O and systemd.
* On session launch:
  ```bash
  incus copy k8s-node1-base/golden node1-{sid} --ephemeral
  incus copy k8s-node2-base/golden node2-{sid} --ephemeral
  incus copy k8s-node3-base/golden node3-{sid} --ephemeral
  incus start node1-{sid} node2-{sid} node3-{sid}
  ```
  *(Provisioning duration: **< 2 seconds** using copy-on-write storage!)*
* On session end / reset: `incus delete -f node1-{sid} node2-{sid} node3-{sid}`.

---

## 5. Inter-Node Communication & Candidate Experience

### 5.1 Predictable Session IPAM
Each candidate session is allocated a dedicated subnet:
* Candidate Session 1: `10.10.1.0/24`
  * `10.10.1.2` -> `cka-desktop-{sid1}`
  * `10.10.1.11` -> `node1` (Control Plane)
  * `10.10.1.12` -> `node2` (Worker Node)
  * `10.10.1.13` -> `node3` (Unjoined Worker for `CA-006`)
* Candidate Session 2: `10.10.2.0/24`

### 5.2 Deterministic Host Resolution
The desktop container's `/etc/hosts` is automatically injected at boot:
```text
10.10.X.11  node1
10.10.X.12  node2
10.10.X.13  node3
```
Candidates run `ssh node1` or `kubectl --context kubeadm-vms ...` without needing to know physical node IPs or port forwards.

---

## 6. Single "Huge Node" Compatibility Mode

If the entire stack is hosted on a single server (e.g. 64 GB / 128 GB bare-metal node):
1. Environment flag `SINGLE_NODE=true` is set in `.env`.
2. The orchestrator skips remote SSH dispatch and targets `localhost` directly:
   * Desktops run on local Docker daemon.
   * `k3d` runs on local Docker daemon.
   * MicroVMs run on local Incus bridge `incusbr0`.
3. The candidate web UI, graders, test manifests, and Redis protocols remain **100% identical**.

---

## 7. Implementation Roadmap

- [x] **Phase 1: Environment Sanitation** (Completed)
  - Wiped stale clusters and freed disk on `10.8.0.15` (reclaimed 25+ GB).
  - Cleaned & reset `.169`, `.188`, `.170`. 14 GB free RAM verified per node.
- [ ] **Phase 2: Compute Node Runtime Setup**
  - Install Docker on `.188` and `.170`.
  - Install & initialize Incus on `.169`, `.188`, `.170`.
- [ ] **Phase 3: Automated Ephemeral Provisioner (`core/sandbox_manager.py`)**
  - Ephemeral k3d cluster driver with strict resource caps.
  - Incus microVM driver with instant snapshot clone/destroy.
- [ ] **Phase 4: Web Platform Sync & Validation**
  - Deploy updated `web/server.py` to `10.8.0.15`.
  - Verify complete lifecycle: Start Exam -> auto-provision -> Grade -> auto-destroy.
