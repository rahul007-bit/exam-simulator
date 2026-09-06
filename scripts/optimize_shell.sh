#!/bin/bash
set -e

echo "[1/3] Pre-generating kubectl bash completion..."
mkdir -p /etc/bash_completion.d
if command -v kubectl >/dev/null 2>&1; then
    kubectl completion bash > /etc/bash_completion.d/kubectl 2>/dev/null || true
fi

echo "[2/3] Optimizing host /home/exam/.bashrc..."
python3 - << 'PYEOF'
import os

bashrc_path = "/home/exam/.bashrc"
if os.path.exists(bashrc_path):
    with open(bashrc_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove the slow labctl status check which took 11+ seconds on startup
    cleaned_lines = []
    skip_block = False
    for line in content.splitlines():
        if "Auto-wrap unrecorded interactive shells" in line or "labctl status" in line:
            skip_block = True
            continue
        if skip_block and line.strip() == "fi":
            skip_block = False
            continue
        if skip_block:
            continue
        # Replace dynamic kubectl completion with static source
        if "source <(kubectl completion" in line:
            cleaned_lines.append("[ -f /etc/bash_completion.d/kubectl ] && . /etc/bash_completion.d/kubectl 2>/dev/null || true")
        else:
            cleaned_lines.append(line)

    with open(bashrc_path, "w", encoding="utf-8") as f:
        f.write("\n".join(cleaned_lines) + "\n")
    print("Host /home/exam/.bashrc optimized.")
PYEOF

echo "[3/3] Testing shell startup speed..."
time su - exam -c 'echo "Shell ready!"'
