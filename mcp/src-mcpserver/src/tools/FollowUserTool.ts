// Library imports
import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";

// Local imports
const { httpPost } = require("../xhs-browser.js");

/**
 * Input interface for FollowUserTool
 */
interface FollowUserInput {
  target_user_id: string;
  follow: boolean;
}

/**
 * Tool for following or unfollowing users on Xiaohongshu platform
 * Provides user relationship management functionality
 */
class FollowUserTool extends MCPTool<FollowUserInput> {
  name = "User Follow Action";
  description = "Follow or unfollow users based on user ID";

  schema = {
    target_user_id: {
      type: z.string(),
      description: "Target user ID, 24-character string",
    },
    follow: {
      type: z.boolean(),
      default: true,
      description: "true to follow, false to unfollow"
    }
  };

  /**
   * Executes user follow/unfollow action
   * @param input - Contains target_user_id and follow boolean
   * @returns Promise<string> - Success or error message
   */
  async execute(input: FollowUserInput): Promise<string> {
    const { target_user_id, follow } = input;
    
    // Input validation
    if (!target_user_id || typeof target_user_id !== 'string' || target_user_id.length !== 24) {
      return JSON.stringify({
        error: true,
        message: 'Invalid target_user_id: Must be a 24-character string'
      });
    }
    
    if (typeof follow !== 'boolean') {
      return JSON.stringify({
        error: true,
        message: 'Invalid follow parameter: Must be a boolean'
      });
    }

    try {
      if (!follow) {
        // Unfollow operation
        await httpPost('/api/sns/web/v1/user/unfollow', {
          target_user_id
        });
        return JSON.stringify({
          success: true,
          message: 'User unfollowed successfully',
          action: 'unfollow',
          target_user_id: target_user_id
        });
      } else {
        // Follow operation
        await httpPost('/api/sns/web/v1/user/follow', {
          target_user_id
        });
        return JSON.stringify({
          success: true,
          message: 'User followed successfully',
          action: 'follow',
          target_user_id: target_user_id
        });
      }
    } catch (error) {
      // Enhanced error handling
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      console.error(`FollowUserTool error (${follow ? 'follow' : 'unfollow'}):`, errorMessage);
      
      return JSON.stringify({
        error: true,
        message: `Failed to ${follow ? 'follow' : 'unfollow'} user: ${errorMessage}`,
        action: follow ? 'follow' : 'unfollow',
        target_user_id: target_user_id,
        timestamp: new Date().toISOString()
      });
    }
  }
}

module.exports = FollowUserTool;