# Mock Exam 05 — Wonka Final Mock

- **Session ID:** `session-1787982014`
- **Total Tasks:** 14
- **Total Points:** 64 pts
- **Time Limit:** 120 minutes
- **Pass Threshold:** 66%
- **Mode:** `batch`

To grade your progress at any time, run:
```bash
./labctl grade
```

---

### Task 1: Chaos: Resolve Pod Resource Starvation and Parent Cgroup Pressure [CRAZY] (6 pts)
- **ID:** `TR-C01`
- **Context:** `k3d-cka`
- **Namespace:** `cgroup-limits`

#### Description
Workloads in namespace `cgroup-limits` are being evicted / killed without clear pod-level OOM events due to severe CPU/Memory request over-subscription.
Analyze the namespace ResourceQuota and LimitRange, adjust container requests and limits on deployment `critical-api` to fit within quota (`requests.cpu: 100m, requests.memory: 128Mi`), and ensure all 3 replicas reach Ready.

---

### Task 2: Chaos: Fix Non-Root Pod SubPath Directory Ownership Conflict [CRAZY] (6 pts)
- **ID:** `TR-C06`
- **Context:** `k3d-cka`
- **Namespace:** `database-tier`

#### Description
Non-root container in `database-tier` fails to write to `/data/db` due to root-owned subPath directory on hostPath volume. Fix via initContainer chown.

---

### Task 3: Enable automountServiceAccountToken on Pod [MEDIUM] (3 pts)
- **ID:** `TR-032`
- **Context:** `k3d-cka`
- **Namespace:** `order-auth`

#### Description
Pod `api-client` in `order-auth` cannot contact Kubernetes API because `automountServiceAccountToken: false` is set. Enable token automounting.

---

### Task 4: Update StatefulSet PVC Retention Policy [MEDIUM] (3 pts)
- **ID:** `TR-034`
- **Context:** `k3d-cka`
- **Namespace:** `stateful-db`

#### Description
Configure StatefulSet `cache-node` in `stateful-db` with `persistentVolumeClaimRetentionPolicy` `whenDeleted: Delete`.

---

### Task 5: Fix ExternalName Service FQDN Typo [MEDIUM] (3 pts)
- **ID:** `TR-036`
- **Context:** `k3d-cka`
- **Namespace:** `external-routing`

#### Description
Service `db-external` in `external-routing` points to misspelled hostname `db.prod.internal.corp`. Fix `externalName` target.

---

### Task 6: Create Batch Job with Parallelism and Completions [EASY] (2 pts)
- **ID:** `WL-009`
- **Context:** `k3d-cka`
- **Namespace:** `batch-processing`

#### Description
Create Job `batch-processor` in `batch-processing` with `completions: 5`, `parallelism: 2`, and `backoffLimit: 4`.

---

### Task 7: Configure Pod Lifecycle preStop Hook [MEDIUM] (3 pts)
- **ID:** `WL-013`
- **Context:** `k3d-cka`
- **Namespace:** `graceful-shutdown`

#### Description
Create Pod `graceful-app` in `graceful-shutdown` with a `preStop` exec hook running `['/bin/sh', '-c', 'sleep 15; nginx -s quit']`.

---

### Task 8: Deploy Canary Deployment Alongside Production Workload [HARD] (4 pts)
- **ID:** `WL-014`
- **Context:** `k3d-cka`
- **Namespace:** `traffic-canary`

#### Description
In namespace `traffic-canary`, deploy `app-v1` (3 replicas) and `app-canary` (1 replica) behind single Service `app-svc` on port 80.

---

### Task 9: Resolve Admission Webhook Deadlock Blocking Pod Creations [CRAZY] (6 pts)
- **ID:** `TR-C02`
- **Context:** `k3d-cka`
- **Namespace:** `cluster-admissions`

#### Description
A rogue ValidatingWebhookConfiguration named strict-policy-enforcer was applied to the cluster with failurePolicy: Fail targeting all Pod creations.
The webhook backend service webhook-service in namespace webhook-system is unreachable, completely deadlocking all new pod creations across the cluster.
Investigate the cluster failure, remove or fix the admission block, and deploy a test pod recovery-app (nginx) into namespace cluster-admissions.

---

### Task 10: Chaos: Resolve CoreDNS Loop Forward Plugin Deadlock [CRAZY] (6 pts)
- **ID:** `TR-C03`
- **Context:** `k3d-cka`
- **Namespace:** `kube-system`

#### Description
CoreDNS is in a 100% CPU crashloop because `/etc/resolv.conf` forwards queries back to CoreDNS IP. Break the circular loop.

---

### Task 11: Chaos: Trigger Dynamic Pod Preemption via PriorityClasses [CRAZY] (6 pts)
- **ID:** `WL-C01`
- **Context:** `k3d-cka`
- **Namespace:** `task-scheduler`

#### Description
Create PriorityClasses `high-priority` (value 1000000) and `low-priority` (value 1000). Deploy high-priority pod that triggers preemption of low-priority pods on saturated node.

---

### Task 12: Chaos: Resolve Nested RBAC Privilege Escalation Deadlock [CRAZY] (6 pts)
- **ID:** `SC-C01`
- **Context:** `k3d-cka`
- **Namespace:** `operator-core`

#### Description
An operator ServiceAccount cannot bind a ClusterRole because it lacks permissions on the target verbs/resources (privilege escalation check). Grant required intermediate permissions.

---

### Task 13: Enforce Pod Security Standards (PSS) Restricted Mode [HARD] (4 pts)
- **ID:** `SC-009`
- **Context:** `k3d-cka`
- **Namespace:** `secure-zone`

#### Description
Enforce Pod Security Standards `restricted` mode on namespace `secure-zone` using label `pod-security.kubernetes.io/enforce: restricted`.

---

### Task 14: Chaos: Clear Stale Iptables Drop Rule Blocking Service CIDR [CRAZY] (6 pts)
- **ID:** `TR-C07`
- **Context:** `k3d-cka`
- **Namespace:** `traffic-edge`

#### Description
A rogue iptables rule is dropping packets destined for ClusterIP `10.43.0.0/16`. Identify and remove the drop rule.

---
