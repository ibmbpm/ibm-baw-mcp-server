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
from unittest.mock import ANY, MagicMock, patch

# Import test fixtures
from tests.client.test_fixtures import MockCredentials

# Add src directory to path for imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

# Use type ignore to suppress IDE errors
from ibm_baw_mcp_server.client.http_client import HTTPConnectionConfig  # type: ignore
from ibm_baw_mcp_server.client.openapi_provider import (
    DirectOpenAPIProvider,  # type: ignore
)
from ibm_baw_mcp_server.client.workflow_client import WorkflowClient  # type: ignore


def configure_mock_get(mock_get: MagicMock) -> MagicMock:
    """Configure a mock for httpx.get function"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = lambda: None
    mock_response.json.return_value = {"data": {"processAppsList": []}}
    mock_get.return_value = mock_response
    return mock_response


def configure_mock_post(mock_post: MagicMock) -> MagicMock:
    """Configure a mock for httpx.post function"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = lambda: None
    mock_response.json.return_value = {"csrf_token": "mock_token", "expiration": 7200}
    mock_post.return_value = mock_response
    return mock_response


class TestWorkflowClientHTTPConfig(unittest.TestCase):
    """Test HTTP configuration in WorkflowClient."""

    def test_verify_ssl_parameter(self) -> None:
        """Test that the verify_ssl parameter is correctly stored and used."""
        # Test with verify_ssl=True (default)
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
        )
        client = WorkflowClient(config)
        self.assertTrue(client.verify_ssl)

        # Test with verify_ssl=False
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            verify_ssl=False,
        )
        client = WorkflowClient(config)
        self.assertFalse(client.verify_ssl)

    @patch("httpx.post")
    @patch("httpx.get")
    def test_verify_ssl_in_requests(
        self, mock_get: MagicMock, mock_post: MagicMock
    ) -> None:
        """Test that the verify_ssl parameter is used in HTTP requests."""
        # Configure the mocks
        configure_mock_get(mock_get)
        configure_mock_post(mock_post)

        # Test with verify_ssl=True
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            verify_ssl=True,
        )
        client = WorkflowClient(config)

        # Mock the _ensure_valid_token method to avoid making real network calls
        with patch.object(DirectOpenAPIProvider, "_ensure_valid_token"):
            client.get_openapi_specs()

        # Check that the call was made with the correct parameters
        # When using the sentinel value, the timeout parameter should not be included
        mock_get.assert_called_with(
            url=f"{MockCredentials.ENDPOINT}/bpm/exposed-services",
            params={"type": "rest", "optional_parts": ["definition"]},
            headers={"Authorization": ANY, "BPMCSRFToken": ANY},
            verify=True,
        )

        # Test with verify_ssl=False
        mock_get.reset_mock()
        mock_post.reset_mock()
        configure_mock_get(mock_get)
        configure_mock_post(mock_post)

        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            verify_ssl=False,
        )
        client = WorkflowClient(config)

        # Mock the _ensure_valid_token method to avoid making real network calls
        with patch.object(DirectOpenAPIProvider, "_ensure_valid_token"):
            client.get_openapi_specs()

        # Check that the call was made with the correct parameters
        # When no timeout is specified, the timeout parameter should not be included
        mock_get.assert_called_with(
            url=f"{MockCredentials.ENDPOINT}/bpm/exposed-services",
            params={"type": "rest", "optional_parts": ["definition"]},
            headers={"Authorization": ANY, "BPMCSRFToken": ANY},
            verify=False,
        )

    @patch("httpx.post")
    @patch("httpx.get")
    def test_api_key_authentication(
        self, mock_get: MagicMock, mock_post: MagicMock
    ) -> None:
        """Test that API key authentication works correctly."""
        # Configure the mocks
        configure_mock_get(mock_get)
        configure_mock_post(mock_post)

        # Test with API key
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT, api_key=MockCredentials.API_KEY
        )
        client = WorkflowClient(config)

        # Mock the _ensure_valid_token method to avoid making real network calls
        with patch.object(DirectOpenAPIProvider, "_ensure_valid_token"):
            client.get_openapi_specs()

        # Check that the call was made with the correct parameters
        # When no timeout is specified, the timeout parameter should not be included
        mock_get.assert_called_with(
            url=f"{MockCredentials.ENDPOINT}/bpm/exposed-services",
            params={"type": "rest", "optional_parts": ["definition"]},
            headers={
                "Authorization": f"Bearer {MockCredentials.API_KEY}",
                "BPMCSRFToken": ANY,
            },
            verify=True,
        )

    def test_auth_validation(self) -> None:
        """Test authentication validation logic."""
        # Test with both auth methods - this should use username/password and ignore api_key # noqa: E501
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            api_key=MockCredentials.API_KEY,
        )
        client = WorkflowClient(config)
        # Check that credentials are encoded (not None)
        self.assertIsNotNone(client._encoded_credentials)
        self.assertEqual(client.api_key, MockCredentials.API_KEY)

        # Test with no auth methods
        with self.assertRaises(ValueError):
            config = HTTPConnectionConfig(endpoint=MockCredentials.ENDPOINT)
            client = WorkflowClient(config)
            client.get_auth_headers()

    @patch("httpx.post")
    @patch("httpx.get")
    def test_timeout_parameter(self, mock_get: MagicMock, mock_post: MagicMock) -> None:
        """Test that the timeout parameter is correctly stored and used."""
        # Configure the mocks
        configure_mock_get(mock_get)
        configure_mock_post(mock_post)

        # Test with default timeout (None)
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
        )
        client = WorkflowClient(config)

        # Mock the _ensure_valid_token method to avoid making real network calls
        with patch.object(DirectOpenAPIProvider, "_ensure_valid_token"):
            client.get_openapi_specs()

        # Check that the call was made with the correct parameters
        # When no timeout is specified, the timeout parameter should not be included
        mock_get.assert_called_with(
            url=f"{MockCredentials.ENDPOINT}/bpm/exposed-services",
            params={"type": "rest", "optional_parts": ["definition"]},
            headers={"Authorization": ANY, "BPMCSRFToken": ANY},
            verify=True,
        )

        # Test with custom timeout
        mock_get.reset_mock()
        mock_post.reset_mock()
        configure_mock_get(mock_get)
        configure_mock_post(mock_post)

        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            timeout=30.5,
        )
        client = WorkflowClient(config)

        # Mock the _ensure_valid_token method to avoid making real network calls
        with patch.object(DirectOpenAPIProvider, "_ensure_valid_token"):
            client.get_openapi_specs()

        # Check that the call was made with the correct parameters
        mock_get.assert_called_with(
            url=f"{MockCredentials.ENDPOINT}/bpm/exposed-services",
            params={"type": "rest", "optional_parts": ["definition"]},
            headers={"Authorization": ANY, "BPMCSRFToken": ANY},
            verify=True,
            timeout=30.5,
        )

    @patch("httpx.AsyncClient")
    def test_timeout_in_async_client(self, mock_async_client: MagicMock) -> None:
        """Test that the timeout parameter is used in async client creation."""
        # Create a mock instance for the AsyncClient
        mock_instance = MagicMock()
        mock_async_client.return_value = mock_instance

        # Test with default timeout (None)
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
        )
        client = WorkflowClient(config)
        client.create_async_client()

        # Check that the client was created with the correct parameters
        # When no timeout is specified, the timeout parameter should not be included
        mock_async_client.assert_called_with(
            base_url=MockCredentials.ENDPOINT,
            headers={"Authorization": ANY},
            verify=True,
        )

        # Test with custom timeout
        mock_async_client.reset_mock()
        mock_async_client.return_value = mock_instance

        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            timeout=45.5,
        )
        client = WorkflowClient(config)
        client.create_async_client()

        # Check that the client was created with the correct parameters
        mock_async_client.assert_called_with(
            base_url=MockCredentials.ENDPOINT,
            headers={"Authorization": ANY},
            verify=True,
            timeout=45.5,
        )


