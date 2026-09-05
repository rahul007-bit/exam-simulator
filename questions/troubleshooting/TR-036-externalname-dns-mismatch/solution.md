# Solution for TR-036: Fix ExternalName Service FQDN Typo

## Summary
Service `db-external` in `external-routing` points to misspelled hostname `db.prod.internal.corp`. Fix `externalName` target.

## Commands
```bash
# Execute diagnosis and fixes for TR-036
kubectl -n external-routing get all
```
