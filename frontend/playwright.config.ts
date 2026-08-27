import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.E2E_BASE_URL || "http://localhost:3000";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: "list",
  use: {
    baseURL,
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: "cd ../backend && . .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000",
      url: "http://localhost:8000/api/health",
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
      env: {
        ...process.env,
        ALLOW_PUBLIC_REGISTRATION: "true",
        APP_ENV: "development",
      },
    },
    {
      command: "npm run dev -- -H 0.0.0.0 -p 3000",
      url: "http://localhost:3000/login",
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
    },
  ],
});
