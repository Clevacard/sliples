"""
Test module for Test Execution and Screenshots tests.

This module connects pytest-bdd scenarios from test_execution.feature
to the API step definitions.
"""

import pytest
from pytest_bdd import scenarios

# Load all scenarios from the feature file
scenarios("test_execution.feature")
