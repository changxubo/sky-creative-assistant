import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";

const { httpGet, sleep, jsonToCsv, downloadCsvData, getJoinedTest } = require("../xhs-browser.js");

interface GetcollectnotesInput {
  user_id: string;
  count: number;
  xsec_token: string;
  download: boolean;
}

class GetcollectnotesTool extends MCPTool<GetcollectnotesInput> {
  name = "get_user_collected_notes";
  description = "Get a list of notes collected by the specified user. If the user needs to get their own account's list, please first get the current account's ID. If user ID is not specified, guide the user to provide an ID to continue. All parameters are required.";
  schema = {
    user_id: {
      type: z.string(),
      description: "User ID, 24 characters in length"
    },
    count: {
      type: z.number(),
      default: 5,
      description: "Number of notes to retrieve, default is 5. To get all notes, set the value to -1"
    },
    xsec_token: {
      type: z.string(),
      description: "xsec_token for request parameter validation, optional"
    },
    download: {
      type: z.boolean(),
      description: 'Whether to export data as a file. If the user specifically requests a download, set to true, otherwise default is false',
      default: false
    }
  };

  async execute(input: GetcollectnotesInput) {
    let { user_id, count, xsec_token, download } = input;
    const results: any[] = [];
    let cursor = '';
    while (true) {
      try {
        const res = await httpGet(`/api/sns/web/v2/note/collect/page?num=10&cursor=${cursor}&user_id=${user_id}&image_formats=jpg,webp,avif&xsec_token=${encodeURIComponent(xsec_token)}&xsec_source=pc_feed`);
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
        return 'Failed to retrieve data: ' + e.message;
      }
      if ((count !== -1) && (results.length >= count)) break;
      await sleep(2);

    }
    const result_csv = jsonToCsv(results, [
      'note_id', 'type', 'title', 'xsec_token', 'liked_count', 'cover', 
      'user_id@user.id', 'user_name@user.nick_name'
    ]);
    if (download) {
      const fileName = `user_likes_${user_id}_${count}_${+new Date}.csv`;
      const download_result = downloadCsvData(fileName, result_csv);
      return download_result['error'] ? `Failed to save data: ${download_result['error']}` : `Data saved. Count: ${results.length}. File: ${download_result.link}`;
    }
    return results;

  }
}

module.exports = GetcollectnotesTool;