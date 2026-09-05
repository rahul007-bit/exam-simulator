# Easy Set 04 — Speed Run

- **Session ID:** `session-1788620858`
- **Total Tasks:** 17
- **Total Points:** 34 pts
- **Time Limit:** 60 minutes
- **Pass Threshold:** 66%
- **Mode:** `sequential`

To navigate tasks during the exam:
- Run `examctl task` to view the current active task
- Run `examctl next` to deploy and advance to the next task
- Run `examctl prev` to return to the previous task
- Run `examctl jump <num>` to jump directly to a task
- Run `examctl status` to view overall exam progress

---

### Task 1: Create Batch Job with Parallelism and Completions [EASY] (2 pts) (PASSED)
- **ID:** `WL-009`
- **Context:** `k3d-cka`
- **Namespace:** `batch-processing`

#### Description
Create Job `batch-processor` in `batch-processing` with `completions: 5`, `parallelism: 2`, and `backoffLimit: 4`.

---

### Task 2: Create CronJob with History Limits [EASY] (2 pts) (PASSED)
- **ID:** `WL-007`
- **Context:** `k3d-cka`
- **Namespace:** `batch-schedules`

#### Description
Create CronJob `log-cleaner` in `batch-schedules` running `*/15 * * * *` with `successfulJobsHistoryLimit: 3`.

---

### Task 3: Configure InitContainer Dependency Gate on Frontend Pod [EASY] (2 pts) (PASSED)
- **ID:** `WL-002`
- **Context:** `k3d-cka`
- **Namespace:** `frontend-ui`

#### Description
Create a Pod named `web-app` in namespace `frontend-ui` with an `initContainer` named `wait-for-db` using image `busybox:1.36` that checks for database availability (`sh -c 'until nc -z -w 2 db-service 3306; do sleep 1; done'`).
The main container `web` should run `nginx:alpine` on port 80.

---

### Task 4: Fix Base64 Encoding Error in Pod Secret Reference [MEDIUM] (2 pts) (PASSED)
- **ID:** `TR-021`
- **Context:** `k3d-cka`
- **Namespace:** `payments`

#### Description
Pod `crypto-service` in namespace `payments` fails to start and remains stuck in `CreateContainerConfigError`.

Investigate the pod and its referenced secret `api-keys`. Fix the issue with the secret so that the pod `crypto-service` starts successfully and reaches `1/1 Running`.

---

### Task 5: Clear Stuck Finalizer on Deleting Resource [EASY] (2 pts) (PASSED)
- **ID:** `TR-010`
- **Context:** `k3d-cka`
- **Namespace:** `legacy-services`

#### Description
ConfigMap `legacy-vault` in namespace `legacy-services` is stuck in `Terminating` state due to a blocking custom finalizer `company.org/backup-protection`.
Remove the finalizer so the resource successfully deletes.

---

### Task 6: Fix Deployment ImagePullBackOff due to Invalid Tag [EASY] (2 pts) (PASSED)
- **ID:** `TR-004`
- **Context:** `k3d-cka`
- **Namespace:** `warehouse`

#### Description
Deployment `inventory-svc` in namespace `warehouse` is failing with `ImagePullBackOff` due to a mistyped image tag.
Fix the deployment image to use `nginx:1.25.4-alpine` so all replicas start successfully.

---

### Task 7: Fix Empty Endpoints on Cart Service [EASY] (2 pts) (CURRENT ACTIVE TASK)
- **ID:** `TR-003`
- **Context:** `k3d-cka`
- **Namespace:** `ecommerce`

#### Description
Service cart-svc in namespace ecommerce has no active endpoints even though the backend Deployment cart-backend has running pods.
Fix the Service selector so traffic routes to the backend pods on port 80.

---

### Task 8: Fix Pod CreateContainerConfigError on Missing ConfigMap Key [EASY] (2 pts) (PASSED)
- **ID:** `TR-002`
- **Context:** `k3d-cka`
- **Namespace:** `auth-system`

#### Description
Pod `auth-api` in namespace `auth-system` is stuck in `CreateContainerConfigError` and fails to start.

1. Investigate the pod events and container definition to identify why the container environment cannot be initialized.
2. Update the ConfigMap `auth-config` in namespace `auth-system` to resolve the missing key reference.
3. Verify that pod `auth-api` starts successfully and reaches `1/1 Running`.

---

