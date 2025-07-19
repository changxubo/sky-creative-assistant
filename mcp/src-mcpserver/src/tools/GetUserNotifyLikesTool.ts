import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";

const { httpGet } = require("../xhs-browser.js");

/**
 * Interface for user notification likes input parameters
 */
interface GetUserNotifyLikesInput {
  count: number;
  cursor: string;
}

/**
 * Tool for retrieving user's likes and collections notifications
 *
 * This tool fetches notifications about users who have liked or collected
 * the current user's notes. It supports pagination through cursor-based navigation.
 *
 * @example
 * ```typescript
 * const tool = new GetUserNotifyLikesTool();
 * const result = await tool.execute({ count: 20, cursor: "" });
 * ```
 */
class GetUserNotifyLikesTool extends MCPTool<GetUserNotifyLikesInput> {
  name = "Get Likes and Collections Notifications";
  description =
    "Get the current user's message notifications in the likes and collections category. For example, which users have recently liked my notes, or collected my notes, can be retrieved with this tool. If the cursor parameter is empty, please pass an empty string";

  schema = {
    count: {
      type: z.number(),
      default: 20,
      description: "Amount of data to retrieve, default is 20",
    },
    cursor: {
      type: z.string(),
      default: "",
      description:
        "The pointer for the next page of data, this pointer is the cursor returned when the data is fetched",
    },
  };

  /**
   * Executes the user notification likes retrieval
   *
   * @param input - The input parameters containing count and cursor
   * @param input.count - Number of notifications to retrieve (default: 20)
   * @param input.cursor - Pagination cursor for next page (empty string for first page)
   * @returns Promise<string> - JSON stringified response or error message
   *
   * @throws {Error} When API request fails or network issues occur
   */
  async execute(input: GetUserNotifyLikesInput): Promise<string> {
    const { count, cursor } = input;

    try {
      // Validate input parameters
      if (count <= 0) {
        throw new Error("Count must be a positive number");
      }

      if (count > 100) {
        throw new Error("Count cannot exceed 100 to prevent API rate limiting");
      }

      // Make API request with proper error handling
      const response = await httpGet(
        `/api/sns/web/v1/you/likes?num=${count}&cursor=${encodeURIComponent(
          cursor
        )}`
      );

      // Validate response structure
      if (!response) {
        throw new Error("Empty response received from API");
      }

      return JSON.stringify(response);
    } catch (error) {
      // Enhanced error handling with detailed logging
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error occurred";
      console.error(
        `GetUserNotifyLikesTool execution failed: ${errorMessage}`,
        {
          input,
          timestamp: new Date().toISOString(),
        }
      );

      // Return structured error response instead of generic message
      return JSON.stringify({
        error: true,
        message: `Failed to retrieve likes and collections notifications: ${errorMessage}`,
        timestamp: new Date().toISOString(),
      });
    }
  }
}

module.exports = GetUserNotifyLikesTool;