# Medium Exam 01 — Full Curriculum

- **Session ID:** `session-1788621813`
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

### Task 1: Perform etcd Snapshot Backup [MEDIUM] (3 pts) (PASSED)
- **ID:** `CA-001`
- **Context:** `kubeadm-vms`
- **Namespace:** `default`

#### Description
A cluster administrator requires a manual etcd snapshot backup before proceeding with maintenance on the `kubeadm-vms` cluster.

1. Connect to the control plane node `node1` (`ssh node1`).
2. Take a snapshot of the running etcd instance using `etcdctl`.
3. Save the snapshot file to `/opt/backup/etcd-snapshot.db`.

---

### Task 2: Upgrade Worker Node with kubeadm [MEDIUM] (3 pts) (PASSED)
- **ID:** `CA-004`
- **Context:** `kubeadm-vms`
- **Namespace:** `default`

#### Description
Given the cluster context `kubeadm-vms`, upgrade worker node `node2` to match the version of the control plane node `node1`.

Ensure that you safely drain the node before maintenance, and return it to an active, schedulable state once the upgrade is complete.

---

### Task 3: Generate Join Token and Join Worker Node [MEDIUM] (3 pts) (FAILED)
- **ID:** `CA-006`
- **Context:** `kubeadm-vms`
- **Namespace:** `default`

#### Description
Given the cluster context `kubeadm-vms`, a new worker node `node3` has been provisioned but has not yet joined the cluster.

Generate a new join token on the control plane, join `node3` to the cluster as a worker node, and ensure it reaches `Ready` status.

---

### Task 4: Create ClusterRole and Binding for Read-Only Cluster Auditor [MEDIUM] (3 pts) (PASSED)
- **ID:** `SC-002`
- **Context:** `k3d-cka`
- **Namespace:** `default`

#### Description
A compliance auditor requires cluster-wide read-only access.

Create a ClusterRole named `cluster-auditor` that grants `get`, `list`, and `watch` permissions on `pods`, `nodes`, and `services`.

Bind this ClusterRole to the user `auditor-user` using a ClusterRoleBinding named `cluster-auditor-binding`.

---

### Task 5: Drop All Capabilities and Add NET_ADMIN Capability [MEDIUM] (3 pts) (PASSED)
- **ID:** `SC-004`
- **Context:** `k3d-cka`
- **Namespace:** `net-tools`

#### Description
Create a Pod named `net-monitor` in namespace `net-tools` using image `busybox:1.36` running the command `sleep 3600`.

Configure the container securityContext to drop `ALL` capabilities and add the `NET_ADMIN` capability.

---

### Task 6: Restrict Secret Access Using RBAC resourceNames [MEDIUM] (3 pts) (PASSED)
- **ID:** `SC-006`
- **Context:** `k3d-cka`
- **Namespace:** `rbac-fine-grained`

#### Description
In namespace `rbac-fine-grained`, multiple secrets exist including `allowed-creds`.

Create a Role named `vault-restricted` that grants `get` permission ONLY on the Secret named `allowed-creds`, using the `resourceNames` constraint.

---

### Task 7: Create Multi-Container Pod with Logging Sidecar [MEDIUM] (3 pts) (PASSED)
- **ID:** `WL-001`
- **Context:** `k3d-cka`
- **Namespace:** `app-logging`

#### Description
Create a Pod named `order-processor` in namespace `app-logging` containing two containers sharing an `emptyDir` volume mounted at `/var/log`:

- An application container named `app` using image `busybox:1.36` that writes timestamps to `/var/log/app.log` every 2 seconds (`while true; do date >> /var/log/app.log; sleep 2; done`).
- A sidecar container named `log-agent` using image `busybox:1.36` that streams `/var/log/app.log` to standard output (`tail -f /var/log/app.log`).

---

### Task 8: Implement HorizontalPodAutoscaler with Target CPU Utilization [MEDIUM] (3 pts) (PASSED)
- **ID:** `WL-004`
- **Context:** `k3d-cka`
- **Namespace:** `customer-portal`

#### Description
In namespace `customer-portal`, an existing Deployment named `scalable-web` is deployed.

Create a HorizontalPodAutoscaler named `web-scaler` that scales `scalable-web` with:
- Minimum replicas: 2
- Maximum replicas: 8
- Target average CPU utilization: 60%

---

### Task 9: Create Dynamic Provisioning StorageClass with Retain Policy [MEDIUM] (3 pts) (PASSED)
- **ID:** `ST-002`
- **Context:** `k3d-cka`
- **Namespace:** `default`

#### Description
Create a new StorageClass named `fast-retain` configured with:
- Provisioner: `rancher.io/local-path`
- Reclaim policy: `Retain`
- Volume binding mode: `WaitForFirstConsumer`

---

### Task 10: Expand Existing PVC Storage Capacity Online [MEDIUM] (3 pts) (PASSED)
- **ID:** `ST-003`
- **Context:** `k3d-cka`
- **Namespace:** `media-store`

#### Description
In namespace `media-store`, an existing PVC named `data-vol` is currently mounted and consumed by a running pod named `data-consumer`.

Expand the PVC storage request from `1Gi` to `3Gi` without terminating or deleting the attached pod.

---

### Task 11: Fix CrashLoopBackOff on Checkout Service [MEDIUM] (3 pts) (PASSED)
- **ID:** `TR-001`
- **Context:** `k3d-cka`
- **Namespace:** `checkout-prod`

#### Description
Pod checkout-api in namespace checkout-prod is failing with CrashLoopBackOff.
Diagnose the failure from logs and pod events, fix the deployment configuration, and ensure the pod achieves 1/1 Running and passes readiness probes.

---

### Task 12: Fix Ingress Path Routing and Backend Service Mapping [MEDIUM] (3 pts) (PASSED)
- **ID:** `TR-006`
- **Context:** `k3d-cka`
- **Namespace:** `gateway-ns`

#### Description
Ingress `api-gateway` in namespace `gateway-ns` is misconfigured with wrong backend service names and port mappings.
Ensure requests to path `/orders` route to service `orders-svc:80` and `/users` route to `users-svc:80`.

---

### Task 13: Fix PVC Stuck in Pending due to Invalid StorageClass [MEDIUM] (3 pts) (PASSED)
- **ID:** `TR-007`
- **Context:** `k3d-cka`
- **Namespace:** `data-ops`

#### Description
PVC data-claim in namespace data-ops is stuck in Pending because it specifies a non-existent StorageClass fast-nvme-ssd.
Update the PVC configuration or provision the correct StorageClass using standard local storage so data-claim becomes Bound.

---

### Task 14: Fix RBAC Permission Denied (403) for Application ServiceAccount [MEDIUM] (3 pts) (CURRENT ACTIVE TASK)
- **ID:** `TR-012`
- **Context:** `k3d-cka`
- **Namespace:** `fintech`

#### Description
An application pod in namespace `fintech` runs under ServiceAccount `vault-reader` and fails with HTTP `403 Forbidden` when attempting to access secrets.

Investigate the RBAC configuration in namespace `fintech`.
Configure RBAC permissions so that ServiceAccount `vault-reader` has permission to `get` and `list` resources of type `secrets` within namespace `fintech`.

---
