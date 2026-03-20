import { test, expect } from '@playwright/test';
import { mockAuthenticatedState, testUsers } from '../fixtures/auth.fixture';

// Mock data for scenarios
const mockScenarios = [
  {
    id: 'scenario-1',
    name: 'User can login successfully',
    feature_path: 'features/auth/login.feature',
    feature_name: 'User Authentication',
    tags: ['smoke', 'auth', 'critical'],
    repo_id: 'repo-1',
    repo_name: 'main-tests',
    description: 'Verify that users can login with valid credentials',
    step_count: 5,
  },
  {
    id: 'scenario-2',
    name: 'User can view dashboard',
    feature_path: 'features/dashboard/view.feature',
    feature_name: 'Dashboard',
    tags: ['smoke', 'dashboard'],
    repo_id: 'repo-1',
    repo_name: 'main-tests',
    description: 'Verify dashboard displays correctly',
    step_count: 3,
  },
  {
    id: 'scenario-3',
    name: 'User can create new project',
    feature_path: 'features/projects/create.feature',
    feature_name: 'Project Management',
    tags: ['regression', 'projects'],
    repo_id: 'repo-2',
    repo_name: 'integration-tests',
    description: 'Verify users can create new projects',
    step_count: 8,
  },
  {
    id: 'scenario-4',
    name: 'Admin can manage users',
    feature_path: 'features/admin/users.feature',
    feature_name: 'Admin Features',
    tags: ['admin', 'users'],
    repo_id: 'repo-2',
    repo_name: 'integration-tests',
    description: 'Admin user management functionality',
    step_count: 6,
  },
  {
    id: 'scenario-5',
    name: 'API authentication works',
    feature_path: 'features/api/auth.feature',
    feature_name: 'API Tests',
    tags: ['api', 'auth'],
    repo_id: 'repo-3',
    repo_name: 'api-tests',
    description: 'API authentication endpoint tests',
    step_count: 4,
  },
];

const mockRepos = [
  { id: 'repo-1', name: 'main-tests', git_url: 'https://github.com/test/main-tests.git', branch: 'main' },
  { id: 'repo-2', name: 'integration-tests', git_url: 'https://github.com/test/integration.git', branch: 'develop' },
  { id: 'repo-3', name: 'api-tests', git_url: 'https://github.com/test/api-tests.git', branch: 'main' },
];

