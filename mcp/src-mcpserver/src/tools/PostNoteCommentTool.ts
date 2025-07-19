// Library imports
import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";

// Local imports
const { httpPost, getJoinedTest } = require("../xhs-browser.js");

/**
 * Input interface for PostNoteCommentTool
 */
interface PostNoteCommentInput {
  note_id: string;
  content: string;
}

/**
 * Tool for posting text comments on Xiaohongshu notes
 * Provides comment interaction functionality
 */
class PostNoteCommentTool extends MCPTool<PostNoteCommentInput> {
  name = "Post Note Comment";
  description = "Post a text comment on a specified Xiaohongshu note";

  schema = {
    note_id: {
      type: z.string(),
      description: "Xiaohongshu note ID",
    },
    content: {
      type: z.string(),
      description: 'Text content of the comment to post'
    }
  };
  // isTest = true;
  // enabled() {
  //   return getJoinedTest();
  // };

  /**
   * Executes posting a comment on a note
   * @param input - Contains note_id and content
   * @returns Promise<string> - Success or error message
   */
  async execute(input: PostNoteCommentInput): Promise<string> {
    const { note_id, content } = input;
    
    // Input validation
    if (!note_id || typeof note_id !== 'string') {
      return JSON.stringify({
        error: true,
        message: 'Invalid note_id: Must be a non-empty string'
      });
    }
    
    if (!content || typeof content !== 'string' || content.trim().length === 0) {
      return JSON.stringify({
        error: true,
        message: 'Invalid content: Must be a non-empty string'
      });
    }
    
    if (content.length > 500) {
      return JSON.stringify({
        error: true,
        message: 'Content too long: Maximum 500 characters allowed'
      });
    }

    try {
      const response = await httpPost('/api/sns/web/v1/comment/post', {
        at_users: [],
        content: content.trim(),
        note_id
      });
      
      const responseStr = JSON.stringify(response);
      if (responseStr.includes('已发布')) {
        return JSON.stringify({
          success: true,
          message: 'Comment posted successfully',
          note_id: note_id,
          content: content.trim()
        });
      }
      
      return JSON.stringify({
        error: true,
        message: 'Comment posting failed',
        response: response
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      console.error('PostNoteCommentTool error:', errorMessage);
      
      return JSON.stringify({
        error: true,
        message: `Failed to post comment: ${errorMessage}`,
        note_id: note_id,
        timestamp: new Date().toISOString()
      });
    }
  }
}

module.exports = PostNoteCommentTool;