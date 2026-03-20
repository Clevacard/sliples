import { test as setup, expect } from '@playwright/test';
import { AUTH_FILE, testUsers } from '../fixtures/auth.fixture';
import fs from 'fs';
import path from 'path';
import jwt from 'jsonwebtoken';

// Real API key for testing
const TEST_API_KEY = 'P9K05ahFmX8DUAco5EEOBVg3rM_zbd7pVEo-I2pbsaI';

// JWT settings (must match backend configuration)
const JWT_SECRET_KEY = 'sliples-jwt-secret-change-in-prod';
const JWT_ALGORITHM = 'HS256';
const JWT_EXPIRY_HOURS = 24;

/**
 * Generate a valid JWT token for the test user
 */
function generateJwtToken(userId: string, email: string): string {
  const now = Math.floor(Date.now() / 1000);
  const expiresIn = JWT_EXPIRY_HOURS * 3600;

  const payload = {
    sub: userId,
    email: email,
    iat: now,
    exp: now + expiresIn,
  };

  return jwt.sign(payload, JWT_SECRET_KEY, { algorithm: JWT_ALGORITHM as jwt.Algorithm });
}

/**
 * Authentication setup - creates a reusable authenticated state
 * This runs once before all tests to set up the authentication with real JWT token
 */
setup('authenticate', async ({ page }) => {
  // Ensure the auth directory exists
  const authDir = path.dirname(AUTH_FILE);
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
  }

  const user = testUsers.user;

  // Generate JWT token
  const jwtToken = generateJwtToken(user.id, user.email);

  // Navigate to login page
  await page.goto('/login');
  await page.waitForLoadState('domcontentloaded');

  // Set the JWT token as a cookie
  await page.context().addCookies([
    {
      name: 'access_token',
      value: jwtToken,
      domain: 'sliples.localhost.in',
      path: '/',
      httpOnly: true,
      secure: true,
      sameSite: 'Lax',
    },
  ]);

  // Set up real authentication state in localStorage
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

  // Reload and navigate to dashboard to verify auth works
  await page.reload();
  await page.goto('/dashboard');
  await page.waitForLoadState('networkidle');

  // Take screenshot of authenticated state
  await page.screenshot({ path: 'screenshots/auth-setup-complete.png', fullPage: true });

  // Save the authenticated state
  await page.context().storageState({ path: AUTH_FILE });
});
