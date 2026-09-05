# Mock Exam 02 — Globex Systems Outage

- **Session ID:** `session-1787981992`
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

### Task 1: Resolve OOMKilled Container Termination by Adjusting Limits [HARD] (4 pts)
- **ID:** `TR-011`
- **Context:** `k3d-cka`
- **Namespace:** `analytics-worker`

#### Description
Pod `data-processor` in namespace `analytics-worker` continuously crashes with `OOMKilled` because its container memory limit is capped at 32Mi.
Increase the container memory requests to `64Mi` and limits to `256Mi` so the application runs stably.

---

### Task 2: Roll Back Broken Deployment Rollout to Previous Working Revision [MEDIUM] (3 pts)
- **ID:** `TR-013`
- **Context:** `k3d-cka`
- **Namespace:** `shipping`

#### Description
Deployment `delivery-service` in namespace `shipping` is stuck on revision 2 due to a broken container configuration.
Identify the issue and roll back the deployment to the previous working revision (revision 1).

---

### Task 3: Fix Headless Service Missing ClusterIP None [MEDIUM] (3 pts)
- **ID:** `TR-015`
- **Context:** `k3d-cka`
- **Namespace:** `db-cluster`

#### Description
StatefulSet `cassandra-cluster` in `db-cluster` cannot discover peers because service `cassandra-svc` is missing `clusterIP: None`.

---

### Task 4: Resolve PVC ReadWriteMany on ReadWriteOnce Storage [MEDIUM] (3 pts)
- **ID:** `TR-017`
- **Context:** `k3d-cka`
- **Namespace:** `media-platform`

#### Description
PVC `shared-data` in `media-platform` fails to bind because accessMode `ReadWriteMany` is unsupported on local disk.

---

### Task 5: Fix InitContainer DNS Resolution Deadlock [MEDIUM] (3 pts)
- **ID:** `TR-019`
- **Context:** `k3d-cka`
- **Namespace:** `frontend-services`

#### Description
Pod `web-frontend` in `frontend-services` is stuck in Init:0/1 because initContainer is checking wrong DB host FQDN. Fix target service hostname.

---

### Task 6: Fix Base64 Encoding Error in Pod Secret Reference [EASY] (2 pts)
- **ID:** `TR-021`
- **Context:** `k3d-cka`
- **Namespace:** `payments`

#### Description
Pod `crypto-service` in `payments` fails with CreateContainerConfigError due to corrupted base64 secret payload in `api-keys`. Fix secret data.

---

### Task 7: Adjust Namespace CPU Quota to Prevent Throttling [MEDIUM] (3 pts)
- **ID:** `TR-022`
- **Context:** `k3d-cka`
- **Namespace:** `analytics`

#### Description
Deployment `data-sync` in `analytics` cannot create required replicas due to namespace CPU ResourceQuota. Increase quota or optimize pod requests.

---

### Task 8: Fix NodePort TargetPort Container Routing [MEDIUM] (3 pts)
- **ID:** `TR-024`
- **Context:** `k3d-cka`
- **Namespace:** `web-services`

#### Description
NodePort Service `web-np` in `web-services` forwards traffic to wrong port `9090` instead of containerPort `80`.

---

### Task 9: Add CPU Requests to Enable HPA Autoscaling [MEDIUM] (3 pts)
- **ID:** `TR-028`
- **Context:** `k3d-cka`
- **Namespace:** `api-gateway`

#### Description
HPA `api-scaler` in `api-gateway` reports `<unknown>/50%` CPU because deployment `api-server` has no CPU requests defined.

---

### Task 10: Implement HorizontalPodAutoscaler with Target CPU Utilization [MEDIUM] (3 pts)
- **ID:** `WL-004`
- **Context:** `k3d-cka`
- **Namespace:** `customer-portal`

#### Description
Create a HorizontalPodAutoscaler named `web-scaler` in namespace `customer-portal` targeting Deployment `scalable-web` (minReplicas: 2, maxReplicas: 8, targetAverageUtilization: 60%).

---

### Task 11: Create CronJob with History Limits [EASY] (2 pts)
- **ID:** `WL-007`
- **Context:** `k3d-cka`
- **Namespace:** `batch-schedules`

#### Description
Create CronJob `log-cleaner` in `batch-schedules` running `*/15 * * * *` with `successfulJobsHistoryLimit: 3`.

---

### Task 12: Configure Liveness, Readiness, and Startup Probes [MEDIUM] (3 pts)
- **ID:** `WL-010`
- **Context:** `k3d-cka`
- **Namespace:** `health-monitoring`

#### Description
Create Pod `health-app` in `health-monitoring` with startupProbe (period 5s, failureThreshold 10), readinessProbe (httpGet /ready), and livenessProbe (httpGet /health).

---

### Task 13: Expand Existing PVC Storage Capacity Online [MEDIUM] (3 pts)
- **ID:** `ST-003`
- **Context:** `k3d-cka`
- **Namespace:** `media-store`

#### Description
Expand PVC `data-vol` in `media-store` from 1Gi to 3Gi without deleting the attached pod.

---

### Task 14: Mount Secret and ConfigMap as File Volumes in Specific Paths [MEDIUM] (3 pts)
- **ID:** `ST-008`
- **Context:** `k3d-cka`
- **Namespace:** `app-configs`

#### Description
Create Pod `config-reader` in `app-configs` mounting Secret `app-secret` at `/etc/secrets/token` and ConfigMap `app-config` at `/etc/config/app.conf`.

---

### Task 15: Expose Application via NodePort Service on Specific Port [EASY] (2 pts)
- **ID:** `CA-009`
- **Context:** `k3d-cka`
- **Namespace:** `external-services`

#### Description
In namespace `external-services`, expose Deployment `web-server` as a Service named `web-nodeport` of type `NodePort` mapping nodePort `30080` to container port `80`.

---

### Task 16: Enforce Non-Root and Read-Only Root Filesystem SecurityContext [MEDIUM] (3 pts)
- **ID:** `SC-003`
- **Context:** `k3d-cka`
- **Namespace:** `sec-apps`

#### Description
Create a Pod named `hardened-api` in namespace `sec-apps` with image `nginx:alpine` configured with SecurityContext:
- `runAsNonRoot: true`
- `runAsUser: 10001`
- `readOnlyRootFilesystem: true`
Mount an `emptyDir` volume at `/var/cache/nginx`, `/var/run`, and `/tmp` so nginx can start without root access.

---

### Task 17: Repair CoreDNS Corefile Syntax Error [MEDIUM] (3 pts)
- **ID:** `TR-005`
- **Context:** `k3d-cka`
- **Namespace:** `kube-system`

#### Description
CoreDNS pods in `kube-system` are crashlooping due to an invalid configuration directive in the `coredns` ConfigMap.
Inspect CoreDNS logs, fix the invalid block in the `coredns` ConfigMap in namespace `kube-system`, and restart the CoreDNS deployment to restore cluster DNS.

---
