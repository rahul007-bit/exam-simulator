# Solution for TR-033: Fix Kube-APIServer Static Pod Manifest Typo

## Summary
Static pod manifest in `/etc/kubernetes/manifests/kube-apiserver.yaml` has invalid flag. Correct the flag.

## Commands
```bash
# Execute diagnosis and fixes for TR-033
kubectl -n default get all
```
