# Solution for TR-C05: Chaos: Re-bootstrap Kubelet with New Token After Cert Expiration

## Summary
Worker node kubelet client certificates expired and bootstrap token revoked. Generate new token with kubeadm and re-join worker node.

## Commands
```bash
# Execute diagnosis and fixes for TR-C05
kubectl -n default get all
```
