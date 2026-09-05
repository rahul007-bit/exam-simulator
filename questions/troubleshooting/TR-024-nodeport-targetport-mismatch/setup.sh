#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="web-services"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-server
  namespace: $NS
spec:
  replicas: 2
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
  name: web-svc
  namespace: $NS
spec:
  type: NodePort
  selector:
    app: web-server
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30081
EOF