if __name__ == "__main__":
    unittest.main()


class TestTimeoutSentinelValue(unittest.TestCase):
    """Test the behavior of the NO_TIMEOUT_PROVIDED sentinel value."""

    @patch("httpx.get")
    def test_sentinel_timeout_behavior(self, mock_get: MagicMock) -> None:
        """Test that when NO_TIMEOUT_PROVIDED is used, no timeout parameter is passed."""  # noqa: E501
        # Configure the mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response

        # Create client with default timeout (which should be NO_TIMEOUT_PROVIDED)
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
        )
        client = WorkflowClient(config)

        # Make a request
        client.get(f"{MockCredentials.ENDPOINT}/test")

        # Get kwargs passed to httpx.get
        _, kwargs = mock_get.call_args

        # Verify timeout parameter is not included
        self.assertNotIn("timeout", kwargs)

    @patch("httpx.AsyncClient")
    def test_sentinel_timeout_in_async_client(
        self, mock_async_client: MagicMock
    ) -> None:
        """Test that when NO_TIMEOUT_PROVIDED is used, no timeout parameter is passed to AsyncClient."""  # noqa: E501
        # Create a mock instance for the AsyncClient
        mock_instance = MagicMock()
        mock_async_client.return_value = mock_instance

        # Create client with default timeout (which should be NO_TIMEOUT_PROVIDED)
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
        )
        client = WorkflowClient(config)
        client.create_async_client()

        # Get kwargs passed to AsyncClient
        _, kwargs = mock_async_client.call_args

        # Verify timeout parameter is not included
        self.assertNotIn("timeout", kwargs)
