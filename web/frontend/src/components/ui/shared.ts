/**
 * Shared class fragments for the UI primitives (FE-012).
 *
 * Every colour, radius and shadow resolves to a token from `tokens.css` — either
 * through the `@theme inline` mapping in `base.css` (e.g. `bg-surface`,
 * `text-accent-text`) or an arbitrary `var(--token)` value. No raw hex, glow or
 * gradient is allowed (FE-002 / FE-014).
 */

/**
 * Keyboard-only focus ring built from the focus-ring tokens. `outline-2` in
 * Tailwind v4 emits the width *and* the solid style, so the ring matches the
 * global `:focus-visible` rule in `base.css` while staying explicit per control.
 */
export const FOCUS_RING =
  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring-color)]'

/** Disabled affordance shared by every interactive primitive. */
export const DISABLED = 'disabled:cursor-not-allowed disabled:opacity-60'
