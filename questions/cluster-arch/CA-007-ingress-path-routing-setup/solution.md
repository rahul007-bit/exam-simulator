# Solution for CA-007
```bash
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  namespace: edge-routing
spec:
  rules:
  - http:
      paths:
      - path: /auth
        pathType: Prefix
        backend:
          service:
            name: auth-svc
            port:
              number: 80
      - path: /pay
        pathType: Prefix
        backend:
          service:
            name: pay-svc
            port:
              number: 80
EOF
```
