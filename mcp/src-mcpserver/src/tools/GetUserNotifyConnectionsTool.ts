import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";

const { httpGet } = require("../xhs-browser.js");

/**
 * Interface for user notify connections input parameters
 */
interface GetUserNotifyConnectionsInput {
  count: number;
  cursor: string;
}

/**
 * Tool for retrieving user message notifications in the new followers category
 * This tool allows fetching a paginated list of recent followers with configurable count and cursor
 */
class GetUserNotifyConnectionsTool extends MCPTool<GetUserNotifyConnectionsInput> {
  name = "Get New Followers List";
  description = "Get user message notifications in the new followers category. For example, which users have recently followed me can be retrieved with this tool. Two parameters are required, count and cursor. The cursor is a pointer for the next page of data, which is the cursor returned when the data is fetched. If this is the first request, please pass an empty string (all parameter names must be passed)";

  schema = {
    count: {
      type: z.number(),
      default: 20,
      description: "Amount of data to retrieve, default is 20",
    },
    cursor: {
      type: z.string(),
      default: "",
      description: "The pointer for the next page of data, which is the cursor returned when the data is fetched. If empty, the first page of data will be retrieved",
    }
  };

  /**
   * Executes the tool to fetch user notification connections
   * @param input - The input parameters containing count and cursor
   * @returns Promise<string> - JSON string of the response or error message
   */
  async execute(input: GetUserNotifyConnectionsInput): Promise<string> {
    console.log('Executing GetUserNotifyConnectionsTool');
    const { count, cursor } = input;
    
    // Validate input parameters
    if (!count || count <= 0) {
      return JSON.stringify({
        error: "Invalid count parameter. Count must be a positive number.",
        success: false
      });
    }

    // Sanitize cursor parameter to prevent injection attacks
    const sanitizedCursor = cursor ? encodeURIComponent(cursor) : "";
    
    console.log(`${this.name} - Fetching followers with count: ${count}, cursor: ${sanitizedCursor}`);
    
    try {
      // Make API request with sanitized parameters
      const response = await httpGet(`/api/sns/web/v1/you/connections?num=${count}&cursor=${sanitizedCursor}`);
      
      // Validate response structure
      if (!response) {
        return JSON.stringify({
          error: "Empty response received from API",
          success: false
        });
      }

      console.log('Successfully retrieved user notify connections');
      return JSON.stringify({
        data: response,
        success: true
      });
    } catch (error) {
      console.error('Error retrieving user notify connections:', error);
      
      // Enhanced error handling with different error types
      let errorMessage = "Failed to retrieve data";
      
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      }
      
      return JSON.stringify({
        error: errorMessage,
        success: false,
        timestamp: new Date().toISOString()
      });
    }
  }
}

module.exports = GetUserNotifyConnectionsTool;