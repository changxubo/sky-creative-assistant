from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MCPServerMetadataRequest(BaseModel):
    """
    Request model for MCP (Model Context Protocol) server metadata.

    This class represents a request to retrieve metadata information from an MCP server.
    It supports both stdio and SSE (Server-Sent Events) transport types.

    Attributes:
        transport: The type of MCP server connection ('stdio' or 'sse')
        command: The command to execute for stdio transport type
        args: Command arguments for stdio transport type
        url: The URL of the SSE server for sse transport type
        env: Environment variables to be passed to the server
        timeout_seconds: Custom timeout in seconds for the operation
    """

    transport: str = Field(
        ...,
        description="The type of MCP server connection (stdio or sse)",
        pattern="^(stdio|sse)$",  # Validation to ensure only valid transport types
    )
    command: Optional[str] = Field(
        None, description="The command to execute (required for stdio transport type)"
    )
    args: Optional[List[str]] = Field(
        None, description="Command arguments (used with stdio transport type)"
    )
    url: Optional[str] = Field(
        None, description="The URL of the SSE server (required for sse transport type)"
    )
    env: Optional[Dict[str, str]] = Field(
        None, description="Environment variables to be passed to the MCP server"
    )
    timeout_seconds: Optional[int] = Field(
        None,
        description="Optional custom timeout in seconds for the operation",
        gt=0,  # Validation to ensure positive timeout values
    )

    def validate_transport_requirements(self) -> None:
        """
        Validate that required fields are present based on transport type.

        Raises:
            ValueError: If required fields are missing for the specified transport type
        """
        if self.transport == "stdio" and not self.command:
            raise ValueError("Command is required for stdio transport type")
        elif self.transport == "sse" and not self.url:
            raise ValueError("URL is required for sse transport type")

class MCPTool(BaseModel):
    """
    Represents a tool available from an MCP server.

    Attributes:
        name: The name of the tool
        description: A brief description of what the tool does
        inputSchema: The schema defining the input parameters for the tool
    """

    name: str = Field(..., description="The name of the tool")
    description: str = Field(..., description="A brief description of the tool's functionality")
    inputSchema: Dict[str, Any] = Field(
        ..., description="The schema defining the input parameters for the tool"
    )

class MCPServerMetadataResponse(BaseModel):
    """
    Response model for MCP (Model Context Protocol) server metadata.

    This class represents the response containing metadata information from an MCP server,
    including the server configuration and available tools.

    Attributes:
        transport: The type of MCP server connection used
        command: The command executed (for stdio transport)
        args: Command arguments used (for stdio transport)
        url: The URL of the SSE server (for sse transport)
        env: Environment variables used by the server
        tools: List of available tools provided by the MCP server
    """

    transport: str = Field(
        ..., description="The type of MCP server connection (stdio or sse)"
    )
    command: Optional[str] = Field(
        None, description="The command executed (for stdio transport type)"
    )
    args: Optional[List[str]] = Field(
        None, description="Command arguments used (for stdio transport type)"
    )
    url: Optional[str] = Field(
        None, description="The URL of the SSE server (for sse transport type)"
    )
    env: Optional[Dict[str, str]] = Field(
        None, description="Environment variables used by the MCP server"
    )
    tools: List = Field(
        default_factory=list,
        description="List of available tools provided by the MCP server",
    )

    def get_tool_count(self) -> int:
        """
        Get the number of available tools.

        Returns:
            int: The number of tools available from the MCP server
        """
        return len(self.tools)

    def get_tool_names(self) -> List[str]:
        """
        Extract tool names from the tools list.

        Returns:
            List[str]: List of tool names, or empty list if no tools available
        """
        return [tool.get("name", "") for tool in self.tools if isinstance(tool, dict)]
