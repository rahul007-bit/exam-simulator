# CKA Simulator Testing Prompt (copy this for each agent, replace PRESET_NAME)

You are testing a CKA exam simulator deployed at http://192.168.1.249:3000. Your assigned preset: **PRESET_NAME** (list: /root/cka-labs/presets/*.yaml). Work autonomously and report all results.

## Environment
- Server SSH: `ssh -o StrictHostKeyChecking=no root@192.168.1.249` (project at `/root/cka-labs`)
- **Local kubeconfig is BROKEN — run ALL kubectl via SSH on the server**
- Clusters: `k3d-cka` (3 nodes, k3s v1.30.2) and `kubeadm-vms`. Most questions use `k3d-cka` (check `target_context` in question.yaml).
- Server project paths: questions at `/root/cka-labs/questions/<domain>/<QID>-*/` (each has `question.yaml`, `setup.sh`, `grader.py`, `solution.md`), presets at `/root/cka-labs/presets/`, session state at `/root/cka-labs/var/session.json`

## API (base: http://192.168.1.249:3000)
- `POST /api/reset` — clears session + cleans cluster. ALWAYS call before starting.
- `POST /api/start` body `{"preset": "PRESET_NAME"}` — starts exam (17 tasks; medium presets have 14)
- `POST /api/action/next` — advance; **auto-grades the task you are leaving**
- `POST /api/action/jump` body `{"task_num": N}` — jump to task N; re-runs its setup.sh; grades the task you left
- `POST /api/action/flag` body `{"task_num": N}` — flag a task (its resources are preserved when navigating away)
- `POST /api/action/submit` — grades the WHOLE exam. **Call ONLY ONCE, after ALL questions are solved.**
- `GET /api/session` — session state
- **Only ONE session can be active on this server at a time** — coordinate with other agents testing other presets; serialize your full test run.

## Testing workflow (per question)
1. Read `question.yaml` (this is what the candidate sees) and `grader.py` (for exact pass criteria). Ignore `solution.md` (often an empty skeleton).
2. Verify setup.sh ran: check the namespace/resources exist. **If missing (known intermittent bug), run manually: `bash /root/cka-labs/questions/<domain>/<QID-dir>/setup.sh`** and note it.
3. Solve the question yourself from the description only (kubectl via SSH). Do NOT copy solution.md.
4. **Before calling `next`/`jump`, wait until the fixed resources are fully ready** (pods Running, endpoints populated, PVCs Bound) — graders are timing-sensitive and a premature transition records a false 0/2. If that happens: jump back to the task, re-run its setup.sh, re-solve, wait for readiness, then jump away to re-grade.
5. For PV/PVC questions: **stale PVs survive reset**. Before solving, delete any stale PV of the same name (`kubectl --context k3d-cka delete pv <name> --ignore-not-found --wait=false`), wait 2s, then apply your PV/PVC.
6. After ALL tasks solved: `POST /api/action/submit` and capture the full scorecard. Expect near-100%; any fail is either a real grader bug, a race, or a broken question — investigate before reporting.
7. At least once per preset: flag a solved task, move 2 tasks away, verify its resources still exist, jump back, confirm re-grading works.

## Known bugs (already documented — do not re-diagnose, just watch for recurrence)
1. setup.sh auto-run on `next` is INTERMITTENT — manually run setup.sh when resources are missing.
2. Reset does NOT delete cluster-scoped PVs — they persist Released/Available across sessions and break PVC binding until manually deleted.
3. TR-021 is a broken question — setup.sh cannot corrupt the Secret (K8s API rejects invalid base64, error swallowed by `2>/dev/null || true`), so it auto-passes 2/2 with zero candidate action.
4. Grading races: TR-002 (kubelet retry can take 7–40s+ to recover pod) and TR-003 (endpoints take seconds to populate) — wait for readiness before `next`.
5. Flagging a solved task resets its stored score to "Flagged for review" — recovered at final submit re-grade.

## Reporting
Append your results to `/home/amazinrahul/Projects/4-sep-test/cka-labs/task-report.md` (create section "## Preset: PRESET_NAME") with:
- Session ID and full question order
- Per-question table: # / question ID / namespace / SOLVED-AUTO-PASS-BUG / score
- New issues found (number them continuing from #8): setup failures, grader inaccuracies, missing resources, empty solution.md files, UX problems — with exact commands and evidence
- Final submit scorecard TOTAL (e.g. 34/34)

Be precise and evidence-based: quote actual grader messages and kubectl output. Do not commit to git.
