#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="maintenance-ops"

# Ensure worker node is schedulable initially
kubectl --context "$CTX" uncordon k3d-dev-agent-0 2>/dev/null || true

kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Deploy workload running on worker node
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: batch-worker
  namespace: $NS
spec:
  replicas: 2
  selector:
    matchLabels:
      app: batch-worker
  template:
    metadata:
      labels:
        app: batch-worker
    spec:
      containers:
      - name: worker
        image: nginx:alpine
        resources:
          requests:
            cpu: "10m"
            memory: "16Mi"
EOF

# Wait for workload to be running
kubectl --context "$CTX" rollout status deployment/batch-worker -n "$NS" --timeout=30s 2>/dev/null || true
