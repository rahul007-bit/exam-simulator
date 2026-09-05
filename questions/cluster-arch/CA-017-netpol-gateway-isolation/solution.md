# Solution: NetworkPolicy Ingress Restrictions

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: protect-order-svc
  namespace: gateway-mesh
spec:
  podSelector:
    matchLabels:
      app: order-svc
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: auth-svc
    ports:
    - protocol: TCP
      port: 80
```
