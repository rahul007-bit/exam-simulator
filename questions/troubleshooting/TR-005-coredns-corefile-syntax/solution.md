# Solution for TR-005
1. Check CoreDNS logs:
```bash
kubectl -n kube-system logs -l k8s-app=kube-dns
```
2. Edit coredns ConfigMap:
```bash
kubectl -n kube-system edit configmap coredns
```
Remove `invalid_broken_plugin_directive`.
3. Restart CoreDNS:
```bash
kubectl -n kube-system rollout restart deployment/coredns
```
