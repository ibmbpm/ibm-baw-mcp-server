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
IBM Business Automation Workflow MCP Server
"""

import logging
import os
from importlib.metadata import version

# Get package version from pyproject.toml
try:
    __version__ = version("ibm-baw-mcp-server")
except Exception:
    # Fallback version if package is not installed
    __version__ = "0.0.0-dev"


# Create a custom logger
def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """
    Set up logging configuration for the entire application.

    Args:
        log_level: The logging level to use (default: logging.INFO)
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers to avoid duplicates
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    # Create formatter and add to handler
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)
    console_handler.setFormatter(formatter)

    # Add handler to the root logger
    root_logger.addHandler(console_handler)

    # Log startup message with version information
    root_logger.info(f"IBM BAW MCP Server v{__version__} - Logging initialized")

    return root_logger


# Initialize logging with default settings
# This can be overridden by calling setup_logging with different parameters
logger = setup_logging(log_level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO")))
