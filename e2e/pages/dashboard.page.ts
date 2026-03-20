import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Dashboard page object
 */
export class DashboardPage extends BasePage {
  // Selectors
  readonly pageHeading: Locator;
  readonly syncReposButton: Locator;
  readonly runAllTestsButton: Locator;
  readonly systemStatusCard: Locator;
  readonly databaseStatusCard: Locator;
  readonly redisStatusCard: Locator;
  readonly totalScenariosCard: Locator;
  readonly passRateCard: Locator;
  readonly last24hRunsCard: Locator;
  readonly failedTestsCard: Locator;
  readonly trendChart: Locator;
  readonly recentRunsTable: Locator;

  constructor(page: Page) {
    super(page);

    this.pageHeading = page.getByRole('heading', { name: 'Dashboard' });
    this.syncReposButton = page.getByRole('button', { name: /sync repos/i });
    this.runAllTestsButton = page.getByRole('button', { name: /run all tests/i });
    this.systemStatusCard = page.locator('.card').filter({ hasText: 'System Status' });
    this.databaseStatusCard = page.locator('.card').filter({ hasText: 'Database' });
    this.redisStatusCard = page.locator('.card').filter({ hasText: 'Redis' });
    this.totalScenariosCard = page.locator('.card').filter({ hasText: 'Total Scenarios' });
    this.passRateCard = page.locator('.card').filter({ hasText: 'Pass Rate' });
    this.last24hRunsCard = page.locator('.card').filter({ hasText: 'Last 24h Runs' });
    this.failedTestsCard = page.locator('.card').filter({ hasText: 'Failed Tests' });
    this.trendChart = page.locator('.card').filter({ hasText: 'Pass/Fail Trend' });
    this.recentRunsTable = page.locator('.card').filter({ hasText: 'Recent Test Runs' });
  }

  async goto(): Promise<void> {
    await this.page.goto('/dashboard');
    await this.waitForPageLoad();
  }

  /**
   * Get system health status
   */
  async getSystemStatus(): Promise<string | null> {
    const statusText = this.systemStatusCard.locator('span').filter({ hasText: /healthy|unhealthy|unknown/i });
    return statusText.textContent();
  }

  /**
   * Get total scenarios count
   */
  async getTotalScenarios(): Promise<string | null> {
    const value = this.totalScenariosCard.locator('p.text-3xl');
    return value.textContent();
  }

  /**
   * Get pass rate
   */
  async getPassRate(): Promise<string | null> {
    const value = this.passRateCard.locator('p.text-3xl');
    return value.textContent();
  }

  /**
   * Click Sync Repos button
   */
  async clickSyncRepos(): Promise<void> {
    await this.syncReposButton.click();
  }

  /**
   * Click Run All Tests button
   */
  async clickRunAllTests(): Promise<void> {
    await this.runAllTestsButton.click();
  }

  /**
   * Get recent runs
   */
  getRecentRuns(): Locator {
    return this.recentRunsTable.locator('tbody tr');
  }

  /**
   * Get recent run by index
   */
  getRecentRunByIndex(index: number): Locator {
    return this.getRecentRuns().nth(index);
  }

  /**
   * Click on a run details link
   */
  async clickRunDetails(index: number): Promise<void> {
    const detailsLink = this.getRecentRunByIndex(index).getByRole('link', { name: 'Details' });
    await detailsLink.click();
  }

  /**
   * Check if dashboard is loading
   */
  async isLoading(): Promise<boolean> {
    const skeleton = this.page.locator('.animate-pulse').first();
    return this.isVisible(skeleton);
  }

  /**
   * Wait for dashboard to load
   */
  async waitForDashboardLoad(): Promise<void> {
    await expect(this.pageHeading).toBeVisible();
    await expect(this.page.locator('.animate-pulse')).not.toBeVisible({ timeout: 10000 });
  }

  /**
   * Get all stat card values
   */
  async getStatValues(): Promise<{
    totalScenarios: string | null;
    passRate: string | null;
    last24hRuns: string | null;
    failedTests: string | null;
  }> {
    return {
      totalScenarios: await this.getTotalScenarios(),
      passRate: await this.getPassRate(),
      last24hRuns: await this.last24hRunsCard.locator('p.text-3xl').textContent(),
      failedTests: await this.failedTestsCard.locator('p.text-3xl').textContent(),
    };
  }
}
