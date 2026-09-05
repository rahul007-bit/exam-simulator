# Solution: Enforce SecurityContext Restrictions

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hardened-worker
  namespace: secure-pipeline
spec:
  serviceAccountName: pipeline-runner
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
  containers:
  - name: worker
    image: busybox:1.28
    command: ['/bin/sh', '-c', 'sleep 3600']
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
```
