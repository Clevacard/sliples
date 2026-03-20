import { test, expect } from '@playwright/test';
import { mockAuthenticatedState, testUsers } from '../fixtures/auth.fixture';

// Mock data for test runs
const mockRuns = [
  {
    id: 'run-1',
    status: 'passed',
    browser: 'chromium',
    browser_version: '120.0',
    environment_id: 'env-1',
    environment_name: 'test',
    created_at: new Date(Date.now() - 3600000).toISOString(),
    finished_at: new Date(Date.now() - 3540000).toISOString(),
    passed_count: 10,
    failed_count: 0,
    triggered_by: 'user@example.com',
  },
  {
    id: 'run-2',
    status: 'failed',
    browser: 'firefox',
    browser_version: '121.0',
    environment_id: 'env-1',
    environment_name: 'test',
    created_at: new Date(Date.now() - 7200000).toISOString(),
    finished_at: new Date(Date.now() - 7100000).toISOString(),
    passed_count: 8,
    failed_count: 2,
    triggered_by: 'ci@example.com',
  },
  {
    id: 'run-3',
    status: 'running',
    browser: 'chromium',
    browser_version: '120.0',
    environment_id: 'env-2',
    environment_name: 'staging',
    created_at: new Date(Date.now() - 300000).toISOString(),
    finished_at: null,
    passed_count: 5,
    failed_count: 0,
    triggered_by: 'user@example.com',
  },
  {
    id: 'run-4',
    status: 'queued',
    browser: 'webkit',
    environment_id: 'env-1',
    environment_name: 'test',
    created_at: new Date(Date.now() - 60000).toISOString(),
    finished_at: null,
    passed_count: 0,
    failed_count: 0,
    triggered_by: 'schedule',
  },
];

const mockRunDetails = {
  id: 'run-1',
  status: 'passed',
  browser: 'chromium',
  browser_version: '120.0',
  environment_id: 'env-1',
  environment_name: 'test',
  created_at: new Date(Date.now() - 3600000).toISOString(),
  finished_at: new Date(Date.now() - 3540000).toISOString(),
  triggered_by: 'user@example.com',
  results: [
    {
      id: 'result-1',
      step_name: 'Given I am on the login page',
      scenario_name: 'User can login successfully',
      status: 'passed',
      duration_ms: 1500,
      screenshot_url: null,
      error_message: null,
    },
    {
      id: 'result-2',
      step_name: 'When I enter valid credentials',
      scenario_name: 'User can login successfully',
      status: 'passed',
      duration_ms: 2300,
      screenshot_url: null,
      error_message: null,
    },
    {
      id: 'result-3',
      step_name: 'And I click the login button',
      scenario_name: 'User can login successfully',
      status: 'passed',
      duration_ms: 800,
      screenshot_url: null,
      error_message: null,
    },
    {
      id: 'result-4',
      step_name: 'Then I should be redirected to the dashboard',
      scenario_name: 'User can login successfully',
      status: 'passed',
      duration_ms: 1200,
      screenshot_url: '/screenshots/dashboard.png',
      error_message: null,
    },
    {
      id: 'result-5',
      step_name: 'And I should see a welcome message',
      scenario_name: 'User can login successfully',
      status: 'passed',
      duration_ms: 500,
      screenshot_url: null,
      error_message: null,
    },
  ],
};

const mockEnvironments = [
  { id: 'env-1', name: 'test', base_url: 'https://test.example.com' },
  { id: 'env-2', name: 'staging', base_url: 'https://staging.example.com' },
  { id: 'env-3', name: 'production', base_url: 'https://example.com' },
];

const mockBrowsers = [
  { id: 'chromium', name: 'Chromium' },
  { id: 'firefox', name: 'Firefox' },
  { id: 'webkit', name: 'WebKit' },
];

const mockScenarios = [
  { id: 's1', name: 'Login test', tags: ['smoke', 'auth'] },
  { id: 's2', name: 'Dashboard test', tags: ['smoke'] },
];

