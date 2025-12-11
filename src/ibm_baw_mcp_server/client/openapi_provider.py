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
Interface and implementation for retrieving OpenAPI specifications from IBM Business Automation Workflow.
"""  # noqa: E501

import abc
import json
import logging
import time
from typing import Any

from ibm_baw_mcp_server.client.http_client import BaseHTTPClient


class OpenAPIProvider(abc.ABC):
    """
    Abstract interface for retrieving OpenAPI specifications from IBM Business Automation Workflow.
    """  # noqa: E501

    @abc.abstractmethod
    def get_openapi_specs(self) -> list[dict[str, Any]]:
        """
        Retrieve OpenAPI specifications for all process applications.

        Returns:
            List of dictionaries containing OpenAPI specifications and metadata:
            {
                "openapi_spec": {...},  # The actual OpenAPI specification
                "process_app_short_name": "...",  # Process app acronym
                "api_title": "..."  # API title
            }
        """
        pass


class DirectOpenAPIProvider(OpenAPIProvider):
    """
    New implementation of OpenAPIProvider that retrieves OpenAPI specifications
    using a single REST API call to /bpm/exposed_services.
    """

    def __init__(self, client: BaseHTTPClient):
        """
        Initialize the DirectOpenAPIProvider with a client.

        Args:
            client: HTTP client for making REST API calls
        """
        self.client = client
        self.logger = logging.getLogger(__name__)
        self.csrf_token = None
        self.token_expiry = 0

    def get_openapi_specs(self) -> list[dict[str, Any]]:
        """
        Retrieve OpenAPI specifications for all process applications using the direct approach.

        Returns:
            List of OpenAPI specifications
        """  # noqa: E501
        self.logger.info("Retrieving OpenAPI specs using direct approach")

        try:
            # Ensure we have a valid CSRF token
            self._ensure_valid_token()

            # Make the request to get all exposed services
            url = f"{self.client.endpoint}/bpm/exposed-services"
            headers = {"BPMCSRFToken": str(self.csrf_token)}
            params = {"type": "rest", "optional_parts": ["definition"]}

            response = self.client.get(url, params=params, headers=headers)
            response_data = response.json()

            # Extract the exposed_services array from the response
            exposed_services = response_data.get("exposed_services", [])

            # Process the response to extract OpenAPI specs
            openapi_specs = []
            for service in exposed_services:
                if service.get("definition"):
                    # Get the OpenAPI spec from the service
                    # The definition might be a JSON string, so we need to parse it
                    definition = service["definition"]

                    # Check if the definition is a string and parse it if needed
                    if isinstance(definition, str):
                        try:
                            openapi_spec = json.loads(definition)
                        except json.JSONDecodeError as e:
                            self.logger.error(
                                f"Error parsing OpenAPI spec for {service.get('name', 'unknown')}: {e!s}"  # noqa: E501
                            )
                            continue
                    else:
                        openapi_spec = definition

                    # Create a dictionary with both the OpenAPI spec and metadata
                    spec_with_metadata = {
                        "openapi_spec": openapi_spec,
                        "process_app_short_name": service.get("container", "unknown"),
                        "api_title": service.get("name", "unknown"),
                    }

                    openapi_specs.append(spec_with_metadata)

            self.logger.info(
                f"Successfully retrieved {len(openapi_specs)} OpenAPI specs"
            )
            return openapi_specs
        except Exception as e:
            self.logger.error(f"Error retrieving OpenAPI specs: {e!s}", exc_info=True)
            raise

    def _ensure_valid_token(self) -> None:
        """
        Ensure we have a valid CSRF token, obtaining a new one if necessary.
        """
        current_time = time.time()

        # Check if token is expired or not set
        if not self.csrf_token or current_time >= self.token_expiry:
            self.logger.info("Obtaining new CSRF token")
            self._obtain_csrf_token()
        else:
            self.logger.debug("Using cached CSRF token")

    def _obtain_csrf_token(self) -> None:
        """
        Obtain a new CSRF token from the server.
        """
        url = f"{self.client.endpoint}/bpm/system/login"
        payload = {
            "refresh_groups": True,
            "requested_lifetime": 7200,  # 2 hours in seconds
        }

        try:
            # Use the client's authentication for this request
            response = self.client.post(url, json=payload)
            token_data = response.json()

            self.csrf_token = token_data["csrf_token"]
            expiration_seconds = token_data.get("expiration", 7200)

            # Set expiry time (current time + expiration - 5 minute buffer)
            self.token_expiry = time.time() + expiration_seconds - 300

            self.logger.info(
                f"Successfully obtained CSRF token, valid for {expiration_seconds} seconds"  # noqa: E501
            )
        except Exception as e:
            self.logger.error(f"Error obtaining CSRF token: {e!s}", exc_info=True)
            raise
