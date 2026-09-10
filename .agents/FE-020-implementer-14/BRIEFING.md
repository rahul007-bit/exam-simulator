# BRIEFING — FE-020

## Mission
Deliver the slim candidate app shell and 52px header so the exam workspace has a
single, minimal primary bar and a `⋯` overflow for everything secondary.

## 🔒 Identity
- Task: FE-020
- Role: implementer
- Working directory: .agents/FE-020-implementer-14
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-012 (UI primitives), FE-014 (icon set) — both `verified`.
- **Acceptance criteria:**
  1. header shows only primary controls (exam name, progress, timer, Flag,
     Submit); secondary controls live in a single overflow menu;
  2. session-id copy and admin End/Reset moved to the overflow;
  3. responsive at 1366x768 and 1920x1080 with no overflow/clipping.
- **Test cases:** T1 load candidate view (header contents + overflow); T2
  screenshot/audit at 1366x768 and 1920x1080 (no overflow/clipping).
- **Verifier:** independent agent (never the implementer).

## Key constraints
- Follow `decisions.md`; no contradicting accepted decisions.
- Strict behavioral parity (D-007): legacy workspace dropdown ordering and
  admin gating preserved; no raw hex/glow/emoji (FE-002/FE-014).
- Scope: only `src/components/layout/**` and `src/views/CandidateView.vue`.
  Never self-certify.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md` (§5 candidate UX)
- Protocol: `.agents/frontend-migration/PROTOCOL.md` (§9 batch rules)
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `web/frontend/src/components/layout/**`,
  `web/frontend/src/views/CandidateView.vue`

## Artifact index
- `.agents/FE-020-implementer-14/DISPATCH.md`
- `.agents/FE-020-implementer-14/progress.md`
- `.agents/FE-020-implementer-14/EVIDENCE.md`
- `.agents/FE-020-implementer-14/TESTPLAN.md`
