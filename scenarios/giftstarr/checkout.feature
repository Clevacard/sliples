@giftstarr @checkout @e2e
Feature: Giftstarr Checkout Flow
  As a customer
  I want to complete my gift card purchase
  So that I can send gift cards to recipients

  Background:
    Given I open the browser
    And the base URL is "https://test.giftstarr.cards"

  # =============================================================================
  # View Cart
  # =============================================================================

  @smoke @critical
  Scenario: View cart with items
    Given I have added the "Netflix" gift card with value "50" to my cart
    When I navigate to "/cart"
    Then I should see the cart page
    And I should see "Netflix" gift card in the cart
    And I should see the value "50"
    And I should see the cart total

  @smoke
  Scenario: View empty cart
    Given I have no items in my cart
    When I navigate to "/cart"
    Then I should see an empty cart message
    And I should see a link to browse gift cards
    And the "Proceed to Checkout" button should be disabled

  @regression
  Scenario: Update quantity in cart
    Given I have a gift card in my cart with quantity 1
    When I navigate to "/cart"
    And I change the quantity to 2
    Then the cart total should update automatically
    And the subtotal should reflect 2 items

  @regression
  Scenario: Remove item from cart
    Given I have multiple gift cards in my cart
    When I navigate to "/cart"
    And I click remove on the first item
    Then the item should be removed from the cart
    And the cart total should update
    And I should see a confirmation message

  @regression
  Scenario: Cart persists across sessions
    Given I have added a gift card to my cart
    When I close the browser
    And I reopen the browser and navigate to "/cart"
    Then I should still see the gift card in my cart

  @regression
  Scenario: Apply discount code in cart
    Given I have a gift card in my cart
    When I navigate to "/cart"
    And I enter discount code "TESTCODE10"
    And I click "Apply"
    Then I should see the discount applied
    And the cart total should be reduced by 10%

  @regression
  Scenario: Invalid discount code shows error
    Given I have a gift card in my cart
    When I navigate to "/cart"
    And I enter discount code "INVALID123"
    And I click "Apply"
    Then I should see an error message
    And the error should say "Invalid discount code"

  # =============================================================================
  # Proceed to Checkout
  # =============================================================================

  @smoke @critical
  Scenario: Proceed to checkout from cart
    Given I have a gift card in my cart
    When I navigate to "/cart"
    And I click "Proceed to Checkout"
    Then I should be on the checkout page
    And I should see the order summary
    And I should see the checkout form

  @smoke
  Scenario: Checkout page displays order summary
    Given I have items in my cart
    When I proceed to checkout
    Then I should see each item in the order summary
    And I should see the subtotal
    And I should see any applicable fees
    And I should see the total amount

  # =============================================================================
  # Checkout Form - Recipient Details
  # =============================================================================

  @smoke @critical
  Scenario: Fill recipient details
    Given I have proceeded to checkout
    When I fill in recipient email "recipient@example.com"
    And I fill in recipient name "John Doe"
    Then the recipient details should be saved
    And I should be able to proceed to payment

  @regression
  Scenario: Recipient email validation
    Given I have proceeded to checkout
    When I fill in recipient email "invalid-email"
    And I try to proceed
    Then I should see an email validation error
    And the error should say "Please enter a valid email address"

  @regression
  Scenario: Recipient name is required
    Given I have proceeded to checkout
    When I leave the recipient name empty
    And I fill in recipient email "test@example.com"
    And I try to proceed
    Then I should see a validation error for recipient name

  @regression
  Scenario: Send to myself option
    Given I have proceeded to checkout
    When I check "Send to myself"
    Then the recipient fields should be auto-filled with my account details

  @regression
  Scenario: Schedule delivery for later
    Given I have proceeded to checkout
    When I select "Schedule for later"
    And I select a future delivery date
    Then the delivery date should be confirmed
    And the order summary should show the scheduled date

  @regression
  Scenario: Add personal message
    Given I have proceeded to checkout
    When I fill in the recipient details
    And I enter a personal message "Happy Birthday!"
    Then the message should be saved
    And the message should appear in the order preview

  # =============================================================================
  # Checkout Form - Sender Details
  # =============================================================================

  @smoke
  Scenario: Fill sender details
    Given I have proceeded to checkout
    When I fill in sender name "Jane Sender"
    And I fill in sender email "sender@example.com"
    Then the sender details should be saved

  @regression
  Scenario: Sender email receives confirmation
    Given I complete a purchase with sender email "sender@example.com"
    Then the confirmation email should be sent to "sender@example.com"

  # =============================================================================
  # Payment
  # =============================================================================

  @smoke @critical
  Scenario: View payment options
    Given I have filled in the checkout form with valid details
    When I proceed to payment
    Then I should see available payment methods
    And I should see "Credit Card" option
    And I should see "iDEAL" option
    And I should see "PayPal" option

  @regression
  Scenario: Select credit card payment
    Given I have filled in the checkout details
    When I proceed to payment
    And I select "Credit Card"
    Then I should see the credit card form
    And I should see fields for card number, expiry, and CVV

  @regression @critical
  Scenario: Credit card form validation
    Given I am on the credit card payment form
    When I enter an invalid card number "1234"
    And I try to complete payment
    Then I should see a card validation error
    And the error should indicate invalid card number

  @regression
  Scenario: Credit card expiry validation
    Given I am on the credit card payment form
    When I enter card number "4111111111111111"
    And I enter expiry date "01/20"
    And I try to complete payment
    Then I should see an expiry validation error
    And the error should indicate the card has expired

  @regression
  Scenario: Select iDEAL payment
    Given I have filled in the checkout details
    When I proceed to payment
    And I select "iDEAL"
    Then I should see a list of Dutch banks
    When I select "Test Bank"
    And I complete payment
    Then I should be redirected to the bank's payment page

  @regression
  Scenario: Select PayPal payment
    Given I have filled in the checkout details
    When I proceed to payment
    And I select "PayPal"
    And I click "Pay with PayPal"
    Then I should be redirected to PayPal

  # =============================================================================
  # Complete Purchase
  # =============================================================================

  @e2e @critical
  Scenario: Complete purchase with credit card
    Given I have a "Netflix" gift card worth "50" in my cart
    When I proceed to checkout
    And I fill in recipient email "recipient@example.com"
    And I fill in recipient name "Test Recipient"
    And I fill in sender name "Test Sender"
    And I fill in sender email "sender@example.com"
    And I proceed to payment
    And I select "Credit Card"
    And I enter valid test card details
    And I click "Complete Purchase"
    Then I should see the order confirmation page
    And I should see "Thank you for your order"
    And I should see the order number
    And I should receive a confirmation email

  @e2e
  Scenario: Complete purchase as guest
    Given I am not logged in
    And I have a gift card in my cart
    When I proceed to checkout
    And I fill in the checkout form with valid details
    And I complete payment
    Then the purchase should be successful
    And I should be offered to create an account

  @regression
  Scenario: Purchase confirmation shows all details
    Given I have completed a purchase
    When I view the order confirmation page
    Then I should see the gift card details
    And I should see the recipient information
    And I should see the payment amount
    And I should see the expected delivery date

  # =============================================================================
  # Error Handling
  # =============================================================================

  @regression
  Scenario: Payment failure shows appropriate error
    Given I have filled in checkout details
    When I proceed with a payment that fails
    Then I should see a payment error message
    And I should be able to try a different payment method
    And my cart should still contain the items

  @regression
  Scenario: Network error during checkout
    Given I have filled in checkout details
    When there is a network error during payment
    Then I should see a connection error message
    And I should be advised to try again
    And my order should not be duplicated

  @regression
  Scenario: Session timeout during checkout
    Given I have started the checkout process
    When my session times out
    Then I should be redirected to login
    And my cart items should be preserved
    And I should be able to resume checkout after login

  # =============================================================================
  # Security
  # =============================================================================

  @regression @security
  Scenario: Checkout page is secure
    When I navigate to the checkout page
    Then the page should be served over HTTPS
    And I should see the security lock icon

  @regression @security
  Scenario: Credit card details are not stored in plain text
    Given I have entered credit card details
    When I view the page source
    Then the card number should not be visible in plain text
    And the CVV should not be stored

  @regression @security
  Scenario: PCI compliance indicators
    When I am on the payment page
    Then I should see PCI compliance badges
    And payment processing should be handled by a certified provider
