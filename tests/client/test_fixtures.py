# Copyright contributors to the IBM BAW MCP Server project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test fixtures for client tests.
This module contains mock data for testing that doesn't contain real credentials.
"""

from typing import Any

# Import test environment variables
from tests.test_env import TestEnv


# Mock credentials for testing - using environment variables
class MockCredentials:
    """Mock credentials for testing."""

    # URL components
    ENDPOINT = TestEnv.ENDPOINT

    # Authentication
    USERNAME = TestEnv.USERNAME
    PASSWORD = TestEnv.PASSWORD
    API_KEY = TestEnv.API_KEY

    # Headers
    AUTH_HEADER = TestEnv.AUTH_HEADER
    API_KEY_HEADER = TestEnv.API_KEY_HEADER

    # URL with credentials for testing URL sanitization
    @classmethod
    def get_url_with_credentials(cls) -> str:
        """Return a URL with credentials for testing sanitization."""
        return TestEnv.get_url_with_credentials()

    @classmethod
    def get_headers(cls) -> dict[str, Any]:
        """Return headers for testing."""
        return TestEnv.get_headers()
