# TESTPLAN — FE-043

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-043` → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | manual | follow docs on a clean host (`PLATFORM_SETUP.md` → provision Node.js >= 20.19 + npm → `tools/build-frontend.sh` → start `k8s-web.service` → open `:3000`) | build + run succeeds; SPA served (no 503) | **DEFERRED** — no clean Linux host available in this sandbox; steps recorded below | |
| T2 | audit | `git grep -n 'STATUS.md\|HANDOVER.md' -- README.md`; inspect README/PLATFORM_SETUP for Node + build-on-deploy | no dead links; Node requirement + build-on-deploy documented | **PASS** — grep no matches; Node.js >= 20.19 + npm and build-on-deploy stated in README + PLATFORM_SETUP | |

## T1 clean-host steps (for the verifier / independent host)

```bash
# 0. Fresh Ubuntu 22.04/24.04 VM, repo at /root/cka-labs
# 1. Provision Node.js >= 20.19 + npm (setup-platform.sh does NOT install Node)
node --version        # expect v20.19+ (LTS 22 fine)
npm --version
# 2. Build the SPA exactly as deploy does
test -x tools/build-frontend.sh || chmod +x tools/build-frontend.sh
./tools/build-frontend.sh
test -f web/dist/index.html && echo "SPA built OK"
# 3. Run the server (or enable the systemd unit; ExecStartPre rebuilds)
sudo systemctl enable --now exam-vnc.service exam-novnc.service k8s-web.service
# 4. Verify the SPA is served (not 503) and /admin hands back index.html
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3000/
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3000/admin
# 5. Negative check: remove the build -> app routes must return 503
mv web/dist /tmp/dist.bak && curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3000/
mv /tmp/dist.bak web/dist
```

## Edge cases / additions
- `web/dist` is git-ignored (D-005) — confirm it is not tracked: `git check-ignore web/dist`.
- `web/static` must not exist (removed in FE-040): `test ! -e web/static`.
- All README relative links resolve: `PLATFORM_SETUP.md`, `PRD.md`,
  `CONCURRENT_MULTI_NODE_ARCHITECTURE.md`, `web/frontend/README.md`.

## Environment
- Commit / build: working tree on `feature/frontend-vue-migration` (no commit made)
- Host: Windows workstation (docs editing only; no Node build attempted)
- Browser(s): n/a

## Verdict
- Implementer: T2 PASS, T1 DEFERRED (2026-09-11)
- Verifier: <PASS/FAIL, timestamp, reasons if FAIL>
