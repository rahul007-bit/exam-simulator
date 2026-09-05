#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="task-scheduler"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Create low-priority priorityclass and saturation deployment
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: low-priority
value: 1000
globalDefault: false
description: "Low priority background workload"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: background-filler
  namespace: $NS
spec:
  replicas: 4
  selector:
    matchLabels:
      app: filler
  template:
    metadata:
      labels:
        app: filler
    spec:
      priorityClassName: low-priority
      containers:
      - name: filler
        image: nginx:stable
        resources:
          requests:
            cpu: "100m"
            memory: "64Mi"
EOF
