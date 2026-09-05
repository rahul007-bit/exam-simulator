#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="monitoring-ns"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Find control-plane node and ensure it is tainted with node-role.kubernetes.io/control-plane:NoSchedule
CP_NODE=$(kubectl --context "$CTX" get nodes -l node-role.kubernetes.io/control-plane --no-headers -o custom-columns=":metadata.name" 2>/dev/null | head -n 1)
if [ -z "$CP_NODE" ]; then
  CP_NODE=$(kubectl --context "$CTX" get nodes --no-headers -o custom-columns=":metadata.name" | grep 'server' | head -n 1)
fi
if [ -n "$CP_NODE" ]; then
  kubectl --context "$CTX" taint nodes "$CP_NODE" node-role.kubernetes.io/control-plane:NoSchedule --overwrite 2>/dev/null || true
fi

# Ensure all worker nodes are uncordoned
kubectl --context "$CTX" get nodes --no-headers -o custom-columns=":metadata.name" | grep -v 'server' | xargs -r kubectl --context "$CTX" uncordon 2>/dev/null || true

# Deploy DaemonSet without control-plane toleration — won't schedule on tainted control-plane nodes
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: $NS
spec:
  selector:
    matchLabels:
      app: node-exporter
  template:
    metadata:
      labels:
        app: node-exporter
    spec:
      containers:
      - name: node-exporter
        image: prom/node-exporter:v1.6.1
        ports:
        - containerPort: 9100
        resources:
          requests:
            cpu: "50m"
            memory: "32Mi"
EOF
