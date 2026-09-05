# Solution for TR-C07: Chaos: Clear Stale Iptables Drop Rule Blocking Service CIDR

## Symptom
- In-cluster pods cannot reach any ClusterIP service: DNS lookups against `kube-dns` time out, `curl` to service IPs hangs.
- The API server, node conditions, and pod health all look normal — the cluster appears healthy via `kubectl get`.

## Diagnosis
All service traffic dies *before* DNAT, which points at the node packet filter rather than kube-proxy config. Inspect the node's iptables from inside the k3d node container:

```bash
# Find the server node container (k3d)
docker ps --format '{{.Names}}' | grep server

# Search all tables for rogue rules targeting the service CIDR
docker exec k3d-cka-server-0 iptables-save | grep -i 10.43

# You will find (mangle table):
# -A PREROUTING -d 10.43.0.0/16 -j DROP
```

On a real kubeadm node you would run the same inspection directly on the host with SSH.

## Fix
Remove the rogue rule from the node:

```bash
docker exec k3d-cka-server-0 iptables -t mangle -D PREROUTING -d 10.43.0.0/16 -j DROP
```

(On kubeadm: `ssh <node> iptables -t mangle -D PREROUTING -d <service-cidr> -j DROP`.)

## Verify
```bash
# In-cluster DNS via the ClusterIP must succeed again
kubectl -n kube-system exec deploy/local-path-provisioner -- nslookup kubernetes.default.svc.cluster.local 10.43.0.10

# Deploy a quick probe if needed
kubectl run nettest --image=busybox:1.28 --restart=Never --rm -it -- nslookup kubernetes.default
```

## Why the cluster looked healthy
The rule sits in `mangle PREROUTING`, so it only swallows packets still addressed to a ClusterIP (10.43.0.0/16), before DNAT can rewrite them. API server traffic, kubelet probes, and node health checks never target the service CIDR, so every `kubectl get` view stayed green while real service connectivity was dead.
