# Solution: Provision Persistent Storage for Data Pipeline

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: pipeline-sc
provisioner: rancher.io/local-path
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pipeline-pv
spec:
  capacity:
    storage: 5Gi
  accessModes:
    - ReadWriteOnce
  storageClassName: pipeline-sc
  hostPath:
    path: /tmp/pipeline-data
```
