import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

// Build output is web/dist, served directly by FastAPI (see FE-003).
// The backend proxy target is configurable for development on the platform host
// or from a workstation pointing at a remote host: VITE_BACKEND=http://<host>:3000
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backend = env.VITE_BACKEND || 'http://localhost:3000'

  return {
    plugins: [vue(), tailwindcss()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    build: {
      outDir: '../dist',
      emptyOutDir: true,
      sourcemap: false,
    },
    server: {
      port: 5173,
      strictPort: true,
      proxy: {
        '/api': { target: backend, changeOrigin: true },
        '/ws': { target: backend, changeOrigin: true, ws: true },
        '/novnc': { target: backend, changeOrigin: true, ws: true },
      },
    },
  }
})
