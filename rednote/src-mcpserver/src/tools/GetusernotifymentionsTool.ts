import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";
const { httpGet } = require("../xhs-browser.js");

interface GetusernotifymentionsInput {
  count: number;
  cursor: string;
}

class GetusernotifymentionsTool extends MCPTool<GetusernotifymentionsInput> {
  name = "Get Comment-related Notifications";
  description = "Get user message notifications in the 'Comments and @' category. For example, which users have recently commented on my notes, or mentioned me in notes, can be retrieved with this tool. If the cursor parameter is empty, please pass an empty string";

  schema = {
    count: {
      type: z.number(),
      default: 20,
      description: "Amount of data to retrieve, default is 20",
    },
    cursor: {
      type: z.string(),
      default: "",
      description: "Pointer for the next page of data, this pointer is the cursor returned when the data is fetched",
    }
  };

  async execute(input: GetusernotifymentionsInput) {
    const { count, cursor } = input;
    try {
      const res = await httpGet(`/api/sns/web/v1/you/mentions?num=${count}&cursor=${cursor}`);
      return JSON.stringify(res);
    } catch (e) {
      console.error('get home.feeds error!', e);
      return 'Failed to retrieve data!';
    }
  }
}

module.exports = GetusernotifymentionsTool;