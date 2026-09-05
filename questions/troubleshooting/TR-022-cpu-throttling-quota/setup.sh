#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="analytics"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: $NS
spec:
  hard:
    requests.cpu: "200m"
    requests.memory: "256Mi"
    limits.cpu: "400m"
    limits.memory: "512Mi"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-sync
  namespace: $NS
spec:
  replicas: 2
  selector:
    matchLabels:
      app: data-sync
  template:
    metadata:
      labels:
        app: data-sync
    spec:
      containers:
      - name: sync
        image: nginx:stable
        resources:
          requests:
            cpu: "200m"
            memory: "64Mi"
          limits:
            cpu: "300m"
            memory: "128Mi"
EOF
