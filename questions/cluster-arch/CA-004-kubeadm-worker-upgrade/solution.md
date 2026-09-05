# Solution for CA-004: Upgrade Worker Node with kubeadm

### Step 1: Drain the worker node from the control-plane node
```bash
kubectl cordon node2
kubectl drain node2 --ignore-daemonsets --force --delete-emptydir-data
```

### Step 2: SSH to the worker node and upgrade kubeadm
```bash
ssh node2
apt-get update && apt-get install -y --allow-change-held-packages kubeadm
```

### Step 3: Run kubeadm upgrade on the worker
```bash
sudo kubeadm upgrade node
```

### Step 4: Upgrade kubelet and restart service
```bash
apt-get install -y --allow-change-held-packages kubelet kubectl
sudo systemctl daemon-reload
sudo systemctl restart kubelet
exit
```

### Step 5: Uncordon the worker node
```bash
kubectl uncordon node2
kubectl get nodes
```
