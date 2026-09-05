import getpass
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

BASE_DIR = Path(__file__).parent.parent
ENV_PATH = BASE_DIR / ".env"
ENV_EXAMPLE_PATH = BASE_DIR / ".env.example"


class ConfigWizard:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or BASE_DIR
        self.env_path = self.base_dir / ".env"
        self.example_path = self.base_dir / ".env.example"
        self.console = Console() if HAS_RICH else None

    def load_existing_env(self) -> Dict[str, str]:
        """Loads key-value pairs from existing .env or .env.example."""
        data = {}
        source = self.env_path if self.env_path.exists() else self.example_path
        if source.exists():
            with open(source, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        data[k.strip()] = v.strip().strip("'\"")
        return data

    def auto_detect_defaults(self) -> Dict[str, str]:
        """Auto-detects sensible system defaults."""
        existing = self.load_existing_env()
        detected = {}

        # 1. Platform Host & User Identities
        detected["EXAM_USER"] = existing.get("EXAM_USER", "exam")
        current_admin = os.getenv("SUDO_USER") or getpass.getuser() or "rahul"
        detected["ADMIN_USER"] = existing.get("ADMIN_USER", current_admin)

        # 2. SSH Configuration
        detected["SSH_USER"] = existing.get("SSH_USER", "root")
        ssh_key = existing.get("SSH_KEY", "~/.ssh/id_rsa")
        for candidate in ["~/.ssh/id_rsa", "~/.ssh/id_ed25519", "~/.ssh/id_ecdsa"]:
            expanded = Path(candidate).expanduser()
            if expanded.exists():
                ssh_key = candidate
                break
        detected["SSH_KEY"] = ssh_key

        # 3. Kubeadm Nodes
        detected["NODE_1"] = existing.get("NODE_1", "192.168.1.57")
        detected["NODE_2"] = existing.get("NODE_2", "192.168.1.56")
        detected["NODE_3"] = existing.get("NODE_3", "")
        detected["KUBEADM_CONTEXT"] = existing.get("KUBEADM_CONTEXT", "kubeadm-vms")

        # 4. Local k3d Cluster
        detected["K3D_CLUSTER_NAME"] = existing.get("K3D_CLUSTER_NAME", "cka")
        detected["K3D_K8S_VERSION"] = existing.get("K3D_K8S_VERSION", "v1.30.2-k3s1")
        detected["K3D_CONTEXT"] = existing.get("K3D_CONTEXT", "k3d-cka")

        # 5. Services & Ports
        detected["WEB_PORT"] = existing.get("WEB_PORT", "3000")
        detected["VNC_PORT"] = existing.get("VNC_PORT", "5901")
        detected["NOVNC_PORT"] = existing.get("NOVNC_PORT", "6080")
        detected["VNC_DISPLAY"] = existing.get("VNC_DISPLAY", ":1")
        detected["VNC_RESOLUTION"] = existing.get("VNC_RESOLUTION", "1920x1080")

        return detected

    def prompt_value(self, prompt: str, default: str, non_interactive: bool = False) -> str:
        """Prompts the user for a value with a default fallback."""
        if non_interactive:
            return default
        try:
            val = input(f"{prompt} [{default}]: ").strip()
            return val if val else default
        except (KeyboardInterrupt, EOFError):
            print("\nConfiguration aborted.")
            exit(1)

    def test_docker(self) -> Tuple[bool, str]:
        """Verifies Docker daemon status."""
        if not shutil.which("docker"):
            return False, "Docker binary not found"
        try:
            res = subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)
            if res.returncode == 0:
                return True, "Docker daemon is active"
            return False, "Docker daemon not running"
        except Exception as e:
            return False, str(e)

    def test_k3d(self, cluster_name: str) -> Tuple[bool, str]:
        """Checks k3d installation and cluster presence."""
        if not shutil.which("k3d"):
            return False, "k3d binary not installed"
        try:
            res = subprocess.run(["k3d", "cluster", "list"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=5)
            if res.returncode == 0:
                if cluster_name in res.stdout:
                    return True, f"Cluster '{cluster_name}' is running"
                return True, f"k3d installed; cluster '{cluster_name}' not yet created"
            return False, "k3d cluster list failed"
        except Exception as e:
            return False, str(e)

    def test_kubectl_context(self, context_name: str) -> Tuple[bool, str]:
        """Checks if a kubectl context is reachable."""
        if not shutil.which("kubectl"):
            return False, "kubectl binary not installed"
        try:
            res = subprocess.run(
                ["kubectl", "--context", context_name, "get", "nodes", "--request-timeout=3s", "--no-headers"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=5,
            )
            if res.returncode == 0:
                node_count = len([line for line in res.stdout.splitlines() if line.strip()])
                return True, f"Connected ({node_count} nodes online)"
            return False, f"Context '{context_name}' unreachable"
        except Exception as e:
            return False, f"Check failed: {e}"

    def test_ssh(self, host: str, user: str, key_path: str) -> Tuple[bool, str]:
        """Verifies SSH connectivity to a remote node."""
        if not host:
            return True, "Not configured (optional)"
        expanded_key = str(Path(key_path).expanduser())
        cmd = [
            "ssh",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=4",
            "-i", expanded_key,
            f"{user}@{host}",
            "uname -n",
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=6)
            if res.returncode == 0:
                hostname = res.stdout.strip()
                return True, f"SSH OK ({hostname})"
            err = res.stderr.strip()[:60] or "Authentication failed or timeout"
            return False, f"SSH failed: {err}"
        except Exception as e:
            return False, f"SSH error: {e}"

    def generate_env_content(self, cfg: Dict[str, str]) -> str:
        """Renders formatted .env content with clean comments."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        return f"""# ==============================================================================
# CKA-LABS ENVIRONMENT CONFIGURATION
# Generated by './labctl configure' on {now_str}
# Zero hardcoded values: all platform scripts, tools, and question modules read from here.
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. Platform Host & User Identities
# ------------------------------------------------------------------------------
EXAM_USER={cfg.get('EXAM_USER', 'exam')}
ADMIN_USER={cfg.get('ADMIN_USER', 'rahul')}

# ------------------------------------------------------------------------------
# 2. Remote Kubeadm Multi-Node Cluster (SSH)
# ------------------------------------------------------------------------------
SSH_USER={cfg.get('SSH_USER', 'root')}
SSH_KEY={cfg.get('SSH_KEY', '~/.ssh/id_rsa')}

NODE_1={cfg.get('NODE_1', '')}
NODE_2={cfg.get('NODE_2', '')}
NODE_3={cfg.get('NODE_3', '')}
KUBEADM_CONTEXT={cfg.get('KUBEADM_CONTEXT', 'kubeadm-vms')}

# ------------------------------------------------------------------------------
# 3. Local k3d Containerized Cluster
# ------------------------------------------------------------------------------
K3D_CLUSTER_NAME={cfg.get('K3D_CLUSTER_NAME', 'cka')}
K3D_K8S_VERSION={cfg.get('K3D_K8S_VERSION', 'v1.30.2-k3s1')}
K3D_CONTEXT={cfg.get('K3D_CONTEXT', 'k3d-cka')}

# ------------------------------------------------------------------------------
# 4. Web Simulator & Desktop Services
# ------------------------------------------------------------------------------
WEB_PORT={cfg.get('WEB_PORT', '3000')}
VNC_PORT={cfg.get('VNC_PORT', '5901')}
NOVNC_PORT={cfg.get('NOVNC_PORT', '6080')}
VNC_DISPLAY={cfg.get('VNC_DISPLAY', ':1')}
VNC_RESOLUTION={cfg.get('VNC_RESOLUTION', '1920x1080')}
"""

    def run(self, non_interactive: bool = False, force: bool = False) -> bool:
        """Executes the setup wizard and runs preflight verification."""
        if self.console:
            self.console.print(Panel.fit(
                "[bold cyan]CKA-Labs Environment Configuration Wizard[/bold cyan]\n"
                "[dim]Interactive setup & preflight validation for universal deployability[/dim]",
                border_style="cyan"
            ))
        else:
            print("=== CKA-Labs Environment Configuration Wizard ===")

        if self.env_path.exists() and not force and not non_interactive:
            choice = input(f"\nExisting .env found at {self.env_path}. Overwrite? [Y/n]: ").strip().lower()
            if choice and not choice.startswith("y"):
                print("Aborting without changes.")
                return False

        defaults = self.auto_detect_defaults()
        cfg = {}

        print("\n[1/4] Platform Host & User Identities")
        cfg["EXAM_USER"] = self.prompt_value("Candidate unprivileged username", defaults["EXAM_USER"], non_interactive)
        cfg["ADMIN_USER"] = self.prompt_value("Platform administrator username (sudoer)", defaults["ADMIN_USER"], non_interactive)

        print("\n[2/4] Remote Kubeadm Multi-Node Cluster (SSH)")
        cfg["SSH_USER"] = self.prompt_value("Remote SSH User", defaults["SSH_USER"], non_interactive)
        cfg["SSH_KEY"] = self.prompt_value("SSH Private Key Path", defaults["SSH_KEY"], non_interactive)
        cfg["NODE_1"] = self.prompt_value("Node 1 (Control Plane IP)", defaults["NODE_1"], non_interactive)
        cfg["NODE_2"] = self.prompt_value("Node 2 (Worker 1 IP)", defaults["NODE_2"], non_interactive)
        cfg["NODE_3"] = self.prompt_value("Node 3 (Worker 2 IP, optional)", defaults["NODE_3"], non_interactive)
        cfg["KUBEADM_CONTEXT"] = self.prompt_value("Kubeadm context name", defaults["KUBEADM_CONTEXT"], non_interactive)

        print("\n[3/4] Local k3d Containerized Cluster")
        cfg["K3D_CLUSTER_NAME"] = self.prompt_value("k3d Cluster Name", defaults["K3D_CLUSTER_NAME"], non_interactive)
        cfg["K3D_K8S_VERSION"] = self.prompt_value("k3d Kubernetes Version", defaults["K3D_K8S_VERSION"], non_interactive)
        cfg["K3D_CONTEXT"] = self.prompt_value("k3d context name", defaults["K3D_CONTEXT"], non_interactive)

        print("\n[4/4] Web Simulator & Services")
        cfg["WEB_PORT"] = self.prompt_value("Web Simulator Port", defaults["WEB_PORT"], non_interactive)
        cfg["VNC_PORT"] = self.prompt_value("TigerVNC Port", defaults["VNC_PORT"], non_interactive)
        cfg["NOVNC_PORT"] = self.prompt_value("noVNC WebSocket Port", defaults["NOVNC_PORT"], non_interactive)
        cfg["VNC_DISPLAY"] = defaults["VNC_DISPLAY"]
        cfg["VNC_RESOLUTION"] = defaults["VNC_RESOLUTION"]

        # Backup existing .env if present
        if self.env_path.exists():
            backup_path = self.base_dir / ".env.bak"
            shutil.copy2(self.env_path, backup_path)

        # Write new .env file
        content = self.generate_env_content(cfg)
        with open(self.env_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"\n✔ Successfully written configuration to {self.env_path}")

        # Run Preflight Verification
        print("\nRunning preflight connectivity verification...")
        results = self.run_preflight(cfg)
        self.render_report(results)

        return all(r[2] for r in results if r[0] != "Node 3 (SSH)")

    def run_preflight(self, cfg: Dict[str, str]) -> List[Tuple[str, str, bool, str]]:
        """Runs connectivity and readiness tests based on configured values."""
        results = []

        # 1. Docker
        ok, msg = self.test_docker()
        results.append(("Docker Daemon", "Active", ok, msg))

        # 2. k3d Cluster
        ok, msg = self.test_k3d(cfg.get("K3D_CLUSTER_NAME", "cka"))
        results.append(("k3d Cluster", cfg.get("K3D_CLUSTER_NAME", "cka"), ok, msg))

        # 3. k3d context
        ok, msg = self.test_kubectl_context(cfg.get("K3D_CONTEXT", "k3d-cka"))
        results.append(("Kubectl Context (k3d)", cfg.get("K3D_CONTEXT", "k3d-cka"), ok, msg))

        # 4. Kubeadm context
        ok, msg = self.test_kubectl_context(cfg.get("KUBEADM_CONTEXT", "kubeadm-vms"))
        results.append(("Kubectl Context (kubeadm)", cfg.get("KUBEADM_CONTEXT", "kubeadm-vms"), ok, msg))

        # 5. SSH to Node 1
        n1 = cfg.get("NODE_1", "")
        if n1:
            ok, msg = self.test_ssh(n1, cfg.get("SSH_USER", "root"), cfg.get("SSH_KEY", "~/.ssh/id_rsa"))
            results.append(("Node 1 (SSH Control Plane)", n1, ok, msg))

        # 6. SSH to Node 2
        n2 = cfg.get("NODE_2", "")
        if n2:
            ok, msg = self.test_ssh(n2, cfg.get("SSH_USER", "root"), cfg.get("SSH_KEY", "~/.ssh/id_rsa"))
            results.append(("Node 2 (SSH Worker)", n2, ok, msg))

        # 7. SSH to Node 3 (optional)
        n3 = cfg.get("NODE_3", "")
        if n3:
            ok, msg = self.test_ssh(n3, cfg.get("SSH_USER", "root"), cfg.get("SSH_KEY", "~/.ssh/id_rsa"))
            results.append(("Node 3 (SSH)", n3, ok, msg))
        else:
            results.append(("Node 3 (SSH)", "Disabled", True, "Optional (skipped)"))

        return results

    def render_report(self, results: List[Tuple[str, str, bool, str]]) -> None:
        """Renders verification results in a rich table or plaintext."""
        if self.console and HAS_RICH:
            table = Table(title="Preflight Connectivity Summary", header_style="bold cyan")
            table.add_column("Component", style="bold")
            table.add_column("Target / Value")
            table.add_column("Status", justify="center")
            table.add_column("Details")

            for comp, target, ok, msg in results:
                status_text = "[green]✔ PASS[/green]" if ok else "[red]✖ FAIL[/red]"
                table.add_row(comp, target, status_text, msg)

            self.console.print("\n", table, "\n")
        else:
            print("\n=== Preflight Connectivity Summary ===")
            for comp, target, ok, msg in results:
                st = "✔ PASS" if ok else "✖ FAIL"
                print(f"[{st}] {comp} ({target}): {msg}")
            print("======================================\n")
