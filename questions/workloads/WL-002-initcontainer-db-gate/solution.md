# Solution for WL-002
```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: web-app
  namespace: frontend-ui
spec:
  initContainers:
  - name: wait-for-db
    image: busybox:1.36
    command: ["sh", "-c", "until nc -z -w 2 db-service 3306; do sleep 1; done"]
  containers:
  - name: web
    image: nginx:alpine
    ports:
    - containerPort: 80
EOF
```
