# Solution: Configure ServiceAccount and Scoped Configuration Role

```bash
kubectl create namespace secure-pipeline
kubectl create sa pipeline-runner -n secure-pipeline
kubectl create role config-manager -n secure-pipeline --verb=get,list,watch --resource=configmaps,secrets
kubectl create rolebinding pipeline-config-binding -n secure-pipeline --role=config-manager --serviceaccount=secure-pipeline:pipeline-runner
```
