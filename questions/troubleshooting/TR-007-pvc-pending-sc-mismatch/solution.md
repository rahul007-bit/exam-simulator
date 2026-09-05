# Solution for TR-007: PVC Pending Invalid StorageClass

## 1. Diagnosis
```bash
kubectl -n data-ops describe pvc data-claim
```
Notice: `storageclass.storage.k8s.io "fast-nvme-ssd" not found`.

## 2. Remediation
Create a matching PersistentVolume for the requested StorageClass so the PVC binds immediately:
```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolume
metadata:
  name: data-pv
spec:
  storageClassName: fast-nvme-ssd
  capacity:
    storage: 1Gi
  accessModes:
  - ReadWriteOnce
  hostPath:
    path: /tmp/data-pv
EOF
```

Verify binding:
```bash
kubectl -n data-ops get pvc data-claim
```
