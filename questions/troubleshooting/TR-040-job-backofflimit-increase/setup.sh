#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="data-import"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Job batch-sync that fails due to bad command with low backoffLimit
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-sync
  namespace: $NS
spec:
  completions: 1
  parallelism: 1
  backoffLimit: 1
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: importer
        image: busybox:1.35
        command: ["sh", "-c", "sync-data-command-not-found"]
        resources:
          requests:
            cpu: "50m"
            memory: "32Mi"
EOF
