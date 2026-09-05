#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="log-aggregator"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Pod with no ephemeral storage limits — will write unbounded logs
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: log-cruncher
  namespace: $NS
spec:
  containers:
  - name: cruncher
    image: busybox:1.35
    command: ["sh", "-c", "while true; do dd if=/dev/urandom bs=1k count=100 >> /tmp/output.log 2>/dev/null; sleep 1; done"]
    resources:
      requests:
        cpu: "50m"
        memory: "32Mi"
EOF
