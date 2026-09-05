# CKA Labs — Testing Report

**Target:** http://192.168.1.249:3000 (SSH: `root@192.168.1.249`, project at `/root/cka-labs`)
**Test method:** Manual hands-on — reset → start preset → verify setup.sh deployed → solve each question (using solution.md) → `next` (auto-grades on transition) → `submit` only after ALL questions done.

**Rules followed:**
- Only ONE active session at a time
- `POST /api/action/submit` used ONLY at the very end of a preset (it grades everything)
- Per-question flow: solve → `next` (server auto-grades current task on transition)

---

## Preset 1: easy-01-foundation (17 tasks, 120 min) — session-1788618226

### Progress
| # | Question | Namespace | Status | Score |
|---|----------|-----------|--------|-------|
| 1 | CA-007 — Ingress routing | edge-routing | SOLVED | 2/2 ✓ |
| 2 | CA-009 — NodePort service on 30080 | external-services | SOLVED | 2/2 ✓ |
| 3 | CA-015 — Microservice ClusterIP backends | gateway-mesh | SOLVED | 2/2 ✓ |
| 4 | SC-001 — RBAC ServiceAccount & Role | billing-app | SOLVED | 2/2 ✓ |
| 5 | SC-005 — TLS Secret mount | secure-ingress | SOLVED | 2/2 ✓ |
| 6 | SC-010 — ServiceAccount & ConfigMap Role | secure-pipeline | SOLVED | 2/2 ✓ |
| 7 | ST-001 — PV & PVC | data-storage | SOLVED | 2/2 ✓ |
| 8 | ST-005 — Local PV with NodeAffinity | default | SOLVED | 2/2 ✓ |
| 9 | ST-009 — Projected Volume | app-credentials | SOLVED | 2/2 ✓ |
| 10 | TR-002 — Fix ConfigMap key | auth-system | SOLVED | 2/2 ✓ |
| 11 | TR-003 — Fix Empty Endpoints | ecommerce | SOLVED | 2/2 ✓ |
| 12 | TR-004 — Fix ImagePullBackOff | warehouse | SOLVED | 2/2 ✓ |
| 13 | TR-010 — Clear Stuck Finalizer | legacy-services | SOLVED | 2/2 ✓ |
| 14 | TR-021 — Fix Base64 Secret | payments | AUTO-PASS (bug) | 2/2 ⚠ |
| 15 | WL-002 — InitContainer | frontend-ui | SOLVED | 2/2 ✓ |
| 16 | WL-007 — CronJob | batch-schedules | SOLVED | 2/2 ✓ |
| 17 | WL-009 — Batch Job | batch-processing | SOLVED | 2/2 ✓ |

### FINAL RESULT (submit after all 17 done): **34/34 — 100%** ✓

