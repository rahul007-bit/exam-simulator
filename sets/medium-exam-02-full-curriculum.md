# Medium Exam 02 — Full Curriculum

- **Session ID:** `session-1788622978`
- **Total Tasks:** 14
- **Total Points:** 42 pts
- **Time Limit:** 120 minutes
- **Pass Threshold:** 66%
- **Mode:** `sequential`

To navigate tasks during the exam:
- Run `examctl task` to view the current active task
- Run `examctl next` to deploy and advance to the next task
- Run `examctl prev` to return to the previous task
- Run `examctl jump <num>` to jump directly to a task
- Run `examctl status` to view overall exam progress

---

### Task 1: Configure Host-Based Ingress with TLS Termination [MEDIUM] (3 pts) (PASSED)
- **ID:** `CA-008`
- **Context:** `k3d-cka`
- **Namespace:** `tls-routing`

#### Description
In namespace `tls-routing`, an existing backend service `app-svc` and a TLS secret named `app-cert` are already provisioned.

Create an Ingress resource named `secure-app` that:
- Directs traffic for host `app.company.org` to service `app-svc` on port 80
- Terminates TLS for host `app.company.org` using the existing TLS secret `app-cert`

---

### Task 2: Configure Custom CoreDNS Hosts Rewrite Rule [MEDIUM] (3 pts) (PASSED)
- **ID:** `CA-010`
- **Context:** `k3d-cka`
- **Namespace:** `kube-system`

#### Description
Configure custom internal DNS resolution in the cluster.

Create a ConfigMap named `coredns-custom` in namespace `kube-system` containing a static hosts mapping for:
- IP: `192.168.1.100`
- FQDN: `db.internal.company`

---

### Task 3: Renew Expiring Control-Plane Certificates [MEDIUM] (3 pts) (PASSED)
- **ID:** `CA-011`
- **Context:** `kubeadm-vms`
- **Namespace:** `default`

#### Description
As part of periodic maintenance on the `kubeadm-vms` control plane node (`node1`), check the expiration status of the Kubernetes control plane certificates.

Renew all expiring control plane certificates on `node1` so they have full one-year validity.

---

### Task 4: Enforce Non-Root and Read-Only Root Filesystem SecurityContext [MEDIUM] (3 pts) (PASSED)
- **ID:** `SC-003`
- **Context:** `k3d-cka`
- **Namespace:** `sec-apps`

#### Description
Create a Pod named `hardened-api` in namespace `sec-apps` with image `nginx:alpine` configured with:
- `runAsNonRoot: true`
- `runAsUser: 10001`
- `readOnlyRootFilesystem: true`

Mount `emptyDir` volumes at `/var/cache/nginx`, `/var/run`, and `/tmp` so nginx can initialize properly.

---

### Task 5: Audit and Revoke Overprivileged ClusterRoleBindings [MEDIUM] (3 pts) (PASSED)
- **ID:** `SC-008`
- **Context:** `k3d-cka`
- **Namespace:** `default`

#### Description
A recent security audit reported that an unauthorized or overprivileged ClusterRoleBinding exists granting the `cluster-admin` ClusterRole to user `dev-operator`.

Audit the existing ClusterRoleBindings in the cluster, identify the overprivileged binding granting `cluster-admin` to user `dev-operator`, and delete it.

---

### Task 6: Enforce SecurityContext Restrictions on Pipeline Workload [MEDIUM] (3 pts) (PASSED)
- **ID:** `SC-012`
- **Context:** `k3d-cka`
- **Namespace:** `secure-pipeline`

#### Description
In namespace `secure-pipeline`, an existing ServiceAccount named `pipeline-runner` is configured.

Create a Pod named `hardened-worker` using image `busybox:1.36` running command `sleep 3600` that:
- Runs under ServiceAccount `pipeline-runner`
- Sets `runAsNonRoot: true`
- Sets `runAsUser: 10001`
- Sets `allowPrivilegeEscalation: false`
- Sets `readOnlyRootFilesystem: true`
- Drops `ALL` capabilities

---

### Task 7: Configure NodeAffinity (Required and Preferred Rules) [MEDIUM] (3 pts) (PASSED)
- **ID:** `WL-005`
- **Context:** `k3d-cka`
- **Namespace:** `web-cluster`

