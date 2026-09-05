# Solution for SC-001: RBAC Deployment Manager

```bash
kubectl -n billing-app create serviceaccount app-deployer
kubectl -n billing-app create role deployment-manager --verb=create,get,list,update,delete --resource=deployments.apps
kubectl -n billing-app create rolebinding deployer-binding --role=deployment-manager --serviceaccount=billing-app:app-deployer

# Verify
kubectl -n billing-app auth can-i create deployments.apps --as=system:serviceaccount:billing-app:app-deployer
```
