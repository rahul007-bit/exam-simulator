# Solution for TR-001: Fix CrashLoopBackOff on Checkout Service

## 1. Diagnosis
Check pod events and container logs:
```bash
kubectl -n checkout-prod get pods
kubectl -n checkout-prod logs -l app=checkout-api
kubectl -n checkout-prod describe pod -l app=checkout-api
```
Notice:
1. Container fails executing `invalid_start_cmd`.
2. Readiness probe is checking port `8080` instead of port `80`.

## 2. Remediation
Edit the deployment:
```bash
kubectl -n checkout-prod edit deployment checkout-api
```
Remove the broken `command: [...]` line or replace it with `command: ["nginx", "-g", "daemon off;"]`, and change `readinessProbe.httpGet.port` from `8080` to `80`.

## 3. Verification
```bash
kubectl -n checkout-prod get pods
# Ensure pod shows 1/1 Running
```
