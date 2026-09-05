#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="compute-pool"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Deploy 5 pods with impossible scheduling constraints (unsatisfiable nodeAffinity and hard antiAffinity)
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: worker-alpha
  namespace: $NS
  labels:
    tier: alpha
spec:
  nodeSelector:
    disktype: ssd-nonexistent
  containers:
  - name: app
    image: nginx:stable
    resources:
      requests:
        cpu: "25m"
        memory: "16Mi"
---
apiVersion: v1
kind: Pod
metadata:
  name: worker-beta
  namespace: $NS
  labels:
    tier: beta
spec:
  nodeSelector:
    region: invalid-zone
  containers:
  - name: app
    image: nginx:stable
    resources:
      requests:
        cpu: "25m"
        memory: "16Mi"
---
apiVersion: v1
kind: Pod
metadata:
  name: worker-gamma
  namespace: $NS
  labels:
    tier: gamma
spec:
  nodeSelector:
    environment: staging-legacy
  containers:
  - name: app
    image: nginx:stable
    resources:
      requests:
        cpu: "25m"
        memory: "16Mi"
---
apiVersion: v1
kind: Pod
metadata:
  name: worker-delta
  namespace: $NS
  labels:
    tier: delta
spec:
  nodeSelector:
    hardware: gpu-h100
  containers:
  - name: app
    image: nginx:stable
    resources:
      requests:
        cpu: "25m"
        memory: "16Mi"
---
apiVersion: v1
kind: Pod
metadata:
  name: worker-epsilon
  namespace: $NS
  labels:
    tier: epsilon
spec:
  nodeSelector:
    rack: rack-99
  containers:
  - name: app
    image: nginx:stable
    resources:
      requests:
        cpu: "25m"
        memory: "16Mi"
EOF
