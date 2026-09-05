#!/usr/bin/env bash
# TR-014 setup: Deploy workload onto a cordoned node scenario
set -e

CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="prod-workers"

kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

WORKER=$(kubectl --context "$CTX" get nodes --no-headers | grep -v control-plane | awk '{print $1}' | head -1)
if [ -n "$WORKER" ]; then
  kubectl --context "$CTX" cordon "$WORKER"
fi

kubectl --context "$CTX" apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker-pool
  namespace: $NS
spec:
  replicas: 3
  selector:
    matchLabels:
      app: worker-pool
  template:
    metadata:
      labels:
        app: worker-pool
    spec:
      containers:
      - name: worker
        image: nginx:stable
        resources:
          requests:
            cpu: "50m"
            memory: "32Mi"
EOF
