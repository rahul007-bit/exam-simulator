# Solution for ST-005: Create Local PersistentVolume with NodeAffinity

Create PersistentVolume `local-node-pv` (5Gi, RWO, storageClassName `local-disk`, hostPath `/opt/data`) with nodeAffinity targeting node `k3d-cka-server-0`.
