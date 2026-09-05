#!/usr/bin/env bash
set -e

CLUSTER_NAME=${K3D_CLUSTER_NAME:-"cka"}
K8S_VERSION=${K3D_K8S_VERSION:-"v1.30.2-k3s1"}
CTX="k3d-cka"

echo "[k3d] Re-creating multi-node cluster '${CLUSTER_NAME}' (1 server + 2 agents)..."

# Delete if exists
if k3d cluster list | grep -q "${CLUSTER_NAME}"; then
    echo "[k3d] Deleting existing cluster '${CLUSTER_NAME}'..."
    k3d cluster delete "${CLUSTER_NAME}"
fi

# Create cluster with pinned version
k3d cluster create "${CLUSTER_NAME}" \
    --image "rancher/k3s:${K8S_VERSION}" \
    --agents 2 \
    --port "8080:80@loadbalancer" \
    --port "8443:443@loadbalancer" \
    --port "30000-30100:30000-30100@server:0"

# Rename context to standard k3d-cka if needed
kubectl config rename-context "k3d-${CLUSTER_NAME}" "${CTX}" 2>/dev/null || true
kubectl config use-context "${CTX}" 2>/dev/null || true

echo "[k3d] Cluster '${CLUSTER_NAME}' is ready! Context: ${CTX}"
kubectl get nodes -o wide

# ---------------------------------------------------------------------------
# Image pre-pull and import
#
# k3d's containerd registry pulls are unreliable (content-digest failures,
# CoreDNS ImagePullBackOff), so every image the question bank deploys is
# pulled on the host and imported into each node's containerd via ctr.
# Set SKIP_IMAGE_IMPORT=1 to bypass.
# ---------------------------------------------------------------------------
import_image() {
    local img="$1"
    local tar
    tar=$(mktemp /tmp/k3d-img-XXXXXX.tar)
    if ! docker save -o "$tar" "$img" 2>/dev/null; then
        echo "[warn] host save failed: $img"
        rm -f "$tar"
        return 1
    fi
    for node in $NODE_CONTAINERS; do
        if ! docker exec -i "$node" ctr -n k8s.io images import - < "$tar" >/dev/null 2>&1; then
            echo "[warn] ctr import failed on ${node}: $img"
        fi
    done
    rm -f "$tar"
    echo "[k3d] Imported ${img}"
}

if [ "${SKIP_IMAGE_IMPORT:-0}" != "1" ]; then
    NODE_CONTAINERS=$(docker ps --format '{{.Names}}' | grep -E "^k3d-${CLUSTER_NAME}-(server|agent)-[0-9]+$" || true)

    if [ -n "$NODE_CONTAINERS" ]; then
        echo "[k3d] Waiting for API server..."
        for _ in $(seq 1 15); do
            kubectl --context "${CTX}" get ns >/dev/null 2>&1 && break
            sleep 2
        done

        # App images referenced by question setups and manifests.
        # NOTE: intentionally excludes nginx:non-existent-tag-999 (ImagePullBackOff drills).
        APP_IMAGES=(
            nginx:stable
            nginx:alpine
            nginx:latest
            nginx:1.25
            busybox:1.35
            busybox:1.36
            alpine:3.18
            bitnami/kubectl:latest
            prom/node-exporter:v1.6.1
        )

        # System images are resolved from live deployment specs so versions
        # always match the pinned k3s release (specs exist even when pulls fail).
        echo "[k3d] Resolving system images from cluster specs..."
        SYSTEM_IMAGES=()
        for dep in coredns local-path-provisioner metrics-server; do
            img=$(kubectl --context "${CTX}" -n kube-system get deploy "$dep" \
                  -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || true)
            [ -n "$img" ] && SYSTEM_IMAGES+=("$img")
        done

        echo "[k3d] Pulling ${#APP_IMAGES[@]} app + ${#SYSTEM_IMAGES[@]} system images on host..."
        for img in "${APP_IMAGES[@]}" "${SYSTEM_IMAGES[@]}"; do
            docker pull -q "$img" >/dev/null 2>&1 || echo "[warn] host pull failed: $img"
            import_image "$img"
        done

        echo "[k3d] Image cache warm on all nodes."
    else
        echo "[warn] No k3d node containers found for cluster '${CLUSTER_NAME}'; skipping image import"
    fi
fi
