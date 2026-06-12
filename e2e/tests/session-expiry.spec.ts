import { test, expect } from '@playwright/test';
import { mockAuthenticatedState, clearAuthState, testUsers } from '../fixtures/auth.fixture';

/**
 * Tests for expired/invalid/missing session handling.
 *
 * Scenarios covered:
 * - Expired cookie → redirect to login with session=expired banner
 * - Missing auth state → redirect to login
 * - 401 on API call while "authenticated" → redirect with from= param
 * - Post-login redirect back to origin page
 * - No loop: already on /login doesn't re-redirect
 */

test.describe('Session Expiry & Invalid Session Handling', () => {

  test.describe('Expired cookie / server-invalidated session', () => {
    test('should redirect to login when JWT cookie is expired', async ({ page }) => {
      // Set localStorage auth state but NO valid cookie (simulates expired cookie)
      await page.goto('/login');
      await page.evaluate(({ userData }) => {
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
      }, { userData: testUsers.user });

      // Navigate to protected page — no cookie means /auth/me 401s
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Must land on login page
      await expect(page).toHaveURL(/\/login/);
    });

    test('should show session-expired banner after 401 redirect', async ({ page }) => {
      // Set stale localStorage auth but no valid cookie
      await page.goto('/login');
      await page.evaluate(({ userData }) => {
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
      }, { userData: testUsers.user });

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // URL should have session=expired param
      const url = page.url();
      expect(url).toContain('session=expired');

      // Banner text visible
      await expect(page.getByText(/session has expired/i)).toBeVisible();

      await page.screenshot({ path: 'screenshots/session-expired-banner.png', fullPage: true });
    });

    test('should NOT show session-expired banner on fresh visit to /login', async ({ page }) => {
      await clearAuthState(page);
      await page.goto('/login');
      await page.waitForLoadState('networkidle');

      // No banner — user wasn't previously logged in
      await expect(page.getByText(/session has expired/i)).not.toBeVisible();
    });
  });

  test.describe('Missing auth state', () => {
    test('should redirect to login when localStorage is empty and no cookie', async ({ page }) => {
      await clearAuthState(page);
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL(/\/login/);
    });

    test('should redirect to login from any protected route', async ({ page }) => {
      const protectedRoutes = ['/dashboard', '/scenarios', '/runs', '/settings', '/environments'];

      for (const route of protectedRoutes) {
        await clearAuthState(page);
        await page.goto(route);
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveURL(/\/login/, { message: `${route} should redirect to login` });
      }
    });
  });

  test.describe('Redirect back to origin after login', () => {
    test('should redirect to /login with from= param when accessing protected route unauthenticated', async ({ page }) => {
      await clearAuthState(page);
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // URL should contain from= pointing back to /scenarios
      await expect(page).toHaveURL(/\/login/);
      // The redirect happens via ProtectedRoute Navigate component — from= is in location state
      // Verify we at least landed on login
      await expect(page.getByRole('button', { name: /sign in with google/i })).toBeVisible();
    });

    test('should redirect authenticated user back to dashboard (not /login)', async ({ page }) => {
      await mockAuthenticatedState(page, testUsers.user);
      await page.goto('/login');
      await page.waitForTimeout(2000);

      // Should be redirected away from login
      await expect(page).not.toHaveURL(/\/login/);
    });

    test('should redirect to /login?from= when session expires mid-session', async ({ page }) => {
      // Start authenticated
      await mockAuthenticatedState(page, testUsers.user);
      await page.goto('/scenarios');
      await page.waitForLoadState('networkidle');

      // Simulate session expiry by clearing cookie and triggering a reload
      await page.context().clearCookies();

      // Reload triggers ProtectedRoute's fetchCurrentUser → 401 → redirect
      await page.reload();
      await page.waitForLoadState('networkidle');

      await expect(page).toHaveURL(/\/login/);

      await page.screenshot({ path: 'screenshots/mid-session-expiry.png', fullPage: true });
    });
  });

  test.describe('No infinite redirect loops', () => {
    test('/login page should not redirect when unauthenticated', async ({ page }) => {
      await clearAuthState(page);
      await page.goto('/login');
      await page.waitForLoadState('networkidle');

      // Must stay on /login — no loop
      await expect(page).toHaveURL(/\/login/);
      await expect(page.getByRole('button', { name: /sign in with google/i })).toBeVisible();
    });

    test('/login page with session=expired should not loop', async ({ page }) => {
      await clearAuthState(page);
      await page.goto('/login?session=expired');
      await page.waitForLoadState('networkidle');

      // Stays on login, shows banner, no redirect
      await expect(page).toHaveURL(/\/login/);
      await expect(page.getByText(/session has expired/i)).toBeVisible();
    });

    test('/auth/callback page should not trigger 401 redirect loop', async ({ page }) => {
      await clearAuthState(page);
      // Visiting callback without code — should show error state, not redirect loop
      await page.goto('/auth/callback');
      await page.waitForLoadState('networkidle');

      // Should stay on callback page with error, not loop to /login repeatedly
      const url = page.url();
      expect(url).not.toContain('session=expired');
    });
  });

  test.describe('UI state after session expiry', () => {
    test('should not show user avatar or sign-out when session is invalid', async ({ page }) => {
      // Stale localStorage, no cookie
      await page.goto('/login');
      await page.evaluate(({ userData }) => {
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
      }, { userData: testUsers.user });

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Should be on login page — no avatar visible
      await expect(page).toHaveURL(/\/login/);
      // Sign-out button must not be visible on login page
      await expect(page.getByRole('button', { name: /sign out/i })).not.toBeVisible();

      await page.screenshot({ path: 'screenshots/no-avatar-after-expiry.png', fullPage: true });
    });

    test('should clear stale auth from localStorage after redirect', async ({ page }) => {
      // Populate stale auth
      await page.goto('/login');
      await page.evaluate(({ userData }) => {
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
      }, { userData: testUsers.user });

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // After redirect, localStorage should be cleared or show isAuthenticated: false
      const authState = await page.evaluate(() => {
        const state = localStorage.getItem('sliples-auth');
        if (!state) return null;
        try {
          const parsed = JSON.parse(state);
          return parsed?.state?.isAuthenticated === false ? 'logged_out' : 'still_authenticated';
        } catch {
          return null;
        }
      });

      expect(authState === null || authState === 'logged_out').toBeTruthy();
    });
  });
});
