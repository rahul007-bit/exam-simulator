# Solution for WL-004
```bash
kubectl -n customer-portal autoscale deployment scalable-web --name=web-scaler --cpu-percent=60 --min=2 --max=8
```
