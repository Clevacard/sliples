@giftstarr @gift-cards
Feature: Giftstarr Gift Cards
  As a customer
  I want to browse and view gift cards
  So that I can find the perfect gift for someone

  Background:
    Given I open the browser
    And the base URL is "https://test.giftstarr.cards"

  # =============================================================================
  # Browse Gift Cards
  # =============================================================================

  @smoke @critical
  Scenario: View gift cards listing page
    When I navigate to "/gift-cards"
    Then I should see a grid of gift cards
    And each gift card should display an image
    And each gift card should display the brand name
    And each gift card should display available values

  @smoke
  Scenario: Gift cards page has filters
    When I navigate to "/gift-cards"
    Then I should see filter options
    And I should see "Category" filter
    And I should see "Price Range" filter
    And I should see "Sort By" dropdown

  @regression
  Scenario: Filter gift cards by category
    When I navigate to "/gift-cards"
    And I select "Gaming" from the category filter
    Then I should only see gift cards in the Gaming category
    And the URL should reflect the filter selection

  @regression
  Scenario: Filter gift cards by price range
    When I navigate to "/gift-cards"
    And I set the price range from "25" to "100"
    Then I should only see gift cards with values between 25 and 100

  @regression
  Scenario Outline: Sort gift cards
    When I navigate to "/gift-cards"
    And I select "<sort_option>" from the Sort By dropdown
    Then the gift cards should be sorted by <sort_option>

    Examples:
      | sort_option      |
      | Popular          |
      | A-Z              |
      | Z-A              |
      | Price: Low-High  |
      | Price: High-Low  |

  @regression
  Scenario: Pagination works on gift cards page
    When I navigate to "/gift-cards"
    And there are more than 20 gift cards available
    Then I should see pagination controls
    When I click on page 2
    Then I should see a different set of gift cards
    And the URL should indicate page 2

  @regression
  Scenario: Infinite scroll loads more gift cards
    When I navigate to "/gift-cards"
    And the site uses infinite scroll
    Then I should see initial set of gift cards
    When I scroll to the bottom of the page
    Then more gift cards should load automatically

  # =============================================================================
  # Search Gift Cards
  # =============================================================================

  @smoke @critical
  Scenario: Search for a specific gift card
    When I navigate to "/"
    And I search for "Netflix" gift cards
    Then I should see search results
    And I should see "Netflix" gift card in the results

  @regression
  Scenario: Search returns relevant results
    When I search for "music streaming" gift cards
    Then I should see results including "Spotify"
    And I should see results including "Apple Music"

  @regression
  Scenario: Search with no results shows helpful message
    When I search for "xyznonexistent123" gift cards
    Then I should see a "No results found" message
    And I should see suggestions to try different search terms

  @regression
  Scenario: Search highlights matching terms
    When I search for "Amazon" gift cards
    Then the search term "Amazon" should be highlighted in the results

  @regression
  Scenario: Search works with partial terms
    When I search for "Net" gift cards
    Then I should see "Netflix" in the results
    And I should see any other cards containing "Net"

  # =============================================================================
  # View Gift Card Details
  # =============================================================================

  @smoke @critical
  Scenario: View gift card detail page
    When I navigate to "/gift-cards"
    And I click on the "Netflix" gift card
    Then I should be on the Netflix gift card detail page
    And I should see the gift card details for "Netflix"
    And I should see available denomination options
    And I should see the "Add to Cart" button

  @smoke
  Scenario: Gift card detail page shows all required information
    When I navigate to a gift card detail page
    Then I should see the brand logo
    And I should see the product description
    And I should see delivery information
    And I should see terms and conditions link

  @regression
  Scenario: Select gift card denomination
    When I navigate to the "Spotify" gift card page
    Then I should see denomination options like "10", "25", "50"
    When I select the "25" denomination
    Then the "25" option should be highlighted
    And the price should update to show "25"

  @regression
  Scenario: Custom amount option
    When I navigate to a gift card that supports custom amounts
    Then I should see a "Custom Amount" option
    When I select "Custom Amount"
    And I enter "75" as the custom value
    Then the price should update to show "75"

  @regression
  Scenario: Gift card detail page shows validity period
    When I navigate to a gift card detail page
    Then I should see validity information
    And it should indicate how long the card is valid

  @regression
  Scenario: View gift card terms and conditions
    When I navigate to a gift card detail page
    And I click on "Terms and Conditions"
    Then I should see the terms for using this gift card
    And I should see redemption instructions

  # =============================================================================
  # Add to Cart
  # =============================================================================

  @smoke @critical
  Scenario: Add gift card to cart
    When I navigate to the "Netflix" gift card page
    And I select the "50" denomination
    And I click "Add to Cart"
    Then I should see a success message
    And the cart icon should show "1" item
    And I should see an option to continue shopping or checkout

  @regression
  Scenario: Add multiple quantities to cart
    When I navigate to a gift card detail page
    And I select the "25" denomination
    And I set quantity to "3"
    And I click "Add to Cart"
    Then the cart should contain 3 items
    And the cart total should reflect the quantity

  @regression
  Scenario: Add gift card with personalization
    When I navigate to a gift card that supports personalization
    And I select a denomination
    And I enter recipient name "John"
    And I enter a personal message "Happy Birthday!"
    And I click "Add to Cart"
    Then the cart should include the personalization details

  @regression
  Scenario: Cannot add to cart without selecting denomination
    When I navigate to a gift card detail page
    And I do not select any denomination
    And I click "Add to Cart"
    Then I should see an error message
    And the error should indicate a denomination must be selected

  @e2e
  Scenario: Add multiple different gift cards to cart
    When I add the "Netflix" gift card with value "25" to cart
    And I add the "Spotify" gift card with value "30" to cart
    Then the cart should show 2 different items
    And the cart total should be "55"

  # =============================================================================
  # Gift Card Categories
  # =============================================================================

  @smoke
  Scenario: Browse Gaming gift cards
    When I navigate to the "Gaming" gift card category
    Then I should see gift cards like "PlayStation", "Xbox", "Steam"
    And all displayed cards should be gaming-related

  @regression
  Scenario: Browse Retail gift cards
    When I navigate to the "Retail" gift card category
    Then I should see gift cards from retail stores
    And I should see cards like "Amazon", "eBay"

  @regression
  Scenario: Browse Entertainment gift cards
    When I navigate to the "Entertainment" gift card category
    Then I should see streaming service gift cards
    And I should see cards like "Netflix", "Spotify", "Disney+"

  @regression
  Scenario: Browse Food & Dining gift cards
    When I navigate to the "Food & Dining" gift card category
    Then I should see restaurant and food delivery gift cards

  # =============================================================================
  # Gift Card Availability
  # =============================================================================

  @regression
  Scenario: Out of stock gift card shows appropriate message
    When I navigate to a gift card that is out of stock
    Then I should see an "Out of Stock" indicator
    And the "Add to Cart" button should be disabled
    And I should see an option to be notified when available

  @regression
  Scenario: Limited availability gift card shows warning
    When I navigate to a gift card with limited availability
    Then I should see a "Limited Availability" warning
    And I should still be able to add it to cart
