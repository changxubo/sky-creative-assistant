import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";
const { httpPost } = require("../xhs-browser.js");

interface FollowuserInput {
  target_user_id: string;
  follow: boolean;
}

class FollowuserTool extends MCPTool<FollowuserInput> {
  name = "user_follow_action";
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

  async execute(input: FollowuserInput) {
    const { target_user_id, follow } = input;
    if (!follow) {
      // Unfollow
      try {
        await httpPost('/api/sns/web/v1/user/unfollow', {
          target_user_id
        });
        return 'Unfollowed user successfully';
      } catch(e: any) {
        return `Failed to unfollow, error message: ${e.message}`;
      }
    } else {
      // Follow
      try {
        await httpPost('/api/sns/web/v1/user/follow', {
          target_user_id
        });
        return "Followed user successfully";
      } catch(e: any) {
        return `Failed to follow, error message: ${e.message}`
      }
    }
  }
}

module.exports = FollowuserTool;