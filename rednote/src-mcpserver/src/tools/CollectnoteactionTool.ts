import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";
const { httpPost, getJoinedTest } = require("../xhs-browser.js");

interface CollectnoteactionInput {
  note_id: string;
  collect: boolean;
}

class CollectnoteactionTool extends MCPTool<CollectnoteactionInput> {
  name = "note_collection_action";
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
  // isTest = true;
  // enabled() {
  //   return getJoinedTest();
  // };
  async execute(input: CollectnoteactionInput) {
    const { note_id, collect } = input;
    if (!collect) {
      // Uncollect
      try {
        await httpPost('/api/sns/web/v1/note/uncollect', {
          note_ids: note_id
        });
        return 'Uncollected note successfully';
      } catch(e: any) {
        return `Failed to uncollect, error message: ${e.message}`;
      }
    } else {
      // Collect
      try {
        await httpPost('/api/sns/web/v1/note/collect', {
          note_id
        });
        return "Collected note successfully";
      } catch(e: any) {
        return `Failed to collect, error message: ${e.message}`
      }
    }
  }
}

module.exports = CollectnoteactionTool;