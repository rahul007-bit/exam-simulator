# Solution for TR-010
```bash
kubectl -n legacy-services patch configmap legacy-vault --type json -p '[{"op": "remove", "path": "/metadata/finalizers"}]'
```
