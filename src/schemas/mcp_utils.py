import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

logger = logging.getLogger(__name__)


async def _get_tools_from_client_session(
    client_context_manager: Any, timeout_seconds: int = 10
) -> List:
    """
    Helper function to get tools from a Model Context Protocol (MCP) client session.

    This function establishes a connection to an MCP server through a client context manager,
    initializes the session, and retrieves the available tools.

    Args:
        client_context_manager (Any): A context manager that returns (read, write) functions
                                    for communicating with the MCP server
        timeout_seconds (int, optional): Timeout in seconds for the read operation.
                                       Defaults to 10 seconds.

    Returns:
        List: A list of available tools from the MCP server

    Raises:
        Exception: If there's an error during connection establishment, session initialization,
                  or tool retrieval process
    """
    try:
        async with client_context_manager as (read, write):
            # Create client session with specified timeout
            async with ClientSession(
                read, write, read_timeout_seconds=timedelta(seconds=timeout_seconds)
            ) as session:
                # Initialize the connection to the MCP server
                await session.initialize()

                # Retrieve available tools from the server
                listed_tools = await session.list_tools()
                return listed_tools.tools

    except Exception as e:
        logger.error(f"Failed to retrieve tools from MCP client session: {str(e)}")
        raise


async def load_mcp_tools(
    server_type: str,
    command: Optional[str] = None,
    args: Optional[List[str]] = None,
    url: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout_seconds: int = 60,  # Longer default timeout for first-time executions
) -> List:
    """
    Load tools from a Model Context Protocol (MCP) server.

    This function supports two types of MCP server connections:
    1. stdio: Standard input/output based connection using command execution
    2. sse: Server-Sent Events based connection using HTTP URLs

    Args:
        server_type (str): The type of MCP server connection. Must be either "stdio" or "sse"
        command (Optional[str]): The command to execute (required for stdio type).
                               Should be the path to the executable or command name.
        args (Optional[List[str]]): Command line arguments to pass to the command
                                  (used with stdio type only)
        url (Optional[str]): The URL of the SSE server (required for sse type).
                           Should be a valid HTTP/HTTPS URL.
        env (Optional[Dict[str, str]]): Environment variables to set when executing
                                      the command (used with stdio type only)
        timeout_seconds (int, optional): Timeout in seconds for server operations.
                                       Defaults to 60 for first-time executions.

    Returns:
        List: A list of available tools from the MCP server

    Raises:
        HTTPException:
            - 400: If required parameters are missing or server_type is unsupported
            - 500: If there's an error loading the tools from the server
    """
    # Validate server type early
    if server_type not in ["stdio", "sse"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported server type: {server_type}. Must be 'stdio' or 'sse'",
        )

    try:
        if server_type == "stdio":
            # Validate required parameters for stdio connection
            if not command:
                raise HTTPException(
                    status_code=400, detail="Command is required for stdio type"
                )

            # Create server parameters for stdio connection
            server_params = StdioServerParameters(
                command=command,  # Executable path or command
                args=args or [],  # Command line arguments (empty list if None)
                env=env,  # Environment variables (can be None)
            )

            # Get tools using stdio client
            return await _get_tools_from_client_session(
                stdio_client(server_params), timeout_seconds
            )

        elif server_type == "sse":
            # Validate required parameters for SSE connection
            if not url:
                raise HTTPException(
                    status_code=400, detail="URL is required for sse type"
                )

            # Get tools using SSE client
            return await _get_tools_from_client_session(
                sse_client(url=url), timeout_seconds
            )

    except HTTPException:
        # Re-raise HTTPExceptions as-is to preserve status codes
        raise
    except Exception as e:
        # Log unexpected errors and convert to HTTPException
        logger.exception(f"Error loading MCP tools from {server_type} server: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load tools from {server_type} server: {str(e)}",
        )
