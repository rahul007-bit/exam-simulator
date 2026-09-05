#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="api-backend"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: v1
kind: PersistentVolume
metadata:
  name: app-volume-pv
spec:
  capacity:
    storage: 1Gi
  accessModes: [ReadWriteOnce]
  persistentVolumeReclaimPolicy: Delete
  hostPath:
    path: /tmp/api-backend-logs
    type: DirectoryOrCreate
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-volume-pvc
  namespace: $NS
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: api-app
  namespace: $NS
spec:
  securityContext:
    runAsUser: 1000
    runAsNonRoot: true
  containers:
  - name: api
    image: busybox:1.35
    command: ["sh", "-c", "echo 'start' > /data/logs/app.log && sleep 3600"]
    volumeMounts:
    - name: shared-vol
      mountPath: /data/logs
      subPath: logs
    resources:
      requests:
        cpu: "50m"
        memory: "32Mi"
  volumes:
  - name: shared-vol
    persistentVolumeClaim:
      claimName: app-volume-pvc
EOF
