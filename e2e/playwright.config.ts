import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for Sliples E2E tests.
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
  timeout: 30000,
  expect: {
    timeout: 10000,
  },

  // Shared settings for all projects
  use: {
    // Base URL to use in actions like `await page.goto('/')`
    baseURL: 'https://sliples.localhost.in:5173',

    // Collect trace when retrying the failed test
    trace: 'on-first-retry',

    // Screenshot on failure
    screenshot: 'only-on-failure',

    // Video recording
    video: 'retain-on-failure',

    // Ignore HTTPS errors (for self-signed certificates in dev)
    ignoreHTTPSErrors: true,

    // Viewport size
    viewport: { width: 1280, height: 720 },

    // Action timeout
    actionTimeout: 10000,

    // Navigation timeout
    navigationTimeout: 15000,
  },

  // Output folder for screenshots and videos
  outputDir: 'test-results',

  // Configure projects for major browsers
  projects: [
    // Setup project - runs authentication once
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
    },

    // Chromium tests
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // Use stored authentication state
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },

    // Firefox tests
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },

    // WebKit tests (Safari)
    {
      name: 'webkit',
      use: {
        ...devices['Desktop Safari'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },

    // Mobile Chrome tests
    {
      name: 'mobile-chrome',
      use: {
        ...devices['Pixel 5'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
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
