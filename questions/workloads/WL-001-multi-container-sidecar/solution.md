# Solution for WL-001: Multi-Container Sidecar Pod

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: order-processor
  namespace: app-logging
spec:
  volumes:
  - name: shared-logs
    emptyDir: {}
  containers:
  - name: app
    image: busybox:1.36
    command: ["/bin/sh", "-c", "while true; do date >> /var/log/app.log; sleep 2; done"]
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log
  - name: log-agent
    image: busybox:1.36
    command: ["/bin/sh", "-c", "tail -n+1 -F /var/log/app.log"]
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log
EOF
```
