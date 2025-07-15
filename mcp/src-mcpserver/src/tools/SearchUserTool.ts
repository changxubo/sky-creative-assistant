import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";

const { httpPost, sleep, downloadCsvData, jsonToCsv } = require("../xhs-browser.js");

const createSearchId = () => {
  const F = () => {
      var timestamp = new Date().getTime().toString();
      if (timestamp.length < 13) {
        timestamp = timestamp.padEnd(13, "0");
      }
      return timestamp
  };
  const J = () => {
      var e;
      var t = BigInt(F())
        , r = BigInt(Math.ceil(2147483646 * Math.random()));
      return t <<= BigInt(64),
      (t += r).toString(36)
  };
  return J();
}

interface SearchuserInput {
  keyword: string;
  // page: number;
  // pageSize: number;
  count: number;
  download: boolean;
}

class SearchuserTool extends MCPTool<SearchuserInput> {
  name = "Search Xiaohongshu Users";
  description = "Search for specific users based on keywords. The returned data may include multiple results, which can be filtered by criteria such as verification status or follower count to help users select an appropriate account. If there are multiple similar results, please remind the user to choose one. The xsec_token in the returned data is very important and may need to be passed to the next tool call";

  schema = {
    keyword: {
      type: z.string(),
      description: 'Keyword for the username to search'
    },
    count: {
      type: z.number(),
      default: 5,
      description: 'The amount of data to be retrieved, default is 5'
    },
    download: {
      type: z.boolean(),
      description: 'Whether to download and export data as a file. If the user specifically requests a download, it will be true, otherwise, the default is false',
      default: false
    }
    // page: {
    //   type: z.number(),
    //   default: 1,
    //   description: 'The page number of the data to be retrieved, default is the 1st page'
    // },
    // pageSize: {
    //   type: z.number().min(1).max(20),
    //   default: 1,
    //   description: 'The amount of user data per page to be retrieved, default is 1 (between 1-20)'
    // }
  };

  async execute(input: SearchuserInput) {
    const { keyword, count, download } = input;
    try {
      const searchId = createSearchId();
      let current_page = 1;
      const pageSize = 20;
      const results_all: any[] = [];
      let loaded_count = 0;

      while (loaded_count < count) {
        try {
          const res = await httpPost('/api/sns/web/v1/search/usersearch', {
            "search_user_request": {
                "keyword": keyword,
                "search_id": searchId,
                "page": current_page,
                "page_size": pageSize,
                "biz_type": "web_search_user",
                "request_id": Math.random().toString().slice(2, 11) + "-" + new Date().getTime()
            }
          })
          if (!res['result'] || !res['result']['success']) throw new Error(JSON.stringify(res['result'] || res));
          // @ts-ignore
          res['users'].map(user => {
            if (loaded_count >= count) return;
            results_all.push(user);
            loaded_count ++;
          });
          if (loaded_count >= count) break;
          current_page += 1;
          await sleep(2);
        } catch(e) {
          // @ts-ignore
          return 'Failed to search user data: ' + e.message;
        }
      }

      // const dataKeys = [
      //   'id', 'image', 'avatar', 'xsecToken', 
      //   'profession', 'subTitle',
      //   'fans', 'noteCount', 'updateTime',
      // ];
      const result_csv = jsonToCsv(results_all, [
        'user_id@id',
        'xsec_token@xsecToken',
        'avatar@avatar',
        'image@image',
        'profession@profession',
        'sub_title@subTitle',
        'fans@fans',
        'note_count@noteCount',
        'updateTime@updateTime'
      ]);
      if (download) {
        const fileName = `search_users_${encodeURIComponent(keyword)}_${count}_${+new Date}.csv`;
        const download_result = downloadCsvData(fileName, result_csv);
        return download_result['error'] ? `Failed to save data: ${download_result['error']}` : `Data saved. Count: ${results_all.length}. File: ${download_result.link}`;
      }
      return result_csv;
    } catch(e) {
      // @ts-ignore
      return 'Failed to search user data: ' + e.message;
    }
  }
}

module.exports = SearchuserTool;