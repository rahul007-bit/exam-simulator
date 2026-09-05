# Solution for TR-028: Add CPU Requests to Enable HPA Autoscaling

## Summary
HPA `api-scaler` in `api-gateway` reports `<unknown>/50%` CPU because deployment `api-server` has no CPU requests defined.

## Commands
```bash
# Execute diagnosis and fixes for TR-028
kubectl -n api-gateway get all
```
