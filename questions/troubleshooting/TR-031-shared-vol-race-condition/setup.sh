#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="log-collector"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Multi-container pod where main app writes to /var/log/app before initContainer creates the dir
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: log-processor
  namespace: $NS
spec:
  initContainers:
  - name: setup
    image: busybox:1.35
    command: ["sh", "-c", "sleep 5"]
    volumeMounts:
    - name: log-vol
      mountPath: /shared
  containers:
  - name: app
    image: busybox:1.35
    command: ["sh", "-c", "echo start >> /var/log/app/service.log && sleep 3600"]
    volumeMounts:
    - name: log-vol
      mountPath: /var/log/app
    resources:
      requests:
        cpu: "50m"
        memory: "32Mi"
  - name: logger
    image: busybox:1.35
    command: ["sh", "-c", "tail -f /var/log/app/service.log"]
    volumeMounts:
    - name: log-vol
      mountPath: /var/log/app
    resources:
      requests:
        cpu: "50m"
        memory: "32Mi"
  volumes:
  - name: log-vol
    emptyDir: {}
EOF
