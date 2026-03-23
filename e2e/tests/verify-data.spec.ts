/**
 * E2E test to verify sample data is visible in the UI.
 * Uses API key authentication stored in localStorage.
 *
 * NOTE: These tests verify local dev seed data and are skipped in production.
 */
import { test, expect } from '@playwright/test';

// Skip these tests in production (they check for local seed data)
const isProduction = process.env.SLIPLES_URL?.includes('agantis.in');
test.skip(!!isProduction, 'Skipping seed data verification tests in production');

// The development API key created earlier
const API_KEY = process.env.SLIPLES_API_KEY || 'P9K05ahFmX8DUAco5EEOBVg3rM_zbd7pVEo-I2pbsaI';

const TEST_USER = {
  id: '11111111-1111-1111-1111-111111111111',
  email: 'e2e-test@agantis.team',
  name: 'E2E Test Admin',
  picture_url: null,
  workspace_domain: 'agantis.team',
  role: 'admin',
  is_active: true,
  created_at: '2026-03-20T00:00:00Z',
  last_login: '2026-03-20T00:00:00Z',
};

test.describe('Sample Data Verification', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the /auth/me endpoint to return our test user
    // This prevents ProtectedRoute from redirecting to login
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(TEST_USER),
      });
    });

    // Navigate to app
    await page.goto('/');

    // Set the API key for backend requests
    await page.evaluate((apiKey) => {
      localStorage.setItem('sliples_api_key', apiKey);
    }, API_KEY);

    // Set the Zustand auth state
    await page.evaluate((user) => {
      const authState = {
        state: {
          user: user,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        },
        version: 0,
      };
      localStorage.setItem('sliples-auth', JSON.stringify(authState));
    }, TEST_USER);

    // Reload to apply the authentication
    await page.reload();
    await page.waitForLoadState('networkidle');
  });

  test('Dashboard shows sample data with 4 scenarios', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Wait for dashboard to load (health status should show "Healthy")
    await expect(page.locator('text=Healthy')).toBeVisible({ timeout: 10000 });

    // Take screenshot of dashboard
    await page.screenshot({ path: 'screenshots/verify-dashboard.png', fullPage: true });

    // Verify Total Scenarios shows 4
    const scenariosCard = page.locator('text=Total Scenarios').locator('..').locator('..');
    await expect(scenariosCard.locator('text=4')).toBeVisible({ timeout: 5000 });

    console.log('Dashboard shows 4 scenarios');
  });

  test('Scenarios page shows Giftstarr scenarios', async ({ page }) => {
    // Navigate to scenarios page
    await page.goto('/scenarios');
    await page.waitForLoadState('networkidle');

    // Wait for scenarios to load - use heading locator
    await expect(page.getByRole('heading', { name: 'Giftstarr Checkout' })).toBeVisible({ timeout: 10000 });

    // Take screenshot
    await page.screenshot({ path: 'screenshots/verify-scenarios.png', fullPage: true });

    // Verify all 4 Giftstarr scenarios are visible (using headings)
    await expect(page.getByRole('heading', { name: 'Giftstarr Checkout' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Giftstarr Gift Cards' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Giftstarr Homepage' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Giftstarr Navigation' })).toBeVisible();

    console.log('All 4 Giftstarr scenarios visible');
  });

  test('Environments page shows Giftstarr Test environment', async ({ page }) => {
    // Navigate to environments page
    await page.goto('/environments');
    await page.waitForLoadState('networkidle');

    // Wait for environments to load
    await expect(page.locator('text=Giftstarr Test')).toBeVisible({ timeout: 10000 });

    // Take screenshot
    await page.screenshot({ path: 'screenshots/verify-environments.png', fullPage: true });

    // Verify base URL is shown
    await expect(page.locator('text=test.giftstarr.cards')).toBeVisible();

    console.log('Giftstarr Test environment visible');
  });

  test('Repos page shows giftstarr-scenarios repository', async ({ page }) => {
    // Navigate to repos page
    await page.goto('/repos');
    await page.waitForLoadState('networkidle');

    // Wait for repos to load
    await expect(page.locator('text=giftstarr-scenarios')).toBeVisible({ timeout: 10000 });

    // Take screenshot
    await page.screenshot({ path: 'screenshots/verify-repos.png', fullPage: true });

    console.log('giftstarr-scenarios repository visible');
  });

  test('Settings page shows API keys', async ({ page }) => {
    // Navigate to settings page
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');

    // Click on API Keys tab
    await page.click('text=API Keys');
    await page.waitForTimeout(1000);

    // Take screenshot
    await page.screenshot({ path: 'screenshots/verify-api-keys.png', fullPage: true });

    // Verify at least one API key is listed
    await expect(page.locator('text=Development Seed Key')).toBeVisible({ timeout: 5000 });

    console.log('API keys visible in settings');
  });
});
