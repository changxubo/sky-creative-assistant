import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";
const { httpPost, downloadCsvData, sleep, jsonToCsv } = require("../xhs-browser.js");

interface GethomefeedsInput {
  count: number;
  category: string;
  download: boolean;
}

class GethomefeedsTool extends MCPTool<GethomefeedsInput> {
  name = "Get Recommended Notes List";
  description = `Get the post list from Xiaohongshu website homepage。
Category data as follows (csv format)：
id,name
homefeed_recommend,Recommended
homefeed.fashion_v3,Fashion
homefeed.food_v3,Food
homefeed.cosmetics_v3,Makeup
homefeed.movie_and_tv_v3,Movies & TV
homefeed.career_v3,Career
homefeed.love_v3,Relationships
homefeed.household_product_v3,Home & Living
homefeed.gaming_v3,Gaming
homefeed.travel_v3,Travel
homefeed.fitness_v3,Fitness

Returned result (csv, type data: normal=Image and Text, video=Video)：
note_id,xsec_token,type,title,liked_count,cover,user_id,user_name,user_xsec_token

Please pass all tool parameters, default parameters are: count=10, category=homefeed_recommend, download=false`;

  schema = {
    count: {
      type: z.number(),
      default: 10,
      description: 'Number of items to retrieve, default is 10'
    },
    category: {
      type: z.string(),
      description: 'Category ID of posts, default is the recommended category',
      default: 'homefeed_recommend'
    },
    download: {
      type: z.boolean(),
      description: 'Whether to export data as a file. If the user specifically requests a download, set to true, otherwise default is false',
      default: false
    }
  };

  async execute(input: GethomefeedsInput) {
    const { count, category, download } = input;

    try {
      let cursor_score = '';
      let note_index = 0;
      // 总共获取了多少
      let loaded_count = 0;
      // 结果缓存
      let results_all: any[] = [];
      while (loaded_count < count) {
        try {
          const res = await httpPost("/api/sns/web/v1/homefeed", {
            "cursor_score": cursor_score,
            "num": 27,
            "refresh_type": 1,
            "note_index": note_index,
            "unread_begin_note_id": "",
            "unread_end_note_id": "",
            "unread_note_count": 0,
            "category": category,
            "search_key": "",
            "need_num": 12,
            "image_formats": [
              "jpg",
              "webp",
              "avif"
            ],
            "need_filter_image": false
          });
          res['items'].map((item: Array<any>) => {
            if (loaded_count >= count) return;
            results_all.push(item);
            loaded_count++;
          })
          if (loaded_count >= count) break;
          cursor_score = res['cursor_score'];
          note_index = res['items'].length;
          await sleep(2);
        } catch (e) {
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
        const fileName = `${category}_${count}_${+new Date}.csv`;
        const download_result = downloadCsvData(fileName, result_csv);
        return download_result['error'] ? `数据保存失败：${download_result['error']}` : `数据已保存。条数：${results_all.length}。文件：${download_result.link}`;
      }
      return result_csv;
    } catch (e: any) {
      return '获取数据列表失败了！错误信息：' + e.message;
    }
  }
}

module.exports = GethomefeedsTool;