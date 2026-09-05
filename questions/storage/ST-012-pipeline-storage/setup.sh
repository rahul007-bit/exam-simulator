#!/usr/bin/env bash
kubectl create namespace storage-pipeline --dry-run=client -o yaml | kubectl apply -f -
