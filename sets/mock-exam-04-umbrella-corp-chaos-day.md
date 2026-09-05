# Mock Exam 04 — Umbrella Corp Chaos Day

- **Session ID:** `session-1787982003`
- **Total Tasks:** 17
- **Total Points:** 60 pts
- **Time Limit:** 120 minutes
- **Pass Threshold:** 66%
- **Mode:** `batch`

To grade your progress at any time, run:
```bash
./labctl grade
```

---

### Task 1: Fix Non-Root SubPath Volume Permission Denied [HARD] (4 pts)
- **ID:** `TR-016`
- **Context:** `k3d-cka`
- **Namespace:** `api-backend`

#### Description
Pod `api-app` in `api-backend` crashes because non-root user cannot write to volume subPath `/data/cache`. Fix permissions or volume mounts.

---

### Task 2: Resolve Pod Anti-Affinity Scheduling Deadlock [HARD] (4 pts)
- **ID:** `TR-020`
- **Context:** `k3d-cka`
- **Namespace:** `web-tier`

#### Description
Deployment `web-redundant` in `web-tier` has 4 replicas but only 2 nodes exist with hard `podAntiAffinity`. Convert to soft affinity (`preferredDuringScheduling`).

---

### Task 3: Fix PodDisruptionBudget minAvailable 100% Blocking Drain [HARD] (4 pts)
- **ID:** `TR-029`
- **Context:** `k3d-cka`
- **Namespace:** `payment-processor`

#### Description
PDB `strict-pdb` in `payment-processor` blocks node eviction because `minAvailable: 100%` is set on a 1-replica deployment.

---

### Task 4: Fix InitContainer Log Directory Creation Race [HARD] (4 pts)
- **ID:** `TR-031`
- **Context:** `k3d-cka`
- **Namespace:** `log-collector`

#### Description
Container `logger` crashes because directory `/var/log/app` in shared volume is not yet initialized by `app`. Add initContainer to ensure path exists.

---

### Task 5: Fix Unsatisfiable TopologySpreadConstraint on Zone-Spread App [MEDIUM] (3 pts)
- **ID:** `TR-042`
- **Context:** `k3d-cka`
- **Namespace:** `geo-distribution`

#### Description
Deployment `zone-spread-app` in namespace `geo-distribution` has 4 replicas but pods are stuck in `Pending`. The `topologySpreadConstraints` uses `whenUnsatisfiable: DoNotSchedule` with `topologyKey: topology.kubernetes.io/zone`, but no nodes have zone labels.
Fix the constraint (change to `ScheduleAnyway`) or label nodes with zone topology so all 4 pods reach `Running`.

---

### Task 6: Configure NodeAffinity (Required and Preferred Rules) [MEDIUM] (3 pts)
- **ID:** `WL-005`
- **Context:** `k3d-cka`
- **Namespace:** `web-cluster`

#### Description
Create Pod `affinity-pod` in `web-cluster` with `requiredDuringSchedulingIgnoredDuringExecution` matching `topology.kubernetes.io/zone: zone-1` and `preferredDuringScheduling` matching `disk: ssd`.

---

### Task 7: Configure PodAntiAffinity to Spread Replicas Across Nodes [MEDIUM] (3 pts)
- **ID:** `WL-008`
- **Context:** `k3d-cka`
- **Namespace:** `resilient-app`

#### Description
Create Deployment `spread-web` with 2 replicas in `resilient-app` using `podAntiAffinity` on `topologyKey: kubernetes.io/hostname`.

---

### Task 8: Configure TopologySpreadConstraints Across Zones [HARD] (4 pts)
- **ID:** `WL-012`
- **Context:** `k3d-cka`
- **Namespace:** `multi-zone-app`

#### Description
Configure Deployment `zone-spread` in `multi-zone-app` with `topologySpreadConstraints` specifying `maxSkew: 1`, `topologyKey: topology.kubernetes.io/zone`, and `whenUnsatisfiable: DoNotSchedule`.

---

### Task 9: Mount Multiple SubPaths from Single PersistentVolume [MEDIUM] (3 pts)
- **ID:** `ST-004`
- **Context:** `k3d-cka`
- **Namespace:** `subpath-multi`

#### Description
Create Pod `multi-subpath` in `subpath-multi` mounting volume `data-storage` at `/app/config` (subPath: `config`) and `/app/logs` (subPath: `logs`).

---

### Task 10: Configure ReadWriteOncePod Access Mode on PVC [MEDIUM] (3 pts)
- **ID:** `ST-010`
- **Context:** `k3d-cka`
- **Namespace:** `exclusive-storage`

#### Description
Create PVC `exclusive-claim` in `exclusive-storage` using accessMode `ReadWriteOncePod` with capacity `1Gi`.

---

### Task 11: Configure Host-Based Ingress with TLS Termination [MEDIUM] (3 pts)
- **ID:** `CA-008`
- **Context:** `k3d-cka`
- **Namespace:** `tls-routing`

#### Description
In `tls-routing`, configure Ingress `secure-app` for host `app.company.org` with TLS secret `app-cert` routing to `app-svc:80`.

---

### Task 12: Drop All Capabilities and Add NET_ADMIN Capability [MEDIUM] (3 pts)
- **ID:** `SC-004`
- **Context:** `k3d-cka`
- **Namespace:** `net-tools`

#### Description
Create a Pod named `net-monitor` in namespace `net-tools` using image `busybox:1.36` (command: `sleep 3600`) with container SecurityContext dropping `ALL` capabilities and adding `NET_ADMIN`.

---

### Task 13: Add WaitForFirstConsumer to Local StorageClass [HARD] (4 pts)
- **ID:** `TR-023`
- **Context:** `k3d-cka`
- **Namespace:** `data-nodes`

#### Description
Local PV cannot bind to PVC because StorageClass lacks `volumeBindingMode: WaitForFirstConsumer`. Update StorageClass.

---

### Task 14: Add Control-Plane Toleration to Monitoring DaemonSet [HARD] (4 pts)
- **ID:** `TR-027`
- **Context:** `k3d-cka`
- **Namespace:** `monitoring-ns`

#### Description
DaemonSet `node-exporter` in `monitoring-ns` is missing toleration for `node-role.kubernetes.io/control-plane:NoSchedule`.

---

### Task 15: Clear Leftover NoSchedule Cordon on Node [MEDIUM] (3 pts)
- **ID:** `TR-014`
- **Context:** `k3d-cka`
- **Namespace:** `prod-workers`

#### Description
Node is cordoned. Uncordon so deployment `worker-pool` in `prod-workers` scales to 3 replicas.

---

### Task 16: Restore Kube-Proxy DaemonSet Operation [HARD] (4 pts)
- **ID:** `TR-018`
- **Context:** `k3d-cka`
- **Namespace:** `kube-system`

#### Description
Kube-proxy pods in `kube-system` are crashlooping due to invalid iptables mode flags in `kube-proxy` configmap. Repair configmap.

---

### Task 17: Patch Broken Webhook failurePolicy to Ignore [HARD] (4 pts)
- **ID:** `TR-025`
- **Context:** `k3d-cka`
- **Namespace:** `policy-enforcement`

#### Description
MutatingWebhookConfiguration `admission-hook` is down and blocking pod deployments. Patch `failurePolicy: Ignore` so pods can schedule.

---
