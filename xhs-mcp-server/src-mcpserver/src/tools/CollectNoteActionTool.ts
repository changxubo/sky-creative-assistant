import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";

const { httpPost, getJoinedTest } = require("../xhs-browser.js");

/**
 * Input interface for the note collection action tool
 */
interface CollectNoteActionInput {
  note_id: string;
  collect: boolean;
}

/**
 * Tool for collecting or uncollecting Xiaohongshu notes
 * Provides functionality to manage user's note collection status
 */
class CollectNoteActionTool extends MCPTool<CollectNoteActionInput> {
  name = "Note Collection Action";
  description = "Collect or uncollect Xiaohongshu notes based on note ID";

  schema = {
    note_id: {
      type: z.string(),
      description: "Xiaohongshu note ID",
    },
    collect: {
      type: z.boolean(),
      default: true,
      description: "true to collect, false to uncollect"
    }
  };

  // Optional: Enable test mode functionality
  // isTest = true;
  // enabled() {
  //   return getJoinedTest();
  // };

  /**
   * Execute the note collection/uncollection action
   * @param input - The input parameters containing note_id and collect flag
   * @returns Promise<string> - Success or error message
   */
  async execute(input: CollectNoteActionInput): Promise<string> {
    const { note_id, collect } = input;

    // Validate input parameters
    if (!note_id || typeof note_id !== 'string') {
      return 'Failed: Invalid note_id provided';
    }

    if (!collect) {
      // Uncollect note operation
      try {
        await httpPost('/api/sns/web/v1/note/uncollect', {
          note_ids: note_id
        });
        return 'Uncollected note successfully';
      } catch (error: any) {
        // Log error for debugging while returning user-friendly message
        console.error('Uncollect operation failed:', error);
        return `Failed to uncollect note, error: ${error.message || 'Unknown error'}`;
      }
    } else {
      // Collect note operation
      try {
        await httpPost('/api/sns/web/v1/note/collect', {
          note_id
        });
        return "Collected note successfully";
      } catch (error: any) {
        // Log error for debugging while returning user-friendly message
        console.error('Collect operation failed:', error);
        return `Failed to collect note, error: ${error.message || 'Unknown error'}`;
      }
    }
  }
}

module.exports = CollectNoteActionTool;