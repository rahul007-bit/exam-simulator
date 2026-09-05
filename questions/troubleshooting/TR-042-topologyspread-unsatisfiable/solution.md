# Solution: Fix Unsatisfiable TopologySpreadConstraint

### Method 1: Change constraint to ScheduleAnyway
Edit the deployment and change `whenUnsatisfiable: DoNotSchedule` to `whenUnsatisfiable: ScheduleAnyway`:

```bash
kubectl edit deployment zone-spread-app -n geo-distribution
```

Or patch it directly:
```bash
kubectl patch deployment zone-spread-app -n geo-distribution --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/topologySpreadConstraints/0/whenUnsatisfiable", "value": "ScheduleAnyway"}]'
```

### Method 2: Label the cluster nodes with topology zones
```bash
kubectl label nodes --all topology.kubernetes.io/zone=zone-a --overwrite
```

Verify all 4 pods reach `Running`:
```bash
kubectl get pods -n geo-distribution
```
