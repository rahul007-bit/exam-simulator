# Solution for TR-011
```bash
kubectl -n analytics-worker delete pod data-processor --force --grace-period=0
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: data-processor
  namespace: analytics-worker
spec:
  containers:
  - name: processor
    image: busybox:1.36
    command: ["sleep", "3600"]
    resources:
      requests:
        memory: 64Mi
      limits:
        memory: 256Mi
EOF
```
