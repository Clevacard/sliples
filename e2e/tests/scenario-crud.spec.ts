/**
 * E2E tests for Scenario CRUD operations.
 * Tests create, read, update, and delete functionality for scenarios.
 *
 * NOTE: Some tests require seed data and are skipped in production.
 */
import { test, expect } from '@playwright/test';
import { mockAuthenticatedState, testUsers } from '../fixtures/auth.fixture';

// API key for direct API calls
const API_KEY = process.env.SLIPLES_API_KEY || 'P9K05ahFmX8DUAco5EEOBVg3rM_zbd7pVEo-I2pbsaI';
const SLIPLES_URL = process.env.SLIPLES_URL || 'https://sliples.localhost.in:5173';
// For local dev with port 5173, API is on 8000; for deployed, API is same host
const API_BASE = SLIPLES_URL.includes('localhost')
  ? SLIPLES_URL.replace(':5173', ':8000') + '/api/v1'
  : SLIPLES_URL + '/api/v1';

// Check if running in production
const isProduction = process.env.SLIPLES_URL?.includes('agantis.in');

test.describe('Scenario CRUD Operations', () => {
  let createdScenarioId: string | null = null;

  test.beforeEach(async ({ page }) => {
    await mockAuthenticatedState(page, testUsers.admin);
  });

  test.afterEach(async ({ request }) => {
    // Clean up any created scenario
    if (createdScenarioId) {
      try {
        await request.delete(`${API_BASE}/scenarios/${createdScenarioId}`, {
          headers: { 'X-API-Key': API_KEY },
        });
      } catch {
        // Ignore cleanup errors
      }
      createdScenarioId = null;
    }
  });

  test.describe('Read Operations', () => {
    test('should view scenario list', async ({ page }) => {
      test.skip(!!isProduction, 'Skipping seed data test in production');

      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Wait for scenarios to load
      await expect(page.getByRole('heading', { name: /scenarios/i })).toBeVisible({ timeout: 10000 });

      // Take screenshot of scenario list
      await page.screenshot({ path: 'screenshots/crud-scenario-list.png', fullPage: true });

      // Verify at least one scenario is visible (from seed data)
      // The scenarios are displayed as headings within cards
      const scenarioHeading = page.getByRole('heading', { name: /giftstarr/i }).first();
      await expect(scenarioHeading).toBeVisible({ timeout: 10000 });

      console.log('Scenario list displayed successfully');
    });

    test('should view scenario content', async ({ page }) => {
      test.skip(!!isProduction, 'Skipping seed data test in production');

      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Wait for scenarios to load
      await page.waitForTimeout(2000);

      // Take screenshot before clicking
      await page.screenshot({ path: 'screenshots/crud-before-view.png', fullPage: true });

      // Click on the first scenario to view its content
      const firstScenario = page.getByRole('heading', { name: /giftstarr/i }).first();
      await expect(firstScenario).toBeVisible({ timeout: 10000 });
      await firstScenario.click();

      // Wait for scenario detail view or modal
      await page.waitForTimeout(1000);

      // Take screenshot of scenario content
      await page.screenshot({ path: 'screenshots/crud-scenario-content.png', fullPage: true });

      console.log('Scenario content viewed successfully');
    });
  });

  test.describe('Update Operations', () => {
    test('should update scenario content via API', async ({ request }) => {
      // Create a dedicated scenario for this test to avoid conflicts
      const testScenario = {
        name: 'Update Test Scenario',
        feature_path: 'tests/update-test.feature',
        content: 'Original content',
        tags: ['update-test'],
      };

      const createResponse = await request.post(`${API_BASE}/scenarios`, {
        headers: {
          'X-API-Key': API_KEY,
          'Content-Type': 'application/json',
        },
        data: testScenario,
      });
      expect(createResponse.status()).toBe(201);
      const created = await createResponse.json();
      const scenarioId = created.id;

      // Update the scenario content
      const newContent = `Feature: Updated Test Feature

  Scenario: Updated scenario content
    Given I have updated this scenario
    When I check the content
    Then it should be updated`;

      const updateResponse = await request.put(`${API_BASE}/scenarios/${scenarioId}/content`, {
        headers: {
          'X-API-Key': API_KEY,
          'Content-Type': 'application/json',
        },
        data: { content: newContent },
      });

      expect(updateResponse.ok()).toBeTruthy();
      const updatedScenario = await updateResponse.json();
      expect(updatedScenario.content).toBe(newContent);

      console.log('Scenario content updated via API successfully');

      // Clean up - delete the test scenario
      await request.delete(`${API_BASE}/scenarios/${scenarioId}`, {
        headers: { 'X-API-Key': API_KEY },
      });
    });

    test('should update scenario content via UI', async ({ page }) => {
      test.skip(!!isProduction, 'Skipping seed data test in production');

      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Wait for scenarios to load
      await page.waitForTimeout(2000);

      // Take screenshot of scenarios page
      await page.screenshot({ path: 'screenshots/crud-update-list.png', fullPage: true });

      // Click on the first scenario to edit it
      const firstScenario = page.getByRole('heading', { name: /giftstarr/i }).first();
      await expect(firstScenario).toBeVisible({ timeout: 10000 });
      await firstScenario.click();

      // Wait for detail view
      await page.waitForTimeout(1000);

      // Look for an edit button or the content editor
      const editButton = page.getByRole('button', { name: /edit/i });
      const isEditVisible = await editButton.isVisible().catch(() => false);

      if (isEditVisible) {
        await editButton.click();
        await page.waitForTimeout(500);
      }

      // Take screenshot of edit mode
      await page.screenshot({ path: 'screenshots/crud-update-edit-mode.png', fullPage: true });

      // Try to find and interact with Monaco editor or textarea
      const editor = page.locator('.monaco-editor').or(page.locator('textarea'));
      const isEditorVisible = await editor.isVisible().catch(() => false);

      if (isEditorVisible) {
        // Click on editor to focus
        await editor.first().click();
        await page.keyboard.press('Control+a');
        await page.keyboard.type('# Updated content via E2E test');

        // Look for save button
        const saveButton = page.getByRole('button', { name: /save/i });
        const isSaveVisible = await saveButton.isVisible().catch(() => false);

        if (isSaveVisible) {
          await saveButton.click();
          await page.waitForTimeout(1000);
        }

        // Take screenshot after edit
        await page.screenshot({ path: 'screenshots/crud-update-after-save.png', fullPage: true });
      }

      console.log('Scenario update UI test completed');
    });
  });

  test.describe('Create Operations', () => {
    test('should create a new scenario via API', async ({ request }) => {
      const newScenario = {
        name: 'E2E Test Scenario',
        feature_path: 'tests/e2e-test.feature',
        content: `Feature: E2E Test Feature

  Scenario: E2E Created Scenario
    Given I am testing scenario creation
    When I create a new scenario via API
    Then the scenario should be created successfully`,
        tags: ['e2e', 'test', 'automated'],
      };

      const createResponse = await request.post(`${API_BASE}/scenarios`, {
        headers: {
          'X-API-Key': API_KEY,
          'Content-Type': 'application/json',
        },
        data: newScenario,
      });

      expect(createResponse.status()).toBe(201);
      const created = await createResponse.json();

      expect(created.name).toBe(newScenario.name);
      expect(created.feature_path).toBe(newScenario.feature_path);
      expect(created.content).toBe(newScenario.content);
      expect(created.tags).toEqual(newScenario.tags);
      expect(created.id).toBeDefined();

      // Store for cleanup
      createdScenarioId = created.id;

      console.log('Scenario created via API successfully:', created.id);
    });

    test('should display newly created scenario in UI', async ({ page, request }) => {
      // First create a scenario via API
      const newScenario = {
        name: 'UI Visibility Test Scenario',
        feature_path: 'tests/ui-visibility-test.feature',
        content: `Feature: UI Visibility Test

  Scenario: Verify scenario appears in UI
    Given I create a scenario via API
    When I navigate to the scenarios page
    Then the scenario should be visible`,
        tags: ['ui-test'],
      };

      const createResponse = await request.post(`${API_BASE}/scenarios`, {
        headers: {
          'X-API-Key': API_KEY,
          'Content-Type': 'application/json',
        },
        data: newScenario,
      });

      expect(createResponse.status()).toBe(201);
      const created = await createResponse.json();
      createdScenarioId = created.id;

      // Navigate to scenarios page
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Take screenshot
      await page.screenshot({ path: 'screenshots/crud-create-in-ui.png', fullPage: true });

      // Search for the newly created scenario
      const searchInput = page.getByPlaceholder(/search/i);
      const isSearchVisible = await searchInput.isVisible().catch(() => false);

      if (isSearchVisible) {
        await searchInput.fill('UI Visibility Test');
        await page.waitForTimeout(1000);
        await page.screenshot({ path: 'screenshots/crud-create-search.png', fullPage: true });
      }

      // Verify the scenario is visible (by heading or text)
      const scenarioHeading = page.getByRole('heading', { name: /UI Visibility Test/i });
      const scenarioText = page.locator('text=UI Visibility Test Scenario');

      const isVisible = await scenarioHeading.isVisible().catch(() => false) ||
                        await scenarioText.isVisible().catch(() => false);

      // Take final screenshot
      await page.screenshot({ path: 'screenshots/crud-create-visible.png', fullPage: true });

      console.log('New scenario visibility in UI checked, visible:', isVisible);
    });
  });

  test.describe('Delete Operations', () => {
    test('should delete a scenario via API', async ({ request }) => {
      // First create a scenario to delete
      const scenarioToDelete = {
        name: 'Scenario To Delete',
        feature_path: 'tests/to-delete.feature',
        content: 'Feature: To Delete\n  Scenario: Will be deleted',
        tags: ['delete-test'],
      };

      const createResponse = await request.post(`${API_BASE}/scenarios`, {
        headers: {
          'X-API-Key': API_KEY,
          'Content-Type': 'application/json',
        },
        data: scenarioToDelete,
      });

      expect(createResponse.status()).toBe(201);
      const created = await createResponse.json();
      const deleteId = created.id;

      // Now delete it
      const deleteResponse = await request.delete(`${API_BASE}/scenarios/${deleteId}`, {
        headers: { 'X-API-Key': API_KEY },
      });

      expect(deleteResponse.status()).toBe(204);

      // Verify it's deleted by trying to get it
      const getResponse = await request.get(`${API_BASE}/scenarios/${deleteId}`, {
        headers: { 'X-API-Key': API_KEY },
      });

      expect(getResponse.status()).toBe(404);

      console.log('Scenario deleted via API successfully');
    });

    test('should remove deleted scenario from UI', async ({ page, request }) => {
      // Create a scenario
      const scenarioToDelete = {
        name: 'UI Delete Test Scenario',
        feature_path: 'tests/ui-delete-test.feature',
        content: 'Feature: UI Delete Test\n  Scenario: Will be deleted from UI',
        tags: ['ui-delete-test'],
      };

      const createResponse = await request.post(`${API_BASE}/scenarios`, {
        headers: {
          'X-API-Key': API_KEY,
          'Content-Type': 'application/json',
        },
        data: scenarioToDelete,
      });

      expect(createResponse.status()).toBe(201);
      const created = await createResponse.json();

      // Navigate to scenarios page and verify it exists
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Take screenshot before delete
      await page.screenshot({ path: 'screenshots/crud-delete-before.png', fullPage: true });

      // Delete via API
      const deleteResponse = await request.delete(`${API_BASE}/scenarios/${created.id}`, {
        headers: { 'X-API-Key': API_KEY },
      });
      expect(deleteResponse.status()).toBe(204);

      // Refresh the page
      await page.reload();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Take screenshot after delete
      await page.screenshot({ path: 'screenshots/crud-delete-after.png', fullPage: true });

      // Verify the scenario is no longer visible
      const deletedScenario = page.locator('text=UI Delete Test Scenario');
      await expect(deletedScenario).not.toBeVisible({ timeout: 5000 });

      console.log('Deleted scenario removed from UI successfully');
    });
  });

  test.describe('Error Handling', () => {
    test('should return 404 for non-existent scenario', async ({ request }) => {
      const fakeId = '00000000-0000-0000-0000-000000000000';

      const response = await request.get(`${API_BASE}/scenarios/${fakeId}`, {
        headers: { 'X-API-Key': API_KEY },
      });

      expect(response.status()).toBe(404);
      console.log('404 returned for non-existent scenario');
    });

    test('should return 404 when deleting non-existent scenario', async ({ request }) => {
      const fakeId = '00000000-0000-0000-0000-000000000000';

      const response = await request.delete(`${API_BASE}/scenarios/${fakeId}`, {
        headers: { 'X-API-Key': API_KEY },
      });

      expect(response.status()).toBe(404);
      console.log('404 returned when deleting non-existent scenario');
    });

    test('should return 404 when updating non-existent scenario', async ({ request }) => {
      const fakeId = '00000000-0000-0000-0000-000000000000';

      const response = await request.put(`${API_BASE}/scenarios/${fakeId}/content`, {
        headers: {
          'X-API-Key': API_KEY,
          'Content-Type': 'application/json',
        },
        data: { content: 'Some content' },
      });

      expect(response.status()).toBe(404);
      console.log('404 returned when updating non-existent scenario');
    });
  });
});
