# EVIDENCE — FS-009 Per-terminal channel recording, conditional provisioning, notifications

Agent: opencode. Date: 2026-09-11. Depends FS-003b. Plan: HANDOVER P1–P4,
decisions D-012 (channels) + D-013 (notifications).

## Deliverable
- **P1 conditional provisioning** — `core/sandbox_orchestrator.py`
  `provision_plan(contexts)`: Incus/kubeadm only when `KUBEADM_CONTEXT` is in the
  session contexts; k3d only for k3d contexts; desktop always; mixed preset
  provisions both. `provision_session(sid, contexts=...)`; callers pass
  `session.target_contexts`; dead `ensure_k3d_cluster_running` removed.
- **P2 per-channel scrollback + render fixes** — `terminal:buffer:{sid}:{channel}`
  (+idle TTL, expire helper); admin web terminal has no candidate scrollback and
  no buffer; `XTerm.vue` connects only when visible and `fit()` re-sends resize +
  repaints.
- **P3 channel+actor recording** — `core/recorder.py` per-channel casts
  `{sid}.{channel}.cast` (legacy `{sid}.cast` = user-web); channel-tagged events;
  `get_cast_path(sid, channel)`; `channels` in `get_recording`;
  `/api/recordings/{sid}/cast?channel=`. Replay UI: User dropdown (Web/Desktop)
  + Admin tab, channel-filtered events, `.cast` download removed.
- **P4 desktop terminal recording** — `docker/desktop/desk-terminal-record.py`
  (pty wrapper) publishes `user-desktop` input+output; entrypoint launches it;
  retired the `xinput` sniffer.
- **Admin notifications** — `POST /api/admin/sessions/{id}/notify` →
  `redis_bus.publish_notification` → `notify:{sid}`; desk-agent shows a **native
  XFCE notification** (`notify-send`, app "Exam", 15s) with `xmessage` fallback;
  Observe overlay "Notify" button + modal.

## Verification
- `tests/test_provision_plan.py`, `tests/test_channel_recording.py`,
  `tests/test_multi_session.py`, `tests/test_session_resolver.py`; frontend
  vitest for replay/recordings/notify UI; build + Playwright.
- Backend suite 107 tests (3 known host-only failures); frontend 283 vitest + 21
  Playwright.
- Host smoke: subscribers `notify:{sid}` = 1, publish receiver = 1,
  `xfce4-notifyd` running, no `xmessage` process (native path).

## Deploy
- `web/api` + `core` + `web/dist` redeployed; image rebuilt
  (`cka-desktop:pre-p4`, `pre-notify`, `pre-notifyd` rollback tags).
- Rollback tarballs: `/tmp/pre-p1..pre-p4`, `/tmp/pre-notify`, `/tmp/pre-final`.
