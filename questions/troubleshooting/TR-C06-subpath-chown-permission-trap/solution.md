# Solution for TR-C06: Chaos: Fix Non-Root Pod SubPath Directory Ownership Conflict

## Summary
Non-root container in `database-tier` fails to write to `/data/db` due to root-owned subPath directory on hostPath volume. Fix via initContainer chown.

## Commands
```bash
# Execute diagnosis and fixes for TR-C06
kubectl -n database-tier get all
```
