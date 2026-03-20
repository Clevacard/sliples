"""Seed data script to populate database with Giftstarr example data.

This script is idempotent - it can be run multiple times without creating duplicates.
It creates:
- Environment: "Giftstarr Test" with base_url="https://test.giftstarr.cards"
- Repository: "giftstarr-scenarios"
- Custom steps for common Giftstarr actions
- Example schedules (daily smoke test, weekly regression)
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    Environment,
    BrowserConfig,
    ScenarioRepo,
    Scenario,
    CustomStep,
    Schedule,
)


# Constants for seed data
GIFTSTARR_ENV_NAME = "Giftstarr Test"
GIFTSTARR_BASE_URL = "https://test.giftstarr.cards"
GIFTSTARR_REPO_NAME = "giftstarr-scenarios"


def get_or_create_environment(db: Session) -> Environment:
    """Get or create the Giftstarr Test environment."""
    env = db.query(Environment).filter(Environment.name == GIFTSTARR_ENV_NAME).first()

    if env:
        return env

    env = Environment(
        name=GIFTSTARR_ENV_NAME,
        base_url=GIFTSTARR_BASE_URL,
        credentials_env="GIFTSTARR_TEST_CREDS",
        variables={
            "timeout": "30",
            "default_language": "en",
            "currency": "EUR",
        },
        retention_days=365,
    )
    db.add(env)
    db.flush()

    # Add browser configurations
    browsers = [
        {"browser": "chromium", "version": "latest", "channel": "stable"},
        {"browser": "firefox", "version": "latest", "channel": "stable"},
        {"browser": "webkit", "version": "latest", "channel": "stable"},
    ]

    for browser_config in browsers:
        bc = BrowserConfig(
            environment_id=env.id,
            browser=browser_config["browser"],
            version=browser_config["version"],
            channel=browser_config["channel"],
        )
        db.add(bc)

    return env


def get_or_create_repo(db: Session) -> ScenarioRepo:
    """Get or create the Giftstarr scenarios repository."""
    repo = db.query(ScenarioRepo).filter(ScenarioRepo.name == GIFTSTARR_REPO_NAME).first()

    if repo:
        return repo

    repo = ScenarioRepo(
        name=GIFTSTARR_REPO_NAME,
        git_url="https://github.com/giftstarr/test-scenarios.git",
        branch="main",
        sync_path="scenarios/giftstarr",
        last_synced=datetime.utcnow(),
    )
    db.add(repo)
    db.flush()

    return repo


def create_custom_steps(db: Session, repo: ScenarioRepo) -> list[CustomStep]:
    """Create custom step definitions for Giftstarr testing."""
    custom_steps_data = [
        {
            "name": "Navigate to gift card category",
            "pattern": 'I navigate to the "{category}" gift card category',
            "code": '''@when('I navigate to the "{category}" gift card category')
def step_navigate_to_category(context, category):
    """Navigate to a specific gift card category."""
    page = context.page
    # Click on the category in navigation or use direct URL
    category_slug = category.lower().replace(" ", "-")
    page.goto(f"{context.base_url}/categories/{category_slug}")
    page.wait_for_load_state("networkidle")
''',
        },
        {
            "name": "Search for gift card",
            "pattern": 'I search for "{query}" gift cards',
            "code": '''@when('I search for "{query}" gift cards')
def step_search_gift_cards(context, query):
    """Search for gift cards using the search functionality."""
    page = context.page
    search_input = page.locator('input[type="search"], input[placeholder*="Search"], .search-input')
    search_input.fill(query)
    search_input.press("Enter")
    page.wait_for_load_state("networkidle")
''',
        },
        {
            "name": "Add gift card to cart",
            "pattern": 'I add the gift card with value "{value}" to cart',
            "code": '''@when('I add the gift card with value "{value}" to cart')
def step_add_to_cart(context, value):
    """Add a gift card with specified value to the shopping cart."""
    page = context.page
    # Select the value option
    value_selector = page.locator(f'[data-value="{value}"], button:has-text("{value}")')
    value_selector.click()
    # Click add to cart button
    add_button = page.locator('button:has-text("Add to Cart"), .add-to-cart-btn')
    add_button.click()
    page.wait_for_timeout(1000)  # Wait for cart update
''',
        },
        {
            "name": "Verify cart total",
            "pattern": 'the cart total should be "{expected_total}"',
            "code": '''@then('the cart total should be "{expected_total}"')
def step_verify_cart_total(context, expected_total):
    """Verify the shopping cart displays the expected total."""
    page = context.page
    cart_total = page.locator('.cart-total, [data-testid="cart-total"]')
    actual_total = cart_total.inner_text()
    assert expected_total in actual_total, f"Expected cart total '{expected_total}', got '{actual_total}'"
''',
        },
        {
            "name": "Fill checkout form",
            "pattern": "I fill in the checkout form with valid details",
            "code": '''@when('I fill in the checkout form with valid details')
def step_fill_checkout_form(context):
    """Fill the checkout form with test data."""
    page = context.page
    # Recipient details
    page.fill('input[name="recipient_name"], #recipient-name', 'Test Recipient')
    page.fill('input[name="recipient_email"], #recipient-email', 'test@example.com')
    # Sender details
    page.fill('input[name="sender_name"], #sender-name', 'Test Sender')
    page.fill('input[name="sender_email"], #sender-email', 'sender@example.com')
    # Optional message
    message_field = page.locator('textarea[name="message"], #gift-message')
    if message_field.is_visible():
        message_field.fill('Happy Birthday! Enjoy your gift card.')
''',
        },
        {
            "name": "Verify gift card details page",
            "pattern": 'I should see the gift card details for "{card_name}"',
            "code": '''@then('I should see the gift card details for "{card_name}"')
def step_verify_gift_card_details(context, card_name):
    """Verify the gift card details page shows correct information."""
    page = context.page
    # Check page title or main heading
    heading = page.locator('h1, .product-title')
    assert card_name.lower() in heading.inner_text().lower(), f"Gift card name '{card_name}' not found in heading"
    # Verify key elements are present
    assert page.locator('.product-image, img[alt*="gift"]').is_visible(), "Product image not visible"
    assert page.locator('.price, [data-testid="price"]').is_visible(), "Price not visible"
''',
        },
        {
            "name": "Open mobile menu",
            "pattern": "I open the mobile navigation menu",
            "code": '''@when('I open the mobile navigation menu')
def step_open_mobile_menu(context):
    """Open the mobile hamburger menu."""
    page = context.page
    # Set mobile viewport if not already
    page.set_viewport_size({"width": 375, "height": 667})
    # Click hamburger menu
    menu_button = page.locator('.hamburger-menu, [aria-label="Menu"], .mobile-menu-toggle')
    menu_button.click()
    page.wait_for_timeout(500)  # Wait for menu animation
''',
        },
        {
            "name": "Verify page load time",
            "pattern": "the page should load within {seconds:d} seconds",
            "code": '''@then('the page should load within {seconds:d} seconds')
def step_verify_page_load_time(context, seconds):
    """Verify the page loads within the specified time."""
    page = context.page
    # Get performance timing
    timing = page.evaluate("""() => {
        const timing = performance.timing;
        return timing.loadEventEnd - timing.navigationStart;
    }""")
    load_time_seconds = timing / 1000
    assert load_time_seconds <= seconds, f"Page took {load_time_seconds:.2f}s to load, expected <= {seconds}s"
''',
        },
    ]

    created_steps = []
    for step_data in custom_steps_data:
        existing = db.query(CustomStep).filter(
            CustomStep.name == step_data["name"],
            CustomStep.repo_id == repo.id,
        ).first()

        if existing:
            created_steps.append(existing)
            continue

        step = CustomStep(
            repo_id=repo.id,
            name=step_data["name"],
            pattern=step_data["pattern"],
            code=step_data["code"],
            committed=False,
        )
        db.add(step)
        created_steps.append(step)

    return created_steps


def create_schedules(db: Session, env: Environment) -> list[Schedule]:
    """Create example schedules for Giftstarr testing."""
    schedules_data = [
        {
            "name": "Giftstarr Daily Smoke Test",
            "cron_expression": "0 6 * * *",  # Every day at 6 AM
            "scenario_tags": ["smoke"],
            "browsers": ["chromium"],
            "enabled": True,
        },
        {
            "name": "Giftstarr Weekly Regression",
            "cron_expression": "0 2 * * 0",  # Every Sunday at 2 AM
            "scenario_tags": ["regression", "e2e"],
            "browsers": ["chromium", "firefox"],
            "enabled": True,
        },
        {
            "name": "Giftstarr Checkout Flow Test",
            "cron_expression": "0 */4 * * *",  # Every 4 hours
            "scenario_tags": ["checkout", "critical"],
            "browsers": ["chromium"],
            "enabled": True,
        },
    ]

    created_schedules = []
    for schedule_data in schedules_data:
        existing = db.query(Schedule).filter(
            Schedule.name == schedule_data["name"]
        ).first()

        if existing:
            created_schedules.append(existing)
            continue

        # Calculate next run time based on cron expression
        next_run = datetime.utcnow() + timedelta(hours=1)  # Simplified: next hour

        schedule = Schedule(
            name=schedule_data["name"],
            cron_expression=schedule_data["cron_expression"],
            scenario_tags=schedule_data["scenario_tags"],
            scenario_ids=[],
            environment_id=env.id,
            browsers=schedule_data["browsers"],
            enabled=schedule_data["enabled"],
            created_by="seed_data",
            next_run_at=next_run,
        )
        db.add(schedule)
        created_schedules.append(schedule)

    return created_schedules


def create_sample_scenarios(db: Session, repo: ScenarioRepo) -> list[Scenario]:
    """Create sample scenario entries in the database."""
    scenarios_data = [
        {
            "name": "Giftstarr Homepage",
            "feature_path": "scenarios/giftstarr/homepage.feature",
            "tags": ["smoke", "homepage", "giftstarr"],
        },
        {
            "name": "Giftstarr Navigation",
            "feature_path": "scenarios/giftstarr/navigation.feature",
            "tags": ["smoke", "navigation", "giftstarr"],
        },
        {
            "name": "Giftstarr Gift Cards",
            "feature_path": "scenarios/giftstarr/gift_cards.feature",
            "tags": ["regression", "gift-cards", "giftstarr"],
        },
        {
            "name": "Giftstarr Checkout",
            "feature_path": "scenarios/giftstarr/checkout.feature",
            "tags": ["e2e", "checkout", "critical", "giftstarr"],
        },
    ]

    created_scenarios = []
    for scenario_data in scenarios_data:
        existing = db.query(Scenario).filter(
            Scenario.feature_path == scenario_data["feature_path"]
        ).first()

        if existing:
            created_scenarios.append(existing)
            continue

        scenario = Scenario(
            repo_id=repo.id,
            name=scenario_data["name"],
            feature_path=scenario_data["feature_path"],
            tags=scenario_data["tags"],
        )
        db.add(scenario)
        created_scenarios.append(scenario)

    return created_scenarios


def seed_database(db: Optional[Session] = None) -> dict:
    """
    Main seed function to populate the database with Giftstarr example data.

    Returns a summary of created/existing entities.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        # Create environment
        env = get_or_create_environment(db)
        env_created = env.id is not None

        # Create repository
        repo = get_or_create_repo(db)
        repo_created = repo.id is not None

        # Create custom steps
        custom_steps = create_custom_steps(db, repo)

        # Create schedules
        schedules = create_schedules(db, env)

        # Create sample scenarios
        scenarios = create_sample_scenarios(db, repo)

        db.commit()

        return {
            "environment": {
                "id": str(env.id),
                "name": env.name,
                "base_url": env.base_url,
            },
            "repository": {
                "id": str(repo.id),
                "name": repo.name,
            },
            "custom_steps_count": len(custom_steps),
            "schedules_count": len(schedules),
            "scenarios_count": len(scenarios),
            "message": "Seed data created successfully",
        }

    except Exception as e:
        db.rollback()
        raise e

    finally:
        if close_db:
            db.close()


