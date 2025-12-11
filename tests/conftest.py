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
Configuration for pytest.
"""

import os
import sys
from pathlib import Path

import httpx
import pytest

# Get the absolute path to the project root directory
project_root = Path(__file__).parent.parent.absolute()

# Add the src directory to the Python path for all tests
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

# This is needed for unittest discovery to work properly
os.environ["PYTHONPATH"] = src_path + (
    f":{os.environ['PYTHONPATH']}" if "PYTHONPATH" in os.environ else ""
)


@pytest.fixture(autouse=True)
def disable_network_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Disable all real network calls during tests.
    This prevents tests from accidentally making real HTTP requests.
    """

    def mock_httpx_request(*args: object, **kwargs: object) -> None:
        url = kwargs.get("url", "")
        if isinstance(url, str) and url.startswith(("http://", "https://")):
            raise RuntimeError(
                f"Network access not allowed during tests. "
                f"Attempted to access {url}. "
                f"Use proper mocking instead."
            )

    # Patch all common HTTP request methods
    monkeypatch.setattr(httpx, "get", mock_httpx_request)
    monkeypatch.setattr(httpx, "post", mock_httpx_request)
    monkeypatch.setattr(httpx, "put", mock_httpx_request)
    monkeypatch.setattr(httpx, "delete", mock_httpx_request)
    monkeypatch.setattr(httpx, "patch", mock_httpx_request)
    monkeypatch.setattr(httpx, "head", mock_httpx_request)
    monkeypatch.setattr(httpx, "options", mock_httpx_request)