### Task 9: Configure Projected Volume Aggregating Secret and DownwardAPI [EASY] (2 pts) (PASSED)
- **ID:** `ST-009`
- **Context:** `k3d-cka`
- **Namespace:** `app-credentials`

#### Description
Create Pod `projected-pod` in `app-credentials` with a projected volume combining Secret `vault-creds` and downwardAPI (pod name and namespace).

---

### Task 10: Create Local PersistentVolume with NodeAffinity [EASY] (2 pts) (PASSED)
- **ID:** `ST-005`
- **Context:** `k3d-cka`
- **Namespace:** `default`

#### Description
Create PersistentVolume `local-node-pv` (5Gi, RWO, storageClassName `local-disk`, hostPath `/opt/data`) with nodeAffinity targeting node `k3d-cka-server-0`.

---

### Task 11: Create PersistentVolume and Bind to PersistentVolumeClaim [EASY] (2 pts) (PASSED)
- **ID:** `ST-001`
- **Context:** `k3d-cka`
- **Namespace:** `data-storage`

#### Description
In namespace `data-storage`:
1. Create a PersistentVolume named `app-pv` with capacity `2Gi`, accessMode `ReadWriteOnce`, hostPath `/mnt/data/app`, and storageClassName `manual`.
2. Create a PersistentVolumeClaim named `app-pvc` in namespace `data-storage` requesting `2Gi` with accessMode `ReadWriteOnce` and storageClassName `manual`.

---

### Task 12: Configure ServiceAccount and Scoped Configuration Role [EASY] (2 pts) (PASSED)
- **ID:** `SC-010`
- **Context:** `k3d-cka`
- **Namespace:** `secure-pipeline`

#### Description
In namespace secure-pipeline:
1. Create a ServiceAccount named pipeline-runner.
2. Create a Role named config-manager allowing verbs get, list, watch on resources configmaps and secrets.
3. Create a RoleBinding named pipeline-config-binding binding Role config-manager to ServiceAccount pipeline-runner.

---

### Task 13: Create TLS Secret and Mount into Nginx Pod [EASY] (2 pts) (PASSED)
- **ID:** `SC-005`
- **Context:** `k3d-cka`
- **Namespace:** `secure-ingress`

#### Description
In namespace `secure-ingress`, create a TLS secret `app-tls-secret` (cert/key) and mount into pod `tls-web` at `/etc/tls`.

---

### Task 14: Configure RBAC ServiceAccount & Role for Deployment Management [EASY] (2 pts) (PASSED)
- **ID:** `SC-001`
- **Context:** `k3d-cka`
- **Namespace:** `billing-app`

#### Description
In namespace billing-app:
1. Create a ServiceAccount named app-deployer.
2. Create a Role named deployment-manager allowing verbs create, get, list, update, delete on resources deployments in API group apps.
3. Create a RoleBinding named deployer-binding binding Role deployment-manager to ServiceAccount app-deployer.

---

### Task 15: Deploy Microservice ClusterIP Backends [EASY] (2 pts) (PASSED)
- **ID:** `CA-015`
- **Context:** `k3d-cka`
- **Namespace:** `gateway-mesh`

#### Description
In namespace gateway-mesh:
1. Create Deployment auth-svc-backend (2 replicas, image: nginx:latest, containerPort: 80, label: app: auth-svc).
2. Create Service auth-svc (ClusterIP, port 80 -> targetPort 80, selector app: auth-svc).
3. Create Deployment order-svc-backend (2 replicas, image: nginx:latest, containerPort: 80, label: app: order-svc).
4. Create Service order-svc (ClusterIP, port 80 -> targetPort 80, selector app: order-svc).

---

### Task 16: Expose Application via NodePort Service on Specific Port [EASY] (2 pts) (PASSED)
- **ID:** `CA-009`
- **Context:** `k3d-cka`
- **Namespace:** `external-services`

#### Description
In namespace `external-services`, expose Deployment `web-server` as a Service named `web-nodeport` of type `NodePort` mapping nodePort `30080` to container port `80`.

---

### Task 17: Configure Ingress Path Routing for Auth and Pay Services [EASY] (2 pts) (PASSED)
- **ID:** `CA-007`
- **Context:** `k3d-cka`
- **Namespace:** `edge-routing`

#### Description
In namespace `edge-routing`, create an Ingress named `app-ingress`:
- Path `/auth` (Prefix) -> service `auth-svc:80`
- Path `/pay` (Prefix) -> service `pay-svc:80`.

---
