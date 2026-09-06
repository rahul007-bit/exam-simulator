echo "=== Resetting node1 (192.168.50.169) ==="
ssh -o StrictHostKeyChecking=no root@192.168.50.169 "kubeadm reset -f 2>/dev/null; systemctl stop kubelet crio 2>/dev/null; rm -rf /etc/kubernetes /var/lib/kubelet /var/lib/etcd /etc/cni/net.d; crictl rm -f \$(crictl ps -aq) 2>/dev/null || true; crictl rmi --all 2>/dev/null || true"

echo "=== Resetting node2 (192.168.50.188) ==="
ssh -o StrictHostKeyChecking=no root@192.168.50.188 "kubeadm reset -f 2>/dev/null; systemctl stop kubelet crio 2>/dev/null; rm -rf /etc/kubernetes /var/lib/kubelet /var/lib/etcd /etc/cni/net.d; crictl rm -f \$(crictl ps -aq) 2>/dev/null || true; crictl rmi --all 2>/dev/null || true"

echo "=== Resetting node3 (192.168.50.170) ==="
ssh -o StrictHostKeyChecking=no root@192.168.50.170 "kubeadm reset -f 2>/dev/null; systemctl stop kubelet crio 2>/dev/null; rm -rf /etc/kubernetes /var/lib/kubelet /var/lib/etcd /etc/cni/net.d; crictl rm -f \$(crictl ps -aq) 2>/dev/null || true; crictl rmi --all 2>/dev/null || true"

echo "=== Cleaning 10.8.0.15 (Docker, k3d, disk logs) ==="
k3d cluster delete --all 2>/dev/null || true
docker stop \$(docker ps -aq) 2>/dev/null || true
docker rm -f \$(docker ps -aq) 2>/dev/null || true
docker system prune -a --volumes -f
rm -f /var/log/syslog.1 /var/log/*.1 /var/log/*.gz
journalctl --vacuum-time=1d

echo "=== Final Status on 10.8.0.15 ==="
df -h /
free -h
