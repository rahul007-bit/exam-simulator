# Solution: Deploy Microservice ClusterIP Backends

```bash
kubectl create namespace gateway-mesh
kubectl create deployment auth-svc-backend -n gateway-mesh --image=nginx:latest --replicas=2 --port=80
kubectl expose deployment auth-svc-backend -n gateway-mesh --name=auth-svc --port=80 --target-port=80
kubectl create deployment order-svc-backend -n gateway-mesh --image=nginx:latest --replicas=2 --port=80
kubectl expose deployment order-svc-backend -n gateway-mesh --name=order-svc --port=80 --target-port=80
```
