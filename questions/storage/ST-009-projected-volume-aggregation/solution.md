# Solution for ST-009: Configure Projected Volume Aggregating Secret and DownwardAPI

Create Pod `projected-pod` in `app-credentials` with a projected volume combining Secret `vault-creds` and downwardAPI (pod name and namespace).
