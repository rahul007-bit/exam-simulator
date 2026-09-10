# DISPATCH — FE-027

## 2026-09-10 11:17 UTC
You are assigned task **FE-027** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-027-implementer-20`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
`useClipboard` composable + headless `ClipboardBridge.vue` implementing
host↔VNC clipboard sync over the session WS (`clipboard_update` /
`clipboard_copy`) with `GET/POST /api/clipboard` fallback and the legacy
`pendingHostClipboardText` user-gesture flush.

### Acceptance criteria
1. Copy in host reaches desktop and vice-versa.
2. Pending-flush logic preserved verbatim for browser permission.
3. No busy `/api/clipboard` polling while the WS is connected.

### Verification method
- `bunx vue-tsc --noEmit` (must pass; only the two owned files are new).
- Manual: copy host → desktop (paste in noVNC), copy desktop → host.
- Network/WS inspect: confirm no recurring `GET /api/clipboard` while the
  `/ws/session/<sid>` socket is OPEN.

### Constraints
- One focused change.
- Preserve parity behavior (WS, clipboard, timer, token routing).
- Update `EVIDENCE.md` with proof.
