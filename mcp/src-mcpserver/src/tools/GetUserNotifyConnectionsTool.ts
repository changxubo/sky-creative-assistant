import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";
const { httpGet } = require("../xhs-browser.js");

interface GetusernotifyconnectionsInput {
  count: number;
  cursor: string;
}

class GetusernotifyconnectionsTool extends MCPTool<GetusernotifyconnectionsInput> {
  name = "Get New Followers List";
  description = "Get user message notifications in the new followers category. For example, which users have recently followed me can be retrieved with this tool. Two parameters are required, count and cursor. The cursor is a pointer for the next page of data, which is the cursor returned when the data is fetched. If this is the first request, please pass an empty string (all parameter names must be passed)";

  schema = {
    count: {
      type: z.number(),
      default: 20,
      description: "Amount of data to retrieve, default is 20",
    },
    cursor: {
      type: z.string(),
      default: ' ',
      description: "The pointer for the next page of data, which is the cursor returned when the data is fetched. If empty, the first page of data will be retrieved",
    }
  };

  async execute(input: GetusernotifyconnectionsInput) {
    console.log('start')
    const { count, cursor } = input;
    console.log(this.name, input, cursor)
    try {
      const res = await httpGet(`/api/sns/web/v1/you/connections?num=${count}&cursor=${cursor}`);
      console.log('ok', res)
      return JSON.stringify(res);
    } catch (e) {
      console.log('err', e)
      // @ts-ignore
      return 'Failed to retrieve data: ' + e.message;
    }
  }
}

module.exports = GetusernotifyconnectionsTool;