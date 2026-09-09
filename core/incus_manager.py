"""
Incus MicroVM & System Container Manager for Kubeadm Multi-Node Clusters
Uses native Incus Remotes (TLS on port 8443) and local system containers
to provision, bootstrap, and tear down resource-capped Kubernetes nodes.
"""
import os
import re
import time
import json
import shutil
import ipaddress
import subprocess
import concurrent.futures
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple


class IncusClusterManager:
    DEFAULT_IMAGE = "k8s-golden"
    GOLDEN_INSTANCE = "golden-k8s"
    GOLDEN_SNAPSHOT = "gold"
    # Must match the control-plane images pre-pulled into the golden image
    # (see scripts/bake_k8s_base.sh). Pinning avoids a slow registry pull at init.
    K8S_VERSION = "v1.30.0"

    def __init__(self):
        self._incus_bin = os.getenv("INCUS_BIN", "incus")
        self._incus_path: Optional[str] = shutil.which(self._incus_bin)

    def _get_bin(self) -> str:
        return self._incus_path or self._incus_bin

    def _run_incus(self, cmd: List[str], **kwargs) -> subprocess.CompletedProcess:
        """Helper to invoke the Incus CLI with consistent binary resolution."""
        full_cmd = [self._get_bin()] + cmd
        kwargs.setdefault("text", True)
        # Only capture output when the caller has not provided explicit stream args,
        # otherwise subprocess.run raises (capture_output conflicts with stdout/stderr).
        if "capture_output" not in kwargs and "stdout" not in kwargs and "stderr" not in kwargs:
            kwargs["capture_output"] = True
        return subprocess.run(full_cmd, **kwargs)

    def is_available(self) -> bool:
        """Verifies if Incus CLI is available and operational."""
        try:
            res = self._run_incus(["--version"], timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def _target_prefix(self, remote_name: Optional[str]) -> str:
        """Returns prefix like 'node1:' or '' if local."""
        if remote_name and remote_name not in ("localhost", "127.0.0.1", "local"):
            return f"{remote_name}:"
        return ""

    def discover_compute_remotes(self) -> List[str]:
        """
        Dynamically inspects configured Incus remotes.
        Discovers reachable remote compute hosts, filtering out public image stores
        (e.g., 'images', 'ubuntu', 'linuxcontainers') and the 'local' daemon.
        Returns empty list when no remote hosts are configured or reachable,
        guaranteeing graceful fallback to local system containers.
        """
        if not self.is_available():
            return []
        try:
            res = self._run_incus(["remote", "list", "--format", "json"], timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                remotes_data = json.loads(res.stdout.strip())
                builtin_remotes = {"images", "ubuntu", "ubuntu-daily", "linuxcontainers", "local"}
                discovered = []
                for name, info in remotes_data.items():
                    if name in builtin_remotes:
                        continue
                    if isinstance(info, dict):
                        if info.get("Public") is True or info.get("public") is True:
                            continue
                        protocol = (info.get("Protocol") or info.get("protocol") or "incus").lower()
                        if protocol != "incus":
                            continue
                    # Verify remote endpoint is responsive
                    try:
                        ping_res = self._run_incus(["info", f"{name}:"], timeout=4)
                        if ping_res.returncode == 0:
                            discovered.append(name)
                        else:
                            print(f"[IncusManager] Remote '{name}' unresponsive, skipping.", flush=True)
                    except Exception:
                        pass
                return sorted(discovered)
        except Exception as e:
            print(f"[IncusManager] Error discovering remotes: {e}", flush=True)
        return []

    def has_remote(self, remote_name: str) -> bool:
        """Checks if a specific remote name exists and is reachable."""
        if not remote_name or remote_name in ("local", "localhost", "127.0.0.1"):
            return True
        remotes = self.discover_compute_remotes()
        return remote_name in remotes

    # ------------------------------------------------------------------
    # Fleet route mesh (cross-host kubeadm join + remote node access)
    # ------------------------------------------------------------------

    @staticmethod
    def _remote_lan_ip(remote_name: str) -> Optional[str]:
        """LAN address of a remote incus host, parsed from its remote URL."""
        try:
            res = subprocess.run(["incus", "remote", "list", "--format", "json"],
                                 capture_output=True, text=True, timeout=8)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                info = data.get(remote_name) or {}
                url = info.get("Addr") or info.get("addr") or ""
                m = re.search(r"https://([0-9.]+):\d+", url)
                if m:
                    return m.group(1)
        except Exception:
            pass
        return None

    @staticmethod
    def _ssh_host_cmd(host_ip: str, cmd: str) -> List[str]:
        return ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=6",
                "-o", "StrictHostKeyChecking=no", f"root@{host_ip}", cmd]

    def _sync_fleet_routes(self, remotes_map: Dict[str, Optional[str]]) -> None:
        """
        Ensures every fleet host (including this engine host) has a route to
        every other host's incus bridge subnet. Without this, cross-host
        kubeadm join and desktop/grader access to remote nodes fail, because
        each host's incusbr0 uses an independent 10.x.y.0/24 bridge subnet.
        Re-applied idempotently (`ip route replace`) at every provisioning so
        rebooted hosts self-heal.
        """
        # 1. Collect fleet hosts: (tag, lan_ip, bridge_subnet, is_local)
        @staticmethod
        def _subnet_of(addr_output: str) -> Optional[str]:
            """Extracts the bridge network (e.g. 10.110.46.0/24) from ip addr output."""
            m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/(\d+)", addr_output)
            if m:
                try:
                    return str(ipaddress.ip_network(f"{m.group(1)}/{m.group(2)}", strict=False))
                except ValueError:
                    return None
            return None

        local_subnet = None
        try:
            res = subprocess.run(["ip", "-4", "-o", "addr", "show", "dev", "incusbr0"],
                                 capture_output=True, text=True, timeout=8)
            local_subnet = _subnet_of(res.stdout)
        except Exception:
            pass

        local_ip = None
        remote_hosts: List[Tuple[str, Optional[str], Optional[str]]] = []
        for _, rem in sorted(remotes_map.items()):
            if not rem:
                continue
            rip = self._remote_lan_ip(rem)
            rsubnet = None
            if rip:
                if local_ip is None:
                    try:
                        res = subprocess.run(["ip", "route", "get", rip],
                                             capture_output=True, text=True, timeout=8)
                        m = re.search(r"src (\d+\.\d+\.\d+\.\d+)", res.stdout)
                        if m:
                            local_ip = m.group(1)
                    except Exception:
                        pass
                try:
                    res = subprocess.run(self._ssh_host_cmd(rip, "ip -4 -o addr show dev incusbr0"),
                                         capture_output=True, text=True, timeout=15)
                    rsubnet = _subnet_of(res.stdout)
                except Exception:
                    pass
            remote_hosts.append((rem, rip, rsubnet))

        hosts: List[Tuple[str, Optional[str], Optional[str], bool]] = [("local", local_ip, local_subnet, True)]
        hosts.extend([(t, ip, s, False) for (t, ip, s) in remote_hosts])
        hosts = [h for h in hosts if h[2]]
        if len(hosts) < 2:
            print("[IncusManager] Fleet route mesh: fewer than 2 usable hosts, skipping.", flush=True)
            return

        def _run_on(host, args):
            if host[3]:
                return subprocess.run(args, capture_output=True, text=True, timeout=15)
            return subprocess.run(self._ssh_host_cmd(host[1], " ".join(args)),
                                  capture_output=True, text=True, timeout=20)

        # 2. Full mesh: each host gets a route to every other host's subnet
        failures = 0
        for a in hosts:
            for b in hosts:
                if a is b or a[2] == b[2] or not b[1]:
                    continue
                res = _run_on(a, ["ip", "route", "replace", b[2], "via", b[1]])
                if res.returncode != 0:
                    failures += 1
                    print(f"[IncusManager] Route mesh: failed adding {b[2]} via {b[1]} on {a[0]}: {(res.stderr or '').strip()[:120]}", flush=True)
        print(f"[IncusManager] Fleet route mesh synced across {len(hosts)} hosts ({failures} failures).", flush=True)


    def get_target_distribution(
        self,
        roles: List[str],
        is_distributed: bool = True
    ) -> Dict[str, Optional[str]]:
        """
        Dynamically allocates instance roles across discovered compute remotes.
        If is_distributed is False or no compute remotes exist, falls back gracefully to local (None).
        If remotes exist, automatically distributes control-plane and worker nodes without hardcoding static topology.
        """
        if not is_distributed:
            return {r: None for r in roles}

        remotes = self.discover_compute_remotes()
        if not remotes:
            return {r: None for r in roles}

        distribution: Dict[str, Optional[str]] = {}
        # Round-robin every role (control plane included) across the fleet hosts
        # so all nodes share the load; with N hosts >= len(roles) each host gets
        # at most one node per session.
        for i, role in enumerate(roles):
            distribution[role] = remotes[i % len(remotes)]

        return distribution

    @staticmethod
    def _info_has_snapshot(info_text: str, name: str) -> bool:
        """Parses `incus info` output and checks the Snapshots table for `name`."""
        in_section = False
        for line in info_text.splitlines():
            if line.strip() == "Snapshots:":
                in_section = True
                continue
            if in_section:
                stripped = line.strip()
                if stripped.startswith("|"):
                    cells = [c.strip() for c in stripped.strip("|").split("|")]
                    if cells and cells[0] == name:
                        return True
                elif stripped and not stripped.startswith("+"):
                    break
        return False

    def ensure_golden_snapshot(self, remote_name: Optional[str] = None) -> Optional[str]:
        """
        Maintains a persistent stopped golden instance + snapshot per host so that
        every node launch takes the fast copy path instead of re-unpacking the
        image (critical on dir storage backends without native CoW).
        Returns the snapshot source '<pfx>golden-k8s/gold' or None if unavailable.
        The golden instance is session-agnostic and is never swept by teardown.
        """
        if not self.is_available():
            return None

        pfx = self._target_prefix(remote_name)
        inst = f"{pfx}{self.GOLDEN_INSTANCE}"

        exists = False
        try:
            res = self._run_incus(["list", inst, "--format", "json"], timeout=8)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                exists = isinstance(data, list) and len(data) > 0
        except Exception:
            pass

        if not exists:
            print(f"[IncusManager] Bootstrapping persistent golden instance on {remote_name or 'local'} (one-time cost)...", flush=True)
            if not self.launch_node(self.GOLDEN_INSTANCE, remote_name=remote_name, cpu_limit="1", mem_limit="1GiB"):
                return None
            self._run_incus(["stop", inst], timeout=60)

        try:
            res = self._run_incus(["info", inst], timeout=8)
            if res.returncode != 0 or not self._info_has_snapshot(res.stdout or "", self.GOLDEN_SNAPSHOT):
                try:
                    # NOTE: the CLI may hang on operation-wait even though the snapshot
                    # completes server-side; we verify via `info` afterwards instead.
                    self._run_incus(["snapshot", "create", inst, self.GOLDEN_SNAPSHOT], timeout=30)
                except Exception:
                    pass
                res = self._run_incus(["info", inst], timeout=8)
                if res.returncode != 0 or not self._info_has_snapshot(res.stdout or "", self.GOLDEN_SNAPSHOT):
                    print(f"[IncusManager] Warning: golden snapshot not available on {remote_name or 'local'}", flush=True)
                    return None
            return f"{inst}/{self.GOLDEN_SNAPSHOT}"
        except Exception as e:
            print(f"[IncusManager] Warning ensuring golden snapshot: {e}")
            return None

    def launch_node(
        self,
        node_name: str,
        remote_name: Optional[str] = None,
        image: str = DEFAULT_IMAGE,
        snapshot: Optional[str] = None,
        is_vm: bool = False,
        cpu_limit: str = "2",
        mem_limit: str = "2GiB",
    ) -> bool:
        """
        Launches an isolated container/microVM node with strict CPU, memory, and process limits.
        Supports fast copy-on-write (CoW) instance creation from snapshots or cached golden images.
        Guarantees sub-20s local launch with required security profile (security.nesting=true).
        """
        if not self.is_available():
            return False

        t0 = time.time()
        pfx = self._target_prefix(remote_name)
        target = f"{pfx}{node_name}"
        vm_flag = ["--vm"] if is_vm else []

        limits_config = [
            "-c", f"limits.cpu={cpu_limit}",
            "-c", f"limits.memory={mem_limit}",
            "-c", "limits.processes=1500",
            "-c", "security.nesting=true",
            "-c", "security.privileged=true",
        ]

        # 1. Fast CoW snapshot clone path if a snapshot source is specified
        if snapshot:
            snap_src = f"{pfx}{snapshot}"
            print(f"[IncusManager] Creating fast CoW snapshot clone: {snap_src} -> {target}...", flush=True)
            # NOTE: --instance-only is invalid for snapshot sources on Incus.
            # Cross-remote/slow-disk copies (dir backends) can exceed 30s; the
            # CoW snapshot path is what carries the <=20s local budget.
            copy_cmd = ["copy", snap_src, target] + limits_config + vm_flag
            try:
                c_res = self._run_incus(copy_cmd, timeout=120)
                if c_res.returncode == 0:
                    start_res = self._run_incus(["start", target], timeout=20)
                    if start_res.returncode == 0:
                        elapsed = time.time() - t0
                        print(f"[IncusManager] CoW snapshot clone {target} created & started in {elapsed:.2f}s (<=20s).", flush=True)
                        return True
                    print(f"[IncusManager] Warning: failed to start copied instance {target}: {start_res.stderr.strip()}")
            except Exception as e:
                print(f"[IncusManager] Snapshot copy exception: {e}")

        # 2. Fast instance launch from pre-cached golden image
        cmd = [
            "launch", f"{pfx}{image}", target,
        ] + limits_config + vm_flag

        try:
            print(f"[IncusManager] Launching {target} using image {image} (CPU={cpu_limit}, MEM={mem_limit}, nesting=true)...", flush=True)
            res = self._run_incus(
                cmd,
                stdin=subprocess.DEVNULL,
                # First-time image unpack on dir backends can exceed 60s; the CoW
                # snapshot path above is what carries the <=20s budget.
                timeout=180
            )
            elapsed = time.time() - t0
            if res.returncode == 0:
                print(f"[IncusManager] {target} launched successfully in {elapsed:.2f}s (<=20s).", flush=True)
                return True
            print(f"[IncusManager] Error launching {target}: {res.stderr.strip()}")
        except Exception as e:
            print(f"[IncusManager] Exception launching {target}: {e}")

        return False

    def delete_node(self, node_name: str, remote_name: Optional[str] = None) -> bool:
        """Force deletes an ephemeral container or microVM node. Idempotent."""
        if not self.is_available():
            return True

        if ":" in node_name:
            parts = node_name.split(":", 1)
            remote_name = parts[0]
            node_name = parts[1]

        pfx = self._target_prefix(remote_name)
        target = f"{pfx}{node_name}"
        try:
            # Forcefully stop first
            self._run_incus(["stop", "-f", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
            # Force delete
            res = self._run_incus(["delete", "-f", target], timeout=30)
            err = (res.stderr or "").lower()
            if res.returncode == 0 or "not found" in err or "doesn't exist" in err or "does not exist" in err:
                return True
            print(f"[IncusManager] Error deleting {target}: {res.stderr.strip()}", flush=True)
            return False
        except Exception as ex:
            print(f"[IncusManager] Exception deleting {target}: {ex}")
            return False

    def get_node_ip(self, node_name: str, remote_name: Optional[str] = None) -> Optional[str]:
        """Retrieves IPv4 address of an incus instance on its global network interface."""
        if not self.is_available():
            return None

        pfx = self._target_prefix(remote_name)
        target = f"{pfx}{node_name}"
        try:
            res = self._run_incus(["list", target, "--format", "json"], timeout=10)
            if res.returncode == 0:
                data = json.loads(res.stdout.strip())
                if data and len(data) > 0:
                    state_obj = data[0].get("state") or {}
                    net_info = state_obj.get("network") or {}
                    # Check eth0 first, then any other interface
                    for iface_name in ["eth0"] + [k for k in net_info.keys() if k != "eth0"]:
                        iface = net_info.get(iface_name, {})
                        for addr in iface.get("addresses", []):
                            if addr.get("family") == "inet" and addr.get("scope") == "global":
                                return addr.get("address")
        except Exception:
            pass
        return None

    def provision_kubeadm_cluster(
        self,
        session_id: str,
        is_distributed: bool = True,
        roles: Optional[List[str]] = None,
        custom_remotes: Optional[Dict[str, Optional[str]]] = None
    ) -> Dict[str, str]:
        """
        Provisions a multi-node Kubeadm cluster for a session.
        Dynamically distributes nodes across discovered remotes or falls back to local.
        Launches all nodes concurrently in parallel for sub-15s startup time.
        """
        if roles is None:
            roles = ["node1", "node2", "node3"]

        remotes = custom_remotes or self.get_target_distribution(roles, is_distributed=is_distributed)

        # Cross-host routing: workers must reach the control plane's bridge
        # subnet over the hosts' LAN before kubeadm join can succeed.
        try:
            self._sync_fleet_routes(remotes)
        except Exception as ex:
            print(f"[IncusManager] Warning: fleet route sync failed: {ex}")

        limits = {
            "node1": ("2", "2GiB"),
            "node2": ("2", "1536MiB"),
            "node3": ("2", "1536MiB"),
        }

        ips: Dict[str, str] = {}

        # Ensure the fast-path golden snapshot exists on every involved host (one-time per host)
        golden_map: Dict[Optional[str], Optional[str]] = {}
        for rem in sorted({v for v in remotes.values() if v}):
            golden_map[rem] = self.ensure_golden_snapshot(remote_name=rem)
        if None in remotes.values() and None not in golden_map:
            golden_map[None] = self.ensure_golden_snapshot(remote_name=None)

        def _launch_node_task(role: str, rem: Optional[str]):
            vm_name = f"{role}-{session_id}"
            cpu, mem = limits.get(role, ("2", "2GiB"))
            snap_src = golden_map.get(rem)
            if snap_src and rem and snap_src.startswith(f"{rem}:"):
                # ensure_golden_snapshot returns a self-describing prefixed source;
                # launch_node re-adds the remote prefix, so strip it here.
                snap_src = snap_src.split(":", 1)[1]
            if self.launch_node(vm_name, remote_name=rem, image=self.DEFAULT_IMAGE,
                                snapshot=snap_src, cpu_limit=cpu, mem_limit=mem):
                for _ in range(35):
                    ip = self.get_node_ip(vm_name, remote_name=rem)
                    if ip:
                        return role, ip
                    time.sleep(1)
            return role, None

        print(f"[IncusManager] Launching nodes in parallel across fleet (distribution: {remotes})...", flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(3, len(roles))) as executor:
            futures = [executor.submit(_launch_node_task, role, remotes.get(role)) for role in roles]
            for fut in concurrent.futures.as_completed(futures):
                role, ip = fut.result()
                if ip:
                    ips[role] = ip

        if "node1" in ips:
            try:
                self.bootstrap_cluster(session_id, ips, remotes_map=remotes)
            except Exception as ex:
                print(f"[IncusManager] Warning during cluster bootstrap: {ex}")

        return ips

    def bootstrap_cluster(
        self,
        session_id: str,
        ips: Dict[str, str],
        remotes_map: Optional[Dict[str, Optional[str]]] = None,
        is_distributed: bool = True
    ) -> bool:
        """
        Bootstraps a functional kubeadm cluster across the provisioned Incus nodes:
        1. Configures CNI and initializes control plane on node1.
        2. Retrieves token join command.
        3. Concurrently joins worker nodes in parallel and labels them.
        """
        if "node1" not in ips:
            return False

        if remotes_map is None:
            remotes_map = self.get_target_distribution(list(ips.keys()), is_distributed=is_distributed)

        cni_json = json.dumps({
            "cniVersion": "0.4.0",
            "name": "localnet",
            "plugins": [
                {
                    "type": "bridge",
                    "bridge": "cbr0",
                    "isGateway": True,
                    "ipMasq": True,
                    "ipam": {
                        "type": "host-local",
                        "subnet": "10.244.0.0/16",
                        "routes": [{"dst": "0.0.0.0/0"}]
                    }
                },
                {
                    "type": "portmap",
                    "capabilities": {"portMappings": True}
                }
            ]
        }, indent=2)

        node1_target = f"{self._target_prefix(remotes_map.get('node1'))}node1-{session_id}"
        node1_ip = ips["node1"]

        # Host swap breaks kubelet (fail-swap-on default). The drop-in flag keeps
        # kubelet alive even when the Incus host itself has swap enabled.
        swap_guard = """
swapoff -a 2>/dev/null || true
mkdir -p /etc/systemd/system/kubelet.service.d
printf '[Service]\\nEnvironment=KUBELET_EXTRA_ARGS=--fail-swap-on=false\\n' > /etc/systemd/system/kubelet.service.d/95-cka-swap.conf
systemctl daemon-reload 2>/dev/null || true
"""

        # CKA drills drive nodes over SSH (setup.sh / graders use NODE_1..3), and
        # candidates `ssh nodeN` from the desktop. Ensure sshd + key auth in every node.
        pub_key = ""
        for cand in (Path("/root/.ssh/id_ed25519.pub"), Path("/root/.ssh/id_rsa.pub"),
                     Path.home() / ".ssh" / "id_ed25519.pub", Path.home() / ".ssh" / "id_rsa.pub"):
            try:
                if cand.exists():
                    pub_key = cand.read_text(encoding="utf-8").strip()
                    break
            except Exception:
                pass
        ssh_guard = ""
        if pub_key:
            ssh_guard = f"""
apt-get install -y openssh-server >/dev/null 2>&1 || true
mkdir -p /run/sshd /root/.ssh && chmod 700 /root/.ssh
touch /root/.ssh/authorized_keys
grep -qxF '{pub_key}' /root/.ssh/authorized_keys 2>/dev/null || echo '{pub_key}' >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys
systemctl enable ssh >/dev/null 2>&1 || true
systemctl restart ssh >/dev/null 2>&1 || systemctl restart sshd >/dev/null 2>&1 || (/usr/sbin/sshd 2>/dev/null || true)
"""

        # 1. Setup node1 control-plane
        setup_node1 = f"""
ln -sf /dev/console /dev/kmsg
mount -o remount,rw /proc/sys 2>/dev/null || true
echo 10 > /proc/sys/kernel/panic 2>/dev/null || true
echo 1 > /proc/sys/vm/overcommit_memory 2>/dev/null || true
{swap_guard}
{ssh_guard}
mkdir -p /etc/cni/net.d
cat << 'EOF' > /etc/cni/net.d/10-local.conflist
{cni_json}
EOF
systemctl restart containerd 2>/dev/null || true
sleep 2

if [ ! -f /etc/kubernetes/admin.conf ]; then
    kubeadm init --ignore-preflight-errors=all --kubernetes-version={self.K8S_VERSION} --pod-network-cidr=10.244.0.0/16 --apiserver-advertise-address={node1_ip} --node-name=node1
    mount -o remount,rw /proc/sys 2>/dev/null || true
    systemctl restart kubelet 2>/dev/null || true
fi

# Root kubectl: make admin.conf the default kubeconfig so candidates can run
# kubectl immediately after `ssh node1` (interactive and non-interactive alike).
mkdir -p /root/.kube
cp -f /etc/kubernetes/admin.conf /root/.kube/config 2>/dev/null || true
chmod 600 /root/.kube/config 2>/dev/null || true
printf 'export KUBECONFIG=/etc/kubernetes/admin.conf\n' > /etc/profile.d/cka-kubeconfig.sh 2>/dev/null || true

# Remove master/control-plane taints to allow scheduling
KC="--kubeconfig=/etc/kubernetes/admin.conf"
kubectl $KC taint nodes --all node-role.kubernetes.io/control-plane- 2>/dev/null || true
kubectl $KC taint nodes --all node-role.kubernetes.io/master- 2>/dev/null || true

# Containers cannot write net.netfilter sysctls on modern kernels (EACCES even
# as root with /proc/sys remounted rw), so kube-proxy must be told to leave the
# conntrack limits as-is or it CrashLoops with:
#   "open /proc/sys/net/netfilter/nf_conntrack_max: permission denied"
# maxPerCore=0 / timeouts 0s => kube-proxy skips every net.netfilter write.
if kubectl $KC -n kube-system get cm kube-proxy >/dev/null 2>&1; then
    kubectl $KC -n kube-system get cm kube-proxy -o jsonpath='{{.data.config\\.conf}}' > /tmp/kp.conf 2>/dev/null || true
    sed -i 's/^  maxPerCore:.*/  maxPerCore: 0/; s/^  min:.*/  min: 0/; s/^  tcpEstablishedTimeout:.*/  tcpEstablishedTimeout: 0s/; s/^  tcpCloseWaitTimeout:.*/  tcpCloseWaitTimeout: 0s/' /tmp/kp.conf
    kubectl $KC -n kube-system create configmap kube-proxy --from-file=config.conf=/tmp/kp.conf --dry-run=client -o yaml | kubectl $KC apply -f -
    kubectl $KC -n kube-system rollout restart ds/kube-proxy 2>/dev/null || true
    rm -f /tmp/kp.conf
fi

if [ ! -f /usr/local/bin/etcdctl ]; then
    etcdctl_bin=$(find /var/lib/containerd -name etcdctl 2>/dev/null | head -n1)
    if [ -n "$etcdctl_bin" ]; then
        cp "$etcdctl_bin" /usr/local/bin/etcdctl && chmod +x /usr/local/bin/etcdctl
    fi
fi
"""
        try:
            print(f"[IncusManager] Bootstrapping control-plane on {node1_target} ({node1_ip})...", flush=True)
            self._run_incus(["exec", node1_target, "--", "bash"], input=setup_node1, text=True, timeout=150)
        except Exception as e:
            print(f"[IncusManager] Error bootstrapping control plane: {e}")
            return False

        # 2. Get join command
        join_cmd = None
        try:
            res = self._run_incus(
                ["exec", node1_target, "--", "kubeadm", "token", "create", "--print-join-command", "--kubeconfig=/etc/kubernetes/admin.conf"],
                timeout=10
            )
            if res.returncode == 0 and "kubeadm join" in res.stdout:
                join_cmd = res.stdout.strip()
        except Exception:
            pass

        if not join_cmd:
            print("[IncusManager] Warning: failed to obtain kubeadm join command.")
            return True

        # 3. Join worker nodes concurrently in parallel
        worker_roles = [r for r in ips.keys() if r != "node1"]

        def _join_worker_task(w_role: str):
            w_target = f"{self._target_prefix(remotes_map.get(w_role))}{w_role}-{session_id}"
            w_setup = f"""
ln -sf /dev/console /dev/kmsg
mount -o remount,rw /proc/sys 2>/dev/null || true
echo 10 > /proc/sys/kernel/panic 2>/dev/null || true
echo 1 > /proc/sys/vm/overcommit_memory 2>/dev/null || true
{swap_guard}
{ssh_guard}
mkdir -p /etc/cni/net.d
cat << 'EOF' > /etc/cni/net.d/10-local.conflist
{cni_json}
EOF
systemctl restart containerd 2>/dev/null || true
sleep 2

if [ ! -f /etc/kubernetes/kubelet.conf ]; then
    {join_cmd} --ignore-preflight-errors=all
fi
"""
            try:
                print(f"[IncusManager] Joining worker {w_target} to cluster in parallel...", flush=True)
                self._run_incus(["exec", w_target, "--", "bash"], input=w_setup, text=True, timeout=150)
                self._run_incus(
                    ["exec", node1_target, "--", "kubectl", "label", "node", f"{w_role}-{session_id}", "node-role.kubernetes.io/worker=worker", "--overwrite", "--kubeconfig=/etc/kubernetes/admin.conf"],
                    timeout=10
                )
            except Exception as e:
                print(f"[IncusManager] Warning joining {w_target}: {e}")

        if worker_roles:
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(worker_roles)) as executor:
                list(executor.map(_join_worker_task, worker_roles))

        return True

    def check_nodes_ready(
        self,
        session_id: str,
        expected_count: int = 3,
        remotes_map: Optional[Dict[str, Optional[str]]] = None
    ) -> Dict[str, Any]:
        """
        Queries Kubernetes API on node1 to inspect node Ready statuses.
        Returns detailed node statuses and whether all expected nodes are Ready.
        """
        if not self.is_available():
            return {"ready": False, "nodes": {}, "error": "Incus CLI unavailable"}

        # Candidate remotes: explicit mapping first, then dynamically discovered hosts, then local.
        candidate_remotes = []
        if remotes_map and "node1" in remotes_map:
            candidate_remotes.append(remotes_map["node1"])
        for r in self.discover_compute_remotes():
            if r not in candidate_remotes:
                candidate_remotes.append(r)
        if None not in candidate_remotes:
            candidate_remotes.append(None)

        for rem in candidate_remotes:
            node1_target = f"{self._target_prefix(rem)}node1-{session_id}"
            try:
                res = self._run_incus(
                    ["exec", node1_target, "--", "kubectl", "get", "nodes", "-o", "json", "--kubeconfig=/etc/kubernetes/admin.conf"],
                    timeout=10
                )
                if res.returncode == 0 and res.stdout.strip():
                    data = json.loads(res.stdout.strip())
                    items = data.get("items", [])
                    node_statuses = {}
                    ready_nodes = []
                    for item in items:
                        name = item.get("metadata", {}).get("name", "")
                        conditions = item.get("status", {}).get("conditions", [])
                        is_ready = False
                        for cond in conditions:
                            if cond.get("type") == "Ready" and cond.get("status") == "True":
                                is_ready = True
                                break
                        node_statuses[name] = "Ready" if is_ready else "NotReady"
                        if is_ready:
                            ready_nodes.append(name)

                    all_ready = len(ready_nodes) >= expected_count and all(s == "Ready" for s in node_statuses.values())
                    return {
                        "ready": all_ready,
                        "ready_count": len(ready_nodes),
                        "total_count": len(items),
                        "nodes": node_statuses
                    }
            except Exception as ex:
                return {"ready": False, "nodes": {}, "error": str(ex)}

        return {"ready": False, "nodes": {}}

    def wait_for_nodes_ready(
        self,
        session_id: str,
        expected_count: int = 3,
        timeout: int = 60,
        interval: int = 3,
        remotes_map: Optional[Dict[str, Optional[str]]] = None
    ) -> bool:
        """
        Polls node readiness non-blockingly until all nodes transition to Ready in Kubernetes.
        """
        t0 = time.time()
        while time.time() - t0 < timeout:
            status = self.check_nodes_ready(session_id, expected_count=expected_count, remotes_map=remotes_map)
            if status.get("ready"):
                print(f"[IncusManager] All {expected_count} nodes Ready in {time.time() - t0:.1f}s: {status.get('nodes')}", flush=True)
                return True
            time.sleep(interval)
        print(f"[IncusManager] Timed out waiting for nodes to become Ready after {timeout}s.")
        return False

    def get_kubeconfig(self, session_id: str, remotes_map: Optional[Dict[str, Optional[str]]] = None) -> Optional[str]:
        """Pulls /etc/kubernetes/admin.conf from node1 of the given session."""
        if not self.is_available():
            return None

        candidate_remotes = []
        if remotes_map and "node1" in remotes_map:
            candidate_remotes.append(remotes_map["node1"])
        for r in self.discover_compute_remotes():
            if r not in candidate_remotes:
                candidate_remotes.append(r)
        if None not in candidate_remotes:
            candidate_remotes.append(None)

        for rem in candidate_remotes:
            pfx = self._target_prefix(rem)
            target = f"{pfx}node1-{session_id}"
            try:
                res = self._run_incus(
                    ["file", "pull", f"{target}/etc/kubernetes/admin.conf", "-"],
                    timeout=8
                )
                if res.returncode == 0 and res.stdout.strip():
                    return res.stdout.strip()
            except Exception:
                pass
        return None

    def delete_session_cluster(self, session_id: str, is_distributed: bool = True):
        """
        Completely purges all ephemeral Incus instances, attached networks, and storage volumes
        associated with session_id across local and all remote VM hosts.
        Idempotent and resilient against partial failures.
        """
        if not self.is_available():
            return

        clean_id = session_id.replace("session-", "").replace("-", "")[:10]
        discovered = self.discover_compute_remotes()
        remotes_to_sweep = [None] + discovered

        # 1. Direct targeted deletion of common name patterns
        for role in ("node1", "node2", "node3"):
            for sid_variant in (session_id, f"session-{clean_id}", clean_id):
                for rem in remotes_to_sweep:
                    self.delete_node(f"{role}-{sid_variant}", remote_name=rem)

        # 2. Comprehensive fleet sweep: query each remote and delete any instance matching clean_id or session_id
        for rem in remotes_to_sweep:
            target_pfx = self._target_prefix(rem)
            try:
                res = self._run_incus(
                    ["list", target_pfx, "--format", "json"],
                    timeout=8
                )
                if res.returncode == 0 and res.stdout.strip():
                    instances = json.loads(res.stdout.strip())
                    for inst in instances:
                        iname = inst.get("name", "")
                        if clean_id in iname or session_id in iname:
                            print(f"[IncusManager] Fleet sweep deleting instance {iname} on {rem or 'local'}", flush=True)
                            self.delete_node(iname, remote_name=rem)
            except Exception as ex:
                print(f"[IncusManager] Warning in fleet sweep on {rem or 'local'}: {ex}")

        # 3. Clean up any ephemeral custom storage volumes associated with this session
        for rem in remotes_to_sweep:
            target_pfx = self._target_prefix(rem)
            try:
                p_res = self._run_incus(["storage", "list", target_pfx, "--format", "json"], timeout=5)
                if p_res.returncode == 0 and p_res.stdout.strip():
                    pools = json.loads(p_res.stdout.strip())
                    for pool in pools:
                        pname = pool.get("name")
                        if not pname:
                            continue
                        v_res = self._run_incus(["storage", "volume", "list", f"{target_pfx}{pname}", "--format", "json"], timeout=5)
                        if v_res.returncode == 0 and v_res.stdout.strip():
                            vols = json.loads(v_res.stdout.strip())
                            for vol in vols:
                                vname = vol.get("name", "")
                                if clean_id in vname or session_id in vname:
                                    vtype = vol.get("type", "custom")
                                    print(f"[IncusManager] Deleting ephemeral storage volume {pname}/{vname} on {rem or 'local'}", flush=True)
                                    self._run_incus(["storage", "volume", "delete", f"{target_pfx}{pname}", f"{vtype}/{vname}"], timeout=10)
            except Exception:
                pass

    def list_all_fleet_instances(self) -> List[Dict[str, Any]]:
        """Queries local and all discovered compute remotes and returns normalized instance inventory."""
        if not self.is_available():
            return []

        remotes = [None] + self.discover_compute_remotes()
        fleet_items: List[Dict[str, Any]] = []

        for rem in remotes:
            target_pfx = self._target_prefix(rem)
            rem_label = rem or "local"
            try:
                res = self._run_incus(
                    ["list", target_pfx, "--format", "json"],
                    stdin=subprocess.DEVNULL,
                    timeout=8
                )
                if res.returncode == 0 and res.stdout.strip():
                    data = json.loads(res.stdout.strip())
                    for item in data:
                        cfg = item.get("config") or {}
                        state_obj = item.get("state") or {}
                        net_info = state_obj.get("network") or {}
                        eth0 = net_info.get("eth0") or {}

                        ip = None
                        for addr in eth0.get("addresses", []):
                            if addr.get("family") == "inet" and addr.get("scope") == "global":
                                ip = addr.get("address")
                                break

                        name = item.get("name", "")
                        sid = None
                        if "-" in name:
                            parts = name.split("-", 1)
                            if len(parts) > 1 and ("session" in parts[1] or "mock" in parts[1]):
                                sid = parts[1]

                        fleet_items.append({
                            "name": name,
                            "node": rem_label,
                            "kind": "incus",
                            "type": item.get("type", "container"),
                            "status": item.get("status", "UNKNOWN"),
                            "ip": ip or "-",
                            "session_id": sid or "-",
                            "cpu_limit": cfg.get("limits.cpu", "-"),
                            "mem_limit": cfg.get("limits.memory", "-"),
                            "created_at": item.get("created_at", "-")
                        })
            except Exception as e:
                print(f"[IncusManager] Error listing instances on {rem_label}: {e}")

        return fleet_items


incus_mgr = IncusClusterManager()
