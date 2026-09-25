#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="payment-processor"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Single-replica deployment with PDB minAvailable: 1 — node drain will hang
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: critical-app
  namespace: $NS
spec:
  replicas: 1
  selector:
    matchLabels:
      app: critical-app
  template:
    metadata:
      labels:
        app: critical-app
    spec:
      containers:
      - name: app
        image: nginx:stable
        resources:
          requests:
            cpu: "50m"
            memory: "32Mi"
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: critical-app-pdb
  namespace: $NS
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: critical-app
EOF
