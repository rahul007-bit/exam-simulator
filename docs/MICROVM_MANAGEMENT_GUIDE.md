# Kubernetes Cluster & MicroVM/Container Management Guide

## 1. Executive Summary & Topology

The CKA Simulator runs **ephemeral, isolated Kubernetes clusters** for each candidate examination session. The platform guarantees strict resource quotas, prevents candidate privilege escalation to host nodes, and provides sub-second environment provisioning through a pre-baked golden image.

### Fleet Topology

```
                   +--------------------------------------------+
                   |          MANAGEMENT HOST (Ubuntu)          |
                   |                10.8.0.15                   |
                   |                                            |
                   |   - FastApi Engine (k8s-web.service :3000) |
                   |   - Containerized Redis (cka-redis :6379)  |
                   |   - Candidate Desktops (cka-desktop-{sid}) |
                   |   - Incus TLS Remotes (:8443 Client)       |
                   +--------------------------------------------+
                                  |
            TLS Control (:8443)   |    Private LAN (192.168.50.x)
        +-------------------------+-------------------------+
        |                                                   |
        v                                                   v
+-------------------------------+   +-------------------------------+   +-------------------------------+
|     COMPUTE NODE 1 (RHEL 9)   |   |     COMPUTE NODE 2 (RHEL 10)  |   |     COMPUTE NODE 3 (RHEL 9)   |
|         192.168.50.169        |   |         192.168.50.188        |   |         192.168.50.170        |
|                               |   |                               |   |                               |
| - Incus 6.23 Server (:8443)   |   | - Incus 6.23 Server (:8443)   |   | - Incus 6.23 Server (:8443)   |
| - Cached 'k8s-golden' image   |   | - Cached 'k8s-golden' image   |   | - Cached 'k8s-golden' image   |
| - Control Plane (node1-{sid}) |   | - Worker 1 (node2-{sid})      |   | - Worker 2 (node3-{sid})      |
| - Limits: 2 vCPU, 2 GiB RAM   |   | - Limits: 2 vCPU, 1.5 GiB RAM |   | - Limits: 2 vCPU, 1.5 GiB RAM |
+-------------------------------+   +-------------------------------+   +-------------------------------+
```

---

## 2. The Golden Image (`k8s-golden`)

To ensure ephemeral clusters boot in **under 2 seconds**, each node maintains a locally cached Incus image named `k8s-golden`.

### Image Specifications:
- **Base OS**: Debian 12 (Bookworm) minimal container image (~106 MB rootfs).
- **CRI Runtime**: `containerd` with `SystemdCgroup = true` enabled in `/etc/containerd/config.toml`.
- **Kubernetes Binaries**: `kubeadm`, `kubelet`, `kubectl` (v1.30.x pinned).
- **Pre-pulled Control Plane Images**:
  - `registry.k8s.io/kube-apiserver:v1.30.0`
  - `registry.k8s.io/kube-controller-manager:v1.30.0`
  - `registry.k8s.io/kube-scheduler:v1.30.0`
  - `registry.k8s.io/kube-proxy:v1.30.0`
  - `registry.k8s.io/etcd:3.5.15-0`
  - `registry.k8s.io/coredns/coredns:v1.11.3`
  - `registry.k8s.io/pause:3.9`
- **Candidate Shell Ergonomics**: `vim`, `bash-completion`, `jq`, `iproute2`, `net-tools`, and `k` alias pre-configured in `/root/.bashrc`.
- **Total Published Size**: ~693 MB (compressed).

### Re-baking or Updating the Image
The golden image is completely reproducible using the automated script:
```bash
# Run via fleet runner on node1:
uv run python fleet.py node1 -f scripts/bake_k8s_base.sh

# Distribute to node2 and node3:
uv run python fleet.py mgmt "incus image copy node1:k8s-golden node2: --alias k8s-golden && incus image copy node1:k8s-golden node3: --alias k8s-golden"
```

---

## 3. Host Prerequisites & Subordinate ID Mapping

