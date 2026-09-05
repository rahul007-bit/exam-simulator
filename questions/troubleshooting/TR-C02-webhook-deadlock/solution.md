# Solution for TR-C02: Admission Webhook Deadlock

## 1. Diagnosis
Attempting to create any pod produces:
Internal error occurred: failed calling webhook "policy.security.company.io"... connection refused

List webhooks:
```bash
kubectl get validatingwebhookconfigurations
```

## 2. Remediation
Delete or patch the rogue webhook:
```bash
kubectl delete validatingwebhookconfiguration strict-policy-enforcer
```

Deploy the recovery pod:
```bash
kubectl -n cluster-admissions run recovery-app --image=nginx:alpine
```
