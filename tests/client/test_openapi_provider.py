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
Tests for the OpenAPIProvider interface and implementation.
"""

from unittest.mock import MagicMock, patch

from ibm_baw_mcp_server.client.openapi_provider import (
    DirectOpenAPIProvider,
)


class TestDirectOpenAPIProvider:
    """Tests for the DirectOpenAPIProvider implementation."""

    def test_get_openapi_specs(self) -> None:
        """Test that get_openapi_specs calls the appropriate methods."""
        # Create a mock client
        mock_client = MagicMock()

        # Set up the mock to return test data
        mock_client.get.return_value.json.return_value = {
            "exposed_services": [
                {
                    "name": "TestService",
                    "description": "Test service description",
                    "type": "rest",
                    "container": "TestApp",
                    "definitionUrl": "https://example.com/api",
                    "definition": {
                        "openapi": "3.0.0",
                        "info": {"title": "Test API"},
                        "paths": {},
                    },
                }
            ]
        }

        # Create the provider with the mock client
        provider = DirectOpenAPIProvider(mock_client)

        # Create a mock for _ensure_valid_token
        mock_ensure_valid_token = MagicMock()

        # Patch the _ensure_valid_token method with our mock
        with patch.object(provider, "_ensure_valid_token", mock_ensure_valid_token):
            # Call the method under test
            result = provider.get_openapi_specs()

            # Verify the result
            assert len(result) == 1
            assert result[0]["openapi_spec"]["info"]["title"] == "Test API"
            assert result[0]["process_app_short_name"] == "TestApp"
            assert result[0]["api_title"] == "TestService"

            # Verify the mock methods were called with the expected arguments
            mock_ensure_valid_token.assert_called_once()
            mock_client.get.assert_called_once()

    def test_ensure_valid_token_refresh(self) -> None:
        """Test that _ensure_valid_token refreshes the token when expired."""
        # Create a mock client
        mock_client = MagicMock()

        # Set up the mock to return test data for token refresh
        mock_client.post.return_value.json.return_value = {
            "csrf_token": "test-token",
            "expiration": 7200,
        }

        # Create the provider with the mock client
        provider = DirectOpenAPIProvider(mock_client)

        # Set token to None to force refresh
        provider.csrf_token = None

        # Call the method under test
        provider._ensure_valid_token()

        # Verify the token was refreshed
        assert provider.csrf_token == "test-token"
        assert provider.token_expiry > 0

        # Verify the mock methods were called with the expected arguments
        mock_client.post.assert_called_once_with(
            f"{mock_client.endpoint}/bpm/system/login",
            json={"refresh_groups": True, "requested_lifetime": 7200},
        )
