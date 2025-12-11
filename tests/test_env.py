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
Environment variables for tests.
This module provides environment variables for testing without hardcoding credentials.
"""

import os
from typing import Any


# Get environment variable or default value
def get_env(name: str, default: str) -> str:
    """Get environment variable or default value."""
    return os.environ.get(f"TEST_{name}", default)


# Test environment variables with default values
# These are intentionally not real credentials
class TestEnv:
    """Test environment variables."""

    # URL components
    ENDPOINT = get_env("ENDPOINT", "https://example.com")

    # Authentication
    USERNAME = get_env("USERNAME", "test_user")
    PASSWORD = get_env("PASSWORD", "dummy_password")
    API_KEY = get_env("API_KEY", "dummy_key")

    # Headers
    AUTH_HEADER = get_env("AUTH_HEADER", "Bearer dummy_token")
    API_KEY_HEADER = get_env("API_KEY_HEADER", "dummy_key_header")

    @classmethod
    def get_url_with_credentials(cls) -> str:
        """Return a URL with credentials for testing sanitization."""
        return f"https://{cls.USERNAME}:****@example.com/api"

    @classmethod
    def get_headers(cls) -> dict[str, Any]:
        """Return headers for testing."""
        return {
            "Content-Type": "application/json",
            "Authorization": cls.AUTH_HEADER,
            "X-Api-Key": cls.API_KEY_HEADER,
        }
