# Solution for WL-008: Configure PodAntiAffinity to Spread Replicas Across Nodes

Create Deployment `spread-web` with 2 replicas in `resilient-app` using `podAntiAffinity` on `topologyKey: kubernetes.io/hostname`.
