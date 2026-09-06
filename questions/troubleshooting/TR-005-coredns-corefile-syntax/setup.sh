#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"

# Backup current CoreDNS ConfigMap
kubectl --context "$CTX" -n kube-system get configmap coredns -o yaml > /tmp/coredns-backup.yaml 2>/dev/null || true

# Inject syntax error (invalid plugin directive)
kubectl --context "$CTX" apply -f - <<'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health
        invalid_broken_plugin_directive
        ready
        kubernetes cluster.local in-addr.arpa ip6.arpa {
            pods insecure
            fallthrough in-addr.arpa ip6.arpa
        }
        forward . /etc/resolv.conf
        cache 30
        loop
        reload
        loadbalance
    }
EOF

kubectl --context "$CTX" -n kube-system rollout restart deployment/coredns 2>/dev/null || true
