import { MCPTool } from "@aicu/mcp-framework";
const { httpGet } = require("../xhs-browser.js");

/**
 * Input interface for GetMyInfoTool
 * Currently no input parameters required
 */
interface GetMyInfoInput {}

/**
 * Tool for retrieving current user account information from XHS (RedNote) platform
 * Fetches comprehensive user data including profile, stats, and additional metadata
 */
class GetMyInfoTool extends MCPTool<GetMyInfoInput> {
  /**
   * Tool identifier for MCP framework
   */
  name = "get_current_account";
  
  /**
   * Human-readable description of tool functionality
   */
  description = "Get detailed data for the current account, including nickname, ID, avatar, follower data, etc.";

  /**
   * Input schema validation (no parameters required)
   */
  schema = {};

  /**
   * Executes the tool to retrieve current user account information
   * @param input - Empty input object (no parameters required)
   * @returns Promise<string> - JSON string containing user data or error message
   */
  async execute(input: GetMyInfoInput): Promise<string> {
    try {
      // Fetch basic user profile information
      const userProfileResponse = await httpGet('/api/sns/web/v2/user/me');
      
      // Fetch additional user metadata and statistics
      const userDetailResponse = await httpGet('/api/sns/web/v1/user/selfinfo');
      
      // Return combined user data as JSON string
      return JSON.stringify({
        user: userProfileResponse,
        moreinfo: userDetailResponse
      });
    } catch (error) {
      // Type-safe error handling
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      return `Failed to get user data: ${errorMessage}`;
    }
  }
}

module.exports = GetMyInfoTool;