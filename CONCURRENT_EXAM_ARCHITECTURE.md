# CKA-Labs: Concurrent Exam Engine & Micro-Virtualization Architecture

**Document Version:** 1.0.0  
**Author:** AI Pair Programming & Platform Engineering Team  
**Date:** September 5, 2026  
**Status:** Architectural Blueprint & Future Roadmap  

---

## 1. Executive Summary

The current CKA-Labs platform operates as a **single-tenant** testing engine:
- Session state is saved to a single file (`var/session.json`).
- The desktop runs a single TigerVNC session on display `:1` (port 5901/6080) for user `exam`.
- The Kubernetes environment relies on a shared `k3d-cka` cluster and static Kubeadm VMs (`node1`, `node2`).
- The web frontend periodically polls `GET /api/clipboard` every 2.5 seconds via HTTP, invoking host subprocesses (`xsel`).

This document outlines the end-to-end architectural blueprint to transform CKA-Labs into a **high-density, multi-tenant concurrent examination platform** capable of serving multiple test-takers simultaneously with instantaneous cluster provisioning, isolated desktops, and zero cross-candidate interference.

---

## 2. High-Level Multi-Tenant Architecture

```
                                      [ Traefik / Nginx Dynamic Reverse Proxy ]
                                                         │
               ┌─────────────────────────────────────────┴─────────────────────────────────────────┐
               ▼                                         ▼                                         ▼
┌───────────────────────────────┐         ┌───────────────────────────────┐         ┌───────────────────────────────┐
│     SESSION A (:3000/s/A)     │         │     SESSION B (:3000/s/B)     │         │     SESSION N (:3000/s/N)     │
│  - Candidate Split-Screen UI  │         │  - Candidate Split-Screen UI  │         │  - Candidate Split-Screen UI  │
│  - Web Terminal PTY Socket    │         │  - Web Terminal PTY Socket    │         │  - Web Terminal PTY Socket    │
│  - WebSocket: /ws/session/A   │         │  - WebSocket: /ws/session/B   │         │  - WebSocket: /ws/session/N   │
└──────────────┬────────────────┘         └──────────────┬────────────────┘         └──────────────┬────────────────┘
               │                                         │                                         │
       ┌───────┴───────┐                         ┌───────┴───────┐                         ┌───────┴───────┐
       ▼               ▼                         ▼               ▼                         ▼               ▼
┌──────────────┐┌──────────────┐         ┌──────────────┐┌──────────────┐         ┌──────────────┐┌──────────────┐
│  Desktop A   ││  Sandbox A   │         │  Desktop B   ││  Sandbox B   │         │  Desktop N   ││  Sandbox N   │
│ (KasmVNC/XFCE││(vCluster/k3d │         │ (KasmVNC/XFCE││(vCluster/k3d │         │ (KasmVNC/XFCE││(vCluster/k3d │
│  Container)  ││+ 3x MicroVMs)│         │  Container)  ││+ 3x MicroVMs)│         │  Container)  ││+ 3x MicroVMs)│
└──────────────┘└──────────────┘         └──────────────┘└──────────────┘         └──────────────┘└──────────────┘
                                                         │
                                                         ▼
                                    ┌─────────────────────────────────────────┐
                                    │              REDIS CLUSTER              │
                                    │  - Active Sessions (Hash & Set)         │
                                    │  - Port & IPAM Allocation Pools         │
                                    │  - Pub/Sub: clipboard:{id}, timer:{id}  │
                                    │  - Streams: telemetry & proctor logs    │
                                    │  - Warm Pool Queue for MicroVMs         │
                                    └─────────────────────────────────────────┘
```

---

## 3. Redis Integration & Protocol Optimization

### 3.1 Eliminating Polling via WebSockets & Redis Pub/Sub

