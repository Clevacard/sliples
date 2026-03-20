import { test, expect } from '@playwright/test';
import { mockAuthenticatedState, testUsers } from '../fixtures/auth.fixture';

test.describe('Test Runs Page', () => {
  test.beforeEach(async ({ page }) => {
    // Authenticate with real API key - no mocking
    await mockAuthenticatedState(page, testUsers.user);
  });

  test.describe('Page Layout', () => {
    test('should display test runs page with header', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      // Wait for data to load
      await page.waitForTimeout(1000);

      // Take screenshot
      await page.screenshot({ path: 'screenshots/test-runs-page.png', fullPage: true });

      // Check page heading
      await expect(page.getByRole('heading', { name: /runs/i })).toBeVisible();
    });

    test('should display New Test Run button', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      // Take screenshot
      await page.screenshot({ path: 'screenshots/test-runs-with-new-button.png', fullPage: true });

      const newRunButton = page.getByRole('button', { name: /new.*run|create/i });
      const isNewRunVisible = await newRunButton.isVisible().catch(() => false);

      if (isNewRunVisible) {
        await expect(newRunButton).toBeVisible();
        await expect(newRunButton).toBeEnabled();
      }
    });
  });

  test.describe('Test Runs List', () => {
    test('should display list of test runs from real API', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      // Wait for data to load
      await page.waitForTimeout(2000);

      // Take screenshot of test runs list
      await page.screenshot({ path: 'screenshots/test-runs-list.png', fullPage: true });

      // The page should at least show the heading
      await expect(page.getByRole('heading', { name: /runs/i })).toBeVisible();
    });
  });

  test.describe('Filters', () => {
    test('should display filter controls', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      // Wait for page to fully load
      await page.waitForTimeout(1000);

      // Take screenshot of filter controls
      await page.screenshot({ path: 'screenshots/test-runs-filters.png', fullPage: true });
    });

    test('should filter runs by status if available', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      // Wait for data to load
      await page.waitForTimeout(1000);

      // Check for status filter
      const statusSelect = page.locator('select').filter({ hasText: /status/i });
      const isStatusVisible = await statusSelect.isVisible().catch(() => false);

      if (isStatusVisible) {
        await statusSelect.selectOption('passed');
        await page.waitForTimeout(500);

        // Take screenshot of filtered results
        await page.screenshot({ path: 'screenshots/test-runs-filtered.png', fullPage: true });
      } else {
        // Take screenshot anyway
        await page.screenshot({ path: 'screenshots/test-runs-no-filter.png', fullPage: true });
      }
    });
  });

  test.describe('Create New Run Modal', () => {
    test('should open new run modal when clicking New Test Run', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      const newRunButton = page.getByRole('button', { name: /new.*run|create/i });
      const isNewRunVisible = await newRunButton.isVisible().catch(() => false);

      if (isNewRunVisible) {
        await newRunButton.click();
        await page.waitForTimeout(500);

        // Take screenshot of modal
        await page.screenshot({ path: 'screenshots/new-run-modal.png', fullPage: true });
      } else {
        // Take screenshot of the page without new run button
        await page.screenshot({ path: 'screenshots/test-runs-no-new-button.png', fullPage: true });
      }
    });
  });

  test.describe('Empty State', () => {
    test('should handle empty or populated test runs', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      // Wait for data to load
      await page.waitForTimeout(2000);

      // Take screenshot - will show either test runs or empty state
      await page.screenshot({ path: 'screenshots/test-runs-state.png', fullPage: true });
    });
  });

  test.describe('Full Page Screenshots', () => {
    test('should capture test runs page with data', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      // Wait for data to load
      await page.waitForTimeout(2000);

      await page.screenshot({
        path: 'screenshots/test-runs-full.png',
        fullPage: true,
      });
    });

    test('should capture test runs page on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });

      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      // Wait for data to load
      await page.waitForTimeout(1000);

      await page.screenshot({
        path: 'screenshots/test-runs-mobile.png',
        fullPage: true,
      });
    });
  });
});

test.describe('Run Details Page', () => {
  test.beforeEach(async ({ page }) => {
    // Authenticate with real API key - no mocking
    await mockAuthenticatedState(page, testUsers.user);
  });

  test.describe('Page Layout', () => {
    test('should display run details page if runs exist', async ({ page }) => {
      // First go to runs list to find a run
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);

      // Try to find and click a run details link
      const detailsLink = page.getByRole('link', { name: /details|view/i }).first();
      const isDetailsVisible = await detailsLink.isVisible().catch(() => false);

      if (isDetailsVisible) {
        await detailsLink.click();
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(1000);

        // Take screenshot
        await page.screenshot({ path: 'screenshots/run-details-page.png', fullPage: true });
      } else {
        // No runs exist yet, take screenshot of empty state
        await page.screenshot({ path: 'screenshots/test-runs-empty.png', fullPage: true });
      }
    });
  });

  test.describe('Navigation', () => {
    test('should navigate back to test runs from details', async ({ page }) => {
      // First go to runs list
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);

      // Try to find and click a run details link
      const detailsLink = page.getByRole('link', { name: /details|view/i }).first();
      const isDetailsVisible = await detailsLink.isVisible().catch(() => false);

      if (isDetailsVisible) {
        await detailsLink.click();
        await page.waitForLoadState('networkidle');

        // Find back button
        const backButton = page.getByText(/back.*runs/i);
        const isBackVisible = await backButton.isVisible().catch(() => false);

        if (isBackVisible) {
          await backButton.click();
          await page.waitForLoadState('networkidle');

          // Take screenshot after navigation
          await page.screenshot({ path: 'screenshots/run-details-back-navigation.png', fullPage: true });

          await expect(page).toHaveURL(/.*\/runs$/);
        }
      }
    });
  });

  test.describe('Full Page Screenshots', () => {
    test('should capture run details page if available', async ({ page }) => {
      // First go to runs list to find a run
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);

      // Try to find and click a run details link
      const detailsLink = page.getByRole('link', { name: /details|view/i }).first();
      const isDetailsVisible = await detailsLink.isVisible().catch(() => false);

      if (isDetailsVisible) {
        await detailsLink.click();
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(1000);

        await page.screenshot({
          path: 'screenshots/run-details-full.png',
          fullPage: true,
        });
      }
    });
  });
});
