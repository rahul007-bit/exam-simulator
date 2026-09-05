# Solution for TR-002: Missing ConfigMap Key

## 1. Diagnosis
```bash
kubectl -n auth-system describe pod auth-api
```
Notice event: `Error: configmap "auth-config" key "SECRET_KEY" does not exist`.

## 2. Remediation
Update ConfigMap `auth-config` in `auth-system` to include `SECRET_KEY`:
```bash
kubectl -n auth-system patch configmap auth-config --type merge -p '{"data":{"SECRET_KEY":"supersecret123"}}'
```
Delete and recreate or wait for the pod to start:
```bash
kubectl -n auth-system delete pod auth-api --force --grace-period=0
kubectl apply -f manifests/pod.yaml
```
