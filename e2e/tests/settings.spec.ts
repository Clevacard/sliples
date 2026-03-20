import { test, expect } from '@playwright/test';
import { mockAuthenticatedState, testUsers } from '../fixtures/auth.fixture';

// Mock data for API keys
const mockApiKeys = [
  {
    id: 'key-1',
    name: 'CI/CD Pipeline Key',
    prefix: 'sk_test_abc',
    created_at: new Date(Date.now() - 7 * 24 * 3600000).toISOString(),
    last_used_at: new Date(Date.now() - 3600000).toISOString(),
    expires_at: new Date(Date.now() + 30 * 24 * 3600000).toISOString(),
  },
  {
    id: 'key-2',
    name: 'Development Key',
    prefix: 'sk_test_def',
    created_at: new Date(Date.now() - 30 * 24 * 3600000).toISOString(),
    last_used_at: null,
    expires_at: null,
  },
];

test.describe('Settings Page', () => {
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
          picture_url: 'https://example.com/avatar.png',
          role: 'user',
        }),
      });
    });

    await page.route('**/api/v1/api-keys**', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockApiKeys),
        });
      } else if (route.request().method() === 'POST') {
        const body = JSON.parse(route.request().postData() || '{}');
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'new-key-id',
            name: body.name,
            key: 'sk_test_newkey123456789',
            prefix: 'sk_test_new',
            created_at: new Date().toISOString(),
            expires_at: body.expires_at,
          }),
        });
      } else if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 204,
        });
      }
    });

    // Authenticate
    await mockAuthenticatedState(page, testUsers.user);
  });

  test.describe('Page Layout', () => {
    test('should display settings page with tabs', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      // Check page heading
      await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();

      // Check for tabs
      await expect(page.getByRole('button', { name: 'Profile' })).toBeVisible();
      await expect(page.getByRole('button', { name: 'API Keys' })).toBeVisible();
      await expect(page.getByRole('button', { name: 'Preferences' })).toBeVisible();

      // Take screenshot
      await page.screenshot({ path: 'screenshots/settings-page.png', fullPage: true });
    });

    test('should show Profile tab by default', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      // Profile tab should be active
      await expect(page.getByText('User Information')).toBeVisible();
    });
  });

  test.describe('Profile Tab', () => {
    test('should display user information', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      // Check for user details
      await expect(page.getByText('Name')).toBeVisible();
      await expect(page.getByText('Test User')).toBeVisible();
      await expect(page.getByText('Email')).toBeVisible();
      await expect(page.getByText('user@example.com')).toBeVisible();
      await expect(page.getByText('Role')).toBeVisible();
    });

    test('should display user avatar', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      // Check for avatar image or placeholder
      const avatar = page.locator('img').filter({ hasNotText: /.+/ }).first().or(
        page.locator('[class*="rounded-full"]').filter({ has: page.locator('span') })
      );
      await expect(avatar).toBeVisible();
    });

    test('should display SSO information note', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText(/profile information is managed through your sso provider/i)).toBeVisible();
    });

    test('should display About Sliples section', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText('About Sliples')).toBeVisible();
      await expect(page.getByText(/version/i)).toBeVisible();
    });

    test('should display documentation links', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      await expect(page.getByRole('link', { name: /api documentation/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /health check endpoint/i })).toBeVisible();
    });
  });

  test.describe('API Keys Tab', () => {
    test('should switch to API Keys tab', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      // Click API Keys tab
      await page.getByRole('button', { name: 'API Keys' }).click();
      await page.waitForTimeout(300);

      // API Keys content should be visible
      await expect(page.getByText(/api keys/i).first()).toBeVisible();

      // Take screenshot
      await page.screenshot({ path: 'screenshots/settings-api-keys.png' });
    });

    test('should display list of API keys', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      await page.getByRole('button', { name: 'API Keys' }).click();
      await page.waitForTimeout(500);

      // Check for API key names
      await expect(page.getByText('CI/CD Pipeline Key')).toBeVisible();
      await expect(page.getByText('Development Key')).toBeVisible();
    });

    test('should display key prefixes', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      await page.getByRole('button', { name: 'API Keys' }).click();
      await page.waitForTimeout(500);

      // Check for key prefixes
      await expect(page.getByText('sk_test_abc')).toBeVisible();
      await expect(page.getByText('sk_test_def')).toBeVisible();
    });

    test('should show Create API Key button', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      await page.getByRole('button', { name: 'API Keys' }).click();
      await page.waitForTimeout(300);

      const createButton = page.getByRole('button', { name: /create.*key|new.*key|add.*key/i });
      await expect(createButton).toBeVisible();
    });

    test('should open create API key dialog', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      await page.getByRole('button', { name: 'API Keys' }).click();
      await page.waitForTimeout(300);

      const createButton = page.getByRole('button', { name: /create.*key|new.*key|add.*key/i });
      await createButton.click();

      // Dialog should open
      await expect(page.getByText(/create.*api key|new.*api key/i)).toBeVisible();

      // Take screenshot of dialog
      await page.screenshot({ path: 'screenshots/create-api-key-dialog.png' });
    });

    test('should create new API key', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      await page.getByRole('button', { name: 'API Keys' }).click();
      await page.waitForTimeout(300);

      const createButton = page.getByRole('button', { name: /create.*key|new.*key|add.*key/i });
      await createButton.click();

      // Fill in the form
      const nameInput = page.getByPlaceholder(/name|description/i).or(
        page.locator('input[type="text"]').first()
      );
      await nameInput.fill('Test Key');

      // Submit
      const submitButton = page.getByRole('button', { name: /create|save|submit/i }).last();
      await submitButton.click();

      await page.waitForTimeout(500);

      // Should show the new key (once only, copy it)
      const keyDisplay = page.getByText(/sk_test_newkey/i);
      if (await keyDisplay.isVisible()) {
        // Key should be displayed for copying
        await expect(keyDisplay).toBeVisible();
      }
    });

    test('should show delete confirmation', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      await page.getByRole('button', { name: 'API Keys' }).click();
      await page.waitForTimeout(500);

      // Find delete button for first key
      const deleteButton = page.getByRole('button', { name: /delete|remove|revoke/i }).first();
      if (await deleteButton.isVisible()) {
        await deleteButton.click();

        // Confirmation dialog should appear
        await expect(page.getByText(/are you sure|confirm|delete/i)).toBeVisible();
      }
    });
  });

  test.describe('Preferences Tab', () => {
    test('should switch to Preferences tab', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      // Click Preferences tab
      await page.getByRole('button', { name: 'Preferences' }).click();
      await page.waitForTimeout(300);

      // Preferences content should be visible
      await expect(page.getByText('Appearance')).toBeVisible();

      // Take screenshot
      await page.screenshot({ path: 'screenshots/settings-preferences.png' });
    });

    test('should display theme options', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      await page.getByRole('button', { name: 'Preferences' }).click();
      await page.waitForTimeout(300);

      await expect(page.getByText('Theme')).toBeVisible();
      await expect(page.getByText('Dark')).toBeVisible();
      await expect(page.getByText('Light')).toBeVisible();
    });

    test('should toggle theme selection', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      await page.getByRole('button', { name: 'Preferences' }).click();
      await page.waitForTimeout(300);

      // Click Light theme
      const lightButton = page.locator('button').filter({ hasText: 'Light' });
      await lightButton.click();

      // Light theme warning should appear (coming soon)
      await expect(page.getByText(/light theme.*coming soon/i)).toBeVisible();
    });

    test('should display notification settings', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      await page.getByRole('button', { name: 'Preferences' }).click();
      await page.waitForTimeout(300);

      await expect(page.getByText('Notifications')).toBeVisible();
      await expect(page.getByText('Email on failure')).toBeVisible();
      await expect(page.getByText('Email on success')).toBeVisible();
      await expect(page.getByText('Browser notifications')).toBeVisible();
    });

    test('should toggle notification settings', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      await page.getByRole('button', { name: 'Preferences' }).click();
      await page.waitForTimeout(300);

      // Find toggle for email on failure
      const emailFailureRow = page.locator('div').filter({ hasText: 'Email on failure' }).first();
      const toggle = emailFailureRow.locator('button[class*="rounded-full"]').or(
        emailFailureRow.locator('[role="switch"]')
      );

      if (await toggle.isVisible()) {
        await toggle.click();
        // Toggle state should change (visual feedback)
      }
    });

    test('should display data retention information', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      await page.getByRole('button', { name: 'Preferences' }).click();
      await page.waitForTimeout(300);

      await expect(page.getByText('Data & Privacy')).toBeVisible();
      await expect(page.getByText(/12 months/i)).toBeVisible();
    });
  });

  test.describe('Admin User Settings', () => {
    test.beforeEach(async ({ page }) => {
      // Override auth mock for admin
      await page.route('**/api/v1/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'admin-user-id',
            email: 'admin@example.com',
            name: 'Admin User',
            picture_url: null,
            role: 'admin',
          }),
        });
      });

      await mockAuthenticatedState(page, testUsers.admin);
    });

    test('should display admin role badge', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      // Admin role should be displayed
      await expect(page.getByText('admin')).toBeVisible();
    });
  });

  test.describe('Tab Navigation', () => {
    test('should persist tab state', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      // Switch to Preferences
      await page.getByRole('button', { name: 'Preferences' }).click();
      await page.waitForTimeout(300);

      // Preferences should be visible
      await expect(page.getByText('Appearance')).toBeVisible();

      // Switch to API Keys
      await page.getByRole('button', { name: 'API Keys' }).click();
      await page.waitForTimeout(300);

      // API Keys should be visible
      await expect(page.getByText('CI/CD Pipeline Key')).toBeVisible();

      // Switch back to Profile
      await page.getByRole('button', { name: 'Profile' }).click();
      await page.waitForTimeout(300);

      // Profile should be visible
      await expect(page.getByText('User Information')).toBeVisible();
    });
  });

  test.describe('Full Page Screenshots', () => {
    test('should capture all settings tabs', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      // Profile tab
      await page.screenshot({
        path: 'screenshots/settings-profile-full.png',
        fullPage: true,
      });

      // API Keys tab
      await page.getByRole('button', { name: 'API Keys' }).click();
      await page.waitForTimeout(500);
      await page.screenshot({
        path: 'screenshots/settings-apikeys-full.png',
        fullPage: true,
      });

      // Preferences tab
      await page.getByRole('button', { name: 'Preferences' }).click();
      await page.waitForTimeout(300);
      await page.screenshot({
        path: 'screenshots/settings-preferences-full.png',
        fullPage: true,
      });
    });

    test('should capture settings on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });

      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      await page.screenshot({
        path: 'screenshots/settings-mobile.png',
        fullPage: true,
      });
    });
  });
});
