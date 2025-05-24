import { MCPTool } from "@aicu/mcp-framework";
const { httpGet } = require("../xhs-browser.js");

interface GetselfinfoInput {}

class GetselfinfoTool extends MCPTool<GetselfinfoInput> {
  name = "Get Current Account Details";
  description = "Get detailed data for the current account, including nickname, ID, avatar, follower data, etc.";

  schema = {};

  async execute(input: GetselfinfoInput) {
    try {
      const res1 = await httpGet('/api/sns/web/v2/user/me');
      const res2 = await httpGet(`/api/sns/web/v1/user/selfinfo`);
      return JSON.stringify({
        user: res1,
        moreinfo: res2
      });
    } catch (e) {
      // @ts-ignore
      return 'Failed to get user data: ' + e.message;
    }
  }
}

module.exports = GetselfinfoTool;