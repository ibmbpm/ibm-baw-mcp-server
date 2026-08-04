# IBM® Business Automation Workflow MCP Server

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

The IBM® Business Automation Workflow MCP Server is a local Model Control Protocol (MCP) server that supports integration of AI agents with IBM® Business Automation Workflow through the Model Context Protocol. It provides a consistent way for agents to access tools through MCP servers, enabling seamless integration with business automation capabilities.

## IBM Public Repository Disclosure
All content in this repository including code has been provided by IBM under the associated open source software license and IBM is under no obligation to provide enhancements, updates, or support. IBM developers produced this code as an open source project (not as an IBM product), and IBM makes no assertions as to the level of quality nor security, and will not be maintaining this code going forward.

## Table of Contents

- [Overview](#overview)
- [Concepts](#concepts)
  - [What is the Model Control Protocol (MCP)?](#what-is-the-model-control-protocol-mcp)
  - [Local MCP server](#local-mcp-server)
  - [Exposed REST services](#exposed-rest-services)
- [Prerequisites](#prerequisites)
- [Configuration properties](#configuration-properties)
  - [Security](#security)
  - [HTTP connection](#http-connection)
  - [Logging](#logging)
- [Getting started with IBM® watsonx Orchestrate®](#getting-started-with-ibm-watsonx-orchestrate)
  - [IBM® watsonx Orchestrate® console](#ibm-watsonx-orchestrate-console)
  - [IBM watsonx Orchestrate Agent Development Kit (ADK)](#ibm-watsonx-orchestrate-agent-development-kit-adk)
- [Best practices and limitations](#best-practices-and-limitations)
  - [Creating effective MCP tools](#creating-effective-mcp-tools)
  - [Asynchronous operations](#asynchronous-operations)
  - [MCP client limitations](#mcp-client-limitations)
- [Troubleshooting](#troubleshooting)
  - [Common errors](#common-errors)
  - [Viewing logs](#viewing-logs)
- [License](#license)

## Overview

The IBM® Business Automation Workflow MCP Server exposes existing REST services from workflow automations as tools to enable AI agent developers to easily integrate them into their agents. This allows agents to provide natural language interfaces that leverage workflow automations.

The MCP server works with IBM® Business Automation Workflow version 25.0.1.0 and IBM® Cloud Pak® for Business Automation 25.0.1 and later, including:

- [IBM® Cloud Pak® for Business Automation (CP4BA)](https://www.ibm.com/products/cloud-pak-for-business-automation)
- [IBM® Business Automation Workflow](https://www.ibm.com/products/business-automation-workflow)

This MCP server is designed for integration with MCP clients like IBM® watsonx Orchestrate® that support local MCP servers written in Python.

## Concepts
### What is the Model Control Protocol (MCP)?

The Model Control Protocol is an open-source standard that allows AI applications to interact with external tools through MCP servers. The MCP protocol enables AI agents to discover and invoke external tools that are provided by MCP servers. These servers act as gateways, offering a standardized interface for workflow capabilities such as claims handling, loan approval, and other business processes.

The MCP specification is available at [https://modelcontextprotocol.io/specification/2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18). 

### Local MCP server

The workflow MCP server is a local MCP server. MCP clients use stdio (standard input/output) for communication with the MCP server. The server runs in the same environment as the MCP client and provides a bridge between AI agents and your workflow environment.

### Exposed REST services

Exposed REST services are custom APIs that are created and exposed by workflow automations. They are strongly typed services that expose specific business services (for example, submit loan request). 

For detailed instructions on creating and exposing these custom automation APIs, refer to:

- [Exposing REST services in Business Automation Workflow](https://www.ibm.com/docs/en/baw/25.0.0?topic=services-rest)
- [Exposing REST services in CP4BA](https://www.ibm.com/docs/en/cloud-paks/cp-biz-automation/25.0.0?topic=services-rest)

All exposed REST services are automatically added as tools by the MCP server. This means that any custom automation API you expose in your workflow environment becomes available to the LLM without additional configuration.

When a REST service has multiple versions, only the default version is added as a tool to the MCP server. This can ensure that LLMs interact with the most up-to-date implementation of each service. If you create new versions, you need to make sure that you only do compatible changes.

## Prerequisites

Before using this MCP server, make sure that you have:

- Access to a workflow environment (version 25.0.1 or later)
- Credentials for a workflow user that is used by the MCP server to interact with the workflow environment
- Network connectivity from the MCP server to your workflow environment

## Configuration properties

The Business Automation Workflow MCP Server requires configuration through environment variables. How you set those depends on the MCP client. For IBM® watsonx Orchestrate® you can use connections.

### Security

You can use one of the following authentication methods:

1. **Environment variables for basic authentication**
   - `USERID`: Your workflow user username
   - `PASSWORD`: Your workflow password

2. **Environment variables for Zen API key authentication** 
for IBM Cloud Pak for Business Automation and IBM Business Automation Workflow on containers
   - `API_KEY`: Your Zen API key (prefixed with 'ZenApiKey')
   - For details on creating and using Zen API keys, see: [Authorizing HTTP requests by using a Zen API key](https://www.ibm.com/docs/en/cloud-paks/cp-biz-automation/25.0.0?topic=administering-authorizing-http-requests-by-using-zen-api-key)

### HTTP connection
**Environment variables**
- `ENDPOINT`: The base URL of your workflow environment (for example, `https://your-baw-server.example.com`)
- `VERIFY_SSL`: Whether to verify SSL certificates (default: "true"). Set to "false" for environments with self-signed certificates.
- `HTTP_TIMEOUT`: Request timeout in seconds (optional)

### Logging
**Environment variables**
- `LOG_LEVEL` (optional): Logging level (default: INFO). Supported values:
  - `DEBUG`: Detailed debugging information
  - `INFO`: Confirmation that things are working as expected
  - `WARNING`: Indication that something unexpected happened, or may happen soon
  - `ERROR`: Due to a more serious problem, the software has not been able to perform some function
  - `CRITICAL`: A serious error, indicating that the program itself may be unable to continue running

## Getting started with IBM® watsonx Orchestrate®

This section provides a guide for integrating the workflow MCP Server with IBM® watsonx Orchestrate®. You can configure the server using either the IBM® watsonx Orchestrate® console or the Agent Development Kit (ADK).

For detailed information, see the [IBM® watsonx Orchestrate® documentation](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=tools-mcp-servers). For local testing, you can use the [IBM® watsonx Orchestrate® Developer Edition](https://developer.watson-orchestrate.ibm.com/developer_edition/wxOde_overview).

### IBM® watsonx Orchestrate® console

This configuration method is recommended when you prefer a graphical interface.

#### Step 1: Create a Key Value Pair connection

1. Log in to IBM® watsonx Orchestrate®
2. Navigate to **Connections** in the settings
3. Click **Add connection** and select **Key Value Pair** as the connection type
4. Configure the connection:
   - **Connection name**: `ibm-baw` (or your preferred name)
   - **Description**: Connection for IBM® Business Automation Workflow MCP Server
5. Add the required key-value pairs (see [Configuration](#configuration) section for details):
   - Authentication credentials (choose one method: Basic, API Key, or Zen API Key)
   - `ENDPOINT`: Your workflow environment URL
   - Optional: `VERIFY_SSL`, `HTTP_TIMEOUT`, `LOG_LEVEL`

6. Save the connection

For detailed instructions, see: [Configuring App Credentials](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=credentials-configuring-app) in the IBM® watsonx Orchestrate® documentation.

#### Step 2: Import the Business Automation Workflow MCP Server

1. Navigate to **MCP Servers** in IBM watsonx Orchestrate
2. Click **Import from MCP server**
3. Configure the server:
   - **Server name**: IBM-BAW (or your preferred name)
   - **Description**: IBM® Business Automation Workflow MCP Server
   - **Command**:
     ```bash
     uvx --from git+https://github.com/ibmbpm/ibm-baw-mcp-server ibm-baw-mcp-server
     ```
     or
     ```bash
     uvx --from https://github.com/ibmbpm/ibm-baw-mcp-server/archive/refs/heads/main.zip ibm-baw-mcp-server
     ``` 
   - **Connection**: Select the `ibm-baw` connection that you created in Step 1
4. Click **Import** to start the server

For detailed instructions, see: [Importing from MCP Server](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=servers-importing-from-mcp-server) in the IBM® watsonx Orchestrate® documentation.

### IBM watsonx Orchestrate Agent Development Kit (ADK)

This configuration method is recommended when you want to script your configuration or when you want to customize the MCP server.

#### Step 1: Install the IBM® watsonx Orchestrate® ADK

Follow the installation guide at: [https://developer.watson-orchestrate.ibm.com/getting_started/installing](https://developer.watson-orchestrate.ibm.com/getting_started/installing) to install the ADK.

#### Step 2: Clone the repository

```bash
git clone https://github.com/ibmbpm/ibm-baw-mcp-server.git
cd ibm-baw-mcp-server
```

#### Step 3: Create a Key Value Pair connection

```bash
# Create a new connection (you can use a custom connection name by replacing 'ibm-baw')
orchestrate connections add -a ibm-baw

# Configure the connection as a Key Value Pair type
orchestrate connections configure --app-id ibm-baw --env draft --kind key_value -t team

# Set credentials and configuration for your connection
# Add all the supported environment variables as key-value pairs
orchestrate connections set-credentials -a ibm-baw --env draft \
    -e ENDPOINT="your-baw-endpoint" \
    -e USERID="your-username" \
    -e PASSWORD="your-password" \
    -e VERIFY_SSL="true"
```

For more configuration options, see the [Configuration](#configuration) section.

#### Step 4: Import the toolkit

```bash
# Import the toolkit
# Use the connection name that you created in Step 3
# Run this command from the root of the project (ibm-baw-mcp-server)
orchestrate toolkits add \
    --kind mcp \
    --name IBM-BAW \
    --description "IBM® Business Automation Workflow MCP Server" \
    --package-root . \
    --command "uv run ibm-baw-mcp-server" \
    --app-id ibm-baw \
    --tools "*"
```

For details about the toolkit import parameters, refer to: [https://developer.watson-orchestrate.ibm.com/tools/toolkits](https://developer.watson-orchestrate.ibm.com/tools/toolkits)

## Best practices and limitations

### Creating effective MCP tools

To create effective MCP tools from your workflow exposed REST services, consider the following best practices:

1. **Design services with AI in mind**
   - Design services with natural language interaction in mind
   - Think about how users might describe the task in conversation
   - Structure inputs and outputs to facilitate smooth dialogue flow
   - Each service should have a single, clear purpose performing specific, well-defined tasks
   - Break down complex services into smaller, more manageable services

2. **Use meaningful names**
   - Choose descriptive names for your services and operations that indicate their function
   - Provide clear names and descriptions for all input and output parameters
   - Avoid generic names like "Process1" or "Service2"
   - Use action verbs when appropriate (for example, "CreateLoanApplication", "GetCustomerStatus")
   - Consider how the name appears to LLMs when tools are selected

3. **Provide detailed service descriptions**
   - Add comprehensive descriptions to your exposed REST services in workflow
   - Use clear, concise language that explains what the service does
   - Anticipate common user questions and ensure your service descriptions address them
   - Include information about required inputs and expected outputs
   - Specify valid parameter ranges and constraints
   - Include example values where helpful
   - Document any dependencies between parameters
   - These descriptions will be used by LLMs to understand when and how to use your tools
   - Example: "Allow to compute loan eligibility. This takes as parameters: age (should be between 18 and 100), income (annual income in USD), credit_score (should be between 300 and 850)"

### Asynchronous operations

The current MCP specification does not support asynchronous tools. This has important implications for workflow services. Operations with an asynchronous request-response pattern (implemented by processes or asynchronous service flows) are invoked as one-way "fire and forget" operations. The MCP server cannot wait for and return the eventual response from asynchronous operations. Design synchronous services where possible. For asynchronous processes, create separate services to check status or retrieve results.

### MCP client limitations

Some MCP clients have limitations that affect which tools can be used. There are the following known issues with IBM watsonx Orchestrate:

- **Dynamic MCP server update limitations for newly added REST services:** Watsonx Orchestrate (wxO) currently does not support updating or restarting an MCP server (toolkit) to dynamically add newly exposed REST services as tools.

   **Workaround:**

   - In the [watsonx Orchestrate documentation](https://developer.watson-orchestrate.ibm.com/tools/toolkits/manage_toolkits#updating-toolkits), you can find a description of the workaround.

   **Note:** These limitations are due to the MCP client's input handling capabilities, not the MCP server itself.

## Troubleshooting

### Common errors

Here are solutions to common issues you might encounter:

1. **Connection errors**:
   - Verify that the `ENDPOINT` is correct and accessible
   - Check network connectivity from the MCP server to the workflow server
   - Make sure that there are no firewalls or network policies blocking the connection
   - Verify that your network allows outbound connections to the workflow environment

2. **Authentication errors**:
   - For basic authentication:
     - Verify that `USERID` and `PASSWORD` are correct
   - For API key authentication:
     - Verify that `API_KEY` is correct
   - Make sure that the user has appropriate permissions to access REST services

3. **No REST services found**:
   - Verify that there is at least one process application with an exposed REST service

4. **SSL certificate issues**:
   - If you encounter SSL certificate validation errors, set `VERIFY_SSL=false`.
   - Note that disabling SSL verification is not recommended for production environments.

5. **Timeout issues**:
   - If requests are timing out, try increasing the `HTTP_TIMEOUT` value.
   - For very long-running operations, you may need to set a higher timeout value.
   - Check network latency between the MCP server and workflow environment.

6. **IBM watsonx Orchestrate import issues** (ADK method):
   - In IBM watsonx Orchestrate SaaS environment, you might need to pass a fully qualified path as package root option.
     - Example: `--package-root /path/to/ibm-baw-mcp-server` instead of `--package-root .`
   - In Windows CLI, you need to use a special path format with forward slash followed by backslash.
     - Example: `--package-root C:/\adk-project/\baw-mcp/\ibm-baw-mcp-server`

7. **IBM watsonx Orchestrate server startup issues**:
   - Check that the GitHub repository is accessible from the IBM watsonx Orchestrate environment.
   - Review the IBM watsonx Orchestrate logs for error messages.

### Viewing logs

For more detailed logging, set the `LOG_LEVEL` environment variable to `DEBUG`.

## License

This project is licensed under the [Apache License 2.0](LICENSE).
