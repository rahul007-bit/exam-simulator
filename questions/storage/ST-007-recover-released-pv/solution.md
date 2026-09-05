# Solution for ST-007: Recover Data from Released PersistentVolume

PV `backup-data-pv` is in `Released` status. Clear the `claimRef` in PV spec so it becomes `Available` for rebinding.
