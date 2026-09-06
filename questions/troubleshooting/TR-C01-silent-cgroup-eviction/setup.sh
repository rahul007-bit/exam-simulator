#!/usr/bin/env bash
kubectl create namespace cgroup-limits --dry-run=client -o yaml | kubectl apply -f -
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: strict-quota
  namespace: cgroup-limits
spec:
  hard:
    requests.cpu: "500m"
    requests.memory: 512Mi
    limits.cpu: "1"
    limits.memory: 1Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: critical-api
  namespace: cgroup-limits
spec:
  replicas: 3
  selector:
    matchLabels:
      app: critical-api
  template:
    metadata:
      labels:
        app: critical-api
    spec:
      containers:
      - name: api
        image: nginx:alpine
        resources:
          requests:
            cpu: "800m" # Exceeds 500m quota
            memory: 800Mi
          limits:
            cpu: "2"
            memory: 2Gi
EOF