#### Description
Create a Pod named `affinity-pod` in namespace `web-cluster` using image `nginx:1.25` with NodeAffinity rules:
- A required rule (`requiredDuringSchedulingIgnoredDuringExecution`) ensuring the pod schedules only on nodes with label `topology.kubernetes.io/zone: zone-1`.
- A preferred rule (`preferredDuringSchedulingIgnoredDuringExecution`) with weight 1 preferring nodes with label `disk: ssd`.

---

### Task 8: Deploy Monitoring DaemonSet on Worker Nodes [MEDIUM] (3 pts) (PASSED)
- **ID:** `WL-006`
- **Context:** `k3d-cka`
- **Namespace:** `node-monitoring`

#### Description
Create a DaemonSet named `system-monitor` in namespace `node-monitoring` using image `nginx:alpine` that runs on all worker nodes.

---

### Task 9: Mount Multiple SubPaths from Single PersistentVolume [MEDIUM] (3 pts) (PASSED)
- **ID:** `ST-004`
- **Context:** `k3d-cka`
- **Namespace:** `subpath-multi`

#### Description
Create a Pod named `multi-subpath` in namespace `subpath-multi` using image `busybox:1.36` (command: `sleep 3600`) with an `emptyDir` volume named `data-storage`.

Mount volume `data-storage` twice into the container using `subPath`:
- Mount at `/app/config` with subPath `config`
- Mount at `/app/logs` with subPath `logs`

---

### Task 10: Deploy StatefulSet with Dynamic VolumeClaimTemplates [MEDIUM] (3 pts) (PASSED)
- **ID:** `ST-006`
- **Context:** `k3d-cka`
- **Namespace:** `redis-cluster`

#### Description
In namespace `redis-cluster`, create a headless Service named `redis-svc` targeting port 6379 with `clusterIP: None`.

Create a StatefulSet named `redis-cluster` with:
- 2 replicas using image `redis:7-alpine`
- `serviceName: redis-svc`
- A volumeClaimTemplate named `data` requesting `1Gi` storage from StorageClass `local-path` mounted at `/data`

---

### Task 11: Repair CoreDNS Corefile Syntax Error [MEDIUM] (3 pts) (PASSED)
- **ID:** `TR-005`
- **Context:** `k3d-cka`
- **Namespace:** `kube-system`

#### Description
CoreDNS pods in `kube-system` are crashlooping due to an invalid configuration directive in the `coredns` ConfigMap.
Inspect CoreDNS logs, fix the invalid block in the `coredns` ConfigMap in namespace `kube-system`, and restart the CoreDNS deployment to restore cluster DNS.

---

### Task 12: Fix Unsatisfiable NodeSelector on Worker Pod [MEDIUM] (3 pts) (PASSED)
- **ID:** `TR-009`
- **Context:** `k3d-cka`
- **Namespace:** `analytics`

#### Description
A workload pod named `analytics-worker` in namespace `analytics` is stuck in `Pending` and cannot schedule.

Investigate the pod's scheduling constraints and remediate the issue so that `analytics-worker` schedules and reaches `1/1 Running`.

---

### Task 13: Roll Back Broken Deployment Rollout to Previous Working Revision [MEDIUM] (3 pts) (PASSED)
- **ID:** `TR-013`
- **Context:** `k3d-cka`
- **Namespace:** `shipping`

#### Description
A recent update to Deployment `delivery-service` in namespace `shipping` failed, leaving the rollout stalled and pods failing to run.

Investigate the rollout history of `delivery-service` and roll back the deployment to the previous working revision so that all 2 replicas become healthy and Ready.

---

### Task 14: Fix Headless Service Missing ClusterIP None [MEDIUM] (3 pts) (CURRENT ACTIVE TASK)
- **ID:** `TR-015`
- **Context:** `k3d-cka`
- **Namespace:** `db-cluster`

#### Description
StatefulSet `cassandra-cluster` in namespace `db-cluster` is configured to use service `cassandra-svc` for direct per-pod network discovery, but individual pods are unable to resolve distinct DNS records for their peers.

Investigate the service configuration of `cassandra-svc` and fix the service so that it functions as a proper headless service for the StatefulSet.

---
