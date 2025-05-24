import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";

const { httpPost, getJoinedTest } = require("../xhs-browser.js");
interface PostnotecommentInput {
  note_id: string;
  content: string;
}

class PostnotecommentTool extends MCPTool<PostnotecommentInput> {
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

  async execute(input: PostnotecommentInput) {
    const { note_id, content } = input;
    if (!note_id || !content) return "错误了：缺少参数";
    try {
      const res = await httpPost('/api/sns/web/v1/comment/post', {
        at_users: [],
        content,
        note_id
      });
      if (JSON.stringify(res).includes('已发布')) {
        return `评论发布成功`;
      }
      return `评论发布失败，返回信息：${JSON.stringify(res)}`;
    } catch(e: any) {
      return `评论发布错误，信息：${e.message}`;
    }
  }
}

module.exports = PostnotecommentTool;