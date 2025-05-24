import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";
const { httpGet } = require("../xhs-browser.js");


interface GetusernotifylikesInput {
  count: number;
  cursor: string;
}

class GetusernotifylikesTool extends MCPTool<GetusernotifylikesInput> {
  name = "Get Likes and Collections Notifications";
  description = "Get the current user's message notifications in the likes and collections category. For example, which users have recently liked my notes, or collected my notes, can be retrieved with this tool. If the cursor parameter is empty, please pass an empty string";

  schema = {
    count: {
      type: z.number(),
      default: 20,
      description: "Amount of data to retrieve, default is 20",
    },
    cursor: {
      type: z.string(),
      default: "",
      description: "The pointer for the next page of data, this pointer is the cursor returned when the data is fetched",
    }
  };

  async execute(input: GetusernotifylikesInput) {
    const { count, cursor } = input;
    try {
      const res = await httpGet(`/api/sns/web/v1/you/likes?num=${count}&cursor=${cursor}`);
      return JSON.stringify(res);
    } catch (e) {
      return 'Failed to retrieve data!';
    }
  }
}

module.exports = GetusernotifylikesTool;