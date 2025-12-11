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

import os
import sys
import unittest

# Import test fixtures
from tests.client.test_fixtures import MockCredentials

# Add src directory to path for imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

# Use type ignore to suppress IDE errors
from ibm_baw_mcp_server.client.http_client import (  # type: ignore
    BaseHTTPClient,
    HTTPConnectionConfig,
)


class TestLogSanitization(unittest.TestCase):
    """Test that sensitive information is not logged."""

    def test_sanitize_url_for_logging(self) -> None:
        """Test that URLs with credentials are properly sanitized."""
        # Test URL with credentials using our test fixture
        url_with_creds = MockCredentials.get_url_with_credentials()
        sanitized = BaseHTTPClient._sanitize_url_for_logging(url_with_creds)
        self.assertEqual(sanitized, "https://[REDACTED]@example.com/api")

        # Test URL without credentials
        url_without_creds = MockCredentials.ENDPOINT
        sanitized = BaseHTTPClient._sanitize_url_for_logging(url_without_creds)
        self.assertEqual(sanitized, url_without_creds)

    def test_sanitize_headers_for_logging(self) -> None:
        """Test that headers with sensitive information are properly sanitized."""
        # Using our test fixtures
        headers = {
            "Content-Type": "application/json",
            "Authorization": MockCredentials.AUTH_HEADER,
            "X-Api-Key": MockCredentials.API_KEY_HEADER,
            "User-Agent": "Test Client",
        }

        sanitized = BaseHTTPClient._sanitize_headers_for_logging(headers)

        # Check that sensitive headers are redacted
        self.assertEqual(sanitized["Authorization"], "[REDACTED]")
        self.assertEqual(sanitized["X-Api-Key"], "[REDACTED]")

        # Check that non-sensitive headers are preserved
        self.assertEqual(sanitized["Content-Type"], "application/json")
        self.assertEqual(sanitized["User-Agent"], "Test Client")

    def test_http_client_debug_logging(self) -> None:
        """Test that HTTP client debug logging doesn't expose sensitive information."""
        # Create a client with debug logging using our test fixtures
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            verify_ssl=True,
        )
        client = BaseHTTPClient(config)

        # Create headers with sensitive information
        headers = {"Authorization": MockCredentials.AUTH_HEADER}

        # Test the sanitization directly
        sanitized_headers = client._sanitize_headers_for_logging(headers)

        # Check that sensitive information was redacted
        self.assertEqual(sanitized_headers["Authorization"], "[REDACTED]")
        self.assertNotIn(MockCredentials.AUTH_HEADER, str(sanitized_headers))
        self.assertIn("[REDACTED]", str(sanitized_headers))


if __name__ == "__main__":
    unittest.main()
