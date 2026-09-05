#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-kubeadm-vms}"

# Inject an invalid mode into kube-proxy configmap to trigger crashloop
kubectl --context "$CTX" -n kube-system get cm kube-proxy -o yaml | \
  sed 's/mode: ""/mode: "invalid_mode"/' | \
  kubectl --context "$CTX" apply -f - 2>/dev/null || true

# Restart kube-proxy pods so they reload config and crashloop
kubectl --context "$CTX" -n kube-system delete pods -l k8s-app=kube-proxy 2>/dev/null || true
