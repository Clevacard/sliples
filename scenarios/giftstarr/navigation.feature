@giftstarr @navigation
Feature: Giftstarr Navigation
  As a visitor
  I want to navigate through the website
  So that I can find the gift cards and information I need

  Background:
    Given I open the browser
    And the base URL is "https://test.giftstarr.cards"
    And I navigate to "/"

  # =============================================================================
  # Main Navigation
  # =============================================================================

  @smoke @critical
  Scenario: Main navigation links are visible
    Then I should see the main navigation bar
    And I should see "Gift Cards" link in the navigation
    And I should see "Categories" link in the navigation
    And I should see "How It Works" link in the navigation
    And I should see "Contact" link in the navigation

  @smoke
  Scenario: Navigate to Gift Cards page
    When I click on "Gift Cards" in the navigation
    Then I should be on the "/gift-cards" page
    And I should see a list of available gift cards

  @smoke
  Scenario: Navigate to Categories page
    When I click on "Categories" in the navigation
    Then I should see the categories dropdown menu
    And I should see category options like "Retail", "Gaming", "Entertainment"

  @regression
  Scenario: Navigate to How It Works page
    When I click on "How It Works" in the navigation
    Then I should be on the "/how-it-works" page
    And I should see step-by-step instructions

  @regression
  Scenario: Navigate to Contact page
    When I click on "Contact" in the navigation
    Then I should be on the "/contact" page
    And I should see the contact form

  @regression
  Scenario Outline: Category navigation works correctly
    When I hover over "Categories" in the navigation
    And I click on "<category>" in the dropdown
    Then I should be on the "/categories/<slug>" page
    And I should see gift cards in the "<category>" category

    Examples:
      | category       | slug           |
      | Retail         | retail         |
      | Gaming         | gaming         |
      | Entertainment  | entertainment  |
      | Food & Dining  | food-dining    |
      | Travel         | travel         |

  # =============================================================================
  # Footer Navigation
  # =============================================================================

  @smoke
  Scenario: Footer links are visible
    When I scroll to the footer
    Then I should see "About Us" link in the footer
    And I should see "Privacy Policy" link in the footer
    And I should see "Terms of Service" link in the footer
    And I should see "FAQ" link in the footer

  @regression
  Scenario: Navigate to About Us page from footer
    When I scroll to the footer
    And I click on "About Us" in the footer
    Then I should be on the "/about" page
    And I should see company information

  @regression
  Scenario: Navigate to Privacy Policy page from footer
    When I scroll to the footer
    And I click on "Privacy Policy" in the footer
    Then I should be on the "/privacy-policy" page
    And I should see the privacy policy content

  @regression
  Scenario: Navigate to Terms of Service page from footer
    When I scroll to the footer
    And I click on "Terms of Service" in the footer
    Then I should be on the "/terms-of-service" page
    And I should see the terms and conditions

  @regression
  Scenario: Navigate to FAQ page from footer
    When I scroll to the footer
    And I click on "FAQ" in the footer
    Then I should be on the "/faq" page
    And I should see frequently asked questions

  @regression
  Scenario: Footer social media links work
    When I scroll to the footer
    Then I should see social media icons
    When I click on the Facebook icon
    Then a new tab should open with the Giftstarr Facebook page
    When I click on the Instagram icon
    Then a new tab should open with the Giftstarr Instagram page

  # =============================================================================
  # Mobile Navigation
  # =============================================================================

  @smoke @mobile
  Scenario: Mobile hamburger menu is visible on small screens
    Given I am using a mobile device viewport
    When I navigate to "/"
    Then I should see the hamburger menu icon
    And I should not see the desktop navigation links

  @smoke @mobile
  Scenario: Mobile menu opens and closes correctly
    Given I am using a mobile device viewport
    When I navigate to "/"
    And I click on the hamburger menu icon
    Then the mobile menu should slide open
    And I should see all navigation links
    When I click on the close button
    Then the mobile menu should close

  @regression @mobile
  Scenario: Mobile navigation links work correctly
    Given I am using a mobile device viewport
    When I navigate to "/"
    And I open the mobile navigation menu
    And I click on "Gift Cards" in the mobile menu
    Then I should be on the "/gift-cards" page
    And the mobile menu should close

  @regression @mobile
  Scenario: Mobile menu categories expand
    Given I am using a mobile device viewport
    When I navigate to "/"
    And I open the mobile navigation menu
    And I tap on "Categories" in the mobile menu
    Then I should see the categories submenu expand
    And I should see category options

  # =============================================================================
  # Breadcrumb Navigation
  # =============================================================================

  @regression
  Scenario: Breadcrumb navigation on category page
    When I navigate to "/categories/gaming"
    Then I should see breadcrumb navigation
    And the breadcrumb should show "Home > Categories > Gaming"
    When I click on "Home" in the breadcrumb
    Then I should be on the homepage

  @regression
  Scenario: Breadcrumb navigation on product page
    When I navigate to a gift card detail page
    Then I should see breadcrumb navigation
    And the breadcrumb should include the category
    When I click on the category in the breadcrumb
    Then I should be on the category page

  # =============================================================================
  # Search Navigation
  # =============================================================================

  @smoke
  Scenario: Search navigates to results page
    When I enter "Netflix" in the search bar
    And I press Enter
    Then I should be on the search results page
    And the URL should contain "search"
    And the search query should be visible

  @regression
  Scenario: Search suggestions are clickable
    When I enter "Spot" in the search bar
    Then I should see search suggestions
    When I click on "Spotify" in the suggestions
    Then I should be on the Spotify gift card page

  # =============================================================================
  # User Account Navigation
  # =============================================================================

  @regression
  Scenario: Navigate to login page
    When I click on the account icon
    Then I should see a login/register dropdown
    When I click on "Login"
    Then I should be on the "/login" page

  @regression
  Scenario: Navigate to cart
    When I click on the cart icon
    Then I should be on the "/cart" page
    And I should see the cart contents or empty cart message

  @regression
  Scenario: Cart icon shows item count
    Given I have added an item to the cart
    When I look at the cart icon
    Then I should see a badge with "1" item count
