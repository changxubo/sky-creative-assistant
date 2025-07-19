import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";

const { httpPost, downloadCsvData, sleep, jsonToCsv } = require("../xhs-browser.js");

/**
 * Input interface for GetHomeFeedsTool
 */
interface GetHomeFeedsInput {
  count: number;
  category: string;
  download: boolean;
}

/**
 * Tool for retrieving recommended notes list from Xiaohongshu website homepage
 * Supports various categories including fashion, food, makeup, movies, career, etc.
 */
class GetHomeFeedsTool extends MCPTool<GetHomeFeedsInput> {
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

  /**
   * Executes the tool to fetch home feeds from Xiaohongshu
   * @param input - The input parameters containing count, category, and download preference
   * @returns Promise<string> - CSV data or download confirmation message
   */
  async execute(input: GetHomeFeedsInput): Promise<string> {
    const { count, category, download } = input;

    // Validate input parameters
    if (count <= 0 || count > 1000) {
      return 'Error: Count must be between 1 and 1000';
    }

    try {
      let cursor_score = '';
      let note_index = 0;
      let loaded_count = 0; // Total number of items loaded
      let results_all: any[] = []; // Cache for results
      let retryCount = 0;
      const MAX_RETRIES = 3;

      while (loaded_count < count && retryCount < MAX_RETRIES) {
        try {
          const response = await this.fetchHomeFeedBatch(cursor_score, note_index, category);
          
          // Process the response items
          if (response?.items && Array.isArray(response.items)) {
            response.items.forEach((item: any) => {
              if (loaded_count >= count) return;
              results_all.push(item);
              loaded_count++;
            });

            // Update pagination parameters
            cursor_score = response.cursor_score || '';
            note_index = response.items.length;
            
            // Add delay between requests to avoid rate limiting
            await sleep(2);
            
            // Reset retry count on successful request
            retryCount = 0;
          } else {
            throw new Error('Invalid response format');
          }

          // Break if we've loaded enough items
          if (loaded_count >= count) break;
          
        } catch (error) {
          retryCount++;
          console.error(`Request failed (attempt ${retryCount}/${MAX_RETRIES}):`, error);
          
          if (retryCount >= MAX_RETRIES) {
            break;
          }
          
          // Exponential backoff for retries
          await sleep(Math.pow(2, retryCount) * 1000);
        }
      }

      // Convert results to CSV format
      const result_csv = this.convertToCSV(results_all);
      
      if (download) {
        return this.handleDownload(category, count, result_csv, results_all.length);
      }
      
      return result_csv;
      
    } catch (error: any) {
      console.error('Failed to fetch home feeds:', error);
      return `Failed to retrieve data list! Error: ${error.message || 'Unknown error'}`;
    }
  }

  /**
   * Fetches a batch of home feed items from the API
   * @param cursor_score - Pagination cursor score
   * @param note_index - Current note index for pagination
   * @param category - Category ID for filtering
   * @returns Promise<any> - API response containing items and pagination info
   */
  private async fetchHomeFeedBatch(cursor_score: string, note_index: number, category: string): Promise<any> {
    const requestPayload = {
      cursor_score,
      num: 27,
      refresh_type: 1,
      note_index,
      unread_begin_note_id: "",
      unread_end_note_id: "",
      unread_note_count: 0,
      category,
      search_key: "",
      need_num: 12,
      image_formats: ["jpg", "webp", "avif"],
      need_filter_image: false
    };

    return await httpPost("/api/sns/web/v1/homefeed", requestPayload);
  }

  /**
   * Converts JSON data to CSV format with predefined field mappings
   * @param data - Array of JSON objects to convert
   * @returns string - CSV formatted data
   */
  private convertToCSV(data: any[]): string {
    const fieldMappings = [
      'note_id@id',
      'xsec_token@xsecToken',
      'note_type@noteCard.type',
      'title@noteCard.displayTitle',
      'liked_count@noteCard.interactInfo.likedCount',
      'cover@noteCard.cover.urlPre',
      'user_id@noteCard.user.userId',
      'user_name@noteCard.user.nickname',
      'user_xsec_token@noteCard.user.xsecToken'
    ];

    return jsonToCsv(data, fieldMappings);
  }

  /**
   * Handles file download functionality
   * @param category - Category ID used for filename
   * @param count - Number of items for filename
   * @param csvData - CSV data to be downloaded
   * @param actualCount - Actual number of items retrieved
   * @returns string - Download result message
   */
  private handleDownload(category: string, count: number, csvData: string, actualCount: number): string {
    const fileName = `${category}_${count}_${Date.now()}.csv`;
    const downloadResult = downloadCsvData(fileName, csvData);
    
    if (downloadResult?.error) {
      return `Data save failed: ${downloadResult.error}`;
    }
    
    return `Data saved successfully. Count: ${actualCount}. File: ${downloadResult.link}`;
  }
}

module.exports = GetHomeFeedsTool;