#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="payments"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Create secret api-keys with valid baseline
kubectl --context "$CTX" create secret generic api-keys \
  -n "$NS" \
  --from-literal=API_KEY="supersecretkeyvalue" \
  --from-literal=DB_PASS="mydbpassword123" \
  --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Patch with raw base64-like strings that look plausible but have invalid trailing whitespace/characters
kubectl --context "$CTX" patch secret api-keys -n "$NS" --type='json' -p='[
  {"op": "replace", "path": "/data/API_KEY", "value": "c3VwZXJzZWNyZXRrZXl2YWx1ZQ=="},
  {"op": "replace", "path": "/data/DB_PASS",  "value": "bXlkYnBhc3N3b3JkMTIz "}
]' 2>/dev/null || true

# Deploy Pod crypto-service referencing api-keys
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: crypto-service
  namespace: $NS
spec:
  containers:
  - name: app
    image: busybox:1.35
    command: ["sh", "-c", "echo key=\$API_KEY && echo pass=\$DB_PASS && sleep 3600"]
    env:
    - name: API_KEY
      valueFrom:
        secretKeyRef:
          name: api-keys
          key: API_KEY
    - name: DB_PASS
      valueFrom:
        secretKeyRef:
          name: api-keys
          key: DB_PASS
    resources:
      requests:
        cpu: "50m"
        memory: "32Mi"
EOF
