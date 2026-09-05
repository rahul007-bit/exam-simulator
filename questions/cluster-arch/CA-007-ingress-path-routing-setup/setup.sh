#!/usr/bin/env bash
kubectl create namespace edge-routing --dry-run=client -o yaml | kubectl apply -f -
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: auth-svc
  namespace: edge-routing
spec:
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: pay-svc
  namespace: edge-routing
spec:
  ports:
  - port: 80
    targetPort: 80
EOF
