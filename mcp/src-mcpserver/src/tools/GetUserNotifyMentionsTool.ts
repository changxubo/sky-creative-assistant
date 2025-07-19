import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";

const { httpGet } = require("../xhs-browser.js");

/**
 * Input interface for GetUserNotifyMentionsTool
 */
interface GetUserNotifyMentionsInput {
  count: number;
  cursor: string;
}

/**
 * API response structure for user notification mentions
 */
interface NotificationMentionsResponse {
  data?: any;
  cursor?: string;
  hasMore?: boolean;
}

/**
 * Tool for retrieving user notification mentions from the 'Comments and @' category
 *
 * This tool allows fetching notifications about:
 * - Users who have recently commented on notes
 * - Users who have mentioned the current user in notes
 *
 * @example
 * ```typescript
 * const tool = new GetUserNotifyMentionsTool();
 * const result = await tool.execute({ count: 20, cursor: "" });
 * ```
 */
class GetUserNotifyMentionsTool extends MCPTool<GetUserNotifyMentionsInput> {
  name = "Get Comment-related Notifications";
  description =
    "Get user message notifications in the 'Comments and @' category. For example, which users have recently commented on my notes, or mentioned me in notes, can be retrieved with this tool. If the cursor parameter is empty, please pass an empty string";

  schema = {
    count: {
      type: z.number().min(1).max(100), // Add validation constraints
      default: 20,
      description: "Amount of data to retrieve, default is 20, maximum 100",
    },
    cursor: {
      type: z.string(),
      default: "",
      description:
        "Pointer for the next page of data, this pointer is the cursor returned when the data is fetched",
    },
  };

  /**
   * Execute the tool to fetch user notification mentions
   *
   * @param input - The input parameters containing count and cursor
   * @returns Promise<string> - JSON stringified response or error message
   *
   * @throws {Error} When API request fails or returns invalid data
   */
  async execute(input: GetUserNotifyMentionsInput): Promise<string> {
    const { count, cursor } = input;

    try {
      // Input validation
      if (count <= 0 || count > 100) {
        return JSON.stringify({
          error: "Invalid count parameter. Must be between 1 and 100.",
        });
      }

      // Sanitize cursor parameter to prevent injection attacks
      const sanitizedCursor = cursor.replace(/[^a-zA-Z0-9_-]/g, "");

      // Make API request with proper error handling
      const response: NotificationMentionsResponse = await httpGet(
        `/api/sns/web/v1/you/mentions?num=${count}&cursor=${sanitizedCursor}`
      );

      // Validate response structure
      if (!response || typeof response !== "object") {
        console.error("Invalid API response structure:", response);
        return JSON.stringify({ error: "Invalid response format from API" });
      }

      return JSON.stringify(response);
    } catch (error) {
      // Enhanced error logging with more context
      console.error("Failed to retrieve user notification mentions:", {
        error: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
        input: { count, cursor: cursor.substring(0, 50) + "..." }, // Log truncated cursor for debugging
      });

      // Return structured error response
      return JSON.stringify({
        error: "Failed to retrieve notification mentions data",
        details: error instanceof Error ? error.message : "Unknown error occurred",
      });
    }
  }
}

module.exports = GetUserNotifyMentionsTool;