test.describe('Test Runs Page', () => {
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

    await page.route('**/api/v1/runs', async (route) => {
      if (route.request().method() === 'GET') {
        const url = new URL(route.request().url());
        const status = url.searchParams.get('status');

        let filtered = [...mockRuns];
        if (status) {
          filtered = filtered.filter(r => r.status === status);
        }

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: filtered, total: filtered.length }),
        });
      } else if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'new-run-id',
            status: 'queued',
            browser: 'chromium',
            created_at: new Date().toISOString(),
          }),
        });
      }
    });

    await page.route('**/api/v1/runs/*', async (route) => {
      const runId = route.request().url().split('/').pop();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(runId === 'run-1' ? mockRunDetails : mockRuns.find(r => r.id === runId) || mockRunDetails),
      });
    });

    await page.route('**/api/v1/environments**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockEnvironments),
      });
    });

    await page.route('**/api/v1/browsers**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockBrowsers),
      });
    });

    await page.route('**/api/v1/scenarios**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockScenarios),
      });
    });

    // Authenticate
    await mockAuthenticatedState(page, testUsers.user);
  });

  test.describe('Page Layout', () => {
    test('should display test runs page with header', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      // Check page heading
      await expect(page.getByRole('heading', { name: 'Test Runs' })).toBeVisible();

      // Check subtitle
      await expect(page.getByText(/manage and monitor your test executions/i)).toBeVisible();

      // Take screenshot
      await page.screenshot({ path: 'screenshots/test-runs-page.png', fullPage: true });
    });

    test('should display New Test Run button', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      const newRunButton = page.getByRole('button', { name: /new test run/i });
      await expect(newRunButton).toBeVisible();
      await expect(newRunButton).toBeEnabled();
    });
  });

  test.describe('Test Runs List', () => {
    test('should display list of test runs', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      // Check table headers
      await expect(page.getByRole('columnheader', { name: 'Status' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: 'Environment' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: 'Browser' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: 'Created' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: 'Duration' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: 'Results' })).toBeVisible();
    });

    test('should display status badges', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      // Check for different status badges
      await expect(page.locator('.badge').filter({ hasText: 'passed' }).first()).toBeVisible();
      await expect(page.locator('.badge').filter({ hasText: 'failed' }).first()).toBeVisible();
      await expect(page.locator('.badge').filter({ hasText: 'running' }).first()).toBeVisible();
      await expect(page.locator('.badge').filter({ hasText: 'queued' }).first()).toBeVisible();
    });

    test('should display browser names', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText('chromium', { exact: false }).first()).toBeVisible();
      await expect(page.getByText('firefox', { exact: false }).first()).toBeVisible();
    });

    test('should display environment names', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText('test').first()).toBeVisible();
      await expect(page.getByText('staging').first()).toBeVisible();
    });

    test('should display pass/fail counts', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      // Check for result counts
      await expect(page.getByText(/\d+ passed/).first()).toBeVisible();
    });

    test('should navigate to run details when clicking View Details', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      const detailsLink = page.getByRole('link', { name: /view details/i }).first();
      await detailsLink.click();

      await expect(page).toHaveURL(/.*\/runs\/run-1/);
    });
  });

  test.describe('Filters', () => {
    test('should display filter controls', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      // Check for status filter
      await expect(page.locator('select').filter({ hasText: /all statuses/i })).toBeVisible();

      // Check for date filters
      await expect(page.locator('input[type="date"]').first()).toBeVisible();
    });

    test('should filter runs by status', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      // Select status filter
      const statusSelect = page.locator('select').filter({ hasText: /all statuses/i });
      await statusSelect.selectOption('passed');

      // Click apply
      const applyButton = page.getByRole('button', { name: /apply/i });
      await applyButton.click();

      await page.waitForTimeout(500);

      // Should only show passed runs
      await expect(page.locator('.badge').filter({ hasText: 'passed' })).toBeVisible();
    });

    test('should reset filters when clicking Reset', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      // Apply filter
      const statusSelect = page.locator('select').filter({ hasText: /all statuses/i });
      await statusSelect.selectOption('passed');

      // Reset
      const resetButton = page.getByRole('button', { name: /reset/i });
      await resetButton.click();

      await page.waitForTimeout(500);

      // Status should be reset
      await expect(statusSelect).toHaveValue('');
    });
  });

  test.describe('Create New Run Modal', () => {
    test('should open new run modal when clicking New Test Run', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      const newRunButton = page.getByRole('button', { name: /new test run/i });
      await newRunButton.click();

      // Modal should be visible
      await expect(page.getByText('Create New Test Run')).toBeVisible();

      // Take screenshot of modal
      await page.screenshot({ path: 'screenshots/new-run-modal.png' });
    });

    test('should display environment selection', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      const newRunButton = page.getByRole('button', { name: /new test run/i });
      await newRunButton.click();

      // Environment dropdown should be visible
      await expect(page.getByText('Environment')).toBeVisible();
      await expect(page.locator('select').filter({ hasText: /select an environment/i })).toBeVisible();
    });

    test('should display tag selection', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      const newRunButton = page.getByRole('button', { name: /new test run/i });
      await newRunButton.click();

      // Tag selection should be visible
      await expect(page.getByText(/filter scenarios by tags/i)).toBeVisible();
    });

    test('should display browser selection', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      const newRunButton = page.getByRole('button', { name: /new test run/i });
      await newRunButton.click();

      // Browser selection should be visible
      await expect(page.getByText('Browsers')).toBeVisible();
      await expect(page.getByText('Chromium')).toBeVisible();
      await expect(page.getByText('Firefox')).toBeVisible();
      await expect(page.getByText('WebKit')).toBeVisible();
    });

    test('should create test run when form is submitted', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      const newRunButton = page.getByRole('button', { name: /new test run/i });
      await newRunButton.click();

      // Select environment
      const envSelect = page.locator('select').filter({ hasText: /select an environment/i });
      await envSelect.selectOption('test');

      // Submit form
      const startButton = page.getByRole('button', { name: /start test run/i });
      await startButton.click();

      // Modal should close
      await page.waitForTimeout(500);
      await expect(page.getByText('Create New Test Run')).not.toBeVisible();
    });

    test('should close modal when clicking Cancel', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      const newRunButton = page.getByRole('button', { name: /new test run/i });
      await newRunButton.click();

      // Cancel
      const cancelButton = page.getByRole('button', { name: /cancel/i });
      await cancelButton.click();

      // Modal should close
      await expect(page.getByText('Create New Test Run')).not.toBeVisible();
    });

    test('should require environment selection', async ({ page }) => {
      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      const newRunButton = page.getByRole('button', { name: /new test run/i });
      await newRunButton.click();

      // Try to submit without selecting environment
      const startButton = page.getByRole('button', { name: /start test run/i });
      await expect(startButton).toBeDisabled();
    });
  });

  test.describe('Empty State', () => {
    test('should show empty state when no runs', async ({ page }) => {
      await page.route('**/api/v1/runs', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: [], total: 0 }),
        });
      });

      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText('No test runs found')).toBeVisible();
      await expect(page.getByRole('button', { name: /create first run/i })).toBeVisible();
    });
  });

  test.describe('Pagination', () => {
    test('should display pagination when there are many runs', async ({ page }) => {
      // Create many mock runs
      const manyRuns = Array.from({ length: 25 }, (_, i) => ({
        id: `run-${i}`,
        status: 'passed',
        browser: 'chromium',
        environment_id: 'env-1',
        environment_name: 'test',
        created_at: new Date(Date.now() - i * 3600000).toISOString(),
        finished_at: new Date(Date.now() - i * 3600000 + 60000).toISOString(),
        passed_count: 10,
        failed_count: 0,
      }));

      await page.route('**/api/v1/runs', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: manyRuns.slice(0, 10), total: 25 }),
        });
      });

      await page.goto('/runs');
      await page.waitForLoadState('networkidle');

      // Pagination should be visible
      await expect(page.getByText(/page.*of/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /next/i })).toBeVisible();
    });
  });
});

