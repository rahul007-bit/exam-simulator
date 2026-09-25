#!/usr/bin/env bash
kubectl create namespace gateway-mesh --dry-run=client -o yaml | kubectl apply -f -