Incus containers isolate processes using Linux user namespaces. RHEL installations require the following one-time configuration:

1. **Subordinate UIDs & GIDs**:
   `/etc/subuid` and `/etc/subgid` must allocate subordinate ranges:
   ```text
   root:1000000:1000000000
   ```
2. **Firewalld Bridge Trust**:
   To allow internal DHCP (UDP 67/68) and DNS (UDP 53) on `incusbr0`:
   ```bash
   firewall-cmd --zone=trusted --add-interface=incusbr0 --permanent
   firewall-cmd --reload
   ```

---

## 4. How Instances Are Created & Orchestrated

When a candidate launches an exam (`POST /api/start` or through candidate token link):

```
       Candidate Clicks 'Start Exam'
                     |
                     v
   +------------------------------------+
   |    core/sandbox_orchestrator.py    |
   +------------------------------------+
         |                        |
         v                        v
  [1. Docker Manager]       [2. Incus Manager]
         |                        |
Spawns cka-desktop-{sid}   Spawns k8s-golden on node1, node2, node3
(1.5 vCPU, 1 GB RAM)       (2.0 vCPU, 2 GB RAM per node)
         |                        |
         v                        v
   Container Starts       Acquires DHCP IPs on incusbr0
         |                        |
         +------------+-----------+
                      |
                      v
     Injects Node IPs into /etc/hosts of cka-desktop-{sid}
     Stores cluster kubeconfig in Redis (session:{sid}:kubeconfig)
     Candidate Terminal attaches cleanly to desktop container
```

### Resource Quotas Enforced:
```bash
incus launch k8s-golden <instance_name> \
  -c limits.cpu=2 \
  -c limits.memory=2GiB \
  -c limits.processes=1500 \
  -c security.nesting=true
```
- **CPU Quota**: Maximum 2 vCPUs allocated per node via cgroup `cpu.max`.
- **Memory Cap**: Maximum 2 GiB physical RAM cap via cgroup `memory.max`.
- **PID Limit**: Cap of 1500 processes to guard against fork-bombs.
- **Nesting**: `security.nesting=true` allows `containerd` inside the instance to manage pod cgroups.

---

## 5. Fleet CLI Runner (`fleet.py`)

To eliminate Windows PowerShell quote-escaping and string mangling, all host commands are executed via `fleet.py`:

```bash
# Execute command on a single node:
uv run python fleet.py node1 "crictl images"

# Execute across all compute nodes simultaneously:
uv run python fleet.py compute "uptime"

# Execute across all 4 fleet nodes (mgmt + compute):
uv run python fleet.py all "free -h"

# Execute a multiline bash script file:
uv run python fleet.py node1 -f path/to/script.sh
```

---

## 6. Real-Time Admin Monitoring & Teardown

### Admin Web Dashboard (`/admin`)
The Admin UI provides an active **Cluster Infrastructure & Fleet Nodes** section:
- **Physical Host Health**: Displays live connectivity and IP addresses for `mgmt`, `node1`, `node2`, and `node3`.
- **Live Inventory Matrix**: Displays every active Docker container and Incus instance, including:
  - Instance Name
  - Host Node
  - Technology Badge (`DOCKER` vs `INCUS`)
  - Associated Session ID (`session-...`)
  - Internal IP address
  - Resource caps (vCPU, RAM)
  - Current status (`RUNNING` / `STOPPED`)
  - 1-Click **Terminate** button

### Automated Session Teardown
When a session concludes, times out, or is terminated by an administrator:
1. `orchestrator.cleanup_sandbox(sid)` is triggered.
2. `core/desktop_manager.py` executes `docker rm -f cka-desktop-{sid}`.
3. `core/incus_manager.py` deletes all associated nodes (`node1-{sid}`, `node2-{sid}`, `node3-{sid}`) via native TLS remote commands.
4. Redis state and cached kubeconfig are archived and purged.
5. 100% of CPU and memory are reclaimed instantly.
