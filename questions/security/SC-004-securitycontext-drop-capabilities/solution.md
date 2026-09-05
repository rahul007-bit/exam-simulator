# Solution for SC-004
```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: net-monitor
  namespace: net-tools
spec:
  containers:
  - name: monitor
    image: busybox:1.36
    command: ["sleep", "3600"]
    securityContext:
      capabilities:
        drop:
        - ALL
        add:
        - NET_ADMIN
EOF
```