| Current Bottleneck | Proposed Redis + WebSocket Solution | Impact |
| :--- | :--- | :--- |
| **Clipboard Polling (`GET /api/clipboard`)** | Channel `clipboard:{session_id}`. Client and host desktop hook publish clipboard events to Redis. Subscribed clients push immediately. | Eliminates recurring `xsel` fork/exec processes every 2.5s; 0% idle CPU overhead; sub-millisecond sync. |
| **Timer / Drift Polling** | Redis key `session:{session_id}:timer` holds authoritative timestamp & TTL. Background scheduler pushes heartbeat ticks & warning events ("15m remaining"). | Eliminates clock skew and repeated session status API calls. |
| **Session State Locks (`session.json`)** | In-memory Redis Hash `session:{session_id}` with atomic `HSET` / `HGET`. | Eliminates disk I/O race conditions between `/next`, `/flag`, `/retry`, and grader processes. |
| **Live Telemetry & Proctoring** | Redis Streams (`XADD session:stream:{session_id} * event ...`) | Allows real-time multi-candidate proctor dashboards and instant session replay without disk lag. |

---

## 4. Multi-Cluster Sandbox Strategy

CKA exams require testing across two distinct tiers:
1. **Tier 1: Kubernetes Application Resources** (`k3d-cka` context) — Pods, Deployments, Services, Ingress, NetworkPolicies, PVCs, RBAC.
2. **Tier 2: Host / Node / Control Plane Engineering** (`kubeadm-vms` context) — `kubeadm upgrade`, static pod manifests, etcd backup/restore, certificate rotation, and `kubeadm join`.

### 4.1 Tier 1: Dynamic Application Clusters
- **Option A: vCluster (Virtual Clusters)**:
  - Deploys inside a single namespace of the host cluster.
  - Startup time: **~1.5 seconds**.
  - Memory consumption: **< 100MB RAM** per session.
  - Provides a 100% compliant Kubernetes API server for workloads, storage, and networking questions.
- **Option B: Ephemeral k3d Clusters**:
  - `k3d cluster create cka-{session_id} --agents 1`.
  - Startup time: **~8 seconds**.
  - Dedicated Docker bridge network per candidate.

### 4.2 Tier 2: Real Kubeadm Multi-Node Sandboxes
Standard containers cannot run true `kubeadm upgrade` or `systemctl restart kubelet` safely because they share the host Linux kernel. Real virtualized nodes are required.

```
+-----------------------------------------------------------------------------------------------+
| CANDIDATE CLUSTER INSTANCE (per session)                                                      |
|                                                                                               |
|  [ node1 (Control Plane) ]          [ node2 (Worker Node) ]          [ node3 (Unjoined Node) ]|
|  - IP: 10.10.X.11                   - IP: 10.10.X.12                 - IP: 10.10.X.13         |
|  - API Server, etcd, systemd        - kubelet, CRI-O, systemd        - Pre-installed runtime  |
|  - Upgradable via kubeadm           - Drain / Cordon target          - Ready for kubeadm join |
+-----------------------------------------------------------------------------------------------+
```

---

## 5. Micro-Virtualization Deep Dive: Firecracker vs Alternatives

### 5.1 Technology Comparison

| Criteria | AWS Firecracker | Cloud-Hypervisor | Incus / LXD (System Containers) | QEMU / KVM |
| :--- | :--- | :--- | :--- | :--- |
| **Boot / Restore Time** | **5ms – 100ms** | ~200ms | < 1 second | 3 – 8 seconds |
| **Memory Overhead** | **< 5MB** | ~15MB | 0MB (shares kernel) | ~100MB – 150MB |
| **Disk Image Format** | Raw ext4 | QCOW2 / Raw | Rootfs container | QCOW2 / Raw |
| **OS / Kernel Support** | Uncompressed `vmlinux` | UEFI / Cloud-Init | Host Kernel (cgroups) | Full standard ISO/UEFI |
| **RAM Snapshot / Restore** | **Yes (Full Memory Dump)**| Yes | State checkpoint (CRIU) | Yes |
| **Kubeadm Feasibility** | High (via KubeFire) | Very High (Direct Cloud Img) | High (Requires privileged cgroups) | Standard |

### 5.2 The Firecracker Snapshot-and-Restore Paradigm (Sub-100ms Provisioning)
1. **Pre-Bake Cluster**:
   - Spin up `node1`, `node2`, and `node3` in a template network.
   - Run `kubeadm init`, install flannel/calico CNI, join `node2`.
   - Prepare `node3` with prerequisites but leave it unjoined (for `CA-006`).
