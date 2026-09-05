# Solution for TR-024: Fix NodePort TargetPort Container Routing

## Summary
NodePort Service `web-np` in `web-services` forwards traffic to wrong port `9090` instead of containerPort `80`.

## Commands
```bash
# Execute diagnosis and fixes for TR-024
kubectl -n web-services get all
```
