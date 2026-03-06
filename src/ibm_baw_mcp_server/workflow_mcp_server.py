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
Main module for the IBM Business Automation Workflow MCP Server.
This module initializes the FastMCP server and mounts OpenAPI specifications.

The server supports different transport options (specified with --transport):
- stdio: Standard input/output (default)
- http: HTTP transport
- sse: Server-Sent Events
- streamable-http: Streamable HTTP

Usage:
    ibm-baw-mcp-server [--transport {stdio,http,sse,streamable-http}]

Example:
    ibm-baw-mcp-server --transport http

If the --transport parameter is not provided, the default value 'stdio' will be used.
"""

import argparse
import logging
import os
from typing import Any, Literal

from fastmcp import FastMCP
from fastmcp.server.providers.openapi import OpenAPITool
from fastmcp.utilities.openapi import format_description_with_responses

from ibm_baw_mcp_server import __version__
from ibm_baw_mcp_server.client import WorkflowClient
from ibm_baw_mcp_server.client.http_client import HTTPConnectionConfig
from ibm_baw_mcp_server.utils import (
    parse_boolean_env_var,
    parse_timeout_env_var,
    replace_invalid_characters,
)

# Define Transport type based on the error message
Transport = Literal["stdio", "http", "sse", "streamable-http"]

# Get logger for this module
logger = logging.getLogger(__name__)


def customize_tool_description(route: Any, component: Any) -> None:
    """
    Customize tool descriptions to include response information.
    Uses FastMCP's format_description_with_responses utility.

    Args:
        route: The HTTP route information (HTTPRoute object)
        component: The OpenAPI component (tool, resource, or template)
    """
    # Only customize tools
    if isinstance(component, OpenAPITool):
        # Get responses directly from the route
        base_description = component.description or ""
        responses = route.responses or {}

        # Use FastMCP's utility to format description with responses
        if responses:
            enhanced_description = format_description_with_responses(
                base_description=base_description,
                responses=responses,
                parameters=route.parameters,
                request_body=route.request_body,
            )
            component.description = enhanced_description


def initialize_workflow_client() -> WorkflowClient:
    """
    Initialize the WorkflowClient with credentials from environment variables.

    This function reads configuration from environment variables and creates
    a properly configured WorkflowClient instance for connecting to the
    IBM Business Automation Workflow server.

    Environment variables:
        ENDPOINT: Required. The base URL of the BAW server.
        USERID: Username for basic authentication.
        PASSWORD: Password for basic authentication.
        API_KEY: API key for token-based authentication. Can be provided in three formats:
                 1. Raw API key (Bearer prefix will be added automatically)
                 2. With Bearer prefix: "Bearer your-api-key-here"
                 3. With ZenApiKey prefix: "ZenApiKey your-base64-encoded-key"
        VERIFY_SSL: Whether to verify SSL certificates (default: "true").
        HTTP_TIMEOUT: Request timeout in seconds (optional).

    Returns:
        WorkflowClient: An initialized WorkflowClient instance.

    Raises:
        ValueError: If required configuration is missing or invalid.
    Initialize the WorkflowClient with credentials from environment variables.

    Returns:
        An initialized WorkflowClient instance
    """  # noqa: E501
    # Read configuration from environment variables
    timeout_value = parse_timeout_env_var("HTTP_TIMEOUT")

    # Get endpoint and remove trailing slash if present
    endpoint = os.environ.get("ENDPOINT")
    if endpoint and endpoint.endswith("/"):
        endpoint = endpoint.rstrip("/")
        logger.info(f"Removed trailing slash from endpoint URL: {endpoint}")

    # Create variables with proper types
    endpoint_str: str | None = endpoint
    username_str: str | None = os.environ.get("USERID")
    password_str: str | None = os.environ.get("PASSWORD")
    api_key_str: str | None = os.environ.get("API_KEY")
    verify_ssl_bool: bool = parse_boolean_env_var("VERIFY_SSL", default=True)

    # Validate required configuration
    # Validate endpoint URL
    if not endpoint_str:
        error_msg = "Missing required environment variable: ENDPOINT"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Validate authentication credentials
    has_basic_auth = all([username_str, password_str])
    has_api_key = bool(api_key_str)

    if not has_basic_auth and not has_api_key:
        error_msg = "Missing authentication credentials. Either USERID and PASSWORD, or API_KEY must be provided."  # noqa: E501
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Log authentication method being used
    auth_method = "basic authentication" if has_basic_auth else "API key authentication"
    logger.info(
        f"Initializing WorkflowClient with endpoint: {endpoint_str}, "
        f"verify_ssl: {verify_ssl_bool}, using {auth_method}"
    )

    # Remove unused credentials to avoid passing unnecessary parameters
    if has_basic_auth:
        api_key_str = None
    else:
        username_str = None
        password_str = None

    # Create and return the client
    try:
        # Create the connection config
        connection_config = HTTPConnectionConfig(
            endpoint=endpoint_str,
            username=username_str,
            password=password_str,
            api_key=api_key_str,
            verify_ssl=verify_ssl_bool,
            timeout=timeout_value,
        )
        return WorkflowClient(connection_config)
    except Exception as e:
        logger.error(f"Failed to initialize WorkflowClient: {e!s}", exc_info=True)
        raise ValueError(f"Failed to initialize WorkflowClient: {e!s}") from e


def create_mcp_server() -> FastMCP:
    """
    Create and configure the FastMCP server.

    Returns:
        Configured FastMCP server instance
    """
    logger.info("Creating main FastMCP server")
    # Create the main FastMCP server - for each OpenAPI another MCP server is mounted into this server # noqa: E501
    main_mcp = FastMCP(name="Business Automation Workflow local MCP Server")

    try:
        # Initialize the workflow client
        workflow_client = initialize_workflow_client()

        # Get all OpenAPI specifications using the provider interface
        logger.info("Retrieving OpenAPI specifications")
        openapi_specs = workflow_client.get_openapi_specs()
        logger.info(f"Found {len(openapi_specs)} OpenAPI specifications")

        # Process each OpenAPI specification
        for spec_data in openapi_specs:
            # Extract process app name, API title, and OpenAPI spec
            process_app_short_name = spec_data["process_app_short_name"]
            api_title = spec_data["api_title"]
            openapi_spec = spec_data["openapi_spec"]

            try:
                base_url = openapi_spec["servers"][0]["url"]
                logger.info(
                    f"Creating MCP server for API: {api_title} with base URL: {base_url}"  # noqa: E501
                )

                # Create an async client with authentication headers
                client = workflow_client.create_async_client(base_url=base_url)

                # Create the MCP server for specific OpenAPI with custom description
                openapi_mcp = FastMCP.from_openapi(
                    openapi_spec=openapi_spec,
                    client=client,
                    name=f"{process_app_short_name}_{api_title}",
                    mcp_component_fn=customize_tool_description,
                )

                # Add a unique namespace to avoid duplicate tool names
                namespace = (
                    f"{process_app_short_name}_{replace_invalid_characters(api_title)}"
                )
                logger.info(f"Mounting API with namespace: {namespace}")
                main_mcp.mount(openapi_mcp, namespace=namespace)
            except Exception as e:
                logger.error(
                    f"Error processing OpenAPI spec for {process_app_short_name}/{api_title}: {e!s}",  # noqa: E501
                    exc_info=True,
                )
                continue
    except Exception as e:
        logger.error(f"Error creating MCP server: {e!s}", exc_info=True)
        raise

    return main_mcp


def main(transport: Transport = "stdio") -> None:
    """
    Main entry point for the application.

    Args:
        transport: The transport method to use ("stdio", "http", "sse", or "streamable-http"). Default is "stdio".
    """  # noqa: E501
    try:
        logger.info(f"Starting IBM BAW MCP Server v{__version__}")
        main_mcp = create_mcp_server()

        logger.info(f"Running MCP server with {transport.upper()} transport")
        if transport == "stdio":
            logger.info(
                "Using STDIO transport - server will communicate through standard input/output"  # noqa: E501
            )
        elif transport == "http":
            logger.info("Using HTTP transport - server will be accessible via HTTP")
        elif transport == "sse":
            logger.info("Using SSE transport - server will use Server-Sent Events")
        elif transport == "streamable-http":
            logger.info(
                "Using Streamable HTTP transport - server will use HTTP with streaming capabilities"  # noqa: E501
            )

        # Disable banner to prevent FastMCP from reading files it may not have access to
        # which can cause PermissionError when attempting to read system files
        main_mcp.run(transport=transport, show_banner=False)
    except Exception as e:
        logger.critical(f"Fatal error in main: {e!s}", exc_info=True)
        raise


def cli_main() -> None:
    """
    Command-line entry point for the application.
    Processes command-line arguments and calls the main function.
    """
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="IBM Business Automation Workflow MCP Server"
    )

    # Add transport argument with choices
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "http", "sse", "streamable-http"],
        default="stdio",
        help="Transport method to use (default: stdio)",
    )

    # Parse arguments
    args = parser.parse_args()
    transport_arg: Transport = args.transport

    logger.info(f"Transport parameter provided: {transport_arg}")
    main(transport=transport_arg)


if __name__ == "__main__":
    cli_main()
