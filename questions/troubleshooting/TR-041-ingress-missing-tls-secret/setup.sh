#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="tls-ingress"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Prepare TLS certificates in /tmp/tls
mkdir -p /tmp/tls
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /tmp/tls/tls.key -out /tmp/tls/tls.crt \
  -subj "/CN=secure.company.internal" 2>/dev/null || true

# Deploy app, service, and ingress expecting secret 'web-tls-cert'
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-web
  namespace: $NS
spec:
  replicas: 1
  selector:
    matchLabels:
      app: secure-web
  template:
    metadata:
      labels:
        app: secure-web
    spec:
      containers:
      - name: web
        image: nginx:stable
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: "50m"
            memory: "32Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: secure-web
  namespace: $NS
spec:
  selector:
    app: secure-web
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: secure-web
  namespace: $NS
spec:
  tls:
  - hosts:
    - secure.company.internal
    secretName: web-tls-cert
  rules:
  - host: secure.company.internal
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: secure-web
            port:
              number: 80
EOF
