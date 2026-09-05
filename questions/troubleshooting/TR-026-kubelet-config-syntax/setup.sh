#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="node-diagnostics"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Deploy diagnostic verification pod
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: node-verifier
  namespace: $NS
spec:
  containers:
  - name: verifier
    image: nginx:stable
    resources:
      requests:
        cpu: "50m"
        memory: "32Mi"
EOF
