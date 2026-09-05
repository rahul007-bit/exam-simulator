# Solution for SC-003
```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: hardened-api
  namespace: sec-apps
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
  volumes:
  - name: cache-vol
    emptyDir: {}
  - name: run-vol
    emptyDir: {}
  - name: tmp-vol
    emptyDir: {}
  containers:
  - name: web
    image: nginx:alpine
    securityContext:
      readOnlyRootFilesystem: true
    volumeMounts:
    - name: cache-vol
      mountPath: /var/cache/nginx
    - name: run-vol
      mountPath: /var/run
    - name: tmp-vol
      mountPath: /tmp
EOF
```
