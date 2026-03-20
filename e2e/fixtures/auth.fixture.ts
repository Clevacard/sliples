import { test as base, expect, Page } from '@playwright/test';
import path from 'path';

// User credentials for testing
export interface TestUser {
  email: string;
  name: string;
  role: 'admin' | 'user' | 'viewer';
}

export const testUsers: Record<string, TestUser> = {
  admin: {
    email: 'admin@example.com',
    name: 'Test Admin',
    role: 'admin',
  },
  user: {
    email: 'user@example.com',
    name: 'Test User',
    role: 'user',
  },
  viewer: {
    email: 'viewer@example.com',
    name: 'Test Viewer',
    role: 'viewer',
  },
};

// Path to the authentication storage state file
export const AUTH_FILE = path.join(__dirname, '../playwright/.auth/user.json');

/**
 * Mock the authentication state in localStorage
 * This bypasses the actual Google OAuth flow for testing
 */
export async function mockAuthenticatedState(page: Page, user: TestUser = testUsers.user) {
  // Navigate to the app first (needed for localStorage access)
  await page.goto('/login');

  // Wait for the page to load
  await page.waitForLoadState('domcontentloaded');

  // Mock the authentication state in localStorage
  await page.evaluate((userData) => {
    const authState = {
      state: {
        user: {
          id: 'test-user-id',
          email: userData.email,
          name: userData.name,
          picture_url: null,
          role: userData.role,
        },
        isAuthenticated: true,
      },
      version: 0,
    };

    localStorage.setItem('sliples-auth', JSON.stringify(authState));
  }, user);

  // Reload to apply the mocked state
  await page.reload();
  await page.waitForLoadState('networkidle');
}

/**
 * Clear the authentication state
 */
export async function clearAuthState(page: Page) {
  await page.evaluate(() => {
    localStorage.removeItem('sliples-auth');
  });
}

/**
 * Setup API mocking for authenticated requests
 */
export async function setupApiMocks(page: Page) {
  // Mock the current user endpoint
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

  // Mock health endpoint
  await page.route('**/api/v1/health', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'healthy',
        database: 'connected',
        redis: 'connected',
      }),
    });
  });
}

/**
 * Extended test fixture with authentication helpers
 */
export const test = base.extend<{
  authenticatedPage: Page;
  adminPage: Page;
}>({
  // Authenticated page as a regular user
  authenticatedPage: async ({ page }, use) => {
    await setupApiMocks(page);
    await mockAuthenticatedState(page, testUsers.user);
    await use(page);
    await clearAuthState(page);
  },

  // Authenticated page as an admin
  adminPage: async ({ page }, use) => {
    await setupApiMocks(page);
    await mockAuthenticatedState(page, testUsers.admin);
    await use(page);
    await clearAuthState(page);
  },
});

export { expect };

/**
 * Page Object helper for common authentication actions
 */
export class AuthPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/login');
  }

  async getTitle() {
    return this.page.locator('h1').first().textContent();
  }

  async getGoogleSignInButton() {
    return this.page.getByRole('button', { name: /sign in with google/i });
  }

  async clickGoogleSignIn() {
    const button = await this.getGoogleSignInButton();
    await button.click();
  }

  async isOnLoginPage() {
    return this.page.url().includes('/login');
  }

  async expectLoginPageVisible() {
    await expect(this.page.locator('h1')).toContainText('Sliples');
    await expect(this.page.getByRole('button', { name: /sign in with google/i })).toBeVisible();
  }

  async expectRedirectedToLogin() {
    await expect(this.page).toHaveURL(/.*\/login/);
  }
}

/**
 * Logout helper
 */
export async function logout(page: Page) {
  // Click on user menu
  const userMenu = page.locator('[data-testid="user-menu"]').or(
    page.getByRole('button', { name: /user menu/i })
  ).or(
    page.locator('button').filter({ hasText: /test user/i })
  );

  if (await userMenu.isVisible()) {
    await userMenu.click();

    // Click logout button
    const logoutButton = page.getByRole('menuitem', { name: /logout/i }).or(
      page.getByRole('button', { name: /logout/i })
    ).or(
      page.locator('button').filter({ hasText: /logout/i })
    );

    await logoutButton.click();
  }
}

/**
 * Wait for page to be ready after authentication
 */
export async function waitForAuthenticatedState(page: Page) {
  // Wait for navigation to complete
  await page.waitForLoadState('networkidle');

  // Ensure we're not on the login page
  const currentUrl = page.url();
  if (currentUrl.includes('/login')) {
    throw new Error('Still on login page after authentication');
  }
}
