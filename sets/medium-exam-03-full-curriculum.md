# Medium Exam 03 — Full Curriculum

- **Session ID:** `session-1788624068`
- **Total Tasks:** 14
- **Total Points:** 40 pts
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

### Task 1: Restore Cluster State from etcd Snapshot [HARD] (4 pts) (PASSED)
- **ID:** `CA-002`
- **Context:** `kubeadm-vms`
- **Namespace:** `default`

#### Description
Restore etcd database from `/opt/backup/etcd-snapshot.db` into `/var/lib/etcd-restored` and update static pod manifest.

---

### Task 2: Upgrade Control-Plane Node with kubeadm [HARD] (4 pts) (FAILED)
- **ID:** `CA-003`
- **Context:** `kubeadm-vms`
- **Namespace:** `default`

#### Description
Upgrade the control-plane node components from v1.29 to v1.30 using `kubeadm upgrade apply v1.30.0` and update kubelet.

---

### Task 3: Configure Ingress Path Routing for Auth and Pay Services [EASY] (2 pts) (PASSED)
- **ID:** `CA-007`
- **Context:** `k3d-cka`
- **Namespace:** `edge-routing`

#### Description
In namespace `edge-routing`, create an Ingress named `app-ingress`:
- Path `/auth` (Prefix) -> service `auth-svc:80`
- Path `/pay` (Prefix) -> service `pay-svc:80`.

---

### Task 4: Configure RBAC ServiceAccount & Role for Deployment Management [EASY] (2 pts) (PASSED)
- **ID:** `SC-001`
- **Context:** `k3d-cka`
- **Namespace:** `billing-app`

#### Description
In namespace billing-app:
1. Create a ServiceAccount named app-deployer.
2. Create a Role named deployment-manager allowing verbs create, get, list, update, delete on resources deployments in API group apps.
3. Create a RoleBinding named deployer-binding binding Role deployment-manager to ServiceAccount app-deployer.

---

### Task 5: Enforce Pod Security Standards (PSS) Restricted Mode [HARD] (4 pts) (PASSED)
- **ID:** `SC-009`
- **Context:** `k3d-cka`
- **Namespace:** `secure-zone`

#### Description
Enforce Pod Security Standards `restricted` mode on namespace `secure-zone` using label `pod-security.kubernetes.io/enforce: restricted`.

---

### Task 6: Configure ServiceAccount and Scoped Configuration Role [EASY] (2 pts) (PASSED)
- **ID:** `SC-010`
- **Context:** `k3d-cka`
- **Namespace:** `secure-pipeline`

#### Description
In namespace secure-pipeline:
1. Create a ServiceAccount named pipeline-runner.
2. Create a Role named config-manager allowing verbs get, list, watch on resources configmaps and secrets.
3. Create a RoleBinding named pipeline-config-binding binding Role config-manager to ServiceAccount pipeline-runner.

---

### Task 7: Configure InitContainer Dependency Gate on Frontend Pod [EASY] (2 pts) (PASSED)
- **ID:** `WL-002`
- **Context:** `k3d-cka`
- **Namespace:** `frontend-ui`

#### Description
Create a Pod named `web-app` in namespace `frontend-ui` with an `initContainer` named `wait-for-db` using image `busybox:1.36` that checks for database availability (`sh -c 'until nc -z -w 2 db-service 3306; do sleep 1; done'`).
The main container `web` should run `nginx:alpine` on port 80.

---

### Task 8: Configure Liveness, Readiness, and Startup Probes [MEDIUM] (3 pts) (PASSED)
- **ID:** `WL-010`
- **Context:** `k3d-cka`
- **Namespace:** `health-monitoring`

#### Description
Create Pod `health-app` in `health-monitoring` with startupProbe (period 5s, failureThreshold 10), readinessProbe (httpGet /ready), and livenessProbe (httpGet /health).

---

### Task 9: Mount Secret and ConfigMap as File Volumes in Specific Paths [MEDIUM] (3 pts) (FAILED)
- **ID:** `ST-008`
- **Context:** `k3d-cka`
- **Namespace:** `app-configs`

#### Description
Create Pod `config-reader` in `app-configs` mounting Secret `app-secret` at `/etc/secrets/token` and ConfigMap `app-config` at `/etc/config/app.conf`.

---

### Task 10: Configure ReadWriteOncePod Access Mode on PVC [MEDIUM] (3 pts) (PASSED)
- **ID:** `ST-010`
- **Context:** `k3d-cka`
- **Namespace:** `exclusive-storage`

#### Description
Create PVC `exclusive-claim` in `exclusive-storage` using accessMode `ReadWriteOncePod` with capacity `1Gi`.

---

### Task 11: Resolve PVC ReadWriteMany on ReadWriteOnce Storage [MEDIUM] (3 pts) (PASSED)
- **ID:** `TR-017`
- **Context:** `k3d-cka`
- **Namespace:** `media-platform`

#### Description
PersistentVolumeClaim `shared-data` in namespace `media-platform` is stuck in `Pending` status and cannot bind to storage.

Investigate the storage configuration and the available PersistentVolume `shared-data-pv`. Resolve the configuration conflict on the PVC so that `shared-data` successfully transitions to `Bound` status.

---

### Task 12: Fix InitContainer DNS Resolution Deadlock [MEDIUM] (3 pts) (PASSED)
- **ID:** `TR-019`
- **Context:** `k3d-cka`
- **Namespace:** `frontend-services`

#### Description
Pod `web-frontend` in `frontend-services` is stuck in Init:0/1 because initContainer is checking wrong DB host FQDN. Fix target service hostname.

---

### Task 13: Fix Base64 Encoding Error in Pod Secret Reference [MEDIUM] (2 pts) (PASSED)
- **ID:** `TR-021`
- **Context:** `k3d-cka`
- **Namespace:** `payments`

#### Description
Pod `crypto-service` in namespace `payments` fails to start and remains stuck in `CreateContainerConfigError`.

Investigate the pod and its referenced secret `api-keys`. Fix the issue with the secret so that the pod `crypto-service` starts successfully and reaches `1/1 Running`.

---

### Task 14: Fix NodePort TargetPort Container Routing [MEDIUM] (3 pts) (CURRENT ACTIVE TASK)
- **ID:** `TR-024`
- **Context:** `k3d-cka`
- **Namespace:** `web-services`

#### Description
NodePort Service `web-np` in `web-services` forwards traffic to wrong port `9090` instead of containerPort `80`.

---
