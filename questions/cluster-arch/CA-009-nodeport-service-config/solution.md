# Solution for CA-009
```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: web-nodeport
  namespace: external-services
spec:
  type: NodePort
  selector:
    app: web-server
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080
EOF
```
