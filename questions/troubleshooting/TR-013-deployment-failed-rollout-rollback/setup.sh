#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="shipping"

kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
kubectl --context "$CTX" delete deployment delivery-service -n "$NS" --ignore-not-found 2>/dev/null || true

cat <<EOF | kubectl --context "$CTX" apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: delivery-service
  namespace: shipping
spec:
  replicas: 2
  selector:
    matchLabels:
      app: delivery
  template:
    metadata:
      labels:
        app: delivery
    spec:
      containers:
      - name: web
        image: nginx:alpine
EOF

# Wait for initial revision 1 rollout
kubectl --context "$CTX" -n "$NS" rollout status deployment/delivery-service --timeout=20s 2>/dev/null || true

# Update to broken revision 2
kubectl --context "$CTX" -n "$NS" set image deployment/delivery-service web=nginx:broken-nonexistent-tag-bad
