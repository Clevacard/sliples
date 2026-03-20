import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Test Runs page object
 */
export class TestRunsPage extends BasePage {
  // Selectors
  readonly pageHeading: Locator;
  readonly newRunButton: Locator;
  readonly statusFilter: Locator;
  readonly dateFromInput: Locator;
  readonly dateToInput: Locator;
  readonly applyFiltersButton: Locator;
  readonly resetFiltersButton: Locator;
  readonly runsTable: Locator;

  constructor(page: Page) {
    super(page);

    this.pageHeading = page.getByRole('heading', { name: 'Test Runs' });
    this.newRunButton = page.getByRole('button', { name: /new test run/i });
    this.statusFilter = page.locator('select').filter({ hasText: /all statuses/i });
    this.dateFromInput = page.locator('input[type="date"]').first();
    this.dateToInput = page.locator('input[type="date"]').last();
    this.applyFiltersButton = page.getByRole('button', { name: /apply/i });
    this.resetFiltersButton = page.getByRole('button', { name: /reset/i });
    this.runsTable = page.locator('table');
  }

  async goto(): Promise<void> {
    await this.page.goto('/runs');
    await this.waitForPageLoad();
  }

  /**
   * Filter by status
   */
  async filterByStatus(status: string): Promise<void> {
    await this.statusFilter.selectOption(status);
    await this.applyFiltersButton.click();
    await this.page.waitForTimeout(500);
  }

  /**
   * Reset filters
   */
  async resetFilters(): Promise<void> {
    await this.resetFiltersButton.click();
    await this.page.waitForTimeout(500);
  }

  /**
   * Click New Test Run button
   */
  async clickNewRun(): Promise<void> {
    await this.newRunButton.click();
  }

  /**
   * Get all run rows
   */
  getRunRows(): Locator {
    return this.runsTable.locator('tbody tr');
  }

  /**
   * Get run by index
   */
  getRunByIndex(index: number): Locator {
    return this.getRunRows().nth(index);
  }

  /**
   * Click View Details for a run
   */
  async clickRunDetails(index: number): Promise<void> {
    const detailsLink = this.getRunByIndex(index).getByRole('link', { name: /view details/i });
    await detailsLink.click();
  }

  /**
   * Check if empty state is shown
   */
  async isEmptyStateVisible(): Promise<boolean> {
    const emptyText = this.page.getByText(/no test runs found/i);
    return this.isVisible(emptyText);
  }

  /**
   * Get run count
   */
  async getRunCount(): Promise<number> {
    const rows = await this.getRunRows().count();
    return rows;
  }
}

/**
 * New Run Modal page object
 */
export class NewRunModal {
  readonly page: Page;
  readonly modal: Locator;
  readonly environmentSelect: Locator;
  readonly startButton: Locator;
  readonly cancelButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.modal = page.locator('[role="dialog"]').or(page.locator('.modal'));
    this.environmentSelect = page.locator('select').filter({ hasText: /select an environment/i });
    this.startButton = page.getByRole('button', { name: /start test run/i });
    this.cancelButton = page.getByRole('button', { name: /cancel/i });
  }

  /**
   * Check if modal is visible
   */
  async isVisible(): Promise<boolean> {
    try {
      await expect(this.page.getByText('Create New Test Run')).toBeVisible({ timeout: 3000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Select environment
   */
  async selectEnvironment(envName: string): Promise<void> {
    await this.environmentSelect.selectOption(envName);
  }

  /**
   * Toggle tag
   */
  async toggleTag(tag: string): Promise<void> {
    const tagButton = this.page.locator('button').filter({ hasText: `@${tag}` });
    await tagButton.click();
  }

  /**
   * Toggle browser
   */
  async toggleBrowser(browser: string): Promise<void> {
    const browserLabel = this.page.locator('label').filter({ hasText: browser });
    await browserLabel.click();
  }

  /**
   * Start the test run
   */
  async start(): Promise<void> {
    await this.startButton.click();
  }

  /**
   * Cancel and close modal
   */
  async cancel(): Promise<void> {
    await this.cancelButton.click();
  }
}

/**
 * Run Details page object
 */
export class RunDetailsPage extends BasePage {
  readonly backButton: Locator;
  readonly statusBadge: Locator;
  readonly runId: Locator;
  readonly viewReportLink: Locator;
  readonly testStepsSection: Locator;
  readonly stepsList: Locator;

  constructor(page: Page) {
    super(page);

    this.backButton = page.getByText('Back to Test Runs');
    this.statusBadge = page.locator('.badge').first();
    this.runId = page.locator('p').filter({ hasText: /ID:/ });
    this.viewReportLink = page.getByRole('link', { name: /view report/i });
    this.testStepsSection = page.locator('.card').filter({ hasText: 'Test Steps' });
    this.stepsList = this.testStepsSection.locator('[class*="rounded-lg border"]');
  }

  async goto(runId: string = 'run-1'): Promise<void> {
    await this.page.goto(`/runs/${runId}`);
    await this.waitForPageLoad();
  }

  /**
   * Go back to test runs list
   */
  async goBack(): Promise<void> {
    await this.backButton.click();
  }

  /**
   * Get run status
   */
  async getStatus(): Promise<string | null> {
    return this.statusBadge.textContent();
  }

  /**
   * Get step count
   */
  async getStepCount(): Promise<number> {
    return this.stepsList.count();
  }

  /**
   * Get step by index
   */
  getStep(index: number): Locator {
    return this.stepsList.nth(index);
  }

  /**
   * Click on a step to expand
   */
  async expandStep(index: number): Promise<void> {
    const step = this.getStep(index);
    await step.click();
  }

  /**
   * Check if step has screenshot
   */
  async stepHasScreenshot(index: number): Promise<boolean> {
    const step = this.getStep(index);
    const screenshotButton = step.locator('button[title*="screenshot"]');
    try {
      await expect(screenshotButton).toBeVisible({ timeout: 1000 });
      return true;
    } catch {
      return false;
    }
  }
}
