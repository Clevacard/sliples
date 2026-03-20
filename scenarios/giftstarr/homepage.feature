@giftstarr @homepage
Feature: Giftstarr Homepage
  As a visitor
  I want to see the homepage
  So that I can learn about Giftstarr and browse gift cards

  Background:
    Given I open the browser
    And the base URL is "https://test.giftstarr.cards"

  @smoke @critical
  Scenario: View homepage
    When I navigate to "/"
    Then I should see the Giftstarr logo
    And I should see "Gift Cards" in the navigation
    And I should see featured gift cards section

  @smoke @performance
  Scenario: Homepage loads within acceptable time
    When I navigate to "/"
    Then the page should load within 3 seconds
    And there should be no JavaScript console errors

  @smoke
  Scenario: Homepage displays key sections
    When I navigate to "/"
    Then I should see the hero banner
    And I should see the "Popular Gift Cards" section
    And I should see the "Categories" section
    And I should see the footer

  @regression
  Scenario: Homepage hero banner is interactive
    When I navigate to "/"
    And I see the hero banner
    Then the hero banner should have a call-to-action button
    When I click the call-to-action button
    Then I should be navigated to the gift cards page

  @regression @seo
  Scenario: Homepage has proper SEO elements
    When I navigate to "/"
    Then the page title should contain "Giftstarr"
    And the page should have a meta description
    And the page should have Open Graph tags
    And there should be only one H1 element

  @regression @accessibility
  Scenario: Homepage is accessible
    When I navigate to "/"
    Then all images should have alt text
    And all interactive elements should be focusable
    And the color contrast should meet WCAG AA standards

  @regression
  Scenario: Homepage displays promotional banner
    When I navigate to "/"
    Then I should see the promotional banner if active
    And the promotional banner should be dismissible

  @regression @i18n
  Scenario: Homepage language selector works
    When I navigate to "/"
    And I click on the language selector
    Then I should see available languages
    When I select "Nederlands"
    Then the page should display in Dutch

  @smoke
  Scenario: Homepage search bar is visible and functional
    When I navigate to "/"
    Then I should see the search bar
    When I enter "Amazon" in the search bar
    Then I should see search suggestions
    When I press Enter
    Then I should see search results for "Amazon"

  @regression
  Scenario: Homepage displays trust indicators
    When I navigate to "/"
    Then I should see payment method icons
    And I should see security badges
    And I should see customer review ratings
