#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="frontend-services"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: web-frontend
  namespace: $NS
spec:
  initContainers:
  - name: wait-for-db
    image: busybox:1.35
    command: ["sh", "-c", "until nslookup postgres-db.frontend-services.svc.cluster.local; do echo waiting; sleep 2; done"]
  containers:
  - name: web
    image: nginx:stable
    ports:
    - containerPort: 80
    resources:
      requests:
        cpu: "50m"
        memory: "32Mi"
EOF
