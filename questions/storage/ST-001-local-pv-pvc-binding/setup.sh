#!/usr/bin/env bash
kubectl create namespace data-storage --dry-run=client -o yaml | kubectl apply -f -
