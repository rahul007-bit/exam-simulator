#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="external-routing"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# ExternalName service pointing to a typo'd FQDN
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: db-external
  namespace: $NS
spec:
  type: ExternalName
  externalName: db.internal.acme.corp.invalid
EOF