def clear_seed_data(db: Optional[Session] = None) -> dict:
    """
    Clear all seed data from the database.

    This removes:
    - The Giftstarr Test environment (and its browser configs)
    - The giftstarr-scenarios repository (and its scenarios/custom steps)
    - Related schedules
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        deleted_counts = {
            "environments": 0,
            "repositories": 0,
            "custom_steps": 0,
            "schedules": 0,
            "scenarios": 0,
        }

        # Find and delete environment
        env = db.query(Environment).filter(Environment.name == GIFTSTARR_ENV_NAME).first()
        if env:
            # Delete related schedules first
            deleted_counts["schedules"] = db.query(Schedule).filter(
                Schedule.environment_id == env.id
            ).delete()

            db.delete(env)  # Cascades to browser_configs
            deleted_counts["environments"] = 1

        # Find and delete repository
        repo = db.query(ScenarioRepo).filter(ScenarioRepo.name == GIFTSTARR_REPO_NAME).first()
        if repo:
            # Delete related custom steps
            deleted_counts["custom_steps"] = db.query(CustomStep).filter(
                CustomStep.repo_id == repo.id
            ).delete()

            # Delete related scenarios
            deleted_counts["scenarios"] = db.query(Scenario).filter(
                Scenario.repo_id == repo.id
            ).delete()

            db.delete(repo)
            deleted_counts["repositories"] = 1

        db.commit()

        return {
            "deleted": deleted_counts,
            "message": "Seed data cleared successfully",
        }

    except Exception as e:
        db.rollback()
        raise e

    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    """Run seed script directly."""
    print("Seeding database with Giftstarr example data...")
    result = seed_database()
    print(f"Result: {result}")
