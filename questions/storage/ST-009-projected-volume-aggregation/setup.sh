#!/usr/bin/env bash
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
kubectl --context "$CTX" create namespace app-credentials --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -
