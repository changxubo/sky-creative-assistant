import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";

const { httpPost, jsonToCsv, sleep, downloadCsvData } = require("../xhs-browser.js");

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

interface SearchnotesInput {
  keyword: string;
  // page: number;
  count: number;
  // pageSize: number;
  sort: string; // popularity_descending = most popular, time_descending=newest; general=comprehensive sorting
  noteType: number; // 0 = all, 1 = video; 2=image and text
  download: boolean;
}

class SearchnotesTool extends MCPTool<SearchnotesInput> {
  name = "Search Xiaohongshu Notes";
  description = `Search for relevant Xiaohongshu notes based on keywords. Note type (note_type) options are:
0 All types
1 Video notes
2 Image and text notes
Search results can be sorted using one of the following sort options:
general Comprehensive sorting
time_descending Newest sorting
popularity_descending Most popular sorting
  `;

  schema = {
    keyword: {
      type: z.string(),
      description: "Keyword to search for notes",
    },
    count: {
      type: z.number(),
      default: 20,
      description: 'Amount of data to retrieve, default is 20'
    },
    sort: {
      type: z.enum(['general', 'time_descending', 'popularity_descending']),
      default: 'general',
      description: 'Search result sorting rule'
    },
    noteType: {
      type: z.number(),
      default: 0,
      description: 'Type of notes to search for'
    },
    download: {
      type: z.boolean(),
      description: 'Whether to export data as a file. If the user specifically requests a download, set to true, otherwise default is false',
      default: false
    }
  };

  async execute(input: SearchnotesInput) {
    const {
      keyword, count, sort, noteType, download
    } = input;
    try {
      const searchId = createSearchId();
      let loaded_count = 0;
      let current_page = 1;
      const results_all: any[] = [];
      while (loaded_count < count) {
        try {
          const res = await httpPost('/api/sns/web/v1/search/notes', {
            "keyword": keyword,
            "page": current_page,
            "page_size": 20,
            "search_id": searchId,
            "sort": sort,
            "note_type": noteType,
            "ext_flags": [],
            "filters": [
              {
                "tags": [
                  "general"
                ],
                "type": "sort_type"
              },
              {
                "tags": [
                  "不限"
                ],
                "type": "filter_note_type"
              },
              {
                "tags": [
                  "不限"
                ],
                "type": "filter_note_time"
              },
              {
                "tags": [
                  "不限"
                ],
                "type": "filter_note_range"
              },
              {
                "tags": [
                  "不限"
                ],
                "type": "filter_pos_distance"
              }
            ],
            "geo": "",
            "image_formats": [
              "jpg",
              "webp",
              "avif"
            ]
          });
          // @ts-ignore
          res['items'].map((item) => {
            if (loaded_count >= count) return;
            // 过滤
            if (item['modelType'] !== 'note') return;
            results_all.push(item);
            loaded_count++;
          })
          if (loaded_count >= count) break;
          current_page++;
          await sleep(2);
        } catch (e) {
          // @ts-ignore
          return `Failed to search notes data: ${e.message}`;
          break;
        }
      }

      const result_csv = jsonToCsv(results_all, [
        'note_id@id',
        'xsec_token@xsecToken',
        'note_type@noteCard.type',
        'title@noteCard.displayTitle',
        'liked_count@noteCard.interactInfo.likedCount',
        'cover@noteCard.cover.urlPre',
        'user_id@noteCard.user.userId',
        'user_name@noteCard.user.nickname',
        'user_xsec_token@noteCard.user.xsecToken'
      ]);
      if (download) {
        const fileName = `search_notes_${encodeURIComponent(keyword)}_${count}_${+new Date}.csv`;
        const download_result = downloadCsvData(fileName, result_csv);
        return download_result['error'] ? `Failed to save data: ${download_result['error']}` : `Data saved. Count: ${results_all.length}. File: ${download_result.link}`;
      }
      return result_csv;
    } catch (e) {
      // @ts-ignore
      return 'Failed to search notes data: ' + e.message;
    }
  }
}

module.exports = SearchnotesTool;