#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="web-tier"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-redundant
  namespace: $NS
spec:
  replicas: 4
  selector:
    matchLabels:
      app: web-redundant
  template:
    metadata:
      labels:
        app: web-redundant
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values: [web-redundant]
            topologyKey: kubernetes.io/hostname
      containers:
      - name: web
        image: nginx:stable
        resources:
          requests:
            cpu: "50m"
            memory: "32Mi"
EOF
