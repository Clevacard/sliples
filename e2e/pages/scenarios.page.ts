import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Scenarios page object
 */
export class ScenariosPage extends BasePage {
  // Selectors
  readonly pageHeading: Locator;
  readonly syncAllButton: Locator;
  readonly searchInput: Locator;
  readonly repoFilter: Locator;
  readonly tagFilter: Locator;
  readonly listViewButton: Locator;
  readonly gridViewButton: Locator;
  readonly clearFiltersButton: Locator;
  readonly scenarioList: Locator;

  constructor(page: Page) {
    super(page);

    this.pageHeading = page.getByRole('heading', { name: 'Scenarios' });
    this.syncAllButton = page.getByRole('button', { name: /sync all repos/i });
    this.searchInput = page.getByPlaceholder(/search/i);
    this.repoFilter = page.locator('select').filter({ hasText: /all repositories/i });
    this.tagFilter = page.locator('select').filter({ hasText: /all tags/i });
    this.listViewButton = page.locator('button[title*="List"]');
    this.gridViewButton = page.locator('button[title*="Grid"]');
    this.clearFiltersButton = page.getByRole('button', { name: /clear filters/i });
    this.scenarioList = page.locator('.card');
  }

  async goto(): Promise<void> {
    await this.page.goto('/scenarios');
    await this.waitForPageLoad();
  }

  /**
   * Search for scenarios
   */
  async search(query: string): Promise<void> {
    await this.searchInput.fill(query);
    await this.page.waitForTimeout(500); // Wait for debounce
  }

  /**
   * Clear search
   */
  async clearSearch(): Promise<void> {
    await this.searchInput.clear();
    await this.page.waitForTimeout(500);
  }

  /**
   * Filter by repository
   */
  async filterByRepo(repoName: string): Promise<void> {
    await this.repoFilter.selectOption({ label: repoName });
    await this.page.waitForTimeout(500);
  }

  /**
   * Filter by tag
   */
  async filterByTag(tag: string): Promise<void> {
    await this.tagFilter.selectOption({ label: `@${tag}` });
    await this.page.waitForTimeout(500);
  }

  /**
   * Clear all filters
   */
  async clearFilters(): Promise<void> {
    if (await this.isVisible(this.clearFiltersButton)) {
      await this.clearFiltersButton.click();
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * Switch to list view
   */
  async switchToListView(): Promise<void> {
    await this.listViewButton.click();
    await this.page.waitForTimeout(300);
  }

  /**
   * Switch to grid view
   */
  async switchToGridView(): Promise<void> {
    await this.gridViewButton.click();
    await this.page.waitForTimeout(300);
  }

  /**
   * Click sync all repos
   */
  async clickSyncAll(): Promise<void> {
    await this.syncAllButton.click();
  }

  /**
   * Get scenario count
   */
  async getScenarioCount(): Promise<number> {
    const text = await this.page.getByText(/\d+ scenarios from/).textContent();
    const match = text?.match(/(\d+) scenarios/);
    return match ? parseInt(match[1], 10) : 0;
  }

  /**
   * Get all scenario cards/rows
   */
  getScenarioItems(): Locator {
    return this.page.locator('[class*="hover:border-blue"]').or(
      this.page.locator('a').filter({ has: this.page.locator('h3') })
    );
  }

  /**
   * Click on a scenario by name
   */
  async clickScenario(name: string): Promise<void> {
    const scenario = this.page.getByText(name).first();
    await scenario.click();
  }

  /**
   * Check if empty state is shown
   */
  async isEmptyStateVisible(): Promise<boolean> {
    const emptyText = this.page.getByText(/no scenarios found/i);
    return this.isVisible(emptyText);
  }

  /**
   * Check if no results message is shown
   */
  async isNoResultsVisible(): Promise<boolean> {
    const noResults = this.page.getByText(/no scenarios match/i);
    return this.isVisible(noResults);
  }

  /**
   * Get visible tags
   */
  async getVisibleTags(): Promise<string[]> {
    const tags = await this.page.locator('.badge').filter({ hasText: '@' }).allTextContents();
    return tags.map(t => t.replace('@', ''));
  }
}
