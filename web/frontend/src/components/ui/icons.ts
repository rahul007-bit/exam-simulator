/**
 * Icon catalogue (FE-014).
 *
 * A single, typed source of truth for every inline SVG glyph used by the UI.
 * Shapes are described declaratively (stroke-based, `viewBox="0 0 24 24"`) so the
 * `Icon.vue` renderer stays tiny and no component needs hand-rolled `<svg>`
 * markup. This replaces the ad-hoc inline SVGs that had accumulated in the toast
 * host, chips, selects and the data table.
 *
 * Constraints (D-003 / FE-014):
 *  - stroke-only, `currentColor`: colours come from the surrounding token utilities;
 *  - no fills, gradients, filters, shadows or emoji — icons are chrome, not art.
 *
 * Lives in a plain `.ts` module (not the SFC) so tests and `tsc` can import the
 * name union without depending on SFC internals (see `env.d.ts`).
 */

export interface IconPath {
  tag: 'path'
  /** SVG path `d` attribute. */
  d: string
  /** Optional utility classes for this individual shape (e.g. the spinner fade). */
  class?: string
}

export interface IconCircle {
  tag: 'circle'
  cx: number
  cy: number
  r: number
  class?: string
}

export type IconShape = IconPath | IconCircle

/**
 * Every glyph the UI needs today (toast variants, close, chevrons, sort,
 * spinner, theme toggle) plus the common chrome glyphs the candidate/admin
 * surfaces will consume next (copy, timer, flag, overflow, replay, workspace).
 */
export const ICONS = {
  info: [
    { tag: 'circle', cx: 12, cy: 12, r: 9 },
    { tag: 'path', d: 'M12 16v-4' },
    { tag: 'path', d: 'M12 8h.01' },
  ],
  success: [
    { tag: 'circle', cx: 12, cy: 12, r: 9 },
    { tag: 'path', d: 'm8.5 12.5 2.5 2.5 4.5-5' },
  ],
  warning: [
    { tag: 'path', d: 'M12 3 2.5 20h19z' },
    { tag: 'path', d: 'M12 9v5' },
    { tag: 'path', d: 'M12 17h.01' },
  ],
  error: [
    { tag: 'circle', cx: 12, cy: 12, r: 9 },
    { tag: 'path', d: 'm9 9 6 6M15 9l-6 6' },
  ],
  close: [{ tag: 'path', d: 'M6 6l12 12M18 6 6 18' }],
  check: [{ tag: 'path', d: 'm5 12 5 5 9-10' }],
  'chevron-up': [{ tag: 'path', d: 'm6 15 6-6 6 6' }],
  'chevron-down': [{ tag: 'path', d: 'm6 9 6 6 6-6' }],
  'chevron-left': [{ tag: 'path', d: 'm15 6-6 6 6 6' }],
  'chevron-right': [{ tag: 'path', d: 'm9 6 6 6-6 6' }],
  'chevrons-up-down': [
    { tag: 'path', d: 'm8 9 4-4 4 4' },
    { tag: 'path', d: 'm16 15-4 4-4-4' },
  ],
  spinner: [
    { tag: 'circle', cx: 12, cy: 12, r: 9, class: 'opacity-25' },
    { tag: 'path', d: 'M21 12a9 9 0 0 0-9-9' },
  ],
  sun: [
    { tag: 'circle', cx: 12, cy: 12, r: 4 },
    {
      tag: 'path',
      d: 'M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4',
    },
  ],
  moon: [{ tag: 'path', d: 'M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z' }],
  copy: [
    { tag: 'path', d: 'M10 8h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-8a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2Z' },
    { tag: 'path', d: 'M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2' },
  ],
  clock: [
    { tag: 'circle', cx: 12, cy: 12, r: 9 },
    { tag: 'path', d: 'M12 7v5l3 2' },
  ],
  flag: [
    { tag: 'path', d: 'M5 21V4' },
    { tag: 'path', d: 'M5 4h13l-3 4 3 4H5' },
  ],
  ellipsis: [{ tag: 'path', d: 'M5 12h.01M12 12h.01M19 12h.01' }],
  menu: [{ tag: 'path', d: 'M4 6h16M4 12h16M4 18h16' }],
  search: [
    { tag: 'circle', cx: 11, cy: 11, r: 7 },
    { tag: 'path', d: 'm21 21-4.3-4.3' },
  ],
  play: [{ tag: 'path', d: 'M7 5v14l11-7z' }],
  pause: [{ tag: 'path', d: 'M8 5v14M16 5v14' }],
  refresh: [
    { tag: 'path', d: 'M21 12a9 9 0 1 1-2.64-6.36' },
    { tag: 'path', d: 'M21 3v6h-6' },
  ],
  'external-link': [
    { tag: 'path', d: 'M15 3h6v6' },
    { tag: 'path', d: 'M10 14 21 3' },
    { tag: 'path', d: 'M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6' },
  ],
  desktop: [
    { tag: 'path', d: 'M4 5h16v11H4z' },
    { tag: 'path', d: 'M9 20h6' },
    { tag: 'path', d: 'M12 16v4' },
  ],
  terminal: [
    { tag: 'path', d: 'm7 8 4 4-4 4' },
    { tag: 'path', d: 'M13 16h4' },
  ],
  'panel-left': [
    { tag: 'path', d: 'M4 4h16v16H4z' },
    { tag: 'path', d: 'M9 4v16' },
    { tag: 'path', d: 'm16 9-3 3 3 3' },
  ],
  maximize: [
    { tag: 'path', d: 'M8 3H5a2 2 0 0 0-2 2v3' },
    { tag: 'path', d: 'M16 3h3a2 2 0 0 1 2 2v3' },
    { tag: 'path', d: 'M16 21h3a2 2 0 0 0 2-2v-3' },
    { tag: 'path', d: 'M8 21H5a2 2 0 0 1-2-2v-3' },
  ],
  minimize: [
    { tag: 'path', d: 'M8 3v3a2 2 0 0 1-2 2H3' },
    { tag: 'path', d: 'M16 3v3a2 2 0 0 0 2 2h3' },
    { tag: 'path', d: 'M16 21v-3a2 2 0 0 1 2-2h3' },
    { tag: 'path', d: 'M8 21v-3a2 2 0 0 0-2-2H3' },
  ],
} as const satisfies Record<string, readonly IconShape[]>

export type IconName = keyof typeof ICONS

/** Stable, ordered list of icon names (used by tests and the dev gallery). */
export const ICON_NAMES = Object.keys(ICONS) as IconName[]
