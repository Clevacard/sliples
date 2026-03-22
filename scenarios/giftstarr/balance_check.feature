@giftstarr @balance @smoke
Feature: Giftstarr Card Balance Check
  As a gift card holder
  I want to check my card balance
  So that I know how much value remains

  @critical
  Scenario: Check gift card balance with valid token
    Given I navigate to "https://test.giftstarr.cards"
    Then I should see "card token"
    When I fill in the token 000000003
    And I click "Go!"
    Then I should see "Your card balance:"
    Then I should see "GBP 10"
    Then I should see "valid until: 2025-12-17"
