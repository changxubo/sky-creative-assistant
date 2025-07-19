import { MCPTool } from "@aicu/mcp-framework";

const { httpGet } = require("../xhs-browser.js");

/**
 * Input interface for GetUserAccountInfoTool
 * Currently empty as no input parameters are required
 */
interface GetUserAccountInfoInput {}

/**
 * Response interface for user account information
 */
interface UserAccountResponse {
  user: any;
  moreinfo: any;
}

/**
 * Tool for retrieving current user account details from the social media platform
 * 
 * This tool fetches comprehensive user information including:
 * - Basic profile data (nickname, ID, avatar)
 * - Follower statistics and engagement metrics
 * - Account settings and preferences
 * 
 * @extends MCPTool<GetUserAccountInfoInput>
 */
class GetUserAccountInfoTool extends MCPTool<GetUserAccountInfoInput> {
  name = "Get Current Account Details";
  description = "Get detailed data for the current account, including nickname, ID, avatar, follower data, etc.";

  schema = {};

  /**
   * Executes the user account information retrieval
   * 
   * Makes parallel API calls to fetch user data from multiple endpoints:
   * - /api/sns/web/v2/user/me: Basic user profile information
   * - /api/sns/web/v1/user/selfinfo: Extended user information and statistics
   * 
   * @param input - Empty input object (no parameters required)
   * @returns Promise<string> - JSON stringified user data or error message
   * 
   * @throws {Error} When API calls fail or user is not authenticated
   */
  async execute(input: GetUserAccountInfoInput): Promise<string> {
    try {
      // Validate that we have necessary authentication context
      if (!httpGet) {
        throw new Error('HTTP client not available - authentication may be required');
      }

      // Fetch user data from multiple endpoints concurrently for better performance
      const [userProfileResponse, userExtendedInfoResponse] = await Promise.all([
        httpGet('/api/sns/web/v2/user/me'),
        httpGet('/api/sns/web/v1/user/selfinfo')
      ]);

      // Validate API responses
      if (!userProfileResponse || !userExtendedInfoResponse) {
        throw new Error('Invalid response from user information API');
      }

      const userAccountData: UserAccountResponse = {
        user: userProfileResponse,
        moreinfo: userExtendedInfoResponse
      };

      return JSON.stringify(userAccountData, null, 2);
    } catch (error) {
      // Enhanced error handling with proper typing
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      
      // Log error for debugging (in production, use proper logging service)
      console.error('GetUserAccountInfoTool execution failed:', {
        error: errorMessage,
        timestamp: new Date().toISOString(),
        tool: this.name
      });

      return `Failed to retrieve user account information: ${errorMessage}`;
    }
  }
}

export default GetUserAccountInfoTool;