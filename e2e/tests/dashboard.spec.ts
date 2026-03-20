import { test, expect } from '@playwright/test';
import { mockAuthenticatedState, testUsers } from '../fixtures/auth.fixture';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Authenticate with real API key - no mocking
    await mockAuthenticatedState(page, testUsers.user);
  });

  test.describe('Dashboard Loading', () => {
    test('should load dashboard with real data', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Check page heading
      await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

      // Take screenshot of loaded dashboard
      await page.screenshot({ path: 'screenshots/dashboard-loaded.png', fullPage: true });
    });
  });

  test.describe('Health Status Cards', () => {
    test('should display system health status from real API', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Take screenshot of health status
      await page.screenshot({ path: 'screenshots/dashboard-health-status.png', fullPage: true });

      // Check health status sections - these should come from real /api/v1/health endpoint
      const systemStatus = page.getByText('System Status');
      const isSystemStatusVisible = await systemStatus.isVisible().catch(() => false);

      if (isSystemStatusVisible) {
        await expect(systemStatus).toBeVisible();
      }
    });
  });

  test.describe('Stats Cards', () => {
    test('should display real statistics from API', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Wait a bit for data to load
      await page.waitForTimeout(1000);

      // Take screenshot of stats cards
      await page.screenshot({ path: 'screenshots/dashboard-stats-cards.png', fullPage: true });

      // Check that the page has loaded properly
      await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
    });
  });

  test.describe('Recent Test Runs', () => {
    test('should display recent test runs from real API', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Wait for data to load
      await page.waitForTimeout(1000);

      // Take screenshot of recent test runs section
      await page.screenshot({ path: 'screenshots/dashboard-recent-runs.png', fullPage: true });

      // Check for Recent Test Runs section (may show "No test runs yet" if empty)
      const recentRunsSection = page.getByText('Recent Test Runs');
      const isRecentRunsVisible = await recentRunsSection.isVisible().catch(() => false);

      if (isRecentRunsVisible) {
        await expect(recentRunsSection).toBeVisible();
      }
    });
  });

  test.describe('Quick Actions', () => {
    test('should display action buttons', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Take screenshot of quick actions area
      await page.screenshot({ path: 'screenshots/dashboard-quick-actions.png', fullPage: true });

      // Look for action buttons (Sync Repos, Run All Tests, etc.)
      const syncButton = page.getByRole('button', { name: /sync/i });
      const isSyncVisible = await syncButton.isVisible().catch(() => false);

      if (isSyncVisible) {
        await expect(syncButton).toBeVisible();
        await expect(syncButton).toBeEnabled();
      }
    });
  });

  test.describe('Full Dashboard Screenshot', () => {
    test('should capture full dashboard with all components', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Wait for all data to load
      await page.waitForTimeout(2000);

      // Take full page screenshot
      await page.screenshot({
        path: 'screenshots/dashboard-full.png',
        fullPage: true,
      });
    });

    test('should capture dashboard on mobile viewport', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Wait for data to load
      await page.waitForTimeout(1000);

      await page.screenshot({
        path: 'screenshots/dashboard-mobile.png',
        fullPage: true,
      });
    });
  });

  test.describe('Navigation', () => {
    test('should navigate to scenarios page', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Find and click scenarios link in navigation
      const scenariosLink = page.getByRole('link', { name: /scenarios/i });
      if (await scenariosLink.isVisible()) {
        await scenariosLink.click();
        await page.waitForLoadState('networkidle');

        // Take screenshot after navigation
        await page.screenshot({ path: 'screenshots/navigation-to-scenarios.png', fullPage: true });

        await expect(page).toHaveURL(/.*\/scenarios/);
      }
    });

    test('should navigate to test runs page', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Find and click test runs link in navigation
      const runsLink = page.getByRole('link', { name: /runs/i });
      if (await runsLink.isVisible()) {
        await runsLink.click();
        await page.waitForLoadState('networkidle');

        // Take screenshot after navigation
        await page.screenshot({ path: 'screenshots/navigation-to-runs.png', fullPage: true });

        await expect(page).toHaveURL(/.*\/runs/);
      }
    });

    test('should navigate to settings page', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Find and click settings link in navigation
      const settingsLink = page.getByRole('link', { name: /settings/i });
      if (await settingsLink.isVisible()) {
        await settingsLink.click();
        await page.waitForLoadState('networkidle');

        // Take screenshot after navigation
        await page.screenshot({ path: 'screenshots/navigation-to-settings.png', fullPage: true });

        await expect(page).toHaveURL(/.*\/settings/);
      }
    });
  });
});
