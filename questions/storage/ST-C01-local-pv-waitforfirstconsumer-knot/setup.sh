#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="local-storage"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

NODE=$(kubectl --context "$CTX" get nodes --no-headers | awk 'NR==1{print $1}')

# Local PV pinned to NODE
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: node-storage-class
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: local-volume-pv
spec:
  capacity:
    storage: 5Gi
  accessModes: [ReadWriteOnce]
  storageClassName: node-storage-class
  persistentVolumeReclaimPolicy: Delete
  local:
    path: /tmp/local-volume-pv
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
  name: local-volume-pvc
  namespace: $NS
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: node-storage-class
  resources:
    requests:
      storage: 5Gi
---
# Pod with conflicting nodeSelector targeting non-existent node 'invalid-target-node'
apiVersion: v1
kind: Pod
metadata:
  name: local-worker
  namespace: $NS
spec:
  nodeSelector:
    kubernetes.io/hostname: invalid-target-node
  containers:
  - name: app
    image: nginx:stable
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
      claimName: local-volume-pvc
EOF
