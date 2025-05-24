import { MCPTool } from "@aicu/mcp-framework";
import { object, z } from "zod";

const { httpGet, sleep, jsonToCsv, downloadCsvData } = require("../xhs-browser.js");

interface GetuserpostsInput {
  user_id: string;
  count: number;
  xsec_token: string;
  download: boolean;
}

class GetuserpostsTool extends MCPTool<GetuserpostsInput> {
  name = "get_user_posts";
  description = "Get the list of published notes for a specified user. All parameters are required.";

  schema = {
    user_id: {
      type: z.string(),
      description: "User ID, not the Xiaohongshu ID, 24 characters in length"
    },
    count: {
      type: z.number(),
      default: 5,
      description: "The number of notes to retrieve, default is 5. Use -1 to retrieve all."
    },
    xsec_token: {
      type: z.string(),
      description: "The xsec_token for request parameter verification, this is required."
    },
    // cursor: {
    //   type: z.string(),
    //   default: "",
    //   description: "The pointer for the next page of data, provided by the cursor in the response of the request."
    // },
    download: {
      type: z.boolean(),
      description: 'Whether to download and export data as a file. Set to true if the user explicitly requests a download, otherwise defaults to false.',
      default: false
    }
  };

  async execute(input: GetuserpostsInput) {
    let { user_id, count, xsec_token, download } = input;
    const results: any[] = [];
    let cursor = '';
    while (true) {
      try {
        const res = await httpGet(`/api/sns/web/v1/user_posted?num=10&cursor=${cursor}&user_id=${user_id}&image_formats=jpg,webp,avif&xsec_token=${encodeURIComponent(xsec_token)}&xsec_source=pc_feed`);
        if (!res['notes'] || res['notes'].length === 0) break;
        // @ts-ignore
        res['notes'].map(note => {
          if ((count > 0 ) && (results.length >= count)) return;
          results.push({
            note_id: note['noteId'],
            title: note['displayTitle'],
            type: note['type'],
            user: {
              id: note['user']['userId'],
              nick_name: note['user']['nickName']
            },
            xsec_token: note['xsecToken'],
            liked_count: note['interactInfo']['likedCount'],
            cover: note['cover']['urlPre']
          })
        });
        if (!res['hasMore']) break;
        cursor = res['cursor'];
      } catch (e) {
        // @ts-ignore
        return 'Failed to get user data: ' + e.message;
      }
      if ((count !== -1) && (results.length >= count)) break;
      await sleep(2);

    }
    const result_csv = jsonToCsv(results, [
      'note_id', 'type', 'title', 'xsec_token', 'liked_count', 'cover', 
      'user_id@user.id', 'user_name@user.nick_name'
    ]);
    if (download) {
      const fileName = `user_posts_${user_id}_${count}_${+new Date}.csv`;
      const download_result = downloadCsvData(fileName, result_csv);
      return download_result['error'] ? `Failed to save data: ${download_result['error']}` : `Data saved. Count: ${results.length}. File: ${download_result.link}`;
    }
    return results;

  }
}

module.exports = GetuserpostsTool;