2. **Snapshot to RAM/Disk**:
   - Trigger Firecracker's `create_snapshot` API to freeze CPU, device state, and memory pages.
3. **Instant Candidate Allocation**:
   - On candidate session start, call `load_snapshot` with a unique memory-mapped overlay.
   - Cluster is active and ready in **< 100 milliseconds**.
4. **Instant Teardown**:
   - Terminate the microVM processes; discard the ephemeral CoW delta. No lingering state or complex cluster cleaning scripts required.

---

## 6. Solving the "Empty Node" Requirement (`CA-006`)

Question `CA-006-kubeadm-token-node-join` requires an unjoined node where the candidate runs `kubeadm join`:

1. **Pre-configured Node 3**:
   - The third microVM (`node3`) is configured with the container runtime (`containerd` or `crio`), `kubelet`, `kubeadm`, and CNI binaries pre-installed.
   - It has **no** cluster certificates in `/etc/kubernetes/` and `kubelet` is waiting for join bootstrap credentials.
2. **Deterministic Host Discovery**:
   - Candidate sandbox `/etc/hosts` resolves `node1`, `node2`, and `node3` to the session's private microVM subnet (`10.X.Y.0/28`).
   - The candidate generates the join token on `node1`:
     ```bash
     kubeadm token create --print-join-command
     ```
   - Candidate SSHes to `node3` and executes the command. The node joins and transitions to `Ready`.

---

## 7. Dynamic Remote Desktop (VNC / KasmVNC) per Candidate

### 7.1 Pure Redis-Driven Architecture (Zero Host Disk I/O)
Instead of running a single host-level X11 display or mounting host directories to disk, each candidate receives an ephemeral, containerized desktop connected directly to the central Redis event bus:

```
                      Candidate Web Browser (Single Port 3000)
                                      │
                                      ▼
                        FastAPI Dynamic Ingress Gateway
                                      │
                     Queries Redis for Container Endpoint
                                      │
                ┌─────────────────────┴─────────────────────┐
                │                                           │
                ▼                                           ▼
      WebSocket: /ws/desktop/{id}                HTTP: /desktop/{id}/*
      Proxies RFB stream                         Proxies noVNC static UI
                │                                           │
                └─────────────────────┬─────────────────────┘
                                      │
                                      ▼
                    Docker Container: cka-desktop:{session_id}
                    (IP: 172.17.0.x — No Host Disk Mounts!)
      ┌──────────────────────────────────────────────────────────────┐
      │  • X11 Display :1 + Openbox + Firefox (In-memory tmpfs)      │
      │  • noVNC / WebSockify listening on container port 6080       │
      │                                                              │
      │  ┌────────────────────────────────────────────────────────┐  │
      │  │ Lightweight Desktop Sidecar Agent (desk-agent)         │  │
      │  │                                                        │  │
      │  │ 1. Subscribes to: clipboard:{session_id}               │  │
      │  │    ──► Instantly pushes web copied snippets into X11   │  │
      │  │                                                        │  │
      │  │ 2. Publishes to: clipboard:{session_id}                │  │
      │  │    ──► Emits desktop copied text back to web & proctor │  │
      │  │                                                        │  │
      │  │ 3. Publishes to: events:{session_id}                   │  │
      │  │    ──► Emits visited doc URLs & active window changes  │  │
      │  │                                                        │  │
      │  │ 4. Heartbeat: SET desktop:{id}:alive 1 EX 15           │  │
      │  └────────────────────────┬───────────────────────────────┘  │
      └───────────────────────────┼──────────────────────────────────┘
                                  │
                                  ▼ (High-speed docker0 loopback)
              Central Host Redis (172.17.0.1:6379)
              ├── HSET desktop:{session_id} container_id ip port
              ├── Channel: clipboard:{session_id}
              ├── Channel: events:{session_id}
              └── Channel: terminal:{session_id}
                                  ▲
                                  │ (In-memory subscription)
              Host Recorder (core/recorder.py)
              - Consumes events:{id} & clipboard:{id}
              - Writes zero-latency timeline directly to session log
```

### 7.2 Key Architectural Decisions

