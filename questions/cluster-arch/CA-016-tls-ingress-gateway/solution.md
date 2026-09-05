# Solution: Configure TLS Ingress Routing

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /tmp/tls.key -out /tmp/tls.crt -subj "/CN=api.internal.company"
kubectl create secret tls gateway-tls-secret -n gateway-mesh --key=/tmp/tls.key --cert=/tmp/tls.crt
```

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mesh-gateway
  namespace: gateway-mesh
spec:
  tls:
  - hosts:
    - api.internal.company
    secretName: gateway-tls-secret
  rules:
  - host: api.internal.company
    http:
      paths:
      - path: /auth
        pathType: Prefix
        backend:
          service:
            name: auth-svc
            port:
              number: 80
      - path: /orders
        pathType: Prefix
        backend:
          service:
            name: order-svc
            port:
              number: 80
```
