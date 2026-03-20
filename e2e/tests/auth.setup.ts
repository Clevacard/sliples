import { test as setup, expect } from '@playwright/test';
import { AUTH_FILE, testUsers } from '../fixtures/auth.fixture';
import fs from 'fs';
import path from 'path';

/**
 * Authentication setup - creates a reusable authenticated state
 * This runs once before all tests to set up the authentication
 */
setup('authenticate', async ({ page }) => {
  // Ensure the auth directory exists
  const authDir = path.dirname(AUTH_FILE);
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
  }

  // Navigate to login page
  await page.goto('/login');
  await page.waitForLoadState('domcontentloaded');

  // Mock the authentication state
  await page.evaluate((user) => {
    const authState = {
      state: {
        user: {
          id: 'test-user-id',
          email: user.email,
          name: user.name,
          picture_url: null,
          role: user.role,
        },
        isAuthenticated: true,
      },
      version: 0,
    };

    localStorage.setItem('sliples-auth', JSON.stringify(authState));
  }, testUsers.user);

  // Setup API mocks that will persist in storage state
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

  // Reload and navigate to dashboard to verify auth works
  await page.reload();
  await page.goto('/dashboard');
  await page.waitForLoadState('networkidle');

  // Save the authenticated state
  await page.context().storageState({ path: AUTH_FILE });
});
