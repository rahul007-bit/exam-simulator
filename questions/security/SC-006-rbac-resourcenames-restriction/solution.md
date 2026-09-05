# Solution for SC-006: Restrict Secret Access Using RBAC resourceNames

Create Role `vault-restricted` in `rbac-fine-grained` allowing `get` only on Secret named `allowed-creds` using `resourceNames` constraint.
