#!/usr/bin/env bash
kubectl create namespace legacy-services --dry-run=client -o yaml | kubectl apply -f -
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: legacy-vault
  namespace: legacy-services
  finalizers:
  - company.org/backup-protection
data:
  key: value
EOF
kubectl -n legacy-services delete configmap legacy-vault --wait=false 2>/dev/null || true
