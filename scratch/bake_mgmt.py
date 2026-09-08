import subprocess, sys, time

B = "/usr/bin/incus"
SOCK = ["-r", "unix:///var/run/containerd/containerd.sock"]
K8S = "v1.30.0"

def run(args, timeout=3600, label=""):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    print(f"{label} rc={r.returncode} {r.stderr.strip()[:120]}", flush=True)
    return r

def incus_exec(script, timeout=3600, label="exec"):
    r = subprocess.run([B, "exec", "k8s-base", "--", "bash", "-c", script],
                       capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    print(f"{label}: rc={r.returncode} {r.stderr.strip()[:200]}", flush=True)
    if r.returncode != 0:
        print(f"FATAL: {label} failed — aborting bake", flush=True)
        sys.exit(2)
    return r

print("=== [1/5] apt packages ===", flush=True)
incus_exec("export DEBIAN_FRONTEND=noninteractive; apt-get update -y && apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release containerd bash-completion vim git jq net-tools iproute2 ethtool", 1800, "apt-base")

print("=== [2/5] containerd + k8s repo ===", flush=True)
incus_exec("mkdir -p /etc/containerd && containerd config default | sed 's/SystemdCgroup = false/SystemdCgroup = true/' > /etc/containerd/config.toml && systemctl restart containerd && systemctl enable containerd", 300, "containerd")
incus_exec("mkdir -p -m 755 /etc/apt/keyrings && curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg && echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' > /etc/apt/sources.list.d/kubernetes.list && apt-get update -y", 600, "k8s-repo")
incus_exec("export DEBIAN_FRONTEND=noninteractive; apt-get install -y kubelet kubeadm kubectl && apt-mark hold kubelet kubeadm kubectl && systemctl enable kubelet", 900, "k8s-packages")

print("=== [3/5] pre-pull control-plane images ===", flush=True)
IMAGES = [
    f"registry.k8s.io/kube-apiserver:{K8S}",
    f"registry.k8s.io/kube-controller-manager:{K8S}",
    f"registry.k8s.io/kube-scheduler:{K8S}",
    f"registry.k8s.io/kube-proxy:{K8S}",
    "registry.k8s.io/etcd:3.5.12-0",
    "registry.k8s.io/coredns/coredns:v1.11.1",
    "registry.k8s.io/pause:3.9",
]
for ref in IMAGES:
    for attempt in (1, 2, 3):
        r = subprocess.run([B, "exec", "k8s-base", "--", "crictl", *SOCK, "pull", ref],
                           capture_output=True, text=True, timeout=1800, stdin=subprocess.DEVNULL)
        print(f"{ref}: attempt {attempt} rc={r.returncode}", flush=True)
        if r.returncode == 0:
            break

print("=== [4/5] verify ===", flush=True)
incus_exec("crictl " + " ".join(SOCK) + " images", 120, "images-list")
incus_exec("which kubeadm kubelet kubectl containerd", 60, "binaries")

print("=== [5/5] publish ===", flush=True)
run([B, "stop", "k8s-base"], 180, "stop")
run([B, "image", "delete", "k8s-golden"], 60, "del-old-image")
r = subprocess.run([B, "publish", "k8s-base", "--alias", "k8s-golden"],
                   capture_output=True, text=True, timeout=1800, stdin=subprocess.DEVNULL)
print("publish:", r.returncode, r.stdout.strip()[-50:], r.stderr.strip()[:100], flush=True)
run([B, "delete", "-f", "k8s-base"], 120, "cleanup")
print("=== BAKE COMPLETE ===", flush=True)
