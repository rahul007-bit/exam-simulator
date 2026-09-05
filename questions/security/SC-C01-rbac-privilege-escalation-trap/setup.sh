#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="operator-core"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

kubectl --context "$CTX" create serviceaccount operator-sa -n "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Create role that lacks escalation permission for operator
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: operator-role
  namespace: $NS
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch", "create"]
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["roles", "rolebindings"]
  verbs: ["create", "get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: operator-binding
  namespace: $NS
subjects:
- kind: ServiceAccount
  name: operator-sa
  namespace: $NS
roleRef:
  kind: Role
  name: operator-role
  apiGroup: rbac.authorization.k8s.io
EOF
