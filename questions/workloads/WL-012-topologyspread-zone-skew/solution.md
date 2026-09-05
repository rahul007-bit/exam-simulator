# Solution for WL-012: Configure TopologySpreadConstraints Across Zones

Configure Deployment `zone-spread` in `multi-zone-app` with `topologySpreadConstraints` specifying `maxSkew: 1`, `topologyKey: topology.kubernetes.io/zone`, and `whenUnsatisfiable: DoNotSchedule`.
