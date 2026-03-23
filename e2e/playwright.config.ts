import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for Sliples E2E tests with real API authentication.
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  // Test directory
  testDir: './tests',

  // Run tests in parallel
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Limit parallel workers on CI
  workers: process.env.CI ? 1 : undefined,

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
  ],

  // Global timeout settings
  timeout: 60000,
  expect: {
    timeout: 15000,
  },

  // Shared settings for all projects
  use: {
    // Base URL to use in actions like `await page.goto('/')`
    // Use SLIPLES_URL env var for deployed environment, default to local dev
    baseURL: process.env.SLIPLES_URL || 'https://sliples.localhost.in:5173',

    // Collect trace on first retry and when explicitly requested
    trace: 'on',

    // Screenshot on success and failure for visibility
    screenshot: 'on',

    // Video recording on failure
    video: 'retain-on-failure',

    // Ignore HTTPS errors (for self-signed certificates in dev)
    ignoreHTTPSErrors: true,

    // Viewport size
    viewport: { width: 1280, height: 720 },

    // Action timeout
    actionTimeout: 15000,

    // Navigation timeout
    navigationTimeout: 30000,
  },

  // Output folder for screenshots and videos
  outputDir: 'test-results',

  // Configure projects for major browsers
  projects: [
    // Chromium tests only for speed during development
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
      },
    },
  ],

  // Web server configuration (optional - if you want Playwright to start the dev server)
  // webServer: {
  //   command: 'npm run dev',
  //   url: 'https://sliples.localhost.in:5173',
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120 * 1000,
  // },
});
