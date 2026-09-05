# Solution for CA-008: Configure Host-Based Ingress with TLS Termination

Create Ingress `secure-app` in namespace `tls-routing`:

```bash
kubectl apply -n tls-routing -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: secure-app
  namespace: tls-routing
spec:
  tls:
  - hosts:
    - app.company.org
    secretName: app-cert
  rules:
  - host: app.company.org
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-svc
            port:
              number: 80
EOF
```

Verify the Ingress configuration:

```bash
kubectl -n tls-routing describe ingress secure-app
```
