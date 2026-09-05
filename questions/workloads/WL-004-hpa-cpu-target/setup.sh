#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="customer-portal"

kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
kubectl --context "$CTX" delete hpa web-scaler -n "$NS" --ignore-not-found 2>/dev/null || true

cat <<EOF | kubectl --context "$CTX" apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scalable-web
  namespace: customer-portal
spec:
  replicas: 2
  selector:
    matchLabels:
      app: scalable-web
  template:
    metadata:
      labels:
        app: scalable-web
    spec:
      containers:
      - name: web
        image: nginx:alpine
        resources:
          requests:
            cpu: 50m
          limits:
            cpu: 100m
EOF
