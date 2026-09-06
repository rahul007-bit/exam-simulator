#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="policy-enforcement"

kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Label the namespace so the webhook selector can match it
kubectl --context "$CTX" label namespace "$NS" policy-enforcement=enabled --overwrite

# Deploy the broken MutatingWebhookConfiguration scoped ONLY to policy-enforcement namespace.
# Using namespaceSelector so it doesn't affect other namespaces (no cross-question interference).
# failurePolicy: Fail + dead backend = all pod creation in policy-enforcement is blocked.
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: admission-hook
webhooks:
- name: hook.corporate.internal
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Fail
  namespaceSelector:
    matchLabels:
      policy-enforcement: "enabled"
  rules:
  - operations: ["CREATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  clientConfig:
    service:
      name: admission-svc
      namespace: $NS
      port: 443
    caBundle: ""
EOF

# Verify the isolation: try to create a pod in policy-enforcement — should fail
echo "Verifying webhook blocks pods in $NS..."
if kubectl --context "$CTX" run probe-test --image=nginx:stable -n "$NS" --dry-run=server 2>&1 | grep -q "failed calling webhook\|connection refused\|no endpoints"; then
  echo "Confirmed: webhook is blocking pod creation in $NS"
else
  echo "Warning: webhook may not be active yet (may need a moment to register)"
fi
