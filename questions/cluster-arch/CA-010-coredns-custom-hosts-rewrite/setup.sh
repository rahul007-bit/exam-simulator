#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"

kubectl --context "$CTX" delete configmap coredns-custom -n kube-system --ignore-not-found 2>/dev/null || true
