#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="data-nodes"
NODE=$(kubectl --context "$CTX" get nodes --no-headers | awk 'NR==1{print $1}')
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-disk-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: Immediate
reclaimPolicy: Delete
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: local-disk-pv
spec:
  capacity:
    storage: 10Gi
  accessModes: [ReadWriteOnce]
  persistentVolumeReclaimPolicy: Delete
  storageClassName: local-disk-storage
  local:
    path: /tmp/local-disk
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values: [$NODE]
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: local-disk-pvc
  namespace: $NS
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: local-disk-storage
  resources:
    requests:
      storage: 10Gi
EOF
