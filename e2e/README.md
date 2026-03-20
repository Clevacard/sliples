# Sliples E2E Tests

End-to-end tests for the Sliples UI using Playwright.

## Prerequisites

- Node.js 18 or later
- npm or yarn
- The Sliples frontend running at `https://sliples.localhost.in:5173`

## Installation

```bash
cd e2e
npm install

# Install Playwright browsers
npx playwright install
```

## Running Tests

### Run all tests
```bash
npm test
```

### Run tests in headed mode (see the browser)
```bash
npm run test:headed
```

### Run tests with Playwright UI
```bash
npm run test:ui
```

### Run tests in debug mode
```bash
npm run test:debug
```

### Run specific browser only
```bash
npm run test:chromium
npm run test:firefox
```

### Run specific test file
```bash
npm run test:auth
npm run test:dashboard
npm run test:scenarios
npm run test:runs
npm run test:settings
```

## Test Structure

```
e2e/
├── fixtures/           # Test fixtures and helpers
│   └── auth.fixture.ts # Authentication helpers
├── pages/              # Page Object Models
│   ├── base.page.ts    # Base page class
│   ├── dashboard.page.ts
│   ├── scenarios.page.ts
│   ├── settings.page.ts
│   └── test-runs.page.ts
├── tests/              # Test specifications
│   ├── auth.setup.ts   # Authentication setup
│   ├── auth.spec.ts    # Authentication tests
│   ├── dashboard.spec.ts
│   ├── scenarios.spec.ts
│   ├── settings.spec.ts
│   └── test-runs.spec.ts
├── playwright/         # Playwright state storage
│   └── .auth/          # Authentication state
├── screenshots/        # Test screenshots
├── test-results/       # Test artifacts
├── playwright-report/  # HTML reports
├── playwright.config.ts
├── package.json
└── README.md
```

## Test Categories

### Authentication Tests (`auth.spec.ts`)
- Login page display
- Google SSO button functionality
- Protected routes redirect
- Logout functionality
- Session management

### Dashboard Tests (`dashboard.spec.ts`)
- Dashboard loading and stats display
- Health status cards
- Quick actions (Sync Repos, Run All Tests)
- Recent test runs table
- Auto-refresh functionality

### Scenarios Tests (`scenarios.spec.ts`)
- Scenario list display
- Search and filter functionality
- Tag and repository filters
- View mode toggle (list/grid)
- Scenario details navigation

### Test Runs Tests (`test-runs.spec.ts`)
- Test runs list display
- Status filtering
- Create new test run modal
- Run details page
- Step results display

### Settings Tests (`settings.spec.ts`)
- Profile tab display
- API key management
- Preferences (theme, notifications)
- Tab navigation

## Screenshots

Screenshots are automatically captured:
- On test failure
- At key points marked in tests with `page.screenshot()`

Screenshots are saved to the `screenshots/` directory.

## Configuration

### Base URL
The default base URL is `https://sliples.localhost.in:5173`. To change it:

```bash
# Using environment variable
BASE_URL=https://your-url.com npm test
```

Or modify `playwright.config.ts`:
```typescript
use: {
  baseURL: 'https://your-url.com',
}
```

### Browsers
By default, tests run on Chromium, Firefox, and WebKit. To run on specific browsers:

```bash
npm run test:chromium
npm run test:firefox
```

### Timeouts
- Global timeout: 30 seconds
- Expect timeout: 10 seconds
- Action timeout: 10 seconds
- Navigation timeout: 15 seconds

Adjust in `playwright.config.ts` as needed.

## Reports

### View HTML Report
After running tests:
```bash
npm run report
```

### CI Integration
On CI, configure reporters in `playwright.config.ts`:
```typescript
reporter: [
  ['html', { outputFolder: 'playwright-report' }],
  ['junit', { outputFile: 'results.xml' }],
  ['list'],
],
```

## Page Object Pattern

Tests use the Page Object pattern for maintainability. Each page has:
- A class extending `BasePage`
- Locators for key elements
- Methods for common actions

Example usage:
```typescript
import { DashboardPage } from '../pages/dashboard.page';

test('should display stats', async ({ page }) => {
  const dashboard = new DashboardPage(page);
  await dashboard.goto();
  const stats = await dashboard.getStatValues();
  expect(stats.totalScenarios).toBe('42');
});
```

## Authentication

Tests use mocked authentication to avoid actual OAuth flow:

1. `auth.setup.ts` runs first to set up authentication state
2. Authentication state is stored in `playwright/.auth/user.json`
3. Other tests reuse this state via `storageState` config

To test with real authentication, modify `auth.fixture.ts` to use actual credentials.

## Troubleshooting

### Tests timeout on CI
Increase timeout in `playwright.config.ts`:
```typescript
timeout: 60000,
```

### HTTPS certificate errors
Enable `ignoreHTTPSErrors` in config (already enabled).

### Tests fail due to animations
Add `animation: 'disabled'` to use config or wait for animations.

### Flaky tests
- Use `await page.waitForLoadState('networkidle')`
- Add explicit waits with `waitForSelector` or `waitForTimeout`
- Increase retries: `retries: 2`

## Contributing

1. Follow the Page Object pattern for new pages
2. Add screenshots at key points
3. Use descriptive test names
4. Mock API responses for reliability
5. Test both success and error states
