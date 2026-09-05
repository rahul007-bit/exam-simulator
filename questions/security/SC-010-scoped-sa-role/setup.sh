#!/usr/bin/env bash
kubectl create namespace secure-pipeline --dry-run=client -o yaml | kubectl apply -f -
