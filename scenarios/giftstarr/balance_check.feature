@giftstarr @balance @smoke
Feature: Giftstarr Card Balance Check
  As a gift card holder
  I want to check my card balance
  So that I know how much value remains

  @critical
  Scenario: Check gift card balance with valid token
    Given I navigate to "https://test.giftstarr.cards"
    Then I should see "card token"
    When I fill input "input" with "000000002"
    And I click "Go!"
    Then I should see "Balance"