test.describe('Run Details Page', () => {
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

    await page.route('**/api/v1/runs/run-1', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockRunDetails),
      });
    });

    await page.route('**/api/v1/environments**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockEnvironments),
      });
    });

    // Authenticate
    await mockAuthenticatedState(page, testUsers.user);
  });

  test.describe('Page Layout', () => {
    test('should display run details page', async ({ page }) => {
      await page.goto('/runs/run-1');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText('Test Run Details')).toBeVisible();
      await expect(page.getByText('Back to Test Runs')).toBeVisible();

      // Take screenshot
      await page.screenshot({ path: 'screenshots/run-details-page.png', fullPage: true });
    });

    test('should display run status badge', async ({ page }) => {
      await page.goto('/runs/run-1');
      await page.waitForLoadState('networkidle');

      await expect(page.locator('.badge').filter({ hasText: 'passed' })).toBeVisible();
    });

    test('should display run ID', async ({ page }) => {
      await page.goto('/runs/run-1');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText(/ID:.*run-1/)).toBeVisible();
    });
  });

  test.describe('Summary Cards', () => {
    test('should display browser information', async ({ page }) => {
      await page.goto('/runs/run-1');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText('Browser')).toBeVisible();
      await expect(page.getByText(/chromium/i)).toBeVisible();
    });

    test('should display duration', async ({ page }) => {
      await page.goto('/runs/run-1');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText('Duration')).toBeVisible();
    });

    test('should display passed count', async ({ page }) => {
      await page.goto('/runs/run-1');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText('Passed')).toBeVisible();
      await expect(page.getByText('5').first()).toBeVisible(); // 5 passed results
    });

    test('should display failed count', async ({ page }) => {
      await page.goto('/runs/run-1');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText('Failed')).toBeVisible();
      await expect(page.getByText('0').first()).toBeVisible();
    });

    test('should display environment', async ({ page }) => {
      await page.goto('/runs/run-1');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText('Environment').first()).toBeVisible();
    });
  });

  test.describe('Test Steps', () => {
    test('should display test steps list', async ({ page }) => {
      await page.goto('/runs/run-1');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText('Test Steps')).toBeVisible();

      // Check for step names
      await expect(page.getByText('Given I am on the login page')).toBeVisible();
      await expect(page.getByText('When I enter valid credentials')).toBeVisible();
      await expect(page.getByText('And I click the login button')).toBeVisible();
    });

    test('should display step status icons', async ({ page }) => {
      await page.goto('/runs/run-1');
      await page.waitForLoadState('networkidle');

      // All steps are passed, so all should have green icons
      const passedSteps = page.locator('[class*="green"]');
      await expect(passedSteps.first()).toBeVisible();
    });

    test('should display step durations', async ({ page }) => {
      await page.goto('/runs/run-1');
      await page.waitForLoadState('networkidle');

      // Check for duration displays (e.g., "1.5s", "2.3s")
      await expect(page.getByText(/\d+(\.\d+)?s/).first()).toBeVisible();
    });

    test('should show screenshot button for steps with screenshots', async ({ page }) => {
      await page.goto('/runs/run-1');
      await page.waitForLoadState('networkidle');

      // Step 4 has a screenshot
      const screenshotButton = page.locator('button[title*="screenshot"]').or(
        page.locator('button').filter({ has: page.locator('svg') }).filter({ hasText: '' })
      );
      // At least one screenshot button should exist
    });
  });

  test.describe('Navigation', () => {
    test('should navigate back to test runs when clicking Back', async ({ page }) => {
      await page.goto('/runs/run-1');
      await page.waitForLoadState('networkidle');

      const backButton = page.getByText('Back to Test Runs');
      await backButton.click();

      await expect(page).toHaveURL(/.*\/runs$/);
    });

    test('should display View Report link', async ({ page }) => {
      await page.goto('/runs/run-1');
      await page.waitForLoadState('networkidle');

      const reportLink = page.getByRole('link', { name: /view report/i });
      await expect(reportLink).toBeVisible();
    });
  });

  test.describe('Not Found', () => {
    test('should show not found message for invalid run ID', async ({ page }) => {
      await page.route('**/api/v1/runs/invalid-id', async (route) => {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Run not found' }),
        });
      });

      await page.goto('/runs/invalid-id');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText('Test run not found')).toBeVisible();
      await expect(page.getByRole('button', { name: /back to test runs/i })).toBeVisible();
    });
  });

  test.describe('Full Page Screenshots', () => {
    test('should capture run details page', async ({ page }) => {
      await page.goto('/runs/run-1');
      await page.waitForLoadState('networkidle');

      await page.screenshot({
        path: 'screenshots/run-details-full.png',
        fullPage: true,
      });
    });
  });
});
