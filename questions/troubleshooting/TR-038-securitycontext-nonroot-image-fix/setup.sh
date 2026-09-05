#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="restricted-runtime"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Pod enforcing runAsNonRoot: true but no runAsUser override — image default user is root → crash
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: alpine-runner
  namespace: $NS
spec:
  securityContext:
    runAsNonRoot: true
  containers:
  - name: runner
    image: alpine:3.18
    command: ["sh", "-c", "id && sleep 3600"]
    resources:
      requests:
        cpu: "50m"
        memory: "32Mi"
EOF
