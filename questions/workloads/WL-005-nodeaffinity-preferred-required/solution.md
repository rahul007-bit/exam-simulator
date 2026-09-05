# Solution for WL-005: Configure NodeAffinity (Required and Preferred Rules)

Create Pod `affinity-pod` in `web-cluster` with `requiredDuringSchedulingIgnoredDuringExecution` matching `topology.kubernetes.io/zone: zone-1` and `preferredDuringScheduling` matching `disk: ssd`.
