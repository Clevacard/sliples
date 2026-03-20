"""
Test module for Scenario Management tests.

This module connects pytest-bdd scenarios from test_scenarios.feature
to the API step definitions.
"""

import pytest
from pytest_bdd import scenarios

# Load all scenarios from the feature file
scenarios("test_scenarios.feature")
