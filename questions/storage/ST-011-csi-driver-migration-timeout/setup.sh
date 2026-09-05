#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="db-storage"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Deploy storage and consumer pod
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: database-pvc
  namespace: $NS
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: local-path
  resources:
    requests:
      storage: 500Mi
---
apiVersion: v1
kind: Pod
metadata:
  name: db-replica
  namespace: $NS
spec:
  containers:
  - name: replica
    image: nginx:stable
    volumeMounts:
    - name: storage
      mountPath: /data
    resources:
      requests:
        cpu: "50m"
        memory: "32Mi"
  volumes:
  - name: storage
    persistentVolumeClaim:
      claimName: database-pvc
EOF
