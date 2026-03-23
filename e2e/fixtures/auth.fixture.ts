import { test as base, expect, Page } from '@playwright/test';
import path from 'path';
import jwt from 'jsonwebtoken';

// Real API key for testing (from env or default for local dev)
const TEST_API_KEY = process.env.SLIPLES_API_KEY || 'P9K05ahFmX8DUAco5EEOBVg3rM_zbd7pVEo-I2pbsaI';

// JWT settings (must match backend configuration)
const JWT_SECRET_KEY = process.env.JWT_SECRET_KEY || 'sliples-jwt-secret-change-in-prod';
const JWT_ALGORITHM = 'HS256';
const JWT_EXPIRY_HOURS = 24;

// Get domain from SLIPLES_URL or default to local dev
function getCookieDomain(): string {
  const url = process.env.SLIPLES_URL || 'https://sliples.localhost.in:5173';
  try {
    return new URL(url).hostname;
  } catch {
    return 'sliples.localhost.in';
  }
}

// User credentials for testing - using real test user
export interface TestUser {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user' | 'viewer';
}

export const testUsers: Record<string, TestUser> = {
  admin: {
    id: '11111111-1111-1111-1111-111111111111',
    email: 'e2e-test@agantis.team',
    name: 'E2E Test Admin',
    role: 'admin',
  },
  user: {
    id: '11111111-1111-1111-1111-111111111111',
    email: 'e2e-test@agantis.team',
    name: 'E2E Test Admin',
    role: 'admin',
  },
  viewer: {
    id: '11111111-1111-1111-1111-111111111111',
    email: 'e2e-test@agantis.team',
    name: 'E2E Test Admin',
    role: 'admin',
  },
};

// Path to the authentication storage state file
export const AUTH_FILE = path.join(__dirname, '../playwright/.auth/user.json');

/**
 * Generate a valid JWT token for the test user
 */
function generateJwtToken(user: TestUser): string {
  const now = Math.floor(Date.now() / 1000);
  const expiresIn = JWT_EXPIRY_HOURS * 3600;

  const payload = {
    sub: user.id,
    email: user.email,
    iat: now,
    exp: now + expiresIn,
  };

  return jwt.sign(payload, JWT_SECRET_KEY, { algorithm: JWT_ALGORITHM as jwt.Algorithm });
}

/**
 * Set up real authentication state
 * This creates a valid JWT token and sets both the cookie and localStorage
 */
export async function mockAuthenticatedState(page: Page, user: TestUser = testUsers.user) {
  // Generate JWT token
  const jwtToken = generateJwtToken(user);

  // Navigate to the app first (needed for localStorage and cookie access)
  await page.goto('/login');
  await page.waitForLoadState('domcontentloaded');

  // Set the JWT token as a cookie (this is what the backend expects for /auth/me)
  await page.context().addCookies([
    {
      name: 'access_token',
      value: jwtToken,
      domain: getCookieDomain(),
      path: '/',
      httpOnly: true,
      secure: true,
      sameSite: 'Lax',
    },
  ]);

  // Set up auth state in localStorage for the Zustand store
  await page.evaluate(({ userData, apiKey }) => {
    // Set the API key for API authentication
    localStorage.setItem('sliples_api_key', apiKey);

    // Set the Zustand auth state
    const authState = {
      state: {
        user: {
          id: userData.id,
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
  }, { userData: user, apiKey: TEST_API_KEY });

  // Reload to apply the state and let the app verify auth
  await page.reload();
  await page.waitForLoadState('networkidle');
}

/**
 * Clear the authentication state
 */
export async function clearAuthState(page: Page) {
  // Clear cookies
  await page.context().clearCookies();

  // Clear localStorage
  await page.evaluate(() => {
    localStorage.removeItem('sliples-auth');
    localStorage.removeItem('sliples_api_key');
  });
}

/**
 * Extended test fixture with authentication helpers
 */
export const test = base.extend<{
  authenticatedPage: Page;
  adminPage: Page;
}>({
  // Authenticated page as a regular user (same as admin for now)
  authenticatedPage: async ({ page }, use) => {
    await mockAuthenticatedState(page, testUsers.user);
    await use(page);
    await clearAuthState(page);
  },

  // Authenticated page as an admin
  adminPage: async ({ page }, use) => {
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
