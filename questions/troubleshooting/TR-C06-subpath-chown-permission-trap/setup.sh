#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="database-tier"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

kubectl --context "$CTX" apply -f - <<EOF
apiVersion: v1
kind: PersistentVolume
metadata:
  name: db-storage-pv
spec:
  capacity:
    storage: 2Gi
  accessModes: [ReadWriteOnce]
  persistentVolumeReclaimPolicy: Delete
  hostPath:
    path: /tmp/database-tier-data
    type: DirectoryOrCreate
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: db-storage-pvc
  namespace: $NS
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 2Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: db-server
  namespace: $NS
spec:
  securityContext:
    runAsUser: 999
    runAsNonRoot: true
  containers:
  - name: db
    image: busybox:1.35
    command: ["sh", "-c", "echo ready > /data/db/status.txt && sleep 3600"]
    volumeMounts:
    - name: storage
      mountPath: /data/db
      subPath: database
    resources:
      requests:
        cpu: "50m"
        memory: "32Mi"
  volumes:
  - name: storage
    persistentVolumeClaim:
      claimName: db-storage-pvc
EOF
