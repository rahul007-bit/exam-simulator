// Vitest global setup.
//
// Node >= 25 defines an experimental global `localStorage` that returns
// `undefined` unless the runtime is started with `--localstorage-file`. Vitest's
// jsdom environment sees that property already present and therefore does not
// install jsdom's Web Storage implementation, which breaks `window.localStorage`
// for the theme-persistence tests. Provide a minimal in-memory shim when the
// runtime storage is missing so the suite is deterministic offline.

function createMemoryStorage(): Storage {
  const entries = new Map<string, string>()
  return {
    get length() {
      return entries.size
    },
    clear() {
      entries.clear()
    },
    getItem(key: string) {
      return entries.has(key) ? (entries.get(key) as string) : null
    },
    key(index: number) {
      return Array.from(entries.keys())[index] ?? null
    },
    removeItem(key: string) {
      entries.delete(key)
    },
    setItem(key: string, value: string) {
      entries.set(key, String(value))
    },
  }
}

const existing = (globalThis as { localStorage?: Storage }).localStorage
if (!existing) {
  const storage = createMemoryStorage()
  Object.defineProperty(globalThis, 'localStorage', {
    value: storage,
    configurable: true,
    writable: true,
  })
  const win = (globalThis as { window?: typeof globalThis }).window
  if (win && win !== globalThis) {
    Object.defineProperty(win, 'localStorage', {
      value: storage,
      configurable: true,
      writable: true,
    })
  }
}
