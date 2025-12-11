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
Base HTTP client for IBM Business Automation Workflow REST API.
Provides centralized handling of authentication headers and HTTP requests.
"""

import base64
import logging
import re
from dataclasses import dataclass
from typing import Any, ClassVar

import httpx

from ibm_baw_mcp_server.utils import NO_TIMEOUT_PROVIDED


@dataclass
class HTTPConnectionConfig:
    """Configuration for HTTP client connection parameters."""

    endpoint: str | None = None
    username: str | None = None
    password: str | None = None
    api_key: str | None = None
    verify_ssl: bool = True
    timeout: float | None | object = NO_TIMEOUT_PROVIDED


class BaseHTTPClient:
    """
    Base HTTP client that handles authentication and common HTTP operations.
    """

    # Headers that might contain sensitive information and should be redacted in logs
    _SENSITIVE_HEADERS: ClassVar[list[str]] = [
        "Authorization",
        "X-Api-Key",
        "Api-Key",
        "Password",
        "Token",
        "Cookie",
        "Set-Cookie",
    ]

    def __init__(
        self,
        config: HTTPConnectionConfig,
    ):
        """
        Initialize the BaseHTTPClient with connection parameters.

        Args:
            config: Connection configuration object containing:
                endpoint: Base URL for the server
                username: Username for basic authentication
                password: Password for basic authentication
                api_key: API key for bearer token authentication
                verify_ssl: Whether to verify SSL certificates (default: True)
                timeout: HTTP request timeout in seconds. Three possible values:
                    - None: Explicitly disables all timeouts
                    - A float value: Sets the timeout to that many seconds
                    - Not provided: Uses httpx default timeout behavior
        """
        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Set instance variables
        self.endpoint = config.endpoint
        self.username = config.username
        self.password = config.password
        self.api_key = config.api_key
        self.verify_ssl = config.verify_ssl
        # Use the timeout value from the config
        self.timeout = config.timeout

        # Encode credentials if provided
        self._encoded_credentials = None
        if config.username and config.password:
            self._encoded_credentials = base64.b64encode(
                f"{config.username}:{config.password}".encode()
            ).decode()
            self.logger.info("Basic authentication credentials encoded")

        # Validate authentication parameters
        has_basic_auth = bool(self._encoded_credentials)
        has_api_key = bool(config.api_key)

        if not has_basic_auth and not has_api_key:
            self.logger.warning(
                "No authentication credentials provided. Authentication will likely fail."  # noqa: E501
            )
        elif has_basic_auth and has_api_key:
            self.logger.info(
                "Both basic auth and API key provided. Basic auth will be used."
            )

        self.logger.info(
            "BaseHTTPClient initialized with endpoint: %s, verify_ssl: %s",
            config.endpoint,
            config.verify_ssl,
        )

    @classmethod
    def _sanitize_url_for_logging(cls, url: str) -> str:
        """
        Sanitize URL to remove sensitive information before logging.

        Args:
            url: URL string that might contain credentials

        Returns:
            URL with sensitive parts redacted
        """
        if not url:
            return ""

        # Remove credentials from URLs like https://[credentials]@example.com
        return re.sub(r"(https?://)([^:@/]+:[^@/]+@)", r"\1[REDACTED]@", url)

    @classmethod
    def _sanitize_headers_for_logging(cls, headers: dict[str, str]) -> dict[str, str]:
        """
        Sanitize headers to remove sensitive information before logging.

        Args:
            headers: Dictionary of HTTP headers

        Returns:
            Dictionary with sensitive headers redacted
        """
        if not headers:
            return {}

        sanitized = {}
        for key, value in headers.items():
            if key in cls._SENSITIVE_HEADERS:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        return sanitized

    def get_auth_headers(self) -> dict[str, str]:
        """
        Get the appropriate authentication headers based on available credentials.

        Supports three authentication methods:
        1. Basic authentication (username/password)
        2. Bearer token authentication (API key with "Bearer" prefix)
        3. ZenApiKey authentication (API key with "ZenApiKey" prefix)

        The API key format determines the authentication method:
        - If the API key starts with "Bearer ", it will be used as-is
        - If the API key starts with "ZenApiKey ", it will be used as-is
        - Otherwise, "Bearer " prefix will be added to the API key

        Returns:
            Dictionary of HTTP headers for authentication
        """
        if self._encoded_credentials:
            return {"Authorization": f"Basic {self._encoded_credentials}"}
        elif self.api_key:
            # Check if the API key already includes a prefix
            if self.api_key.startswith("Bearer ") or self.api_key.startswith(
                "ZenApiKey "
            ):
                return {"Authorization": self.api_key}
            else:
                return {"Authorization": f"Bearer {self.api_key}"}
        else:
            self.logger.error("No authentication credentials available")
            raise ValueError("No authentication credentials available")

    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Perform a GET request with authentication headers.

        Args:
            url: URL to request
            params: Query parameters
            headers: Additional headers to include

        Returns:
            HTTP response
        """
        # Combine auth headers with any additional headers
        all_headers = self.get_auth_headers()
        if headers:
            all_headers.update(headers)

        # Log the request with sanitized headers
        if self.logger.isEnabledFor(logging.DEBUG):
            sanitized_headers = self._sanitize_headers_for_logging(all_headers)
            self.logger.debug(f"GET request to {url} with headers: {sanitized_headers}")

        try:
            # Create request kwargs
            request_kwargs: dict[str, Any] = {
                "url": url,
                "params": params,
                "headers": all_headers,
                "verify": self.verify_ssl,
            }

            # Handle timeout:
            # - If timeout is None, explicitly pass None to disable timeout
            # - If timeout is not None and not the sentinel value, pass the timeout value # noqa: E501
            # - If timeout is the sentinel value, don't pass timeout parameter (use httpx default) # noqa: E501
            if self.timeout is None:
                request_kwargs["timeout"] = None
            elif self.timeout is not NO_TIMEOUT_PROVIDED:
                # We know self.timeout is a float at this point
                request_kwargs["timeout"] = self.timeout
            # If self.timeout is NO_TIMEOUT_PROVIDED, don't pass timeout parameter (use httpx default) # noqa: E501

            self.logger.debug(f"Sending GET request to {url}")
            response = httpx.get(**request_kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            # Log only status code to avoid potential sensitive data in response
            self.logger.error(f"HTTP error: {e.response.status_code}")
            raise
        except Exception as e:
            self.logger.error(f"Error in GET request: {e!s}", exc_info=True)
            raise

    def post(
        self,
        url: str,
        json: dict[str, Any] | None = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Perform a POST request with authentication headers.

        Args:
            url: URL to request
            json: JSON data to send
            data: Form data to send
            headers: Additional headers to include

        Returns:
            HTTP response
        """
        # Combine auth headers with any additional headers
        all_headers = self.get_auth_headers()
        if headers:
            all_headers.update(headers)

        # Log the request with sanitized headers
        if self.logger.isEnabledFor(logging.DEBUG):
            sanitized_headers = self._sanitize_headers_for_logging(all_headers)
            self.logger.debug(
                f"POST request to {url} with headers: {sanitized_headers}"
            )

        try:
            # Create request kwargs
            request_kwargs: dict[str, Any] = {
                "url": url,
                "json": json,
                "data": data,
                "headers": all_headers,
                "verify": self.verify_ssl,
            }

            # Handle timeout:
            # - If timeout is None, explicitly pass None to disable timeout
            # - If timeout is not None and not the sentinel value, pass the timeout value # noqa: E501
            # - If timeout is the sentinel value, don't pass timeout parameter (use httpx default) # noqa: E501
            if self.timeout is None:
                request_kwargs["timeout"] = None
            elif self.timeout is not NO_TIMEOUT_PROVIDED:
                # We know self.timeout is a float at this point
                request_kwargs["timeout"] = self.timeout
            # If self.timeout is NO_TIMEOUT_PROVIDED, don't pass timeout parameter (use httpx default) # noqa: E501

            self.logger.debug(f"Sending POST request to {url}")
            response = httpx.post(**request_kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            # Log only status code to avoid potential sensitive data in response
            self.logger.error(f"HTTP error: {e.response.status_code}")
            raise
        except Exception as e:
            self.logger.error(f"Error in POST request: {e!s}", exc_info=True)
            raise

    def create_async_client(
        self, base_url: str | None = None, headers: dict[str, str] | None = None
    ) -> httpx.AsyncClient:
        """
        Create an async HTTP client with authentication headers.

        Args:
            base_url: Base URL for the client (defaults to self.endpoint if not provided)
            headers: Additional headers to include

        Returns:
            Configured AsyncClient instance
        """  # noqa: E501
        # Use the provided base_url or fall back to self.endpoint
        client_base_url = base_url or self.endpoint

        # Ensure we have a valid base_url
        if not client_base_url:
            raise ValueError("No base URL provided and no endpoint set in client")

        # Combine auth headers with any additional headers
        all_headers = self.get_auth_headers()
        if headers:
            all_headers.update(headers)

        # Log the client creation with sanitized headers
        if self.logger.isEnabledFor(logging.DEBUG):
            sanitized_headers = self._sanitize_headers_for_logging(all_headers)
            self.logger.debug(
                f"Creating AsyncClient with base_url: {client_base_url}, headers: {sanitized_headers}"  # noqa: E501
            )

        # Create client kwargs
        client_kwargs: dict[str, Any] = {
            "base_url": client_base_url,
            "headers": all_headers,
            "verify": self.verify_ssl,
        }

        # Handle timeout:
        # - If timeout is None, explicitly pass None to disable timeout
        # - If timeout is not None and not the sentinel value, pass the timeout value
        # - If timeout is the sentinel value, don't pass timeout parameter (use httpx default) # noqa: E501
        if self.timeout is None:
            client_kwargs["timeout"] = None
        elif self.timeout is not NO_TIMEOUT_PROVIDED:
            # We know self.timeout is a float at this point
            client_kwargs["timeout"] = self.timeout
        # If self.timeout is NO_TIMEOUT_PROVIDED, don't pass timeout parameter (use httpx default) # noqa: E501

        return httpx.AsyncClient(**client_kwargs)
