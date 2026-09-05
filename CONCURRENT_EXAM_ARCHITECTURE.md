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

### 7.1 Architecture: Ephemeral Containerized Desktops
Instead of running a host-level X11 display, spawn an isolated desktop container per session:
```bash
docker run -d \
  --name desktop-sess-101 \
  --network exam-net-sess-101 \
  -e PUID=1000 -e PGID=1000 \
  -e VNC_PW=exam \
  -v /var/run/exam-sess-101/home:/config \
  lscr.io/linuxserver/webtop:ubuntu-xfce
```

### 7.2 Key Advantages
- **Reverse Proxy Routing**: Accessible via `http://<HOST>/desktop/{session_id}/` (no port conflicts on 6080).
- **Resource Footprint**: ~200MB RAM, < 0.5% CPU per idle user.
- **Sandboxed Browser**: Candidate runs Firefox in an isolated container with pre-loaded Kubernetes documentation bookmarks and zero access to the host root filesystem.
- **KasmVNC Protocol**: Offers WebRTC / WebGL hardware-accelerated video streaming with dynamic resolution resizing and direct browser clipboard integration.

---

## 8. Implementation Roadmap (Phased Rollout)

### Phase 3.1: Redis Core & Real-Time WebSockets
- [ ] Deploy Redis instance on host.
- [ ] Refactor `core/deployer.py` and `web/server.py` to persist sessions in Redis hashes (`session:{id}`).
- [ ] Implement WebSocket endpoint `/ws/session/{session_id}`.
- [ ] Connect host clipboard listener to Redis Pub/Sub channel `clipboard:{session_id}` to eliminate HTTP polling.

### Phase 3.2: Ephemeral Desktops & Dynamic Ingress
- [ ] Package standardized candidate desktop container (XFCE + Firefox + CKA bookmarks).
- [ ] Configure dynamic reverse proxy (Traefik or FastAPI WebSocket proxy) for `/desktop/{session_id}`.
- [ ] Add dynamic PTY allocation per candidate sandbox.

### Phase 3.3: MicroVM Kubeadm Sandboxes
- [ ] Evaluate **Cloud-Hypervisor** vs **Firecracker (KubeFire)** on the host kernel.
- [ ] Build minimal `vmlinux` kernel and raw rootfs image containing containerd and kubeadm tools.
- [ ] Implement Copy-on-Write snapshot restore mechanism for instant (< 200ms) 3-node cluster provisioning.
- [ ] Implement Redis-backed warm VM pool manager to maintain 2 ready-to-use cluster sets on standby.
