#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="order-auth"
kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# ServiceAccount and RBAC so kubectl get pods succeeds once token is mounted
kubectl --context "$CTX" apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: api-reader
  namespace: $NS
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-viewer
  namespace: $NS
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pod-viewer-binding
  namespace: $NS
subjects:
- kind: ServiceAccount
  name: api-reader
  namespace: $NS
roleRef:
  kind: Role
  name: pod-viewer
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: v1
kind: Pod
metadata:
  name: api-client
  namespace: $NS
spec:
  serviceAccountName: api-reader
  automountServiceAccountToken: false
  containers:
  - name: client
    image: bitnami/kubectl:latest
    command: ["sh", "-c", "kubectl get pods -n $NS && sleep 3600"]
    resources:
      requests:
        cpu: "50m"
        memory: "32Mi"
EOF
