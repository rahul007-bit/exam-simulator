# Solution for TR-003: Service Selector Mismatch

## 1. Diagnosis
```bash
kubectl -n ecommerce get endpoints cart-svc
kubectl -n ecommerce get pods --show-labels
```
The pods have labels `app=cart-app,tier=backend`, but `cart-svc` selects `app=shopping-cart`.

## 2. Remediation
```bash
kubectl -n ecommerce patch service cart-svc --type merge -p '{"spec":{"selector":{"app":"cart-app","tier":"backend"}}}'
```
