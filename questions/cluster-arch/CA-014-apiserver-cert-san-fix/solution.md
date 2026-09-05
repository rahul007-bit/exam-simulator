# Solution for CA-014: Add Missing IP SAN to API Server Certificate

API server is unreachable via external load balancer IP `10.0.0.50`. Update kubeadm config to include IP in SANs and regenerate apiserver cert.
