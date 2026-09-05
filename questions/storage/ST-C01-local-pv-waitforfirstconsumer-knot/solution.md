# Solution for ST-C01: Chaos: Local PV Binding Deadlock with Conflicting NodeSelectors

PVC is unbound because Local PV has nodeAffinity for Node A while Pod has nodeSelector for Node B. Fix node constraints so PVC binds.
