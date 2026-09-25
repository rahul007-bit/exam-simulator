#!/usr/bin/env bash
kubectl create namespace secure-pipeline --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap app-config -n secure-pipeline --from-literal=key=val --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic app-secret -n secure-pipeline --from-literal=pass=secret --dry-run=client -o yaml | kubectl apply -f -
