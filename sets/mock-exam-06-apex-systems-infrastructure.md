# Mock Exam 06 — Apex Systems Infrastructure

- **Session ID:** `session-1787980443`
- **Total Tasks:** 17
- **Total Points:** 49 pts
- **Time Limit:** 120 minutes
- **Pass Threshold:** 66%
- **Mode:** `batch`

To grade your progress at any time, run:
```bash
./labctl grade
```

---

### Task 1: Provision Persistent Storage for Data Pipeline [MEDIUM] (3 pts)
- **ID:** `ST-012`
- **Context:** `k3d-cka`
- **Namespace:** `storage-pipeline`

#### Description
In namespace storage-pipeline:
1. Create a StorageClass named pipeline-sc using provisioner rancher.io/local-path, reclaimPolicy: Retain, and volumeBindingMode: WaitForFirstConsumer.
2. Create a PersistentVolume named pipeline-pv with capacity 5Gi, accessMode ReadWriteOnce, hostPath: /tmp/pipeline-data, and storageClassName: pipeline-sc.

---

### Task 2: Deploy Data Worker with PersistentVolumeClaim [MEDIUM] (3 pts)
- **ID:** `ST-013`
- **Context:** `k3d-cka`
- **Namespace:** `storage-pipeline`

#### Description
In namespace storage-pipeline:
1. Create a PersistentVolumeClaim named pipeline-pvc requesting 5Gi with storageClassName: pipeline-sc and accessModes: [ReadWriteOnce].
2. Create a Deployment named pipeline-worker (1 replica, image: nginx:latest) mounting pipeline-pvc at /var/pipeline.

---

### Task 3: Decommission Worker and Retain Underlying Storage Volume [MEDIUM] (3 pts)
- **ID:** `ST-014`
- **Context:** `k3d-cka`
- **Namespace:** `storage-pipeline`

#### Description
In namespace storage-pipeline:
1. Delete deployment pipeline-worker.
2. Delete PersistentVolumeClaim pipeline-pvc.
3. Verify that PersistentVolume pipeline-pv transitions to Released status and is preserved without deletion.

---

### Task 4: Deploy Microservice ClusterIP Backends [EASY] (2 pts)
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

### Task 5: Configure TLS Ingress Routing for Internal API Gateway [MEDIUM] (3 pts)
- **ID:** `CA-016`
- **Context:** `k3d-cka`
- **Namespace:** `gateway-mesh`

#### Description
In namespace gateway-mesh:
1. Generate a self-signed TLS certificate and create a Secret named gateway-tls-secret (type: kubernetes.io/tls).
2. Create an Ingress named mesh-gateway with host api.internal.company:
   - Path /auth (Prefix) -> auth-svc:80
   - Path /orders (Prefix) -> order-svc:80
   - TLS secret gateway-tls-secret for host api.internal.company.

---

### Task 6: Enforce NetworkPolicy Ingress Restrictions on Backend Service [HARD] (4 pts)
- **ID:** `CA-017`
- **Context:** `k3d-cka`
- **Namespace:** `gateway-mesh`

#### Description
In namespace gateway-mesh:
1. Create a NetworkPolicy named protect-order-svc targeting pods with label app: order-svc.
2. Allow Ingress traffic to order-svc pods on port 80 ONLY from pods with label app: auth-svc.
3. Ensure all other ingress traffic to order-svc is restricted.

---

### Task 7: Configure ServiceAccount and Scoped Configuration Role [EASY] (2 pts)
- **ID:** `SC-010`
- **Context:** `k3d-cka`
- **Namespace:** `secure-pipeline`

#### Description
In namespace secure-pipeline:
1. Create a ServiceAccount named pipeline-runner.
2. Create a Role named config-manager allowing verbs get, list, watch on resources configmaps and secrets.
3. Create a RoleBinding named pipeline-config-binding binding Role config-manager to ServiceAccount pipeline-runner.

---

### Task 8: Enforce SecurityContext Restrictions on Pipeline Workload [MEDIUM] (3 pts)
- **ID:** `SC-012`
- **Context:** `k3d-cka`
- **Namespace:** `secure-pipeline`

#### Description
In namespace secure-pipeline:
1. Create a Pod named hardened-worker using image busybox:1.28, command ['/bin/sh', '-c', 'sleep 3600'], and serviceAccountName: pipeline-runner.
2. Configure securityContext:
   - runAsNonRoot: true
   - runAsUser: 10001
   - allowPrivilegeEscalation: false
   - readOnlyRootFilesystem: true
   - capabilities.drop: ['ALL']

