# Medium Exam 04 — Full Curriculum

- **Session ID:** `session-1788624711`
- **Total Tasks:** 14
- **Total Points:** 46 pts
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

### Task 1: Deploy Static Pod for Cluster Node Health Monitor [HARD] (4 pts) (CURRENT ACTIVE TASK)
- **ID:** `CA-012`
- **Context:** `kubeadm-vms`
- **Namespace:** `default`

#### Description
Create a static pod manifest `/etc/kubernetes/manifests/node-monitor.yaml` running `busybox:1.36` (sleep 3600).

---

### Task 2: Add Missing IP SAN to API Server Certificate [HARD] (4 pts)
- **ID:** `CA-014`
- **Context:** `kubeadm-vms`
- **Namespace:** `default`

#### Description
API server is unreachable via external load balancer IP `10.0.0.50`. Update kubeadm config to include IP in SANs and regenerate apiserver cert.

---

### Task 3: Chaos: Recover Single-Node etcd from Quorum Loss [CRAZY] (6 pts)
- **ID:** `CA-C01`
- **Context:** `kubeadm-vms`
- **Namespace:** `default`

#### Description
2 of 3 etcd nodes permanently died causing quorum loss. Re-bootstrap cluster from single survivor using `--force-new-cluster`.

---

### Task 4: Create TLS Secret and Mount into Nginx Pod [EASY] (2 pts)
- **ID:** `SC-005`
- **Context:** `k3d-cka`
- **Namespace:** `secure-ingress`

#### Description
In namespace `secure-ingress`, create a TLS secret `app-tls-secret` (cert/key) and mount into pod `tls-web` at `/etc/tls`.

---

### Task 5: Configure ServiceAccount Token Projection with Audience [HARD] (4 pts)
- **ID:** `SC-007`
- **Context:** `k3d-cka`
- **Namespace:** `auth-tokens`

#### Description
Create Pod `vault-agent` in `auth-tokens` with projected volume `vault-token` specifying `serviceAccountToken` with audience `vault.company.io` and expiration `3600`.

---

### Task 6: Restrict RBAC Access to Specific ConfigMap and Secret Names [HARD] (4 pts)
- **ID:** `SC-013`
- **Context:** `k3d-cka`
- **Namespace:** `secure-pipeline`

#### Description
In namespace secure-pipeline:
1. Create ConfigMap app-config and Secret app-secret.
2. Update Role config-manager so that permissions get, list, watch apply ONLY to ConfigMap app-config and Secret app-secret using resourceNames.

---

### Task 7: Create CronJob with History Limits [EASY] (2 pts)
- **ID:** `WL-007`
- **Context:** `k3d-cka`
- **Namespace:** `batch-schedules`

#### Description
Create CronJob `log-cleaner` in `batch-schedules` running `*/15 * * * *` with `successfulJobsHistoryLimit: 3`.

---

### Task 8: Configure Pod Lifecycle preStop Hook [MEDIUM] (3 pts)
- **ID:** `WL-013`
- **Context:** `k3d-cka`
- **Namespace:** `graceful-shutdown`

#### Description
Create Pod `graceful-app` in `graceful-shutdown` with a `preStop` exec hook running `['/bin/sh', '-c', 'sleep 15; nginx -s quit']`.

---

### Task 9: Create PersistentVolume and Bind to PersistentVolumeClaim [EASY] (2 pts)
- **ID:** `ST-001`
- **Context:** `k3d-cka`
- **Namespace:** `data-storage`

#### Description
In namespace `data-storage`:
1. Create a PersistentVolume named `app-pv` with capacity `2Gi`, accessMode `ReadWriteOnce`, hostPath `/mnt/data/app`, and storageClassName `manual`.
2. Create a PersistentVolumeClaim named `app-pvc` in namespace `data-storage` requesting `2Gi` with accessMode `ReadWriteOnce` and storageClassName `manual`.

---

### Task 10: Provision Persistent Storage for Data Pipeline [MEDIUM] (3 pts)
- **ID:** `ST-012`
- **Context:** `k3d-cka`
- **Namespace:** `storage-pipeline`

#### Description
In namespace storage-pipeline:
1. Create a StorageClass named pipeline-sc using provisioner rancher.io/local-path, reclaimPolicy: Retain, and volumeBindingMode: WaitForFirstConsumer.
2. Create a PersistentVolume named pipeline-pv with capacity 5Gi, accessMode ReadWriteOnce, hostPath: /tmp/pipeline-data, and storageClassName: pipeline-sc.

---

### Task 11: Fix Kubelet Service Configuration Error on Node [MEDIUM] (3 pts)
- **ID:** `TR-026`
- **Context:** `k3d-cka`
- **Namespace:** `node-diagnostics`

#### Description
Kubelet configuration on node contains syntax error. Identify and fix config.

---

### Task 12: Add CPU Requests to Enable HPA Autoscaling [MEDIUM] (3 pts)
- **ID:** `TR-028`
- **Context:** `k3d-cka`
- **Namespace:** `api-gateway`

#### Description
HPA `api-scaler` in `api-gateway` reports `<unknown>/50%` CPU because deployment `api-server` has no CPU requests defined.

---

### Task 13: Resolve CronJob Concurrency Deadlock [MEDIUM] (3 pts)
- **ID:** `TR-030`
- **Context:** `k3d-cka`
- **Namespace:** `batch-schedules`

#### Description
CronJob `daily-report` in `batch-schedules` is blocked due to `concurrencyPolicy: Forbid` and a hung job. Delete active job and update policy to Replace.

---

### Task 14: Enable automountServiceAccountToken on Pod [MEDIUM] (3 pts)
- **ID:** `TR-032`
- **Context:** `k3d-cka`
- **Namespace:** `order-auth`

#### Description
Pod `api-client` in namespace `order-auth` cannot contact the Kubernetes API because ServiceAccount token automounting was disabled on the pod specification.

Investigate pod `api-client` in namespace `order-auth`.
Configure token automounting so that the ServiceAccount token is automatically mounted into the pod, recreate or update the pod, and verify that `api-client` reaches `1/1 Running`.

---
