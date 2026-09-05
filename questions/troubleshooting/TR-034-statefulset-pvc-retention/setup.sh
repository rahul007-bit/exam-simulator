#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="stateful-db"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# StatefulSet cache-node with Retain PVC policy
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: cache-node
  namespace: $NS
spec:
  serviceName: cache-headless
  replicas: 2
  selector:
    matchLabels:
      app: cache-node
  persistentVolumeClaimRetentionPolicy:
    whenDeleted: Retain
    whenScaled: Retain
  template:
    metadata:
      labels:
        app: cache-node
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        volumeMounts:
        - name: data
          mountPath: /data
        resources:
          requests:
            cpu: "50m"
            memory: "32Mi"
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ReadWriteOnce]
      resources:
        requests:
          storage: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: cache-headless
  namespace: $NS
spec:
  clusterIP: None
  selector:
    app: cache-node
  ports:
  - port: 6379
EOF
