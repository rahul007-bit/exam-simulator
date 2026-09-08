#!/usr/bin/env bash
# Lab network wiring for distributed kubeadm clusters across Incus hosts.
#
# Topology (discovered 2026-09-08):
#   mgmt "exam-standardpc": LAN 192.168.50.122 (ens18), VPN 10.8.0.15 (tun0),
#     incusbr0 = 10.50.100.1/24 (ZFS pool zfspool, CP runs here).
#   node1 192.168.50.169: incusbr0 = 10.110.46.1/24 (dir)
#   node2 192.168.50.188: incusbr0 = 10.240.60.1/24 (dir)
#   node3 192.168.50.170: incusbr0 = 10.192.95.1/24 (dir)
#
# Workers on the RHEL hosts join the control plane via mgmt's LAN IP (the VPN
# address 10.8.0.15 is NOT reachable from the RHEL segment). Docker's FORWARD
# policy (DROP) on the mgmt host would otherwise swallow LAN -> CP traffic.
#
# Routes/firewall rules are runtime-only; this script is installed as a
# systemd template unit (scripts/lab-routes@.service) on every host so they
# are re-applied automatically at boot:
#   systemctl enable --now lab-routes@mgmt.service   # on the mgmt host
#   systemctl enable --now lab-routes@node1.service  # on 192.168.50.169
#   (likewise lab-routes@node2 / lab-routes@node3)
# Docker resets the FORWARD policy when it starts, so the unit is ordered
# After=docker.service; kubelet swap tolerance is handled inside the engine's
# bootstrap (swapoff + fail-swap-on=false drop-in), no extra unit needed.
set -euo pipefail

MGM_LAN="192.168.50.122"
CP_SUBNET="10.50.100.0/24"
NODE1="192.168.50.169"; NODE1_SUBNET="10.110.46.0/24"
NODE2="192.168.50.188"; NODE2_SUBNET="10.240.60.0/24"
NODE3="192.168.50.170"; NODE3_SUBNET="10.192.95.0/24"

case "${1:-}" in
  mgmt)
    echo "===> On mgmt host: routes to RHEL bridge subnets + FORWARD accepts"
    ip route replace "$NODE1_SUBNET" via "$NODE1" dev ens18
    ip route replace "$NODE2_SUBNET" via "$NODE2" dev ens18
    ip route replace "$NODE3_SUBNET" via "$NODE3" dev ens18
    iptables -C FORWARD -d "$CP_SUBNET" -j ACCEPT 2>/dev/null || iptables -I FORWARD 1 -d "$CP_SUBNET" -j ACCEPT
    iptables -C FORWARD -s "$CP_SUBNET" -j ACCEPT 2>/dev/null || iptables -I FORWARD 1 -s "$CP_SUBNET" -j ACCEPT
    echo "OK: kubectl/desktop reach CP containers; LAN traffic forwarded to incusbr0."
    ;;
  node1|node2|node3)
    echo "===> On $1: route CP subnet via mgmt LAN IP"
    ip route replace "$CP_SUBNET" via "$MGM_LAN" dev ens18
    echo "OK: workers can kubeadm-join the control plane."
    ;;
  *)
    echo "Usage: $0 mgmt | node1 | node2 | node3" >&2
    exit 1
    ;;
esac
