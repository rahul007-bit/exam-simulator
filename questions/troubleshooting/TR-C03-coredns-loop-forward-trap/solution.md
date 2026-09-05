# Solution for TR-C03: Chaos: Resolve CoreDNS Loop Forward Plugin Deadlock

## Summary
CoreDNS is in a 100% CPU crashloop because `/etc/resolv.conf` forwards queries back to CoreDNS IP. Break the circular loop.

## Commands
```bash
# Execute diagnosis and fixes for TR-C03
kubectl -n kube-system get all
```
