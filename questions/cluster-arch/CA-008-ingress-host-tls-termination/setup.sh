#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="tls-routing"

kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Pre-create backend Deployment and Service app-svc
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-deploy
  namespace: $NS
spec:
  replicas: 1
  selector:
    matchLabels:
      app: secure-app
  template:
    metadata:
      labels:
        app: secure-app
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: app-svc
  namespace: $NS
spec:
  selector:
    app: secure-app
  ports:
  - port: 80
    targetPort: 80
EOF

# Pre-create TLS secret app-cert
TMP_KEY=$(mktemp)
TMP_CRT=$(mktemp)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$TMP_KEY" -out "$TMP_CRT" \
  -subj "/CN=app.company.org/O=Company" 2>/dev/null || true

kubectl --context "$CTX" -n "$NS" create secret tls app-cert \
  --cert="$TMP_CRT" --key="$TMP_KEY" \
  --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
rm -f "$TMP_KEY" "$TMP_CRT"

# Clean up any existing Ingress
kubectl --context "$CTX" -n "$NS" delete ingress secure-app --ignore-not-found 2>/dev/null || true
