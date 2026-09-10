# FE-004 — Live openapi.json comparison (platform host)

Date: 2026-09-10
Source: `http://10.8.0.15:3000/openapi.json` (live FastAPI), captured after the VPN MTU
fix (HTTP 200, 17,500 bytes).
Snapshot: `web/frontend/openapi.json` (curated, used by `scripts/gen-api.mjs`).

## Result

The two artifacts intentionally differ in shape:

- **Shared schemas (by name) match on property names + `required`** — no differences
  reported. This includes the request models (`StartRequest`, `JumpRequest`,
  `FlagRequest`, `AdminLoginRequest`, `AdminConfigRequest`, `SetResourceLimitRequest`,
  `CreateSessionInviteRequest`, `RestoreSessionRequest`, ...).
- **LIVE-only paths (17)** not yet in the snapshot (belong to later migration tasks):
  `/admin`, `/api/questions`, `/api/clipboard`, `/api/recordings`,
  `/api/recordings/{session_id}`, `/api/recordings/{session_id}/cast`,
  `/api/recordings/{session_id}/event`, `/api/recordings/{session_id}/events`,
  `/api/reports`, `/api/reports/{filename}`, `/api/sessions`,
  `/api/admin/infrastructure`, `/api/admin/infrastructure/terminate`,
  `/api/admin/session/{session_id}`, `/api/admin/sessions/{identifier}/terminate`,
  `/api/admin/sessions/{identifier}/reset`, `/api/admin/sessions/{identifier}/end`.
- **LIVE-only schemas (5)**: `ClientEventRequest`, `ClipboardRequest`,
  `HTTPValidationError`, `TerminateResourceRequest`, `ValidationError`.
- **SNAPSHOT-only schemas (25)**: the curated response types
  (`SessionResponse`, `SessionActive/Inactive/Invited`, `TimerResponse`,
  `PresetsResponse`, `Preset`, `PresetLockedInfo`, `TaskData`, `TaskScoreData`,
  `FlagResponse`, `SubmitResponse`, `ScorecardRow`, `AdminSessionItem`,
  `AdminSessionsResponse`, `ResourceInfo`, `ErrorDetail`, etc.).

## Interpretation

FastAPI only emits schemas for request bodies and `response_model`-declared returns;
the server returns plain dicts, so the live spec carries **no response schemas**. The
snapshot therefore deliberately *adds* response typings for the client. The correct
oracle for those response types is `web/server.py` source (already used by
`verifier-3`), not the raw spec. The live diff confirms:
1. all covered request contracts match, and
2. the missing live paths correspond to features not yet migrated (expected).

No snapshot change required for FE-004 (changing it would invalidate FE-004
verification without improving correctness). The 17 missing paths will be added as
their UI tasks land (candidate clipboard/recordings/reports; admin infra/session
actions).
