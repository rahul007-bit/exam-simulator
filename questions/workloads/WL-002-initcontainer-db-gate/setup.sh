#!/usr/bin/env bash
kubectl create namespace frontend-ui --dry-run=client -o yaml | kubectl apply -f -
# Create dummy db-service so initContainer can pass
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: db-service
  namespace: frontend-ui
spec:
  ports:
  - port: 3306
    targetPort: 3306
---
apiVersion: v1
kind: Pod
metadata:
  name: mock-db
  namespace: frontend-ui
  labels:
    app: mock-db
spec:
  containers:
  - name: db
    image: busybox:1.36
    command: ["nc", "-lk", "-p", "3306", "-e", "echo", "ready"]
EOF
kubectl -n frontend-ui patch service db-service --type merge -p '{"spec":{"selector":{"app":"mock-db"}}}' 2>/dev/null || true
