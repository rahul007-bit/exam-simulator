#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="backup-vault"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Create a PV and PVC, bind them, then delete the PVC — leaves PV in Released state
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: v1
kind: PersistentVolume
metadata:
  name: backup-data-pv
spec:
  capacity:
    storage: 10Gi
  accessModes: [ReadWriteOnce]
  persistentVolumeReclaimPolicy: Retain
  hostPath:
    path: /tmp/backup-data
    type: DirectoryOrCreate
EOF

kubectl --context "$CTX" apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: backup-volume-claim
  namespace: $NS
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 10Gi
  volumeName: backup-data-pv
EOF

# Wait for binding, then delete PVC to put PV into Released state
sleep 5
kubectl --context "$CTX" delete pvc backup-volume-claim -n "$NS" --ignore-not-found
