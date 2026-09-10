# Original User Request

## 2026-09-07T18:01:52Z

This is a single self-contained fix; keep it small and focused. Implement and stabilize a dynamic, fast Incus node provisioning engine for CKA multi-node cluster scenarios, supporting sub-15s local copy-on-write snapshot launching and dynamically scaling across multiple remote VM hosts when available.

Working directory: C:/Users/HP/Projects/4-sep-test/cka-labs
Integrity mode: development

## Requirements

### R1. Dynamic Incus Engine with Fast CoW Snapshot Provisioning
The provisioning engine must dynamically inspect available Incus remotes/hosts and support fast copy-on-write (CoW) instance creation from pre-cached golden images. When running locally on a single machine, it must launch local Incus system containers in under 20 seconds. When additional VM hosts/remotes are configured in the cluster environment, it must automatically discover and distribute worker nodes across them without hardcoding static topology.

### R2. Resilient Kubeadm Bootstrap, Worker Join, & Kubeconfig Distribution
Automate the control-plane initialization or worker node join sequence across the provisioned Incus instances. Kubeconfig must be automatically sanitized and synced into Redis, the host, and the active candidate container (`cka-desktop-{session_id}`) with the context name `kubeadm-vms`. Node readiness must be polled non-blockingly so the web platform and UI remain fully responsive.

### R3. Safe Lifecycle Teardown & Resource Isolation
Provide robust session teardown that completely stops and deletes all ephemeral Incus instances, attached networks, and storage volumes upon session termination or reset. Teardown must be idempotent, resilient against partial failures, and must never leave orphaned containers or network devices running in background.

## Verification Resources

- Existing codebase implementation: `core/incus_manager.py`, `core/sandbox_orchestrator.py`, `core/desktop_manager.py`.
- Automated test script: programmatic test script exercising launch, node readiness assertion, kubeconfig validation, and clean teardown.

## Acceptance Criteria

### Node Provisioning & Speed
- [ ] Local Incus node instance creation using copy-on-write snapshots completes in <= 20 seconds per node.
- [ ] The engine dynamically detects whether remote Incus endpoints exist, gracefully using local system containers when remotes are absent.
- [ ] Nodes are launched with required security profiles (`security.nesting=true`) and appropriate CPU/memory caps.

### Multi-Node Clustering & Networking
- [ ] Control-plane and worker instances successfully communicate over the Incus bridge network.
- [ ] All provisioned nodes transition to `Ready` status in Kubernetes (`kubectl get nodes`).
- [ ] Context `kubeadm-vms` is injected into `cka-desktop-{session_id}` and verified operable via `docker exec`.

### Teardown & Clean State
- [ ] Calling teardown on a session completely purges all associated Incus instances without errors.
- [ ] No orphaned Incus instances or stale kubeconfig contexts remain after `POST /api/reset` or session termination.
- [ ] A programmatic verification test script executes end-to-end and passes with exit code 0.
