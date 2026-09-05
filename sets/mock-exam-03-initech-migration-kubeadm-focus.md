# Mock Exam 03 — Initech Migration (kubeadm Focus)

- **Session ID:** `session-1787982242`
- **Total Tasks:** 17
- **Total Points:** 57 pts
- **Time Limit:** 120 minutes
- **Pass Threshold:** 66%
- **Mode:** `batch`

To grade your progress at any time, run:
```bash
./labctl grade
```

---

### Task 1: Configure PodDisruptionBudget for Web Application [MEDIUM] (3 pts)
- **ID:** `WL-011`
- **Context:** `k3d-cka`
- **Namespace:** `web-application`

#### Description
Create PodDisruptionBudget `web-pdb` in `web-application` targeting selector `app=web-app` with `minAvailable: 2`.

---

### Task 2: Perform etcd Snapshot Backup [MEDIUM] (3 pts)
- **ID:** `CA-001`
- **Context:** `kubeadm-vms`
- **Namespace:** `default`

#### Description
Take an etcd snapshot on the control-plane node using `etcdctl snapshot save` and save to `/opt/backup/etcd-snapshot.db`.

---

### Task 3: Restore Cluster State from etcd Snapshot [HARD] (4 pts)
- **ID:** `CA-002`
- **Context:** `kubeadm-vms`
- **Namespace:** `default`

#### Description
Restore etcd database from `/opt/backup/etcd-snapshot.db` into `/var/lib/etcd-restored` and update static pod manifest.

---

### Task 4: Upgrade Control-Plane Node with kubeadm [HARD] (4 pts)
- **ID:** `CA-003`
- **Context:** `kubeadm-vms`
- **Namespace:** `default`

#### Description
Upgrade the control-plane node components from v1.29 to v1.30 using `kubeadm upgrade apply v1.30.0` and update kubelet.

---

### Task 5: Upgrade Worker Node with kubeadm [MEDIUM] (3 pts)
- **ID:** `CA-004`
- **Context:** `kubeadm-vms`
- **Namespace:** `default`

#### Description
Drain worker node, run `kubeadm upgrade node`, upgrade kubelet/kubectl packages, and uncordon.

---

### Task 6: Safely Drain Worker Node for Maintenance [MEDIUM] (3 pts)
- **ID:** `CA-005`
- **Context:** `k3d-cka`
- **Namespace:** `default`

#### Description
Drain node `k3d-cka-agent-0` safely (ignoring DaemonSets and local data). After verification, uncordon the node.

---

### Task 7: Generate Join Token and Join Worker Node [MEDIUM] (3 pts)
- **ID:** `CA-006`
- **Context:** `kubeadm-vms`
- **Namespace:** `default`

#### Description
Generate a new join token on control plane (`kubeadm token create --print-join-command`) and join new worker node.

---

### Task 8: Renew Expiring Control-Plane Certificates [MEDIUM] (3 pts)
- **ID:** `CA-011`
- **Context:** `kubeadm-vms`
- **Namespace:** `default`

#### Description
Check certificate expiration with `kubeadm certs check-expiration` and renew all certificates using `kubeadm certs renew all`.

---

### Task 9: Deploy Static Pod for Cluster Node Health Monitor [HARD] (4 pts)
- **ID:** `CA-012`
- **Context:** `kubeadm-vms`
- **Namespace:** `default`

#### Description
Create a static pod manifest `/etc/kubernetes/manifests/node-monitor.yaml` running `busybox:1.36` (sleep 3600).

---

### Task 10: Fix Kube-APIServer Static Pod Manifest Typo [HARD] (4 pts)
- **ID:** `TR-033`
- **Context:** `kubeadm-vms`
- **Namespace:** `default`

#### Description
Static pod manifest in `/etc/kubernetes/manifests/kube-apiserver.yaml` has invalid flag. Correct the flag.

---

### Task 11: Align Kubelet Cgroup Driver with Container Runtime [HARD] (4 pts)
- **ID:** `TR-035`
- **Context:** `kubeadm-vms`
- **Namespace:** `node-runtime`

#### Description
Kubelet fails to start due to `cgroupDriver: cgroupfs` while containerd uses `systemd`. Update kubelet config to `systemd`.

---

### Task 12: Clear Corrupted Etcd WAL Lock on Dedicated Control Node [HARD] (4 pts)
- **ID:** `TR-039`
- **Context:** `kubeadm-vms`
- **Namespace:** `controlplane-storage`

#### Description
Etcd static pod fails to start due to lock contention on data dir `/var/lib/etcd`. Clean lock and restore etcd member.

---

### Task 13: Create ClusterRole and Binding for Read-Only Cluster Auditor [MEDIUM] (3 pts)
- **ID:** `SC-002`
- **Context:** `k3d-cka`
- **Namespace:** `default`

#### Description
Create ClusterRole `cluster-auditor` granting `get, list, watch` on `pods, nodes, services` across all namespaces. Bind to user `auditor-user`.

---

### Task 14: Audit and Revoke Overprivileged ClusterRoleBindings [MEDIUM] (3 pts)
- **ID:** `SC-008`
- **Context:** `k3d-cka`
- **Namespace:** `default`

#### Description
Identify overprivileged binding `dev-ops-binding` granting cluster-admin to group `interns` and delete the binding.

---

### Task 15: Create Local PersistentVolume with NodeAffinity [EASY] (2 pts)
- **ID:** `ST-005`
- **Context:** `k3d-cka`
- **Namespace:** `default`

#### Description
Create PersistentVolume `local-node-pv` (5Gi, RWO, storageClassName `local-disk`, hostPath `/opt/data`) with nodeAffinity targeting node `k3d-cka-server-0`.

---

### Task 16: Recover Data from Released PersistentVolume [HARD] (4 pts)
- **ID:** `ST-007`
- **Context:** `k3d-cka`
- **Namespace:** `backup-vault`

#### Description
PV `backup-data-pv` is in `Released` status. Clear the `claimRef` in PV spec so it becomes `Available` for rebinding.

---

### Task 17: Deploy Monitoring DaemonSet on Worker Nodes [MEDIUM] (3 pts)
- **ID:** `WL-006`
- **Context:** `k3d-cka`
- **Namespace:** `node-monitoring`

#### Description
Create DaemonSet `system-monitor` in `node-monitoring` running `nginx:alpine` on all worker nodes.

---
