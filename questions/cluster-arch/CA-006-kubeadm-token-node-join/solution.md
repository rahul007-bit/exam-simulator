# Solution for CA-006: Generate Join Token and Join Worker Node

1. Connect to control plane node `node1`:
```bash
ssh node1
kubeadm token create --print-join-command
```

2. Connect to worker node `node3` and execute the printed join command as root:
```bash
ssh node3
kubeadm join 192.168.50.169:6443 --token <token> --discovery-token-ca-cert-hash sha256:<hash>
```

3. From `node1`, verify that `node3` has joined the cluster and transitioned to `Ready`:
```bash
kubectl get nodes
```
