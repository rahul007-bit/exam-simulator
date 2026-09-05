# Solution for ST-006: Deploy StatefulSet with Dynamic VolumeClaimTemplates

Create StatefulSet `redis-cluster` (2 replicas) in `redis-cluster` with `volumeClaimTemplates` requesting `1Gi` storage from StorageClass `local-path`.
