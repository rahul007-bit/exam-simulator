#!/usr/bin/env bash
set -e

echo "=== CKA Lab Engine Preflight Check ==="

# Check Python
if command -v python3 >/dev/null 2>&1; then
    echo "✔ Python 3 installed: $(python3 --version)"
else
    echo "✖ Python 3 not found. Please install python3."
    exit 1
fi

# Check Docker
if command -v docker >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1; then
        echo "✔ Docker is running"
    else
        echo "✖ Docker daemon is not running. Please start Docker."
    fi
else
    echo "✖ Docker not found. Please install docker."
fi

# Check k3d
if command -v k3d >/dev/null 2>&1; then
    echo "✔ k3d installed: $(k3d --version | head -n 1)"
else
    echo "⚠ k3d not found. (Install with: curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash)"
fi

# Check kubectl
if command -v kubectl >/dev/null 2>&1; then
    echo "✔ kubectl installed: $(kubectl version --client --short 2>/dev/null || kubectl version --client 2>/dev/null | head -n 1)"
else
    echo "✖ kubectl not found. Please install kubectl."
fi

echo "======================================"
