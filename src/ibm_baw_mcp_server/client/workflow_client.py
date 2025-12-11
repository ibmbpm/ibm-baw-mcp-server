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
Client for interacting with IBM Business Automation Workflow REST API.
"""

from typing import Any

from ibm_baw_mcp_server.client.http_client import BaseHTTPClient, HTTPConnectionConfig
from ibm_baw_mcp_server.client.openapi_provider import (
    DirectOpenAPIProvider,
    OpenAPIProvider,
)


class WorkflowClient(BaseHTTPClient, OpenAPIProvider):
    """
    Client for interacting with IBM Business Automation Workflow REST API.
    Provides methods for authentication and workflow operations.
    Implements OpenAPIProvider interface to retrieve OpenAPI specifications.
    """

    def __init__(
        self,
        config: HTTPConnectionConfig,
    ):
        """
        Initialize the WorkflowClient with connection parameters.

        Args:
            config: Connection configuration object containing:
                endpoint: Base URL for the BAW server
                username: Username for basic authentication
                password: Password for basic authentication
                api_key: API key for authentication (alternative to basic auth).
                         Can be provided in three formats:
                         1. Raw API key (Bearer prefix will be added automatically)
                         2. With Bearer prefix (used as-is): "Bearer your-api-key-here"
                         3. With ZenApiKey prefix (used as-is): "ZenApiKey your-base64-encoded-key"
                verify_ssl: Whether to verify SSL certificates (default: True)
                timeout: HTTP request timeout in seconds (default: None, uses httpx default)
        """  # noqa: E501
        super().__init__(config)

        # Sanitize endpoint URL before logging (remove any credentials that might be in the URL) # noqa: E501
        safe_endpoint = (
            BaseHTTPClient._sanitize_url_for_logging(config.endpoint)
            if config.endpoint
            else None
        )
        self.logger.info(
            "WorkflowClient initialized with endpoint: %s, verify_ssl: %s",
            safe_endpoint,
            config.verify_ssl,
        )

        self._openapi_provider = DirectOpenAPIProvider(self)

    def get_openapi_specs(self) -> list[dict[str, Any]]:
        """
        Retrieve OpenAPI specifications for all process applications.
        Delegates to the configured OpenAPI provider implementation.

        Returns:
            List of OpenAPI specifications
        """
        self.logger.info("Retrieving OpenAPI specs for all process applications")
        return self._openapi_provider.get_openapi_specs()
