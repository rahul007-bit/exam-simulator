# Solution for TR-012
```bash
kubectl -n fintech create role secret-reader --verb=get,list --resource=secrets
kubectl -n fintech create rolebinding vault-reader-binding --role=secret-reader --serviceaccount=fintech:vault-reader
```
