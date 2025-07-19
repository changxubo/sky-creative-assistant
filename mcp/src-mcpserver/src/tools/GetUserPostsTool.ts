import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";

const { httpGet, sleep, jsonToCsv, downloadCsvData } = require("../xhs-browser.js");

/**
 * Input interface for GetUserPostsTool
 */
interface GetUserPostsInput {
  user_id: string;
  count: number;
  xsec_token: string;
  download: boolean;
}

/**
 * Tool for retrieving user posts from Xiaohongshu platform
 * Handles pagination and data export functionality
 */
class GetUserPostsTool extends MCPTool<GetUserPostsInput> {
  name = "Get User Notes List";
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
    download: {
      type: z.boolean(),
      description: 'Whether to download and export data as a file. Set to true if the user explicitly requests a download, otherwise defaults to false.',
      default: false
    }
  };

  /**
   * Executes the user posts retrieval operation
   * @param input - The input parameters for fetching user posts
   * @returns Promise<string> - CSV data or download confirmation message
   */
  async execute(input: GetUserPostsInput): Promise<string> {
    const { user_id, count, xsec_token, download } = input;
    
    // Validate input parameters
    if (!user_id || user_id.length !== 24) {
      return 'Error: Invalid user_id. Must be 24 characters long.';
    }
    
    if (!xsec_token || xsec_token.trim() === '') {
      return 'Error: xsec_token is required and cannot be empty.';
    }
    
    const results: any[] = [];
    let cursor = '';
    
    try {
      // Paginate through all available posts
      while (true) {
        const apiUrl = `/api/sns/web/v1/user_posted?num=10&cursor=${cursor}&user_id=${user_id}&image_formats=jpg,webp,avif&xsec_token=${encodeURIComponent(xsec_token)}&xsec_source=pc_feed`;
        
        const response = await httpGet(apiUrl);
        
        // Check if response is valid
        if (!response || !response.notes || response.notes.length === 0) {
          break;
        }
        
        // Process each note in the response
        response.notes.forEach((note: any) => {
          if (count > 0 && results.length >= count) return;
          
          // Extract and structure note data
          results.push({
            note_id: note.noteId || '',
            title: note.displayTitle || '',
            type: note.type || '',
            user: {
              id: note.user?.userId || '',
              nick_name: note.user?.nickName || ''
            },
            xsec_token: note.xsecToken || '',
            liked_count: note.interactInfo?.likedCount || 0,
            cover: note.cover?.urlPre || ''
          });
        });
        
        // Check if there are more pages
        if (!response.hasMore) break;
        
        cursor = response.cursor || '';
        
        // Stop if we've reached the requested count
        if (count !== -1 && results.length >= count) break;
        
        // Add delay to prevent rate limiting
        await sleep(2);
      }
      
      // Convert results to CSV format
      const resultCsv = jsonToCsv(results, [
        'note_id', 'type', 'title', 'xsec_token', 'liked_count', 'cover', 
        'user_id@user.id', 'user_name@user.nick_name'
      ]);
      
      // Handle download request
      if (download) {
        const fileName = `user_posts_${user_id}_${count}_${Date.now()}.csv`;
        const downloadResult = downloadCsvData(fileName, resultCsv);
        
        if (downloadResult.error) {
          return `Failed to save data: ${downloadResult.error}`;
        }
        
        return `Data saved successfully. Count: ${results.length}. File: ${downloadResult.link}`;
      }
      
      return resultCsv;
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      return `Failed to retrieve user posts: ${errorMessage}`;
    }
  }
}

module.exports = GetUserPostsTool;