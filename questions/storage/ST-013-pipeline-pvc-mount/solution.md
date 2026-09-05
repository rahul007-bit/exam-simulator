# Solution: Deploy Data Worker with PersistentVolumeClaim

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pipeline-pvc
  namespace: storage-pipeline
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: pipeline-sc
  resources:
    requests:
      storage: 5Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pipeline-worker
  namespace: storage-pipeline
spec:
  replicas: 1
  selector:
    matchLabels:
      app: pipeline-worker
  template:
    metadata:
      labels:
        app: pipeline-worker
    spec:
      containers:
      - name: worker
        image: nginx:latest
        volumeMounts:
        - name: data
          mountPath: /var/pipeline
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: pipeline-pvc
```