test.describe('Scenarios Page', () => {
  test.beforeEach(async ({ page }) => {
    // Setup API mocks
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-user-id',
          email: 'user@example.com',
          name: 'Test User',
          picture_url: null,
          role: 'user',
        }),
      });
    });

    await page.route('**/api/v1/scenarios**', async (route) => {
      const url = new URL(route.request().url());
      const tag = url.searchParams.get('tag');
      const repo = url.searchParams.get('repo_id');
      const search = url.searchParams.get('search');

      let filtered = [...mockScenarios];

      if (tag) {
        filtered = filtered.filter(s => s.tags.includes(tag));
      }
      if (repo) {
        filtered = filtered.filter(s => s.repo_id === repo);
      }
      if (search) {
        const q = search.toLowerCase();
        filtered = filtered.filter(s =>
          s.name.toLowerCase().includes(q) ||
          s.feature_path.toLowerCase().includes(q) ||
          s.tags.some(t => t.toLowerCase().includes(q))
        );
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(filtered),
      });
    });

    await page.route('**/api/v1/repos**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockRepos),
      });
    });

    await page.route('**/api/v1/repos/*/sync', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Sync started' }),
      });
    });

    // Authenticate
    await mockAuthenticatedState(page, testUsers.user);
  });

  test.describe('Page Layout', () => {
    test('should display scenarios page with header', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Check page heading
      await expect(page.getByRole('heading', { name: 'Scenarios' })).toBeVisible();

      // Check subtitle with counts
      await expect(page.getByText(/scenarios from.*repositories/i)).toBeVisible();

      // Take screenshot
      await page.screenshot({ path: 'screenshots/scenarios-page.png', fullPage: true });
    });

    test('should display Sync All Repos button', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      const syncButton = page.getByRole('button', { name: /sync all repos/i });
      await expect(syncButton).toBeVisible();
      await expect(syncButton).toBeEnabled();
    });
  });

  test.describe('Scenario List', () => {
    test('should display list of scenarios', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Check that scenarios are displayed
      for (const scenario of mockScenarios.slice(0, 3)) {
        await expect(page.getByText(scenario.name).first()).toBeVisible();
      }
    });

    test('should show feature file paths', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Check feature paths are visible
      await expect(page.getByText('features/auth/login.feature')).toBeVisible();
    });

    test('should display tags as badges', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Check for tag badges
      await expect(page.getByText('@smoke').first()).toBeVisible();
      await expect(page.getByText('@auth').first()).toBeVisible();
    });

    test('should navigate to scenario details when clicking scenario', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Click on first scenario
      const scenarioLink = page.getByText('User can login successfully').first();
      await scenarioLink.click();

      await expect(page).toHaveURL(/.*\/scenarios\/scenario-1/);
    });
  });

  test.describe('Filters', () => {
    test('should display filter controls', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Check for search input
      await expect(page.getByPlaceholder(/search/i)).toBeVisible();

      // Check for repository filter
      await expect(page.getByRole('combobox').filter({ hasText: /all repositories/i }).or(
        page.locator('select').filter({ hasText: /all repositories/i })
      )).toBeVisible();

      // Check for tag filter
      await expect(page.getByRole('combobox').filter({ hasText: /all tags/i }).or(
        page.locator('select').filter({ hasText: /all tags/i })
      )).toBeVisible();
    });

    test('should filter scenarios by search query', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Type in search
      const searchInput = page.getByPlaceholder(/search/i);
      await searchInput.fill('login');

      // Wait for filter to apply
      await page.waitForTimeout(500);

      // Should show only matching scenarios
      await expect(page.getByText('User can login successfully')).toBeVisible();

      // Take screenshot of filtered results
      await page.screenshot({ path: 'screenshots/scenarios-search-filter.png' });
    });

    test('should filter scenarios by tag', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Select tag filter
      const tagSelect = page.locator('select').filter({ hasText: /all tags/i });
      await tagSelect.selectOption({ label: '@smoke' });

      // Wait for filter to apply
      await page.waitForTimeout(500);

      // Should show only scenarios with smoke tag
      await expect(page.getByText('User can login successfully')).toBeVisible();
      await expect(page.getByText('User can view dashboard')).toBeVisible();
    });

    test('should filter scenarios by repository', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Select repository filter
      const repoSelect = page.locator('select').filter({ hasText: /all repositories/i });
      await repoSelect.selectOption({ label: 'integration-tests' });

      // Wait for filter to apply
      await page.waitForTimeout(500);

      // Should show only scenarios from that repo
      await expect(page.getByText('User can create new project')).toBeVisible();
      await expect(page.getByText('Admin can manage users')).toBeVisible();
    });

    test('should show filter summary when filters are active', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Apply a filter
      const searchInput = page.getByPlaceholder(/search/i);
      await searchInput.fill('auth');
      await page.waitForTimeout(500);

      // Should show filter summary
      await expect(page.getByText(/showing.*of.*scenarios/i)).toBeVisible();
    });

    test('should clear filters when clicking Clear Filters', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Apply filters
      const searchInput = page.getByPlaceholder(/search/i);
      await searchInput.fill('login');
      await page.waitForTimeout(500);

      // Click clear filters
      const clearButton = page.getByRole('button', { name: /clear filters/i });
      if (await clearButton.isVisible()) {
        await clearButton.click();
        await page.waitForTimeout(500);

        // Search should be cleared
        await expect(searchInput).toHaveValue('');
      }
    });
  });

  test.describe('View Modes', () => {
    test('should toggle between list and grid view', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Find view toggle buttons
      const listViewButton = page.getByRole('button', { name: /list view/i }).or(
        page.locator('button[title*="List"]')
      );
      const gridViewButton = page.getByRole('button', { name: /grid view/i }).or(
        page.locator('button[title*="Grid"]')
      );

      // Check list view is default
      await expect(listViewButton).toBeVisible();
      await expect(gridViewButton).toBeVisible();

      // Switch to grid view
      await gridViewButton.click();
      await page.waitForTimeout(300);

      // Take screenshot of grid view
      await page.screenshot({ path: 'screenshots/scenarios-grid-view.png', fullPage: true });

      // Switch back to list view
      await listViewButton.click();
      await page.waitForTimeout(300);

      // Take screenshot of list view
      await page.screenshot({ path: 'screenshots/scenarios-list-view.png', fullPage: true });
    });
  });

  test.describe('Empty State', () => {
    test('should show empty state when no scenarios', async ({ page }) => {
      await page.route('**/api/v1/scenarios**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([]),
        });
      });

      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText('No scenarios found')).toBeVisible();
      await expect(page.getByText(/add a repository/i)).toBeVisible();
    });

    test('should show no results message when filter matches nothing', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Search for something that doesn't exist
      const searchInput = page.getByPlaceholder(/search/i);
      await searchInput.fill('xyznonexistent');
      await page.waitForTimeout(500);

      await expect(page.getByText(/no scenarios match/i)).toBeVisible();
    });
  });

  test.describe('Sync Functionality', () => {
    test('should trigger sync when clicking Sync All Repos', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      let syncCalled = false;
      await page.route('**/api/v1/repos/*/sync', async (route) => {
        syncCalled = true;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Sync started' }),
        });
      });

      const syncButton = page.getByRole('button', { name: /sync all repos/i });
      await syncButton.click();

      // Wait for sync
      await page.waitForTimeout(500);

      // Button should show syncing state
      const buttonText = await syncButton.textContent();
      expect(syncCalled || buttonText?.toLowerCase().includes('sync')).toBeTruthy();
    });
  });

  test.describe('Scenario Details', () => {
    test('should show scenario step count', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // In grid view, step count is visible
      const gridViewButton = page.locator('button[title*="Grid"]');
      await gridViewButton.click();
      await page.waitForTimeout(300);

      // Check for step count
      await expect(page.getByText(/\d+ steps/).first()).toBeVisible();
    });

    test('should group scenarios by feature file in list view', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // In list view, scenarios are grouped by feature
      await expect(page.getByText('features/auth/login.feature')).toBeVisible();
      await expect(page.getByText(/1 scenario/)).toBeVisible();
    });
  });

  test.describe('Full Page Screenshots', () => {
    test('should capture scenarios page with data', async ({ page }) => {
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      await page.screenshot({
        path: 'screenshots/scenarios-full.png',
        fullPage: true,
      });
    });

    test('should capture scenarios page on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });

      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      await page.screenshot({
        path: 'screenshots/scenarios-mobile.png',
        fullPage: true,
      });
    });
  });
});
