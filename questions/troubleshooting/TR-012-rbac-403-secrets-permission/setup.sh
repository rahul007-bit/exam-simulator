#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="fintech"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Create ServiceAccount vault-reader
kubectl --context "$CTX" create serviceaccount vault-reader -n "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Secret to read
kubectl --context "$CTX" create secret generic api-key \
  --from-literal=token="fintech-prod-secret-9999" \
  -n "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Pod that tries to read the secret and fails with 403
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: secret-consumer
  namespace: $NS
spec:
  serviceAccountName: vault-reader
  containers:
  - name: consumer
    image: bitnami/kubectl:latest
    command: ["sh", "-c", "kubectl get secrets api-key -n $NS && sleep 3600"]
    resources:
      requests:
        cpu: "50m"
        memory: "32Mi"
EOF
