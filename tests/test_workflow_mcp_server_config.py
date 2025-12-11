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
from unittest.mock import MagicMock, patch

# Import test fixtures
from tests.client.test_fixtures import MockCredentials

# Add src directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Use type ignore to suppress IDE errors
from ibm_baw_mcp_server.client.http_client import HTTPConnectionConfig
from ibm_baw_mcp_server.utils import NO_TIMEOUT_PROVIDED
from ibm_baw_mcp_server.workflow_mcp_server import (
    initialize_workflow_client,  # type: ignore
)


class TestWorkflowMCPServerConfig(unittest.TestCase):
    """Test configuration handling in workflow_mcp_server."""

    def setUp(self) -> None:
        """Set up test environment."""
        # Save original environment variables
        self.original_env = os.environ.copy()

        # Set required environment variables for testing
        os.environ["ENDPOINT"] = MockCredentials.ENDPOINT
        os.environ["USERID"] = MockCredentials.USERNAME
        os.environ["PASSWORD"] = MockCredentials.PASSWORD

        # Create a patcher for the WorkflowClient
        self.workflow_client_patcher = patch(
            "ibm_baw_mcp_server.workflow_mcp_server.WorkflowClient"
        )  # type: ignore
        self.mock_workflow_client = self.workflow_client_patcher.start()

        # Configure the mock
        self.mock_instance = MagicMock()
        self.mock_workflow_client.return_value = self.mock_instance

    def tearDown(self) -> None:
        """Clean up after tests."""
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)

        # Stop the patcher
        self.workflow_client_patcher.stop()

    def test_verify_ssl_true(self) -> None:
        """Test that VERIFY_SSL=true is correctly interpreted."""
        os.environ["VERIFY_SSL"] = "true"
        initialize_workflow_client()
        # Create expected HTTPConnectionConfig object
        expected_config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            api_key=None,
            verify_ssl=True,
            timeout=NO_TIMEOUT_PROVIDED,
        )
        self.mock_workflow_client.assert_called_with(expected_config)

    def test_verify_ssl_false(self) -> None:
        """Test that VERIFY_SSL=false is correctly interpreted."""
        os.environ["VERIFY_SSL"] = "false"
        initialize_workflow_client()
        # Create expected HTTPConnectionConfig object
        expected_config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            api_key=None,
            verify_ssl=False,
            timeout=NO_TIMEOUT_PROVIDED,
        )
        self.mock_workflow_client.assert_called_with(expected_config)

    def test_verify_ssl_zero(self) -> None:
        """Test that VERIFY_SSL=0 is correctly interpreted as False."""
        os.environ["VERIFY_SSL"] = "0"
        initialize_workflow_client()
        # Create expected HTTPConnectionConfig object
        expected_config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            api_key=None,
            verify_ssl=False,
            timeout=NO_TIMEOUT_PROVIDED,
        )
        self.mock_workflow_client.assert_called_with(expected_config)

    def test_verify_ssl_not_set(self) -> None:
        """Test that when VERIFY_SSL is not set, it defaults to True."""
        if "VERIFY_SSL" in os.environ:
            del os.environ["VERIFY_SSL"]
        initialize_workflow_client()
        # Create expected HTTPConnectionConfig object
        expected_config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            api_key=None,
            verify_ssl=True,
            timeout=NO_TIMEOUT_PROVIDED,
        )
        self.mock_workflow_client.assert_called_with(expected_config)

    def test_api_key_authentication(self) -> None:
        """Test that API_KEY is correctly used for authentication."""
        # Remove basic auth credentials
        del os.environ["USERID"]
        del os.environ["PASSWORD"]

        # Set API key
        os.environ["API_KEY"] = MockCredentials.API_KEY

        initialize_workflow_client()
        # Create expected HTTPConnectionConfig object
        expected_config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=None,
            password=None,
            api_key=MockCredentials.API_KEY,
            verify_ssl=True,
            timeout=NO_TIMEOUT_PROVIDED,
        )
        self.mock_workflow_client.assert_called_with(expected_config)

    def test_both_auth_methods(self) -> None:
        """Test that when both auth methods are provided, basic auth is preferred."""
        # Set API key in addition to basic auth
        os.environ["API_KEY"] = MockCredentials.API_KEY

        initialize_workflow_client()
        # Create expected HTTPConnectionConfig object
        expected_config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            api_key=None,  # API key is removed in initialize_workflow_client when basic auth is used # noqa: E501
            verify_ssl=True,
            timeout=NO_TIMEOUT_PROVIDED,
        )
        self.mock_workflow_client.assert_called_with(expected_config)

    def test_no_auth_methods(self) -> None:
        """Test that an error is raised when no auth methods are provided."""
        # Remove all auth credentials
        del os.environ["USERID"]
        del os.environ["PASSWORD"]

        with self.assertRaises(ValueError):
            initialize_workflow_client()

    def test_http_timeout_not_set(self) -> None:
        """Test that when HTTP_TIMEOUT is not set, no timeout is provided."""
        if "HTTP_TIMEOUT" in os.environ:
            del os.environ["HTTP_TIMEOUT"]
        initialize_workflow_client()
        # Create expected HTTPConnectionConfig object
        expected_config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            api_key=None,
            verify_ssl=True,
            timeout=NO_TIMEOUT_PROVIDED,
        )
        self.mock_workflow_client.assert_called_with(expected_config)

    def test_http_timeout_numeric(self) -> None:
        """Test that HTTP_TIMEOUT with a numeric value is correctly interpreted."""
        os.environ["HTTP_TIMEOUT"] = "30.5"
        initialize_workflow_client()
        # Create expected HTTPConnectionConfig object
        expected_config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            api_key=None,
            verify_ssl=True,
            timeout=30.5,
        )
        self.mock_workflow_client.assert_called_with(expected_config)

    def test_http_timeout_none(self) -> None:
        """Test that HTTP_TIMEOUT='None' is correctly interpreted as None."""
        os.environ["HTTP_TIMEOUT"] = "None"
        initialize_workflow_client()
        # Create expected HTTPConnectionConfig object
        expected_config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            api_key=None,
            verify_ssl=True,
            timeout=None,
        )
        self.mock_workflow_client.assert_called_with(expected_config)

    def test_http_timeout_invalid(self) -> None:
        """Test that invalid HTTP_TIMEOUT values are handled correctly."""
        os.environ["HTTP_TIMEOUT"] = "invalid"
        initialize_workflow_client()
        # Create expected HTTPConnectionConfig object
        expected_config = HTTPConnectionConfig(
            endpoint=MockCredentials.ENDPOINT,
            username=MockCredentials.USERNAME,
            password=MockCredentials.PASSWORD,
            api_key=None,
            verify_ssl=True,
            timeout=None,
        )
        self.mock_workflow_client.assert_called_with(expected_config)


if __name__ == "__main__":
    unittest.main()
