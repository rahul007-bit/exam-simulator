# Solution for TR-015: Fix Headless Service Missing ClusterIP None

## Summary
StatefulSet `cassandra-cluster` in `db-cluster` cannot discover peers because service `cassandra-svc` is missing `clusterIP: None`.

## Commands
```bash
# Execute diagnosis and fixes for TR-015
kubectl -n db-cluster get all
```
