# Solution for TR-038: Override Non-Root User ID in Pod SecurityContext

## Summary
Pod `alpine-runner` in `restricted-runtime` has `runAsNonRoot: true` but image runs as user 0 (root). Add `runAsUser: 1000` to SecurityContext.

## Commands
```bash
# Execute diagnosis and fixes for TR-038
kubectl -n restricted-runtime get all
```
