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
Utility functions for the IBM Business Automation Workflow MCP Server.
"""

import logging
import os
import re

# Get logger for this module
logger = logging.getLogger(__name__)


def replace_invalid_characters(text: str) -> str:
    """
    Replace invalid characters in a string with underscores.

    Args:
        text: The input string

    Returns:
        A string with invalid characters replaced
    """
    if not text:
        return ""

    # Replace spaces and common separators with underscores
    result = re.sub(r"[\s\-\.]+", "_", text)

    # Remove non-alphanumeric characters except underscores
    result = re.sub(r"[^a-zA-Z0-9_]", "", result)

    return result


def parse_boolean_env_var(var_name: str, default: bool = False) -> bool:
    """
    Parse a boolean environment variable.

    Args:
        var_name: Name of the environment variable
        default: Default value if the variable is not set

    Returns:
        Boolean value of the environment variable
    """
    value = os.environ.get(var_name)
    if value is None:
        return default

    value = value.lower()
    return value not in ("false", "0", "no", "n", "f")


# Special sentinel value to indicate that no timeout should be provided
NO_TIMEOUT_PROVIDED = object()


def parse_timeout_env_var(var_name: str) -> float | None | object:
    """
    Parse a timeout environment variable.

    The function handles the following cases:
    1. If the environment variable is not set, returns NO_TIMEOUT_PROVIDED sentinel value,
       which indicates that no timeout should be provided to httpx client.
    2. If the environment variable is set to "None" (case-insensitive) or empty string,
       returns None, which will set an unlimited timeout in httpx.
    3. If the environment variable is set to a valid numeric value, returns that value as a float.
    4. If the environment variable is set to an invalid value, returns None.

    Args:
        var_name: Name of the environment variable

    Returns:
        - Float value of the timeout if a numeric value is provided
        - None if "None" string is provided or invalid value
        - NO_TIMEOUT_PROVIDED sentinel if the environment variable is not set
    """  # noqa: E501
    # Check if the environment variable exists
    if var_name not in os.environ:
        logger.info(
            f"{var_name} environment variable not set. No timeout will be provided."
        )
        return NO_TIMEOUT_PROVIDED

    timeout_str = os.environ.get(var_name)
    if not timeout_str or timeout_str.lower() == "none":
        logger.info(f"{var_name} set to 'None'. Using None as timeout.")
        return None

    try:
        timeout = float(timeout_str)
        logger.info(f"Using {var_name} from environment: {timeout}")
        return timeout
    except ValueError:
        logger.warning(
            f"Invalid {var_name} value: {timeout_str}. Using None as timeout."
        )
        return None
