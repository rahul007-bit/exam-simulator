// `highlight.js` ships types for the package root only, but the browser-friendly
// common-language bundle (`highlight.js/lib/common`) is what we import to keep
// the bundle small. Provide the ambient declaration for that subpath (FE-022).

declare module 'highlight.js/lib/common' {
  import type { HLJSApi } from 'highlight.js'

  const hljs: HLJSApi
  export default hljs
}
