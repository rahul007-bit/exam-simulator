# Scaling & OSS-deployment discussion (OPEN)

> Status: **open for discussion** — nothing here is decided. This doc records the
> thinking so far (2026-09-25) so anyone can pick it up, poke holes, or extend it.
> Priority order agreed so far: k8s (CKA-style) exams first; other technologies later.

## The problem statement

Today the platform assumes a beefy single host: docker (k3d) + Incus VMs + systemd
+ root SSH. That is fine for the homelab trainer it is now, but:

1. **OSS adoption blocker**: an enthusiastic clone-and-run user has docker at
   most — not Incus, not a Proxmox, not three RHEL VMs.
2. **Scale blocker**: one host cannot serve many concurrent candidates, and the
   "exam = break a real cluster" model can't be nested inside someone else's k8s
   wholesale.
3. **Generality wish**: same engine for other cluster technologies
   (Postgres, Redis, Kafka, Hadoop/Spark...) with realistic *workload-driven*
   grading (e.g. for Kafka, run a perf client and check the cluster survives load).

## Idea 1 — Capability-tiered sandboxes (the OSS-friendly core)

Not all exam content needs real VMs. Tier the content, not the platform:

| Tier | Needs | Content it unlocks |
|---|---|---|
| **0** | docker only (k3d; kind/podman later) | namespace-scoped CKA bank: workloads, scheduling/taints, RBAC, netpol, services/ingress, storage objects, CRDs — est. 60–70% of questions |
| **1** | docker only | *simulated* node trouble inside the k3d cluster: virtual "node" pods, node conditions/taints, static-pod misconfig drills — 90% of the reasoning without a real node |
| **2** | VMs (opt-in) | genuinely host-level CKA tasks: etcd backup/restore, kubeadm upgrades, systemd kubelet repair. Incus/kubeadm-vms/Proxmox stay as **optional plugins** |

Mechanics: `question.yaml` gets `sandbox: [tier0|tier2]` (and
`requires: [real-nodes, systemd]`). Preset generation becomes **tier-aware**:
on a tier-0-only host, tier-2 tasks are auto-swapped out of presets, or marked
"skipped — host can't run X" (grader SKIPPED semantics already exist).

## Idea 2 — Multiple hosts via worker/queue (scale concurrency)

Keep the engine as the worker; add a thin control plane + queue (Redis exists).
Workers register capacity; the scheduler assigns sessions to workers; workers
provision locally through the *existing* `provision_session`/`teardown_session`
boundaries. Scale = add hosts. No k8s-in-k8s anywhere — workers are just
machines, which keeps CKA realism intact.

## Idea 3 — Lab spec abstraction (multi-technology exams)

Generalize `provision_plan(contexts)` into a declarative **lab spec** per exam
type: provision recipe, grading assertions, teardown. Graders become
**workload-driven** where it makes sense (the grader runs a real client —
produce/consume for Kafka, a query load for Postgres — and asserts behavior,
not just manifest shape). Kafka/Postgres/Redis fit tier 0 naturally: they are
just workloads.

## Idea 4 — Kubernetes-native control plane (later / maybe never)

Control plane as a Deployment in a management cluster, sessions as CRDs
(`ExamSession`), sandboxes via vcluster/k3s-system-containers/Kata. Reality
check: kubelet/etcd/systemd CKA tasks can never be graded on a vcluster — so
even in a SaaS future this stays hybrid: k8s-native for tier-0/1 labs, VM fleet
path reserved for tier 2.

## Rough sequencing (proposal, not decision)

1. Tier field + tier-aware preset generation → the day the platform is
   clone-and-run with docker alone.
2. Thin backend abstraction over k3d/kind/podman.
3. Worker/queue split for anyone with >1 host.
4. Lab specs for the 2nd technology (probably Postgres or Redis — cheap tier-0).
5. K8s-native control plane only if/when multi-tenant SaaS is real.

## Open questions

- How much CKA fidelity are we willing to trade for tier-0/1 simulation
  ("kubeadm v1.31 expired-cert drills" cannot be faked)? Do we badge presets
  by tier so buyers/learners know what they get?
- Workload-driven graders: how do we keep grading deterministic and
  resource-bounded (a perf probe must not OOM a shared worker)?
- Licensing/attribution for built-in question banks if this goes public.

*Participants: Rahul, Hermes (AI pair). Last updated: 2026-09-25.*
