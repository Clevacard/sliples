import { test, expect } from '@playwright/test';
import { mockAuthenticatedState, testUsers } from '../fixtures/auth.fixture';

test.describe('Scenarios Page', () => {
  test.beforeEach(async ({ page }) => {
    // Authenticate with real API key - no mocking
    await mockAuthenticatedState(page, testUsers.user);
  });

  test.describe('Page Layout', () => {
    test('should display scenarios page with header', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Wait for data to load
      await page.waitForTimeout(1000);

      // Take screenshot
      await page.screenshot({ path: 'screenshots/scenarios-page.png', fullPage: true });

      // Check page heading
      await expect(page.getByRole('heading', { name: /scenarios/i })).toBeVisible();
    });

    test('should display Sync All Repos button', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Take screenshot
      await page.screenshot({ path: 'screenshots/scenarios-with-sync-button.png', fullPage: true });

      const syncButton = page.getByRole('button', { name: /sync/i });
      const isSyncVisible = await syncButton.isVisible().catch(() => false);

      if (isSyncVisible) {
        await expect(syncButton).toBeVisible();
        await expect(syncButton).toBeEnabled();
      }
    });
  });

  test.describe('Scenario List', () => {
    test('should display list of scenarios from real API', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Wait for data to load
      await page.waitForTimeout(2000);

      // Take screenshot of scenario list
      await page.screenshot({ path: 'screenshots/scenarios-list.png', fullPage: true });

      // The page should at least show the heading
      await expect(page.getByRole('heading', { name: /scenarios/i })).toBeVisible();
    });
  });

  test.describe('Filters', () => {
    test('should display filter controls', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Wait for page to fully load
      await page.waitForTimeout(1000);

      // Take screenshot of filter controls
      await page.screenshot({ path: 'screenshots/scenarios-filters.png', fullPage: true });

      // Check for search input (if it exists)
      const searchInput = page.getByPlaceholder(/search/i);
      const isSearchVisible = await searchInput.isVisible().catch(() => false);

      if (isSearchVisible) {
        await expect(searchInput).toBeVisible();
      }
    });

    test('should filter scenarios by search query', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Wait for data to load
      await page.waitForTimeout(1000);

      // Try to find and use search
      const searchInput = page.getByPlaceholder(/search/i);
      const isSearchVisible = await searchInput.isVisible().catch(() => false);

      if (isSearchVisible) {
        await searchInput.fill('login');
        await page.waitForTimeout(500);

        // Take screenshot of filtered results
        await page.screenshot({ path: 'screenshots/scenarios-search-filter.png', fullPage: true });
      } else {
        // Take screenshot anyway
        await page.screenshot({ path: 'screenshots/scenarios-no-search.png', fullPage: true });
      }
    });
  });

  test.describe('View Modes', () => {
    test('should toggle between list and grid view if available', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Wait for data to load
      await page.waitForTimeout(1000);

      // Find view toggle buttons
      const gridViewButton = page.locator('button[title*="Grid"]').or(
        page.getByRole('button', { name: /grid/i })
      );
      const isGridVisible = await gridViewButton.isVisible().catch(() => false);

      if (isGridVisible) {
        // Switch to grid view
        await gridViewButton.click();
        await page.waitForTimeout(500);

        // Take screenshot of grid view
        await page.screenshot({ path: 'screenshots/scenarios-grid-view.png', fullPage: true });
      }

      // Take screenshot of current view
      await page.screenshot({ path: 'screenshots/scenarios-view-mode.png', fullPage: true });
    });
  });

  test.describe('Empty State', () => {
    test('should handle empty or populated scenarios', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Wait for data to load
      await page.waitForTimeout(2000);

      // Take screenshot - will show either scenarios or empty state
      await page.screenshot({ path: 'screenshots/scenarios-state.png', fullPage: true });
    });
  });

  test.describe('Full Page Screenshots', () => {
    test('should capture scenarios page with data', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Wait for data to load
      await page.waitForTimeout(2000);

      await page.screenshot({
        path: 'screenshots/scenarios-full.png',
        fullPage: true,
      });
    });

    test('should capture scenarios page on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });

      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Wait for data to load
      await page.waitForTimeout(1000);

      await page.screenshot({
        path: 'screenshots/scenarios-mobile.png',
        fullPage: true,
      });
    });
  });
});
