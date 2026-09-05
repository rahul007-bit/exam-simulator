# Solution for SC-002: Create ClusterRole and Binding for Read-Only Cluster Auditor

Create ClusterRole `cluster-auditor` granting `get, list, watch` on `pods, nodes, services` across all namespaces. Bind to user `auditor-user`.
