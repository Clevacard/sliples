import { Page, Locator, expect } from '@playwright/test';

/**
 * Base page object that all page objects extend from.
 * Contains common methods and utilities.
 */
export abstract class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Navigate to this page
   */
  abstract goto(): Promise<void>;

  /**
   * Get the page title
   */
  async getTitle(): Promise<string | null> {
    return this.page.title();
  }

  /**
   * Get the current URL
   */
  getUrl(): string {
    return this.page.url();
  }

  /**
   * Wait for the page to be fully loaded
   */
  async waitForPageLoad(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Take a screenshot
   */
  async takeScreenshot(name: string, fullPage = true): Promise<void> {
    await this.page.screenshot({
      path: `screenshots/${name}.png`,
      fullPage,
    });
  }

  /**
   * Check if an element is visible
   */
  async isVisible(locator: Locator): Promise<boolean> {
    try {
      await expect(locator).toBeVisible({ timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Wait for an element to appear
   */
  async waitForElement(locator: Locator, timeout = 10000): Promise<void> {
    await locator.waitFor({ state: 'visible', timeout });
  }

  /**
   * Click an element with retry
   */
  async clickWithRetry(locator: Locator, retries = 3): Promise<void> {
    for (let i = 0; i < retries; i++) {
      try {
        await locator.click({ timeout: 5000 });
        return;
      } catch (error) {
        if (i === retries - 1) throw error;
        await this.page.waitForTimeout(500);
      }
    }
  }

  /**
   * Fill a form field
   */
  async fillField(locator: Locator, value: string): Promise<void> {
    await locator.clear();
    await locator.fill(value);
  }

  /**
   * Get text content from an element
   */
  async getText(locator: Locator): Promise<string | null> {
    return locator.textContent();
  }

  /**
   * Check if the page has a heading with specific text
   */
  async hasHeading(text: string): Promise<boolean> {
    const heading = this.page.getByRole('heading', { name: text });
    return this.isVisible(heading);
  }

  /**
   * Wait for API response
   */
  async waitForApiResponse(urlPattern: string | RegExp): Promise<void> {
    await this.page.waitForResponse(urlPattern);
  }

  /**
   * Get the navigation sidebar
   */
  getNavSidebar(): Locator {
    return this.page.locator('nav').or(this.page.locator('[role="navigation"]'));
  }

  /**
   * Navigate using sidebar
   */
  async navigateTo(pageName: string): Promise<void> {
    const navLink = this.page.getByRole('link', { name: pageName });
    await navLink.click();
    await this.waitForPageLoad();
  }
}
