#!/usr/bin/env bash
set -e
CTX="${KUBECTL_CONTEXT:-k3d-cka}"
NS="traffic-edge"
CLUSTER_NAME="${K3D_CLUSTER_NAME:-${CTX#k3d-}}"
SERVICE_CIDR="10.43.0.0/16"

kubectl --context "$CTX" create namespace "$NS" --dry-run=client -o yaml | kubectl --context "$CTX" apply -f -

# Locate the k3d server node container backing this context.
# 1) conventional name: k3d-<cluster>-server-0
NODE_CONTAINER=""
for cand in "k3d-${CLUSTER_NAME}-server-0" "k3d-${CLUSTER_NAME}-server"; do
  if docker inspect "$cand" >/dev/null 2>&1; then NODE_CONTAINER="$cand"; break; fi
done

# 2) resolve via the API server port published by the cluster's serverlb
if [ -z "$NODE_CONTAINER" ]; then
  API_SERVER=$(kubectl --context "$CTX" config view --minify -o jsonpath='{.clusters[0].cluster.server}' 2>/dev/null || true)
  PORT="${API_SERVER##*:}"; PORT="${PORT%%/*}"
  if [ -n "$PORT" ] && [ "$PORT" != "$API_SERVER" ]; then
    LB=$(docker ps --format '{{.Names}} {{.Ports}}' | awk -v p="$PORT" '$0 ~ ":"p"->6443" {print $1; exit}')
    if [ -n "$LB" ]; then
      CAND="${LB%-serverlb}-server-0"
      docker inspect "$CAND" >/dev/null 2>&1 && NODE_CONTAINER="$CAND" || NODE_CONTAINER="$LB"
    fi
  fi
fi

# 3) last resort: the only running k3d server container
if [ -z "$NODE_CONTAINER" ]; then
  NODE_CONTAINER=$(docker ps --format '{{.Names}}' | grep -E "^k3d-.*-server(-0)?$" | head -1 || true)
fi

if [ -z "$NODE_CONTAINER" ]; then
  echo "[warn] No k3d server container found for context '${CTX}'; skipping iptables seeding" >&2
  exit 0
fi

# Rogue rule: drop all packets to the service CIDR in mangle PREROUTING
# (priority -150), so they die before DNAT (-100). The API server and node
# health stay green while all ClusterIP traffic silently vanishes. DROP is not
# permitted in the nat table on nf_tables backends, hence mangle. Idempotent.
docker exec "$NODE_CONTAINER" sh -c "iptables -t mangle -C PREROUTING -d ${SERVICE_CIDR} -j DROP 2>/dev/null || iptables -t mangle -I PREROUTING 1 -d ${SERVICE_CIDR} -j DROP"

echo "[chaos] Drop rule active on ${NODE_CONTAINER}: traffic to ${SERVICE_CIDR} is dropped"
