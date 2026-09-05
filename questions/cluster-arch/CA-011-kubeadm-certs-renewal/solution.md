# Solution for CA-011: Renew Expiring Control-Plane Certificates

1. Access control plane node `node1`:
```bash
ssh node1
```

2. Check certificate expiration:
```bash
kubeadm certs check-expiration
```
Notice that `apiserver` certificate is expiring soon.

3. Renew all expiring control plane certificates:
```bash
kubeadm certs renew all
```
*(or `kubeadm certs renew apiserver`)*

4. Verify all certificates now have full validity:
```bash
kubeadm certs check-expiration
```

