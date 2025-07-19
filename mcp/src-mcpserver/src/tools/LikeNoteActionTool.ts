// Library imports
import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";

// Local imports
const { httpPost, getJoinedTest } = require("../xhs-browser.js");

/**
 * Input interface for like/unlike note actions
 */
interface LikeNoteActionInput {
  note_id: string;
  like: boolean;
}

/**
 * Tool for performing like/unlike actions on Xiaohongshu notes
 * Provides functionality to like or unlike notes based on note ID
 */
class LikeNoteActionTool extends MCPTool<LikeNoteActionInput> {
  name = "like_note_action";
  description = "Like or unlike Xiaohongshu notes based on note ID";

  schema = {
    note_id: {
      type: z.string(),
      description: "Xiaohongshu note ID - unique identifier for the note",
    },
    like: {
      type: z.boolean(),
      default: true,
      description: "true to like the note, false to unlike the note"
    }
  };
  
  // TODO: Enable test mode when testing functionality
  // isTest = true;
  // enabled() {
  //   return getJoinedTest();
  // };

  /**
   * Executes the like/unlike action for a Xiaohongshu note
   * @param input - Contains note_id and like boolean flag
   * @returns Promise<string> - Success or error message
   */
  async execute(input: LikeNoteActionInput): Promise<string> {
    const { note_id, like } = input;
    
    // Validate input parameters
    if (!note_id || typeof note_id !== 'string' || note_id.trim() === '') {
      throw new Error('Invalid note_id: must be a non-empty string');
    }
    
    if (!like) {
      // Unlike operation
      try {
        await httpPost('/api/sns/web/v1/note/dislike', {
          note_oid: note_id
        });
        return `Successfully unliked note with ID: ${note_id}`;
      } catch (error: any) {
        // Log error for debugging purposes
        console.error(`Failed to unlike note ${note_id}:`, error);
        return `Failed to unlike note: ${error?.message || 'Unknown error occurred'}`;
      }
    } else {
      // Like operation
      try {
        await httpPost('/api/sns/web/v1/note/like', {
          note_oid: note_id
        });
        return `Successfully liked note with ID: ${note_id}`;
      } catch (error: any) {
        // Log error for debugging purposes
        console.error(`Failed to like note ${note_id}:`, error);
        return `Failed to like note: ${error?.message || 'Unknown error occurred'}`;
      }
    }
  }
}

module.exports = LikeNoteActionTool;