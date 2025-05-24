import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";
const { httpPost, getJoinedTest } = require("../xhs-browser.js");

interface LikenoteacionInput {
  note_id: string;
  like: boolean;
}

class LikenoteacionTool extends MCPTool<LikenoteacionInput> {
  name = "like_note_action";
  description = "Like or unlike Xiaohongshu notes based on note ID";

  schema = {
    note_id: {
      type: z.string(),
      description: "Xiaohongshu note ID",
    },
    like: {
      type: z.boolean(),
      default: true,
      description: "true to like, false to unlike"
    }
  };
  // isTest = true;
  // enabled() {
  //   return getJoinedTest();
  // };
  async execute(input: LikenoteacionInput) {
    const { note_id, like } = input;
    if (!like) {
      // Unlike
      try {
        await httpPost('/api/sns/web/v1/note/dislike', {
          note_oid: note_id
        });
        return 'Unliked note successfully';
      } catch(e: any) {
        return `Failed to unlike, error message: ${e.message}`;
      }
    } else {
      // Like
      try {
        await httpPost('/api/sns/web/v1/note/like', {
          note_oid: note_id
        })
        return "Liked note successfully";
      } catch(e: any) {
        return `Failed to like, error message: ${e.message}`
      }
    }
  }
}

module.exports = LikenoteacionTool;