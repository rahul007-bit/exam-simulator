#!/usr/bin/env bash
kubectl create namespace billing-app --dry-run=client -o yaml | kubectl apply -f -
