import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Settings page object
 */
export class SettingsPage extends BasePage {
  // Selectors
  readonly pageHeading: Locator;
  readonly profileTab: Locator;
  readonly apiKeysTab: Locator;
  readonly preferencesTab: Locator;

  constructor(page: Page) {
    super(page);

    this.pageHeading = page.getByRole('heading', { name: 'Settings' });
    this.profileTab = page.getByRole('button', { name: 'Profile' });
    this.apiKeysTab = page.getByRole('button', { name: 'API Keys' });
    this.preferencesTab = page.getByRole('button', { name: 'Preferences' });
  }

  async goto(): Promise<void> {
    await this.page.goto('/settings');
    await this.waitForPageLoad();
  }

  /**
   * Switch to Profile tab
   */
  async goToProfile(): Promise<void> {
    await this.profileTab.click();
    await this.page.waitForTimeout(300);
  }

  /**
   * Switch to API Keys tab
   */
  async goToApiKeys(): Promise<void> {
    await this.apiKeysTab.click();
    await this.page.waitForTimeout(300);
  }

  /**
   * Switch to Preferences tab
   */
  async goToPreferences(): Promise<void> {
    await this.preferencesTab.click();
    await this.page.waitForTimeout(300);
  }

  /**
   * Get active tab
   */
  async getActiveTab(): Promise<string | null> {
    const activeTab = this.page.locator('button[class*="bg-gray-700"]');
    return activeTab.textContent();
  }
}

/**
 * Profile tab page object
 */
export class ProfileTab {
  readonly page: Page;
  readonly userNameField: Locator;
  readonly userEmailField: Locator;
  readonly userRoleField: Locator;
  readonly userAvatar: Locator;
  readonly aboutSection: Locator;
  readonly apiDocsLink: Locator;
  readonly healthCheckLink: Locator;

  constructor(page: Page) {
    this.page = page;
    this.userNameField = page.locator('.card').filter({ hasText: 'User Information' }).getByText(/Test User|Admin User/);
    this.userEmailField = page.getByText(/@example\.com/);
    this.userRoleField = page.locator('span').filter({ hasText: /admin|user|viewer/ });
    this.userAvatar = page.locator('img[class*="rounded-full"]').or(
      page.locator('div[class*="rounded-full"]').filter({ has: page.locator('span') })
    );
    this.aboutSection = page.locator('.card').filter({ hasText: 'About Sliples' });
    this.apiDocsLink = page.getByRole('link', { name: /api documentation/i });
    this.healthCheckLink = page.getByRole('link', { name: /health check endpoint/i });
  }

  /**
   * Get user name
   */
  async getUserName(): Promise<string | null> {
    const nameElement = this.page.locator('.card').filter({ hasText: 'User Information' }).locator('p.text-gray-100').first();
    return nameElement.textContent();
  }

  /**
   * Get user email
   */
  async getUserEmail(): Promise<string | null> {
    return this.userEmailField.textContent();
  }

  /**
   * Get user role
   */
  async getUserRole(): Promise<string | null> {
    return this.userRoleField.textContent();
  }

  /**
   * Check if avatar is visible
   */
  async isAvatarVisible(): Promise<boolean> {
    try {
      await expect(this.userAvatar).toBeVisible({ timeout: 3000 });
      return true;
    } catch {
      return false;
    }
  }
}

/**
 * API Keys tab page object
 */
export class ApiKeysTab {
  readonly page: Page;
  readonly createKeyButton: Locator;
  readonly keysList: Locator;

  constructor(page: Page) {
    this.page = page;
    this.createKeyButton = page.getByRole('button', { name: /create.*key|new.*key|add.*key/i });
    this.keysList = page.locator('[class*="border"]').filter({ has: page.locator('[class*="font-mono"]') });
  }

  /**
   * Click create key button
   */
  async clickCreateKey(): Promise<void> {
    await this.createKeyButton.click();
  }

  /**
   * Get all API keys
   */
  async getKeyCount(): Promise<number> {
    return this.keysList.count();
  }

  /**
   * Get key by name
   */
  getKeyByName(name: string): Locator {
    return this.page.locator('div').filter({ hasText: name }).first();
  }

  /**
   * Delete a key by name
   */
  async deleteKey(name: string): Promise<void> {
    const keyRow = this.getKeyByName(name);
    const deleteButton = keyRow.getByRole('button', { name: /delete|remove|revoke/i });
    await deleteButton.click();
  }
}

/**
 * Create API Key Modal
 */
export class CreateApiKeyModal {
  readonly page: Page;
  readonly nameInput: Locator;
  readonly createButton: Locator;
  readonly cancelButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.nameInput = page.getByPlaceholder(/name|description/i).or(
      page.locator('input[type="text"]').first()
    );
    this.createButton = page.getByRole('button', { name: /create|save|submit/i }).last();
    this.cancelButton = page.getByRole('button', { name: /cancel/i });
  }

  /**
   * Check if modal is visible
   */
  async isVisible(): Promise<boolean> {
    try {
      await expect(this.page.getByText(/create.*api key|new.*api key/i)).toBeVisible({ timeout: 3000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Fill the name field
   */
  async fillName(name: string): Promise<void> {
    await this.nameInput.fill(name);
  }

  /**
   * Create the key
   */
  async create(): Promise<void> {
    await this.createButton.click();
  }

  /**
   * Cancel
   */
  async cancel(): Promise<void> {
    await this.cancelButton.click();
  }
}

/**
 * Preferences tab page object
 */
export class PreferencesTab {
  readonly page: Page;
  readonly darkThemeButton: Locator;
  readonly lightThemeButton: Locator;
  readonly emailOnFailureToggle: Locator;
  readonly emailOnSuccessToggle: Locator;
  readonly browserNotificationsToggle: Locator;

  constructor(page: Page) {
    this.page = page;
    this.darkThemeButton = page.locator('button').filter({ hasText: 'Dark' });
    this.lightThemeButton = page.locator('button').filter({ hasText: 'Light' });
    this.emailOnFailureToggle = page.locator('div').filter({ hasText: 'Email on failure' }).locator('button[class*="rounded-full"]');
    this.emailOnSuccessToggle = page.locator('div').filter({ hasText: 'Email on success' }).locator('button[class*="rounded-full"]');
    this.browserNotificationsToggle = page.locator('div').filter({ hasText: 'Browser notifications' }).locator('button[class*="rounded-full"]');
  }

  /**
   * Select dark theme
   */
  async selectDarkTheme(): Promise<void> {
    await this.darkThemeButton.click();
  }

  /**
   * Select light theme
   */
  async selectLightTheme(): Promise<void> {
    await this.lightThemeButton.click();
  }

  /**
   * Toggle email on failure
   */
  async toggleEmailOnFailure(): Promise<void> {
    await this.emailOnFailureToggle.click();
  }

  /**
   * Toggle email on success
   */
  async toggleEmailOnSuccess(): Promise<void> {
    await this.emailOnSuccessToggle.click();
  }

  /**
   * Toggle browser notifications
   */
  async toggleBrowserNotifications(): Promise<void> {
    await this.browserNotificationsToggle.click();
  }
}
