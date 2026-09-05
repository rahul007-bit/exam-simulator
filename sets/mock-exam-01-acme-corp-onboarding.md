# Mock Exam 01 — ACME Corp Onboarding

- **Session ID:** `session-1788253602`
- **Total Tasks:** 17
- **Total Points:** 43 pts
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

### Task 1: Fix CrashLoopBackOff on Checkout Service [MEDIUM] (3 pts) (PASSED)
- **ID:** `TR-001`
- **Context:** `k3d-cka`
- **Namespace:** `checkout-prod`

#### Description
Pod checkout-api in namespace checkout-prod is failing with CrashLoopBackOff.
Diagnose the failure from logs and pod events, fix the deployment configuration, and ensure the pod achieves 1/1 Running and passes readiness probes.

---

### Task 2: Fix Pod CreateContainerConfigError on Missing ConfigMap Key [EASY] (2 pts) (CURRENT ACTIVE TASK)
- **ID:** `TR-002`
- **Context:** `k3d-cka`
- **Namespace:** `auth-system`

#### Description
Pod auth-api in namespace auth-system is stuck in CreateContainerConfigError.
Identify the missing ConfigMap key referenced by the container environment and update the ConfigMap auth-config so the pod starts properly.

---

### Task 3: Fix Empty Endpoints on Cart Service [EASY] (2 pts)
- **ID:** `TR-003`
- **Context:** `k3d-cka`
- **Namespace:** `ecommerce`

#### Description
Service cart-svc in namespace ecommerce has no active endpoints even though the backend Deployment cart-backend has running pods.
Fix the Service selector so traffic routes to the backend pods on port 80.

---

### Task 4: Fix Deployment ImagePullBackOff due to Invalid Tag [EASY] (2 pts)
- **ID:** `TR-004`
- **Context:** `k3d-cka`
- **Namespace:** `warehouse`

#### Description
Deployment `inventory-svc` in namespace `warehouse` is failing with `ImagePullBackOff` due to a mistyped image tag.
Fix the deployment image to use `nginx:1.25.4-alpine` so all replicas start successfully.

---

### Task 5: Fix Ingress Path Routing and Backend Service Mapping [MEDIUM] (3 pts)
- **ID:** `TR-006`
- **Context:** `k3d-cka`
- **Namespace:** `gateway-ns`

#### Description
Ingress `api-gateway` in namespace `gateway-ns` is misconfigured with wrong backend service names and port mappings.
Ensure requests to path `/orders` route to service `orders-svc:80` and `/users` route to `users-svc:80`.

---

### Task 6: Fix PVC Stuck in Pending due to Invalid StorageClass [MEDIUM] (3 pts)
- **ID:** `TR-007`
- **Context:** `k3d-cka`
- **Namespace:** `data-ops`

#### Description
PVC data-claim in namespace data-ops is stuck in Pending because it specifies a non-existent StorageClass fast-nvme-ssd.
Update the PVC configuration or provision the correct StorageClass using standard local storage so data-claim becomes Bound.

---

### Task 7: Clear Invalid Taint and Uncordon Worker Node [MEDIUM] (3 pts)
- **ID:** `TR-008`
- **Context:** `k3d-cka`
- **Namespace:** `default`

#### Description
Worker node is tainted with `maintenance=true:NoSchedule` and cordoned, preventing workloads in namespace `production-apps` from scheduling.
Remove the taint, uncordon all worker nodes, and ensure the deployment `mission-critical` has all replicas Running.

---

### Task 8: Fix Unsatisfiable NodeSelector on Worker Pod [MEDIUM] (3 pts)
- **ID:** `TR-009`
- **Context:** `k3d-cka`
- **Namespace:** `analytics`

#### Description
Pod `analytics-worker` in namespace `analytics` is stuck in `Pending` because its `nodeSelector` requires `disk=nvme-fast`, which does not exist on any node.
Fix the pod or label a worker node with `disk=nvme-fast` so the pod gets scheduled and reaches `1/1 Running`.

---

### Task 9: Clear Stuck Finalizer on Deleting Resource [EASY] (2 pts)
- **ID:** `TR-010`
- **Context:** `k3d-cka`
- **Namespace:** `legacy-services`

