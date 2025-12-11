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
Tests for the BaseHTTPClient class.
"""

import base64
import os
import sys
from typing import ClassVar
from unittest.mock import Mock, patch

# External dependencies - need to be installed
import httpx
import pytest

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

# Constants for test values
TEST_NUMERIC_TIMEOUT = 30.0
TEST_CUSTOM_TIMEOUT = 45.5

# HTTP status code constants
HTTP_OK = 200
HTTP_CREATED = 201


class TestBaseHTTPClient:
    """Test cases for the BaseHTTPClient class."""

    def test_init_with_username_password(self) -> None:
        """Test initialization with username and password."""
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            verify_ssl=True,
        )
        client = BaseHTTPClient(config)

        # Check that credentials were properly encoded
        assert client._encoded_credentials is not None
        decoded = base64.b64decode(client._encoded_credentials).decode()
        assert decoded == f"{MockCredentials.USERNAME}:{MockCredentials.PASSWORD}"

        # Check other properties
        assert client.endpoint == MockCredentials.ENDPOINT
        assert client.verify_ssl is True
        assert client.api_key is None

    def test_init_with_api_key(self) -> None:
        """Test initialization with API key."""
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            api_key=MockCredentials.API_KEY,
            verify_ssl=True,
        )
        client = BaseHTTPClient(config)

        # Check properties
        assert client._encoded_credentials is None
        assert client.endpoint == MockCredentials.ENDPOINT
        assert client.verify_ssl is True
        assert client.api_key == MockCredentials.API_KEY

    def test_get_auth_headers_basic_auth(self) -> None:
        """Test getting auth headers with basic auth."""
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
        )
        client = BaseHTTPClient(config)

        headers = client.get_auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")
        assert headers["Authorization"] == f"Basic {client._encoded_credentials}"

    def test_get_auth_headers_api_key(self) -> None:
        """Test getting auth headers with API key."""
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT, api_key=MockCredentials.API_KEY
        )
        client = BaseHTTPClient(config)

        headers = client.get_auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == f"Bearer {MockCredentials.API_KEY}"

    def test_get_auth_headers_api_key_with_bearer_prefix(self) -> None:
        """Test getting auth headers with API key that already has Bearer prefix."""
        bearer_key = f"Bearer {MockCredentials.API_KEY}"

        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT, api_key=bearer_key
        )
        client = BaseHTTPClient(config)

        headers = client.get_auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == bearer_key

    def test_get_auth_headers_api_key_with_zen_prefix(self) -> None:
        """Test getting auth headers with API key that has ZenApiKey prefix."""
        zen_key = "ZenApiKey bXl1c2VybmFtZTpteWFwaWtleQ=="

        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT, api_key=zen_key
        )
        client = BaseHTTPClient(config)

        headers = client.get_auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == zen_key

    def test_get_auth_headers_no_credentials(self) -> None:
        """Test getting auth headers with no credentials raises error."""
        config = HTTPConnectionConfig(endpoint=MockCredentials.ENDPOINT)
        client = BaseHTTPClient(config)

        with pytest.raises(ValueError, match="No authentication credentials available"):
            client.get_auth_headers()

    @patch("httpx.get")
    def test_get_request(self, mock_get: Mock) -> None:
        """Test GET request with authentication."""
        # Create client
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
        )
        client = BaseHTTPClient(config)

        # Create a mock response that will work with raise_for_status
        mock_response = Mock()
        mock_response.status_code = HTTP_OK
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status = lambda: None
        mock_response.is_success = True

        # Configure the mock to return our response
        mock_get.return_value = mock_response

        # Make the request
        resource_url = f"{MockCredentials.ENDPOINT}/api/resource"
        response = client.get(resource_url)

        # Check response
        assert response.status_code == HTTP_OK
        assert response.json() == {"status": "success"}

        # Verify the mock was called with correct parameters
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert "url" in kwargs
        assert kwargs["url"] == resource_url
        assert "headers" in kwargs
        assert "Authorization" in kwargs["headers"]

    @patch("httpx.post")
    def test_post_request(self, mock_post: Mock) -> None:
        """Test POST request with authentication."""
        # Create client
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT, api_key=MockCredentials.API_KEY
        )
        client = BaseHTTPClient(config)

        # Create a mock response that will work with raise_for_status
        mock_response = Mock()
        mock_response.status_code = HTTP_CREATED
        mock_response.json.return_value = {"status": "created"}
        mock_response.raise_for_status = lambda: None
        mock_response.is_success = True

        # Configure the mock to return our response
        mock_post.return_value = mock_response

        # Make the request
        resource_url = f"{MockCredentials.ENDPOINT}/api/resource"
        response = client.post(resource_url, json={"name": "test"})

        # Check response
        assert response.status_code == HTTP_CREATED
        assert response.json() == {"status": "created"}

        # Verify the mock was called with correct parameters
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert "url" in kwargs
        assert kwargs["url"] == resource_url
        assert "json" in kwargs
        assert kwargs["json"] == {"name": "test"}
        assert "headers" in kwargs
        assert "Authorization" in kwargs["headers"]
        # Since we're using a raw API key (without prefix), Bearer should be added
        assert kwargs["headers"]["Authorization"] == f"Bearer {MockCredentials.API_KEY}"

    @patch("httpx.post")
    def test_post_request_with_zen_api_key(self, mock_post: Mock) -> None:
        """Test POST request with ZenApiKey authentication."""
        zen_key = "ZenApiKey bXl1c2VybmFtZTpteWFwaWtleQ=="

        # Create client
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT, api_key=zen_key
        )
        client = BaseHTTPClient(config)

        # Create a mock response that will work with raise_for_status
        mock_response = Mock()
        mock_response.status_code = HTTP_CREATED
        mock_response.json.return_value = {"status": "created"}
        mock_response.raise_for_status = lambda: None
        mock_response.is_success = True

        # Configure the mock to return our response
        mock_post.return_value = mock_response

        # Make the request
        resource_url = f"{MockCredentials.ENDPOINT}/api/resource"
        response = client.post(resource_url, json={"name": "test"})

        # Check response
        assert response.status_code == HTTP_CREATED
        assert response.json() == {"status": "created"}

        # Verify the mock was called with correct parameters
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert "url" in kwargs
        assert kwargs["url"] == resource_url
        assert "json" in kwargs
        assert kwargs["json"] == {"name": "test"}
        assert "headers" in kwargs
        assert "Authorization" in kwargs["headers"]
        # The ZenApiKey prefix should be preserved
        assert kwargs["headers"]["Authorization"] == zen_key

    def test_create_async_client(self) -> None:
        """Test creating an async client with authentication."""
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
        )
        client = BaseHTTPClient(config)

        # Mock httpx.AsyncClient to avoid actual HTTP client creation
        original_async_client = httpx.AsyncClient

        try:
            # Create a mock AsyncClient class
            class MockAsyncClient:
                def __init__(self, **kwargs: object) -> None:
                    self.base_url = kwargs.get("base_url")
                    self.headers = kwargs.get("headers", {})
                    self.verify = kwargs.get("verify", True)

            # Replace the original AsyncClient with our mock
            httpx.AsyncClient = MockAsyncClient

            # Now test the method
            async_client = client.create_async_client()

            # Check async client properties
            assert async_client.base_url == MockCredentials.ENDPOINT
            assert async_client.headers["Authorization"].startswith("Basic ")
            # Type ignore to suppress IDE errors with the mock class
            assert async_client.verify is True  # type: ignore
        finally:
            # Restore the original AsyncClient
            httpx.AsyncClient = original_async_client

    def test_create_async_client_custom_base_url(self) -> None:
        """Test creating an async client with a custom base URL."""
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT, api_key=MockCredentials.API_KEY
        )
        client = BaseHTTPClient(config)

        # Mock httpx.AsyncClient to avoid actual HTTP client creation
        original_async_client = httpx.AsyncClient

        try:
            # Create a mock AsyncClient class
            class MockAsyncClient:
                def __init__(self, **kwargs: object) -> None:
                    self.base_url = kwargs.get("base_url")
                    self.headers = kwargs.get("headers", {})
                    self.verify = kwargs.get("verify", True)

            # Replace the original AsyncClient with our mock
            httpx.AsyncClient = MockAsyncClient

            custom_base_url = "https://api.example.com"
            async_client = client.create_async_client(base_url=custom_base_url)

            # Check async client properties
            assert async_client.base_url == custom_base_url
            assert (
                async_client.headers["Authorization"]
                == f"Bearer {MockCredentials.API_KEY}"
            )
            # Type ignore to suppress IDE errors with the mock class
        finally:
            # Restore the original AsyncClient
            httpx.AsyncClient = original_async_client

    def test_create_async_client_additional_headers(self) -> None:
        """Test creating an async client with additional headers."""
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
        )
        client = BaseHTTPClient(config)

        # Mock httpx.AsyncClient to avoid actual HTTP client creation
        original_async_client = httpx.AsyncClient

        try:
            # Create a mock AsyncClient class
            class MockAsyncClient:
                def __init__(self, **kwargs: object) -> None:
                    self.base_url = kwargs.get("base_url")
                    self.headers = kwargs.get("headers", {})
                    self.verify = kwargs.get("verify", True)

            # Replace the original AsyncClient with our mock
            httpx.AsyncClient = MockAsyncClient

            async_client = client.create_async_client(
                headers={"X-Custom-Header": "value"}
            )

            # Check async client headers
            assert async_client.headers["Authorization"].startswith("Basic ")
            assert async_client.headers["X-Custom-Header"] == "value"
        finally:
            # Restore the original AsyncClient
            httpx.AsyncClient = original_async_client

    def test_init_with_timeout_parameter(self) -> None:
        """Test initialization with timeout parameter."""
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            timeout=TEST_NUMERIC_TIMEOUT,
        )
        client = BaseHTTPClient(config)

        # Check timeout property
        assert client.timeout == TEST_NUMERIC_TIMEOUT

    def test_init_with_custom_timeout(self) -> None:
        """Test initialization with custom timeout value."""
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            timeout=TEST_CUSTOM_TIMEOUT,
        )
        client = BaseHTTPClient(config)

        # Check timeout property
        assert client.timeout == TEST_CUSTOM_TIMEOUT

    def test_init_with_explicit_timeout(self) -> None:
        """Test initialization with explicit timeout parameter."""
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            timeout=None,
        )
        client = BaseHTTPClient(config)

        # Check timeout property is None when None is passed
        assert client.timeout is None

    @patch("httpx.get")
    def test_get_request_with_none_timeout(self, mock_get: Mock) -> None:
        """Test GET request with None timeout (should disable timeout)."""
        # Create client with None timeout
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            timeout=None,
        )
        client = BaseHTTPClient(config)

        # Create a mock response
        mock_response = Mock()
        mock_response.status_code = HTTP_OK
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status = lambda: None
        mock_response.is_success = True

        # Configure the mock to return our response
        mock_get.return_value = mock_response

        # Make the request
        resource_url = f"{MockCredentials.ENDPOINT}/api/resource"
        client.get(resource_url)

        # Verify the mock was called with correct parameters
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args

        # Check that timeout=None was explicitly passed to httpx.get
        assert "timeout" in kwargs
        assert kwargs["timeout"] is None

    @patch("httpx.get")
    def test_get_request_with_numeric_timeout(self, mock_get: Mock) -> None:
        """Test GET request with numeric timeout."""
        # Create client with numeric timeout
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            timeout=TEST_NUMERIC_TIMEOUT,
        )
        client = BaseHTTPClient(config)

        # Create a mock response
        mock_response = Mock()
        mock_response.status_code = HTTP_OK
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status = lambda: None
        mock_response.is_success = True

        # Configure the mock to return our response
        mock_get.return_value = mock_response

        # Make the request
        resource_url = f"{MockCredentials.ENDPOINT}/api/resource"
        client.get(resource_url)

        # Verify the mock was called with correct parameters
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args

        # Check that timeout=TEST_NUMERIC_TIMEOUT was passed to httpx.get
        assert "timeout" in kwargs
        assert kwargs["timeout"] == TEST_NUMERIC_TIMEOUT

    @patch("httpx.get")
    def test_get_request_without_timeout_param(self, mock_get: Mock) -> None:
        """Test GET request without timeout parameter (should use httpx default)."""
        # Create client without specifying timeout
        # This will use the default None value from the method signature
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
        )
        client = BaseHTTPClient(config)

        # Create a mock response
        mock_response = Mock()
        mock_response.status_code = HTTP_OK
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status = lambda: None
        mock_response.is_success = True

        # Configure the mock to return our response
        mock_get.return_value = mock_response

        # Make the request
        resource_url = f"{MockCredentials.ENDPOINT}/api/resource"
        client.get(resource_url)

        # Verify the mock was called with correct parameters
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args

        # Check that timeout parameter is not included when NO_TIMEOUT_PROVIDED is used
        assert "timeout" not in kwargs

    @patch("httpx.post")
    def test_post_request_with_none_timeout(self, mock_post: Mock) -> None:
        """Test POST request with None timeout (should disable timeout)."""
        # Create client with None timeout
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            timeout=None,
        )
        client = BaseHTTPClient(config)

        # Create a mock response
        mock_response = Mock()
        mock_response.status_code = HTTP_CREATED
        mock_response.json.return_value = {"status": "created"}
        mock_response.raise_for_status = lambda: None
        mock_response.is_success = True

        # Configure the mock to return our response
        mock_post.return_value = mock_response

        # Make the request
        resource_url = f"{MockCredentials.ENDPOINT}/api/resource"
        client.post(resource_url, json={"name": "test"})

        # Verify the mock was called with correct parameters
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args

        # Check that timeout=None was explicitly passed to httpx.post
        assert "timeout" in kwargs
        assert kwargs["timeout"] is None

    @patch("httpx.post")
    def test_post_request_with_sentinel_timeout(self, mock_post: Mock) -> None:
        """Test POST request with sentinel timeout value (should not pass timeout)."""
        # Create client without specifying timeout (will use sentinel value)
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
        )
        client = BaseHTTPClient(config)

        # Create a mock response
        mock_response = Mock()
        mock_response.status_code = HTTP_CREATED
        mock_response.json.return_value = {"status": "created"}
        mock_response.raise_for_status = lambda: None
        mock_response.is_success = True

        # Configure the mock to return our response
        mock_post.return_value = mock_response

        # Make the request
        resource_url = f"{MockCredentials.ENDPOINT}/api/resource"
        client.post(resource_url, json={"name": "test"})

        # Verify the mock was called with correct parameters
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args

        # Check that timeout parameter is not included when NO_TIMEOUT_PROVIDED is used
        assert "timeout" not in kwargs

    def test_create_async_client_with_none_timeout(self) -> None:
        """Test creating an async client with None timeout."""
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            timeout=None,
        )
        client = BaseHTTPClient(config)

        # Mock httpx.AsyncClient to avoid actual HTTP client creation
        original_async_client = httpx.AsyncClient

        try:
            # Create a mock AsyncClient class
            class MockAsyncClient:
                def __init__(self, **kwargs: object) -> None:
                    self.base_url = kwargs.get("base_url")
                    self.headers = kwargs.get("headers", {})
                    self.verify = kwargs.get("verify", True)
                    self.timeout = kwargs.get("timeout")

            # Replace the original AsyncClient with our mock
            httpx.AsyncClient = MockAsyncClient

            # Now test the method
            async_client = client.create_async_client()

            # Check that timeout=None was explicitly passed to AsyncClient
            assert hasattr(async_client, "timeout")
            assert async_client.timeout is None
        finally:
            # Restore the original AsyncClient
            httpx.AsyncClient = original_async_client

    def test_create_async_client_with_sentinel_timeout(self) -> None:
        """Test creating an async client with the sentinel value (should not pass timeout)."""  # noqa: E501
        # Create client without specifying timeout (will use sentinel value)
        config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
        )
        client = BaseHTTPClient(config)

        # Mock httpx.AsyncClient to avoid actual HTTP client creation
        original_async_client = httpx.AsyncClient

        try:
            # Create a mock AsyncClient class that tracks kwargs
            class MockAsyncClient:
                last_kwargs: ClassVar[dict[str, object]] = {}

                def __init__(self, **kwargs: object) -> None:
                    self.base_url = kwargs.get("base_url")
                    self.headers = kwargs.get("headers", {})
                    self.verify = kwargs.get("verify", True)
                    MockAsyncClient.last_kwargs = kwargs

            # Replace the original AsyncClient with our mock
            httpx.AsyncClient = MockAsyncClient

            # Now test the method
            client.create_async_client()

            # Check that timeout parameter was not passed
            assert "timeout" not in MockAsyncClient.last_kwargs
        finally:
            # Restore the original AsyncClient
            httpx.AsyncClient = original_async_client
