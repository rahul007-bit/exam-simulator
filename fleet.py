#!/usr/bin/env python3
"""
Fleet Runner - Execute raw bash commands & scripts across cluster nodes
without PowerShell or SSH quote-escaping headaches.

Usage:
  python fleet.py node1 "echo 'root:1000000:1000000000' >> /etc/subuid"
  python fleet.py compute "systemctl restart incus"
  python fleet.py all script.sh
  python fleet.py node2 -f path/to/script.sh
"""
import sys
import os
import subprocess
from pathlib import Path
from typing import List, Dict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

NODES: Dict[str, str] = {
    "mgmt": "10.8.0.15",
    "vpn": "10.8.0.15",
    "node1": "192.168.50.169",
    "node2": "192.168.50.188",
    "node3": "192.168.50.170",
}

GROUPS: Dict[str, List[str]] = {
    "compute": ["node1", "node2", "node3"],
    "all": ["mgmt", "node1", "node2", "node3"],
}

MGMT_HOST = "10.8.0.15"


import base64

def run_on_target(target: str, script_content: str) -> int:
    ip = NODES.get(target)
    if not ip:
        print(f"[{target}] Unknown target!", file=sys.stderr)
        return 1

    b64_script = base64.b64encode(script_content.encode("utf-8")).decode("ascii")
    runner_cmd = f"echo '{b64_script}' | base64 -d > /tmp/fleet_run.sh && bash /tmp/fleet_run.sh; rc=$?; rm -f /tmp/fleet_run.sh; exit $rc"

    if target in ("mgmt", "vpn"):
        ssh_cmd = [
            "ssh",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=no",
            f"root@{MGMT_HOST}",
            runner_cmd
        ]
    else:
        # Route through mgmt to reach LAN IP
        inner = f"ssh -o StrictHostKeyChecking=no root@{ip} \"{runner_cmd}\""
        ssh_cmd = [
            "ssh",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=no",
            f"root@{MGMT_HOST}",
            inner
        ]

    try:
        proc = subprocess.Popen(
            ssh_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        raw_stdout, raw_stderr = proc.communicate(input=script_content.encode("utf-8"))
        stdout = raw_stdout.decode("utf-8", errors="replace")
        stderr = raw_stderr.decode("utf-8", errors="replace")
        
        # Print output prefixed with target name
        for line in stdout.splitlines():
            print(f"[{target}] {line}")
        for line in stderr.splitlines():
            if "WARNING: connection is not using a post-quantum" in line:
                continue
            if "This session may be vulnerable" in line or "The server may need to be upgraded" in line:
                continue
            print(f"[{target}:err] {line}", file=sys.stderr)

        return proc.returncode
    except Exception as ex:
        print(f"[{target}:fail] {ex}", file=sys.stderr)
        return 1


def main():
    if len(sys.argv) < 3 and not (len(sys.argv) == 2 and not sys.stdin.isatty()):
        print(__doc__)
        sys.exit(1)

    target_arg = sys.argv[1].lower()

    # Determine script content
    if len(sys.argv) >= 3:
        arg2 = sys.argv[2]
        if arg2 in ("-f", "--file") and len(sys.argv) >= 4:
            script_path = Path(sys.argv[3])
            script_content = script_path.read_text(encoding="utf-8")
        elif Path(arg2).is_file():
            script_content = Path(arg2).read_text(encoding="utf-8")
        else:
            # Join all remaining arguments as the script
            script_content = " ".join(sys.argv[2:])
    else:
        # Read from stdin
        script_content = sys.stdin.read()

    # Determine list of targets
    if target_arg in GROUPS:
        targets = GROUPS[target_arg]
    elif target_arg in NODES:
        targets = [target_arg]
    else:
        print(f"Error: Unknown target or group '{target_arg}'. Available: {list(NODES.keys()) + list(GROUPS.keys())}")
        sys.exit(1)

    # Normalize line endings for Linux bash
    script_content = script_content.replace("\r\n", "\n").replace("\r", "\n")

    overall_code = 0
    for t in targets:
        rc = run_on_target(t, script_content)
        if rc != 0:
            overall_code = rc

    sys.exit(overall_code)


if __name__ == "__main__":
    main()
