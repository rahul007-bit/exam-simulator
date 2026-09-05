# Solution for TR-016: Fix Non-Root SubPath Volume Permission Denied

## Summary
Pod `api-app` in `api-backend` crashes because non-root user cannot write to volume subPath `/data/cache`. Fix permissions or volume mounts.

## Commands
```bash
# Execute diagnosis and fixes for TR-016
kubectl -n api-backend get all
```