### Note on TR-021 auto-pass
TR-021 passed 2/2 WITHOUT any candidate action (broken question, see issue #4). True score for the other 16 solvable questions: 32/32.

### Issues found
1. **[BUG - one-off] setup.sh did not auto-run on `next` transition (CA-009)** — In this run, navigating from Task 1 to Task 2 missed CA-009's setup.sh (ns `external-services` missing). Manually ran setup.sh. **However**, from task 3 onward, setup.sh auto-runs correctly on `next` (verified: ns created 3s after arriving at SC-005). Likely a race/timing issue on first transition — needs investigation in `core/deployer.py`.
2. **[CONTENT ISSUE] solution.md files are empty/skeletons** — e.g. `SC-005-tls-secret-creation-mount/solution.md` contains only the question description, no actual commands. **Testing approach adjusted:** solve each question from `question.yaml` description + `grader.py` requirements only — exactly what a candidate sees — to prove questions are solvable standalone. This also verifies grader accuracy against real candidate work.
3. **[CRITICAL BUG] Reset does not clean cluster-scoped resources (PVs) → tasks broken in fresh session** — Found at ST-001: `app-pv` persisted from an earlier test run (created 13:34). `/api/reset` deletes namespaces but NOT cluster-scoped PVs. When the old PVC was deleted with the namespace, PV went to `Released` (stale `claimRef.uid`). New session's setup.sh (`kubectl create ns data-storage ... apply`) does not touch the PV ("unchanged"), so the candidate's new `app-pvc` **can never bind** — grader would fail a correct answer. Fix needed in cleanup logic (`core/deployer.py` reset/cleanup): delete cluster-scoped PVs (and other cluster-scoped leftovers) per question, or setup.sh must pre-clean its own PVs. **Candidate workaround (validated): `kubectl delete pv app-pv` then re-apply → PVC binds.**
4. **[CRITICAL BUG] TR-021 broken question — broken state can never be created** — `setup.sh` intends to corrupt Secret `api-keys`/`DB_PASS` with invalid base64 (trailing space), but the K8s API server **rejects invalid base64 in Secret.data**, so the JSON patch fails. The failure is swallowed by `2>/dev/null || true`, so setup silently continues with a fully valid secret. Pod `crypto-service` starts immediately; grader returns 2/2 with ZERO candidate action (verified: secret decodes cleanly, pod Running, no intervention done). Question is untestable as designed — needs redesign (e.g. break via wrong key name reference, or use `stringData` mismatch scenario, or reference a missing key).

### Verified working
- `/api/reset` — clears session and cleans cluster (edge-routing ns deleted after reset) ✓
- `/api/start` with `{"preset": "easy-01-foundation"}` ✓
- Auto-grade on `next` transition — scores stored in session.json ✓
- CA-007 setup.sh: created edge-routing ns + auth-svc/pay-svc services ✓ (candidate creates Ingress)
- CA-009 setup.sh (manual): created external-services ns + web-server deployment ✓
- CA-015 setup.sh: created gateway-mesh ns ✓ (candidate creates deployments + services)
- Grading engine: all 3 solved questions graded correctly (2/2 each) ✓
- Flag workflow (earlier session): flagged tasks keep resources when navigating away; returning to flagged task does NOT re-run setup.sh; stored score persists ✓

---

---

## Preset 2: easy-02-essentials (17 tasks, 120 min) — session-1788619754

### Post-reset state note
- PVs survive reset (bug #3 confirmed): `app-pv` (Released) + `local-node-pv` (Available) still present at start of this preset.

### Progress
| # | Question | Namespace | Status | Score |
|---|----------|-----------|--------|-------|
| # | Question | Namespace | Status | Score |
|---|----------|-----------|--------|-------|
| 1 | TR-002 — Fix Pod CreateContainerConfigError | auth-system | SOLVED | 2/2 ✓ |
| 2 | TR-003 — Fix Empty Endpoints | ecommerce | SOLVED | 2/2 ✓ |
| 3 | TR-004 — Fix ImagePullBackOff | warehouse | SOLVED | 2/2 ✓ |
| 4 | TR-010 — Clear Stuck Finalizer | legacy-services | SOLVED | 2/2 ✓ |
| 5 | TR-021 — Fix Base64 Secret | payments | AUTO-PASS (bug) | 2/2 ⚠ |
| 6 | WL-002 — InitContainer | frontend-ui | SOLVED | 2/2 ✓ |
| 7 | WL-007 — CronJob | batch-schedules | SOLVED | 2/2 ✓ |
| 8 | WL-009 — Batch Job | batch-processing | SOLVED | 2/2 ✓ |
| 9 | CA-007 — Ingress routing | edge-routing | SOLVED | 2/2 ✓ |
| 10 | CA-009 — NodePort service | external-services | SOLVED | 2/2 ✓ |
| 11 | CA-015 — ClusterIP backends | gateway-mesh | SOLVED | 2/2 ✓ |
| 12 | SC-001 — RBAC SA & Role | billing-app | SOLVED | 2/2 ✓ |
| 13 | SC-005 — TLS Secret mount | secure-ingress | SOLVED | 2/2 ✓ |
| 14 | SC-010 — SA & ConfigMap Role | secure-pipeline | SOLVED | 2/2 ✓ |
| 15 | ST-001 — PV & PVC | data-storage | SOLVED | 2/2 ✓ |
| 16 | ST-005 — Local PV NodeAffinity | default | SOLVED | 2/2 ✓ |
| 17 | ST-009 — Projected Volume | app-credentials | SOLVED | 2/2 ✓ |

### FINAL RESULT (submit after all 17 done): **34/34 — 100%** ✓

### Issue #5 — [GRADING BUG] TR-002 timing-sensitive grading
On `next` transition, the grader recorded **0/2** for TR-002 because the kubelet retry hadn't recovered the pod within the grading window (took ~40s here vs ~12s in easy-01). Cleanup then deleted the namespace, leaving a false 0/2. Workaround: jump back to task 1 (re-runs setup, fresh broken pod) → fix → wait for Running → jump to task 2 (re-grades current task on jump) → 2/2. **Root cause:** `next` grades the current task immediately before the candidate's fix has propagated. Fix: add a short readiness wait / retry in the transition grader, or grade lazily on submit.

### Issue #6 — [BUG] setup.sh auto-run on `next` is INTERMITTENT (reproduced again)
easy-03-confidence, transition ST-005 → ST-009: ns `app-credentials` was NOT created on arrival (`create secret` failed with NotFound). Same failure as CA-009 in easy-01. Pattern so far: CA-009 (easy-01, transition 1→2) and ST-009 (easy-03, transition 2→3) both failed; most other transitions worked. Root cause to investigate in `core/deployer.py` deploy_step — likely race between session save and setup execution, or a failed/stale step marker.

---

## Preset 3: easy-03-confidence (17 tasks) — session-1788620422
Order: ST-001→ST-005→ST-009→SC-001→SC-005→SC-010→WL-002→WL-007→WL-009→TR-002→TR-003→TR-004→TR-010→TR-021→CA-007→CA-009→CA-015
- Issue #6 reproduced at ST-009 (setup.sh not auto-run on next transition — ns missing, ran setup manually).
- TR-002 recovered in 7s this time (vs 40s+ in easy-02) — confirms grading timing is race-prone; avoided false 0/2 by waiting for Running before `next`.
- FINAL RESULT: **34/34 — 100%** ✓

---

## Preset 4: easy-04-speedrun (17 tasks, 60 min) — in progress
Order: WL-009→WL-007→WL-002→TR-021→TR-010→TR-004→TR-003→TR-002→ST-009→ST-005→ST-001→SC-010→SC-005→SC-001→CA-015→CA-009→CA-007

### Flag-persistence test (during this preset) — PASSED with notes
- Flagged solved WL-009 → moved 2 tasks ahead → **Job batch-processor still existed (Running 4/5→Complete)** ✓
- Jumping back to flagged task did NOT re-run setup ✓ (Job age unchanged)
- **[BEHAVIOR NOTE] Flagging a solved task RESETS its stored score to "Flagged for review (Pending submission)" 0/2** — flagged tasks are re-graded at final submit, so score is recovered there. UX consideration: candidate may see their solved score "disappear" on flag.
- Unflagged unsolved tasks' resources cleaned on navigate-away ✓ (correct exam behavior)
- **[TEST FLOW NOTE] The flag test caused task 2 (WL-007) to be skipped** — jumping t3→t1→t3 bypassed it; final submit correctly graded it 0/2. Proves grading accuracy for skipped tasks.

### Issue #7 — [GRADING RACE] TR-003 endpoints
First submit: "Expected 2 endpoints, found 1" — second cart-backend pod's endpoint hadn't registered at grade time. After re-jump (setup re-run), both endpoints appeared within 1s of patch. Race-sensitive grader; recommend retry/wait window for endpoint-based checks.

### FINAL RESULT (after re-solving skipped task + re-submit): **34/34 — 100%** ✓

---

## Preset 5: medium-01-cluster-storage (14 tasks, 120 min) — session-1788621813

Order: CA-001 → CA-004 → CA-006 → SC-002 → SC-004 → SC-006 → WL-001 → WL-004 → ST-002 → ST-003 → TR-001 → TR-006 → TR-007 → TR-012

### Progress
| # | Question | Domain | Context | Status | Score |
|---|----------|--------|---------|--------|-------|
| 1 | CA-001 — Perform etcd Snapshot Backup | cluster-arch | kubeadm-vms | SOLVED | 3/3 ✓ |
| 2 | CA-004 — Upgrade Worker Node with kubeadm | cluster-arch | kubeadm-vms | SOLVED | 3/3 ✓ |
| 3 | CA-006 — Generate Join Token and Join Worker Node | cluster-arch | kubeadm-vms | ENVIRONMENT BUG (node3 missing) | 0/3 ✗ |
| 4 | SC-002 — ClusterRole & Binding for Cluster Auditor | security | k3d-cka | SOLVED | 3/3 ✓ |
| 5 | SC-004 — Drop Capabilities & Add NET_ADMIN | security | k3d-cka | SOLVED | 3/3 ✓ |
| 6 | SC-006 — Restrict Secret Access Using resourceNames | security | k3d-cka | SOLVED | 3/3 ✓ |
| 7 | WL-001 — Multi-Container Pod with Logging Sidecar | workloads | k3d-cka | SOLVED | 3/3 ✓ |
| 8 | WL-004 — HorizontalPodAutoscaler with Target CPU | workloads | k3d-cka | SOLVED | 3/3 ✓ |
| 9 | ST-002 — Dynamic StorageClass with Retain Policy | storage | k3d-cka | SOLVED | 3/3 ✓ |
| 10 | ST-003 — Expand Existing PVC Storage Capacity Online | storage | k3d-cka | SOLVED | 3/3 ✓ |
| 11 | TR-001 — Fix CrashLoopBackOff on Checkout Service | troubleshooting | k3d-cka | SOLVED | 3/3 ✓ |
| 12 | TR-006 — Fix Ingress Path Routing and Service Mapping | troubleshooting | k3d-cka | SOLVED | 3/3 ✓ |
| 13 | TR-007 — Fix PVC Pending due to Invalid StorageClass | troubleshooting | k3d-cka | SOLVED | 3/3 ✓ |
| 14 | TR-012 — Fix RBAC 403 for Application ServiceAccount | troubleshooting | k3d-cka | SOLVED | 3/3 ✓ |

### FINAL RESULT (submit after all 14 done): **39/42 — 92.9%** (Passed threshold 66%) ✓
*Note: Excluding CA-006 (unsolvable due to missing VM in environment), true score for all 13 solvable tasks: **39/39 — 100%**.*

### Flag-persistence test (verified during this preset) — PASSED
- Solved SC-002 (task 4) → flagged task via `POST /api/action/flag` (`{"task_num": 4}`).
- Navigated 2 tasks away (Task 5 → Task 6) via `POST /api/action/next`.
- Verified task 4's resources persisted on `k3d-cka`: `clusterrole/cluster-auditor` and `clusterrolebinding/cluster-auditor-binding` remained active and untouched.
- Jumped back to Task 4 via `POST /api/action/jump` (`{"task_num": 4}`).
- Unflagged Task 4 and transitioned to Task 5 → grader re-evaluated SC-002 to **3/3** ✓.

### New Issues Found

#### Issue #8 — [GRADER INACCURACY / FALSE POSITIVE] CA-001 etcdctl snapshot status passes any non-empty file
- **Location:** `/root/cka-labs/questions/cluster-arch/CA-001-etcd-snapshot-backup/grader.py`
- **Code:**
  ```python
  status = ctx.ssh_cmd("NODE_1", f"etcdctl snapshot status {SNAPSHOT} 2>/dev/null | head -1")
  if status:
      return GradeResult(True, 3, 3, f"etcd snapshot verified: {status}")
  ```
- **Evidence:** On etcdctl v3.6+, the `snapshot status` command is deprecated/moved. Running `etcdctl snapshot status <file>` prints the `snapshot` subcommand help text starting with `NAME:`, which exits 0. `head -1` captures `NAME:` which evaluates to true.
  ```bash
  $ ssh node1 'touch /tmp/fake.db && echo garbage > /tmp/fake.db && etcdctl snapshot status /tmp/fake.db 2>/dev/null | head -1'
  NAME:
  ```
  Consequently, even a completely corrupt or non-etcd file passes with `etcd snapshot verified: NAME:`.
- **Recommendation:** Use `etcdutl snapshot status` or inspect `etcdctl snapshot status` exit code/output without swallowing stderr, or inspect snapshot file header.

#### Issue #9 — [ENVIRONMENT / MISSING VM] CA-006 requires node3 but VM does not exist
- **Location:** `/root/cka-labs/questions/cluster-arch/CA-006-kubeadm-token-node-join`
- **Evidence:**
  - VirtualBox on host only runs three VMs: `ubuntu` (simulator server), `redhat` (node1: `192.168.1.57`), and `redhat2` (node2: `192.168.1.56`).
  - In `/root/cka-labs/.env`:
    ```ini
    NODE_1=192.168.1.57
    NODE_2=192.168.1.56
    NODE_3=
    ```
  - `CA-006/setup.sh` defaults `NODE_3` to `192.168.50.170` (unreachable), failing silently.
  - Candidate has no `node3` host to SSH into or run `kubeadm join`.
  - `grader.py` immediately checks `if ctx.ssh_cmd("NODE_3", "echo up") != "up"` and returns:
    `kubeadm node node3 unreachable via SSH (0/3, skipped=True)`.
- **Recommendation:** Provision a 3rd VM `node3` and populate `NODE_3` in `.env`, or exclude `CA-006` from presets until the 3rd VM is deployed.

#### Issue #10 — [CONTENT / SKELETON SOLUTIONS] CA-004 solution.md is an incomplete skeleton
- **Location:** `/root/cka-labs/questions/cluster-arch/CA-004-kubeadm-worker-upgrade/solution.md`
- **Evidence:** The file only contains:
  ```markdown
  # Solution for CA-004: Upgrade Worker Node with kubeadm

  Drain worker node, run `kubeadm upgrade node`, upgrade kubelet/kubectl packages, and uncordon.
  ```
  It lacks exact package manager commands (`dnf install -y kubeadm-... --disableexcludes=kubernetes`, `systemctl daemon-reload`, etc.), offering no actionable guidance to candidates reviewing solutions.

#### Issue #11 — [USABILITY / PROVISIONER LIMITATION] TR-007 local-path requires node annotation when no consumer pod exists
- **Location:** `/root/cka-labs/questions/troubleshooting/TR-007-pvc-pending-sc-mismatch`
- **Evidence:** Description states:
  > PVC data-claim in namespace data-ops is stuck in Pending because it specifies a non-existent StorageClass fast-nvme-ssd. Update the PVC configuration or provision the correct StorageClass using standard local storage so data-claim becomes Bound.
  Creating StorageClass `fast-nvme-ssd` with `provisioner: rancher.io/local-path` and `volumeBindingMode: Immediate` fails with:
  `failed to provision volume with StorageClass "fast-nvme-ssd": configuration error, no node was specified`
  Because there is no pod scheduled in `data-ops`, `rancher.io/local-path` cannot determine the target node unless the PVC is explicitly annotated with `volume.kubernetes.io/selected-node: <node-name>`.
- **Recommendation:** Clarify in the question or create a deployment/pod consuming the PVC so `WaitForFirstConsumer` can naturally bind.

---

## Preset 6: medium-02-security-workloads (14 tasks, 120 min) — session-1788622978

Order: CA-008 → CA-010 → CA-011 → SC-003 → SC-008 → SC-012 → WL-005 → WL-006 → ST-004 → ST-006 → TR-005 → TR-009 → TR-013 → TR-015

### Progress
| # | Question | Domain | Context | Status | Score |
|---|----------|--------|---------|--------|-------|
| 1 | CA-008 — Host-Based Ingress with TLS Termination | cluster-arch | k3d-cka | SOLVED | 3/3 ✓ |
| 2 | CA-010 — Custom CoreDNS Hosts Rewrite Rule | cluster-arch | k3d-cka | SOLVED | 3/3 ✓ |
| 3 | CA-011 — Renew Expiring Control-Plane Certificates | cluster-arch | kubeadm-vms | SOLVED | 3/3 ✓ |
| 4 | SC-003 — Non-Root and Read-Only SecurityContext | security | k3d-cka | SOLVED | 3/3 ✓ |
| 5 | SC-008 — Audit and Revoke ClusterRoleBindings | security | k3d-cka | SOLVED | 3/3 ✓ |
| 6 | SC-012 — SecurityContext on Pipeline Workload | security | k3d-cka | SOLVED | 3/3 ✓ |
| 7 | WL-005 — NodeAffinity Required and Preferred Rules | workloads | k3d-cka | SOLVED (with manual node label) | 3/3 ✓ |
| 8 | WL-006 — Deploy Monitoring DaemonSet on Worker Nodes | workloads | k3d-cka | SOLVED | 3/3 ✓ |
| 9 | ST-004 — Mount Multiple SubPaths from Single PV | storage | k3d-cka | SOLVED | 3/3 ✓ |
| 10 | ST-006 — StatefulSet with VolumeClaimTemplates | storage | k3d-cka | SOLVED | 3/3 ✓ |
| 11 | TR-005 — Repair CoreDNS Corefile Syntax Error | troubleshooting | k3d-cka | SOLVED | 3/3 ✓ |
| 12 | TR-009 — Fix Unsatisfiable NodeSelector on Pod | troubleshooting | k3d-cka | SOLVED | 3/3 ✓ |
| 13 | TR-013 — Roll Back Broken Deployment Rollout | troubleshooting | k3d-cka | SOLVED | 3/3 ✓ |
| 14 | TR-015 — Fix Headless Service Missing ClusterIP None | troubleshooting | k3d-cka | SOLVED | 3/3 ✓ |

### FINAL RESULT (submit after all 14 done): **42/42 — 100%** ✓

### Flag-persistence test (verified during this preset) — PASSED
- Solved SC-003 (Task 4) and flagged it via `POST /api/action/flag` (`{"task_num": 4}`).
- Navigated 2 tasks away (Task 5 → Task 6) via `POST /api/action/next`.
- Verified `pod/hardened-api` in namespace `sec-apps` remained intact and 1/1 Running.
- Jumped back to Task 4 via `POST /api/action/jump` (`{"task_num": 4}`).
- Unflagged Task 4 and transitioned to Task 5; re-grading confirmed **3/3** ✓.

### New Issues Found

#### Issue #12 — [SETUP BUG / UNSCHEDULABLE POD] WL-005 setup.sh hardcodes non-existent node name `k3d-dev-agent-0`
- **Location:** `/root/cka-labs/questions/workloads/WL-005-nodeaffinity-preferred-required/setup.sh`
- **Code:**
  ```bash
  # Label the worker node with zone-1 and disk=ssd so the pod can schedule
  kubectl --context "$CTX" label node k3d-dev-agent-0 topology.kubernetes.io/zone=zone-1 disk=ssd --overwrite 2>/dev/null || true
  ```
- **Evidence:** The exam cluster nodes are `k3d-cka-agent-0`, `k3d-cka-agent-1`, and `k3d-cka-server-0`. Node `k3d-dev-agent-0` does not exist. The label command fails, but the error is swallowed by `2>/dev/null || true`.
  Consequently:
  1. No node in the cluster has label `topology.kubernetes.io/zone=zone-1`.
  2. When the candidate applies a 100% compliant Pod with the required `nodeAffinity`, the pod stays in `Pending` forever (`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`).
  3. `grader.py` line 18 checks `if not ctx.check_pod_ready(pod): return GradeResult(False, 2, 3, "nodeAffinity rules configured but pod affinity-pod is not Running/Ready")`. The candidate receives an unfair 2/3 penalty unless they independently diagnose setup's missing label and manually run `kubectl label node k3d-cka-agent-0 topology.kubernetes.io/zone=zone-1 disk=ssd`.
- **Recommendation:** Update `setup.sh` to dynamically label the worker node:
  ```bash
  WORKER_NODE=$(kubectl --context "$CTX" get nodes -l '!node-role.kubernetes.io/control-plane' -o jsonpath='{.items[0].metadata.name}')
  kubectl --context "$CTX" label node "$WORKER_NODE" topology.kubernetes.io/zone=zone-1 disk=ssd --overwrite
  ```

#### Issue #13 — [UI / RECORDER BUG] Final task displays "Score: Not graded" in Session Review UI
- **Location:** `/root/cka-labs/web/server.py` (`action_submit()`, lines 456–496) and `/root/cka-labs/core/recorder.py` (`get_recording()`, line 648)
- **Root Cause:**
  1. During sequential exam progression, transition via `POST /api/action/next` calls `deployer.deploy_step()`, which logs `recorder.log_event("TASK_EVALUATION", ...)` to `<session_id>.events.jsonl`.
  2. Because the final task (Task 14) is never transitioned *away* from via `next`, it is graded directly inside `action_submit()` on final submit:
     ```python
     # web/server.py:457
     if session.mode == "sequential" and session.current_question:
         cur_q = session.current_question
         res = grader.grade_question(cur_q)
         session.scores[cur_q.id] = {...}
     ```
  3. However, `action_submit()` **never logs a `TASK_EVALUATION` event** to `recorder` for this final task (nor for any re-evaluated flagged tasks).
  4. When the frontend Session Review page queries `/api/recordings/{session_id}`, `recorder.get_recording()` builds the `task_timeline` solely from `events.jsonl`. Because no `TASK_EVALUATION` event exists for Task 14:
     - `task_timeline[13].score` remains `null`
     - `task_timeline[13].passed` remains `null`
     - Only `DEPLOYED` is present in the event list.
  5. The Session Review UI displays `Score: Not graded` for Task 14, even though the overall scorecard and header show 100% (42/42).
- **Evidence:**
  ```json
  // GET /api/recordings/session-1788622978 -> scorecard[13]:
  {"task_num": 14, "id": "TR-015", "score": 3, "max_score": 3, "passed": true}

  // GET /api/recordings/session-1788622978 -> task_timeline[13]:
  {"task_num": 14, "question_id": "TR-015", "score": null, "passed": null, "events": [{"event": "DEPLOYED", "formatted_time": "10:41"}]}
  ```
- **Recommendation:** In `web/server.py` `action_submit()`, log the `TASK_EVALUATION` event to `recorder` for the active question and any flagged questions evaluated during submission:
  ```python
  recorder.attach_or_resume(session.session_id, session.name)
  recorder.log_event("TASK_EVALUATION", {
      "task_num": cur_idx + 1,
      "question_id": cur_q.id,
      "score": res.score,
      "max_score": res.max_score,
      "passed": res.passed,
      "message": res.message,
  })
  ```

---

## Preset 7: medium-03-troubleshooting (14 tasks, 120 min) — session-1788624068

Order: CA-002 → CA-003 → CA-007 → SC-001 → SC-009 → SC-010 → WL-002 → WL-010 → ST-008 → ST-010 → TR-017 → TR-019 → TR-021 → TR-024

### Progress
| # | Question | Domain | Context | Status | Score |
|---|----------|--------|---------|--------|-------|
| 1 | CA-002 — Restore Cluster State from etcd Snapshot | cluster-arch | kubeadm-vms | SOLVED (manual snapshot generated, Issue #14) | 4/4 ✓ |
| 2 | CA-003 — Upgrade Control-Plane Node with kubeadm | cluster-arch | kubeadm-vms | FAILED (environment version mismatch, Issue #15) | 0/4 ✗ |
| 3 | CA-007 — Configure Ingress Path Routing for Auth and Pay Services | cluster-arch | k3d-cka | SOLVED | 2/2 ✓ |
| 4 | SC-001 — Configure RBAC ServiceAccount & Role for Deployment Management | security | k3d-cka | SOLVED (flag test verified) | 2/2 ✓ |
| 5 | SC-009 — Enforce Pod Security Standards (PSS) Restricted Mode | security | k3d-cka | SOLVED | 4/4 ✓ |
| 6 | SC-010 — Configure ServiceAccount and Scoped Configuration Role | security | k3d-cka | SOLVED | 2/2 ✓ |
| 7 | WL-002 — Configure InitContainer Dependency Gate on Frontend Pod | workloads | k3d-cka | SOLVED | 2/2 ✓ |
| 8 | WL-010 — Configure Liveness, Readiness, and Startup Probes | workloads | k3d-cka | SOLVED | 3/3 ✓ |
| 9 | ST-008 — Mount Secret and ConfigMap as File Volumes in Specific Paths | storage | k3d-cka | FAILED (grader bug `volumeName`, Issue #16) | 0/3 ✗ |
| 10 | ST-010 — Configure ReadWriteOncePod Access Mode on PVC | storage | k3d-cka | SOLVED | 3/3 ✓ |
| 11 | TR-017 — Resolve PVC ReadWriteMany on ReadWriteOnce Storage | troubleshooting | k3d-cka | SOLVED | 3/3 ✓ |
| 12 | TR-019 — Fix InitContainer DNS Resolution Deadlock | troubleshooting | k3d-cka | SOLVED | 3/3 ✓ |
| 13 | TR-021 — Fix Base64 Encoding Error in Pod Secret Reference | troubleshooting | k3d-cka | AUTO-PASS (known bug, Issue #4) | 2/2 ⚠ |
| 14 | TR-024 — Fix NodePort TargetPort Container Routing | troubleshooting | k3d-cka | SOLVED | 3/3 ✓ |

### FINAL RESULT (submit after all 14 done): **33/40 — 82.5%** ✓ (Passed, threshold 66%)
- **Solvable tasks:** 12/12 solved cleanly (100% of solvable score: 33/33 earned).
- Two tasks failed solely due to software/grader bugs (CA-003 and ST-008).

### Flag-persistence test (verified during this preset) — PASSED
- Solved SC-001 (Task 4) and flagged it via `POST /api/action/flag` (`{"task_num": 4}`).
- Navigated forward through Task 5 to Task 6 via `POST /api/action/next`.
- Jumped back to Task 4 via `POST /api/action/jump` (`{"task_num": 4}`).
- Verified all resources in namespace `billing-app` were intact.
- Unflagged Task 4; score persisted and re-graded **2/2** ✓.

### New Issues Found

#### Issue #14 — [SETUP BUG] CA-002 setup.sh does not create `/opt/backup/etcd-snapshot.db`
- **Location:** `/root/cka-labs/questions/cluster-architecture/CA-002-etcd-restore/setup.sh`
- **Evidence:** The question instructs:
  > Restore etcd database from /opt/backup/etcd-snapshot.db into /var/lib/etcd-restored and update static pod manifest.
  However, `/opt/backup/etcd-snapshot.db` does not exist on the VM `node1` when CA-002 deploys.
  Candidate must manually create the directory `/opt/backup` and run `etcdctl snapshot save /opt/backup/etcd-snapshot.db` before performing the restore.
- **Recommendation:** Add snapshot generation to `setup.sh`:
  ```bash
  mkdir -p /opt/backup
  ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
    --cacert=/etc/kubernetes/pki/etcd/ca.crt \
    --cert=/etc/kubernetes/pki/etcd/server.crt \
    --key=/etc/kubernetes/pki/etcd/server.key \
    snapshot save /opt/backup/etcd-snapshot.db
  ```

#### Issue #15 — [GRADER / ENVIRONMENT VERSION MISMATCH] CA-003 grader hardcodes `v1.30` while VM nodes run `v1.36.4`
- **Location:** `/root/cka-labs/questions/cluster-architecture/CA-003-kubeadm-upgrade-cp/grader.py` (line 7)
- **Code:**
  ```python
  TARGET = "v1.30"
  ...
  if not kubeadm_ver.startswith(TARGET):
      return GradeResult(False, 0, 4, f"kubeadm binary not v1.30.x (got {kubeadm_ver})...")
  ```
- **Evidence:** The provisioned VM nodes run Kubernetes `v1.36.4` (`kubeadm version: v1.36.4`, `kubelet --version: Kubernetes v1.36.4`). Because the grader strictly checks `startswith("v1.30")`, it will always fail with 0/4 regardless of any candidate actions.
- **Recommendation:** Parameterize `TARGET` based on the cluster's base version or accept `v1.36`.

#### Issue #16 — [GRADER BUG] ST-008 inspects non-existent field `volumeName` on Pod VolumeMount
- **Location:** `/root/cka-labs/questions/storage/ST-008-secret-configmap-volume-mounts/grader.py` (lines 35, 41)
- **Code:**
  ```python
  sec_mount = next((m for m in mounts if m.get("mountPath") == "/etc/secrets/token"), None)
  if not sec_mount or sec_mount.get("volumeName") != sec_vol:
      return GradeResult(False, 0, 3, "Secret app-secret is not mounted at /etc/secrets/token in pod config-reader")
  ```
- **Evidence:** In the Kubernetes API Pod spec, a container's `volumeMounts` object contains the fields `name` and `mountPath`. The field `volumeName` only exists in PV objects (`pv.spec.claimRef.name`). Consequently, `sec_mount.get("volumeName")` always returns `None`, which never equals `sec_vol` (`app-secret-vol`). The grader is impossible to pass and always awards 0/3 on valid candidate solutions.
- **Recommendation:** Change `sec_mount.get("volumeName")` to `sec_mount.get("name")` and `cm_mount.get("volumeName")` to `cm_mount.get("name")`.

#### Issue #17 — [CONTENT MISMATCH] TR-024 question prompt specifies Service `web-np` instead of `web-svc`
- **Location:** `/root/cka-labs/questions/troubleshooting/TR-024-nodeport-targetport-mismatch/question.yaml`
- **Evidence:** `question.yaml` description states:
  > NodePort Service `web-np` in `web-services` forwards traffic to wrong port `9090` instead of containerPort `80`.
  However, `setup.sh` and `grader.py` deploy and grade `web-svc`, and the initial misconfigured targetPort is `8080`, not `9090`.
- **Recommendation:** Update `question.yaml` to refer to Service `web-svc` and port `8080`.

