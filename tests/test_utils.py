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
Tests for utility functions in the ibm_baw_mcp_server.utils module.
"""

import os
import sys
from unittest.mock import patch

import pytest  # type: ignore # noqa

# Add src directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Use type ignore to suppress IDE errors
from ibm_baw_mcp_server.utils import (  # type: ignore
    NO_TIMEOUT_PROVIDED,
    parse_timeout_env_var,
)

# Constants for test values
TEST_INTEGER_TIMEOUT = 45.0
TEST_FLOAT_TIMEOUT = 30.5


class TestParseTimeoutEnvVar:
    """Test cases for the parse_timeout_env_var function."""

    def test_parse_timeout_env_var_none_string(self) -> None:
        """Test parsing 'None' string value."""
        with patch.dict(os.environ, {"TEST_TIMEOUT": "None"}):
            result = parse_timeout_env_var("TEST_TIMEOUT")
            assert result is None

    def test_parse_timeout_env_var_none_lowercase(self) -> None:
        """Test parsing 'none' lowercase string value."""
        with patch.dict(os.environ, {"TEST_TIMEOUT": "none"}):
            result = parse_timeout_env_var("TEST_TIMEOUT")
            assert result is None

    def test_parse_timeout_env_var_empty_string(self) -> None:
        """Test parsing empty string value."""
        with patch.dict(os.environ, {"TEST_TIMEOUT": ""}):
            result = parse_timeout_env_var("TEST_TIMEOUT")
            assert result is None

    def test_parse_timeout_env_var_numeric(self) -> None:
        """Test parsing numeric value."""
        with patch.dict(os.environ, {"TEST_TIMEOUT": "30.5"}):
            result = parse_timeout_env_var("TEST_TIMEOUT")
            assert result == TEST_FLOAT_TIMEOUT

    def test_parse_timeout_env_var_integer(self) -> None:
        """Test parsing integer value."""
        with patch.dict(os.environ, {"TEST_TIMEOUT": "45"}):
            result = parse_timeout_env_var("TEST_TIMEOUT")
            assert result == TEST_INTEGER_TIMEOUT

    def test_parse_timeout_env_var_invalid(self) -> None:
        """Test parsing invalid value."""
        with patch.dict(os.environ, {"TEST_TIMEOUT": "invalid"}):
            result = parse_timeout_env_var("TEST_TIMEOUT")
            assert result is None

    def test_parse_timeout_env_var_not_set(self) -> None:
        """Test behavior when environment variable is not set."""
        # Ensure the environment variable doesn't exist
        if "TEST_TIMEOUT" in os.environ:
            del os.environ["TEST_TIMEOUT"]

        result = parse_timeout_env_var("TEST_TIMEOUT")
        assert result is NO_TIMEOUT_PROVIDED
