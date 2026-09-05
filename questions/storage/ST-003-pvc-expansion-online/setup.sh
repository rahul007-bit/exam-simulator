#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="media-store"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Create a StorageClass that allows volume expansion, a PVC, and a Pod consuming it
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: standard-expandable
provisioner: rancher.io/local-path
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-vol
  namespace: $NS
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: standard-expandable
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: data-consumer
  namespace: $NS
spec:
  containers:
  - name: app
    image: busybox:1.35
    command: ["sh", "-c", "sleep 3600"]
    volumeMounts:
    - name: data
      mountPath: /data
    resources:
      requests:
        cpu: "50m"
        memory: "32Mi"
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: data-vol
EOF
