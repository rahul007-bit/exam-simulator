#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="batch-schedules"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# CronJob with concurrencyPolicy: Forbid — deploy with a stuck running Job to simulate deadlock
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: data-export
  namespace: $NS
spec:
  schedule: "*/1 * * * *"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: Never
          containers:
          - name: export
            image: busybox:1.35
            command: ["sh", "-c", "sleep 180"]
            resources:
              requests:
                cpu: "50m"
                memory: "32Mi"
EOF

# Manually trigger a Job that runs indefinitely to block the CronJob
kubectl --context "$CTX" create job data-export-init \
  --from=cronjob/data-export \
  -n "$NS" 2>/dev/null || true
