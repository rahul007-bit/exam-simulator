# FE-025 — orchestrator resolution

The implementer delivered `XTerm.vue` + `useTerminal.ts` but reported **BLOCKED** on
missing runtime deps.

Resolved after the batch:
- Installed `@xterm/xterm@5.5.0` and `@xterm/addon-fit@0.10.0` (versions matching the
  legacy `index.html` pins).
- `bunx vue-tsc --noEmit` → **exit 0** (the island now compiles; the earlier block was
  the absent packages).

Testing profile: **paused per user directive** — only the typecheck above was run.
Runtime/Playwright verification of the terminal island is deferred (requires the
Linux backend + `/ws/terminal`), to be covered at the FE-V3 gate.
