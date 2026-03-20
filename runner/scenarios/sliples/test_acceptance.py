"""
Test module for Sliples acceptance tests.

This module connects pytest-bdd scenarios from sliples-acceptance.feature
to the step definitions.
"""

import pytest
from pytest_bdd import scenarios

# Load all scenarios from the feature file
scenarios("sliples-acceptance.feature")