#### Description
ConfigMap `legacy-vault` in namespace `legacy-services` is stuck in `Terminating` state due to a blocking custom finalizer `company.org/backup-protection`.
Remove the finalizer so the resource successfully deletes.

---

### Task 10: Fix RBAC Permission Denied (403) for Application ServiceAccount [MEDIUM] (3 pts)
- **ID:** `TR-012`
- **Context:** `k3d-cka`
- **Namespace:** `fintech`

#### Description
ServiceAccount `vault-reader` in namespace `fintech` receives 403 Forbidden when attempting to read Secrets in its namespace.
Create or update a Role `secret-reader` and bind it to `vault-reader` granting `get, list` on `secrets`.

---

### Task 11: Create Multi-Container Pod with Logging Sidecar [MEDIUM] (3 pts)
- **ID:** `WL-001`
- **Context:** `k3d-cka`
- **Namespace:** `app-logging`

#### Description
Create a Pod named order-processor in namespace app-logging with two containers sharing an emptyDir volume mounted at /var/log:
1. Main container app: image busybox:1.36, writing date timestamps to /var/log/app.log every 2 seconds.
2. Sidecar container log-agent: image busybox:1.36, streaming /var/log/app.log to stdout.

---

### Task 12: Configure InitContainer Dependency Gate on Frontend Pod [EASY] (2 pts)
- **ID:** `WL-002`
- **Context:** `k3d-cka`
- **Namespace:** `frontend-ui`

#### Description
Create a Pod named `web-app` in namespace `frontend-ui` with an `initContainer` named `wait-for-db` using image `busybox:1.36` that checks for database availability (`sh -c 'until nc -z -w 2 db-service 3306; do sleep 1; done'`).
The main container `web` should run `nginx:alpine` on port 80.

---

### Task 13: Configure Deployment RollingUpdate Strategy Parameters [MEDIUM] (3 pts)
- **ID:** `WL-003`
- **Context:** `k3d-cka`
- **Namespace:** `order-services`

#### Description
Configure Deployment `payment-api` in namespace `order-services` with 4 replicas (image: `nginx:1.25`) and a RollingUpdate strategy specifying `maxSurge: 1` and `maxUnavailable: 0`.

---

### Task 14: Create PersistentVolume and Bind to PersistentVolumeClaim [EASY] (2 pts)
- **ID:** `ST-001`
- **Context:** `k3d-cka`
- **Namespace:** `data-storage`

#### Description
In namespace `data-storage`:
1. Create a PersistentVolume named `app-pv` with capacity `2Gi`, accessMode `ReadWriteOnce`, hostPath `/mnt/data/app`, and storageClassName `manual`.
2. Create a PersistentVolumeClaim named `app-pvc` in namespace `data-storage` requesting `2Gi` with accessMode `ReadWriteOnce` and storageClassName `manual`.

---

### Task 15: Create Dynamic Provisioning StorageClass with Retain Policy [MEDIUM] (3 pts)
- **ID:** `ST-002`
- **Context:** `k3d-cka`
- **Namespace:** `default`

#### Description
Create a StorageClass named `fast-retain` using provisioner `rancher.io/local-path` with `reclaimPolicy: Retain` and `volumeBindingMode: WaitForFirstConsumer`.

---

### Task 16: Configure Ingress Path Routing for Auth and Pay Services [EASY] (2 pts)
- **ID:** `CA-007`
- **Context:** `k3d-cka`
- **Namespace:** `edge-routing`

#### Description
In namespace `edge-routing`, create an Ingress named `app-ingress`:
- Path `/auth` (Prefix) -> service `auth-svc:80`
- Path `/pay` (Prefix) -> service `pay-svc:80`.

---

### Task 17: Configure RBAC ServiceAccount & Role for Deployment Management [EASY] (2 pts)
- **ID:** `SC-001`
- **Context:** `k3d-cka`
- **Namespace:** `billing-app`

#### Description
In namespace billing-app:
1. Create a ServiceAccount named app-deployer.
2. Create a Role named deployment-manager allowing verbs create, get, list, update, delete on resources deployments in API group apps.
3. Create a RoleBinding named deployer-binding binding Role deployment-manager to ServiceAccount app-deployer.

---
