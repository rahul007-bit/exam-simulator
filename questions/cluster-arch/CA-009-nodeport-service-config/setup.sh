#!/usr/bin/env bash
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
kubectl --context "$CTX" create namespace external-services --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
cat <<EOF | kubectl --context "$CTX" apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-server
  namespace: external-services
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web-server
  template:
    metadata:
      labels:
        app: web-server
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
EOF
