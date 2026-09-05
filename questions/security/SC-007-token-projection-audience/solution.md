# Solution for SC-007: Configure ServiceAccount Token Projection with Audience

Create Pod `vault-agent` in `auth-tokens` with projected volume `vault-token` specifying `serviceAccountToken` with audience `vault.company.io` and expiration `3600`.