1. **Rejection of Host Disk Mounts & SQLite Polling**:
   - Polling browser history from disk (`places.sqlite` with `shutil.copy2`) creates unnecessary disk thrashing, file locks, and host-container coupling.
   - In this architecture, the desktop runs **100% statelessly** with in-memory `tmpfs`.
   - Destroying the container (`docker rm -f`) instantly frees 100% of memory with zero residual disk cleanup required.

2. **Event-Driven Telemetry Integration with Existing Recorder**:
   - The container sidecar agent hooks browser visits and X11 clipboard events, publishing them directly to Redis channels `events:{session_id}` and `clipboard:{session_id}`.
   - The host's `core/recorder.py` subscribes in-memory to these channels, seamlessly appending documentation visits, copy/paste operations, and window events to `{session_id}.events.jsonl` with zero disk polling.
   - Terminal recording remains unified in asciinema `.cast` format. No heavy video encoding (MP4/FFmpeg) is needed.

3. **Portless Dynamic Ingress Gateway**:
   - Containers bind only to the internal bridge (`172.17.0.x:6080`).
   - Registration: Upon boot, the desktop publishes `HSET desktop:{session_id} ip <ip> port 6080`.
   - Reverse Proxy: FastAPI routes:
     * `GET /desktop/{session_id}/*`: Reverse proxies static noVNC HTML/JS/CSS.
     * `WebSocket /ws/desktop/{session_id}`: Dynamically proxies the binary RFB WebSocket stream.
   - Result: All candidate interactions occur over standard port 3000 (or 80/443), eliminating all firewall conflicts and port collisions.

4. **Authentic CKA Exam Browser Environment**:
   - Minimal Openbox/XFCE window manager (~45 MB RAM).
   - Pre-seeded Firefox profile with official allowed bookmarks toolbar:
     * Kubernetes Documentation (`https://kubernetes.io/docs/home/`)
     * Kubectl Cheat Sheet (`https://kubernetes.io/docs/reference/kubectl/cheatsheet/`)
     * Kubernetes Tasks & Tutorials (`https://kubernetes.io/docs/tasks/`)
     * Helm Documentation (`https://helm.sh/docs/`)
     * Kubernetes Blog (`https://kubernetes.io/blog/`)

---

## 8. Implementation Roadmap (Phased Rollout)

### Phase 3.1: Redis Core & Real-Time WebSockets (COMPLETED)
- [x] Deploy Redis instance on host (`redis-server`).
- [x] Refactor `core/deployer.py` and `web/server.py` to persist sessions in Redis hashes (`session:{id}`).
- [x] Implement WebSocket endpoint `/ws/session/{session_id}` with live timer ticks and task transitions.
- [x] Connect clipboard listener to Redis Pub/Sub channel `clipboard:{session_id}` (zero HTTP polling).
- [x] Stepped task transition progress bar with cluster race protection.
- [x] Document Issue #18 (tmux session persistence vs raw scrollback replay).

### Phase 3.2: Ephemeral Desktops & Dynamic Ingress (ACTIVE)
- [ ] Configure Redis on host to bind to `172.17.0.1` (`docker0` bridge) for container access.
- [ ] Implement Dynamic Ingress Reverse Proxy in `web/server.py` (`/desktop/{session_id}` and `/ws/desktop/{session_id}`).
- [ ] Package minimal `cka-desktop:latest` Dockerfile (Openbox + TigerVNC + noVNC + Firefox CKA bookmarks + desk-agent).
- [ ] Implement `core/desktop_pool.py` to orchestrate container spin-up on exam start and teardown on submit.
- [ ] Wire desktop Redis Pub/Sub events directly into `core/recorder.py`.

### Phase 3.3: MicroVM Kubeadm Sandboxes
- [ ] Evaluate **Cloud-Hypervisor** vs **Firecracker (KubeFire)** on the host kernel.
- [ ] Build minimal `vmlinux` kernel and raw rootfs image containing containerd and kubeadm tools.
- [ ] Implement Copy-on-Write snapshot restore mechanism for instant (< 200ms) 3-node cluster provisioning.
- [ ] Implement Redis-backed warm VM pool manager to maintain ready-to-use cluster sets on standby.