---

### Task 9: Restrict RBAC Access to Specific ConfigMap and Secret Names [HARD] (4 pts)
- **ID:** `SC-013`
- **Context:** `k3d-cka`
- **Namespace:** `secure-pipeline`

#### Description
In namespace secure-pipeline:
1. Create ConfigMap app-config and Secret app-secret.
2. Update Role config-manager so that permissions get, list, watch apply ONLY to ConfigMap app-config and Secret app-secret using resourceNames.

---

### Task 10: Fix CrashLoopBackOff on Checkout Service [MEDIUM] (3 pts)
- **ID:** `TR-001`
- **Context:** `k3d-cka`
- **Namespace:** `checkout-prod`

#### Description
Pod checkout-api in namespace checkout-prod is failing with CrashLoopBackOff.
Diagnose the failure from logs and pod events, fix the deployment configuration, and ensure the pod achieves 1/1 Running and passes readiness probes.

---

### Task 11: Fix Empty Endpoints on Cart Service [EASY] (2 pts)
- **ID:** `TR-003`
- **Context:** `k3d-cka`
- **Namespace:** `ecommerce`

#### Description
Service cart-svc in namespace ecommerce has no active endpoints even though the backend Deployment cart-backend has running pods.
Fix the Service selector so traffic routes to the backend pods on port 80.

---

### Task 12: Fix Ingress Path Routing and Backend Service Mapping [MEDIUM] (3 pts)
- **ID:** `TR-006`
- **Context:** `k3d-cka`
- **Namespace:** `gateway-ns`

#### Description
Ingress `api-gateway` in namespace `gateway-ns` is misconfigured with wrong backend service names and port mappings.
Ensure requests to path `/orders` route to service `orders-svc:80` and `/users` route to `users-svc:80`.

---

### Task 13: Create Multi-Container Pod with Logging Sidecar [MEDIUM] (3 pts)
- **ID:** `WL-001`
- **Context:** `k3d-cka`
- **Namespace:** `app-logging`

#### Description
Create a Pod named order-processor in namespace app-logging with two containers sharing an emptyDir volume mounted at /var/log:
1. Main container app: image busybox:1.36, writing date timestamps to /var/log/app.log every 2 seconds.
2. Sidecar container log-agent: image busybox:1.36, streaming /var/log/app.log to stdout.

---

### Task 14: Configure Deployment RollingUpdate Strategy Parameters [MEDIUM] (3 pts)
- **ID:** `WL-003`
- **Context:** `k3d-cka`
- **Namespace:** `order-services`

#### Description
Configure Deployment `payment-api` in namespace `order-services` with 4 replicas (image: `nginx:1.25`) and a RollingUpdate strategy specifying `maxSurge: 1` and `maxUnavailable: 0`.

---

### Task 15: Configure RBAC ServiceAccount & Role for Deployment Management [EASY] (2 pts)
- **ID:** `SC-001`
- **Context:** `k3d-cka`
- **Namespace:** `billing-app`

#### Description
In namespace billing-app:
1. Create a ServiceAccount named app-deployer.
2. Create a Role named deployment-manager allowing verbs create, get, list, update, delete on resources deployments in API group apps.
3. Create a RoleBinding named deployer-binding binding Role deployment-manager to ServiceAccount app-deployer.

---

### Task 16: Create Dynamic Provisioning StorageClass with Retain Policy [MEDIUM] (3 pts)
- **ID:** `ST-002`
- **Context:** `k3d-cka`
- **Namespace:** `default`

#### Description
Create a StorageClass named `fast-retain` using provisioner `rancher.io/local-path` with `reclaimPolicy: Retain` and `volumeBindingMode: WaitForFirstConsumer`.

---

### Task 17: Clear Invalid Taint and Uncordon Worker Node [MEDIUM] (3 pts)
- **ID:** `TR-008`
- **Context:** `k3d-cka`
- **Namespace:** `default`

#### Description
Worker node is tainted with `maintenance=true:NoSchedule` and cordoned, preventing workloads in namespace `production-apps` from scheduling.
Remove the taint, uncordon all worker nodes, and ensure the deployment `mission-critical` has all replicas Running.

---
