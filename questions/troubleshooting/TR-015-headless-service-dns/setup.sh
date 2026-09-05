#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="db-cluster"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: cassandra-svc
  namespace: $NS
spec:
  selector:
    app: cassandra
  ports:
  - port: 9042
    targetPort: 9042
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: cassandra-cluster
  namespace: $NS
spec:
  serviceName: cassandra-svc
  replicas: 2
  selector:
    matchLabels:
      app: cassandra
  template:
    metadata:
      labels:
        app: cassandra
    spec:
      containers:
      - name: cassandra
        image: nginx:stable
        ports:
        - containerPort: 9042
        resources:
          requests:
            cpu: "50m"
            memory: "32Mi"
EOF
