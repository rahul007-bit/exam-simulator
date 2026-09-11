import { defineConfig, devices } from '@playwright/test'

const PORT = 5173

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL: `http://localhost:${PORT}`,
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: `http://localhost:${PORT}`,
    // Never reuse a dev server (which might be proxying to a live backend).
    // Always start fresh and point the proxy at a dead port; the E2E specs mock
    // `/api/**` themselves, so tests can never reach a real platform.
    reuseExistingServer: false,
    timeout: 120_000,
    env: {
      ...process.env,
      VITE_BACKEND: process.env.E2E_BACKEND ?? 'http://127.0.0.1:9',
    },
  },
})
