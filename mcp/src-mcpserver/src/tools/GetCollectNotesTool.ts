import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";

// Local imports
const { httpGet, sleep, jsonToCsv, downloadCsvData, getJoinedTest } = require("../xhs-browser.js");

/**
 * Input interface for GetCollectNotesTool
 */
interface GetCollectNotesInput {
  user_id: string;
  count: number;
  xsec_token: string;
  download: boolean;
}

/**
 * Tool for retrieving a user's collected notes from the platform
 * Handles pagination, data formatting, and optional file export
 */
class GetCollectNotesTool extends MCPTool<GetCollectNotesInput> {
  name = "Get User Collected Notes List";
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

  /**
   * Execute the tool to retrieve user's collected notes
   * @param input - The input parameters for the tool
   * @returns Promise<string> - CSV data or success/error message
   */
  async execute(input: GetCollectNotesInput): Promise<string> {
    const { user_id, count, xsec_token, download } = input;
    
    // Validate user_id format (24 characters)
    if (!user_id || user_id.length !== 24) {
      return 'Error: Invalid user_id format. Must be exactly 24 characters long.';
    }
    
    // Validate count parameter
    if (count === 0) {
      return 'Error: Count must be greater than 0 or -1 for all notes.';
    }
    
    const results: any[] = [];
    let cursor = '';
    let requestCount = 0;
    const maxRequests = 100; // Prevent infinite loops
    
    while (true) {
      // Safety check to prevent infinite loops
      if (requestCount >= maxRequests) {
        return `Error: Maximum request limit (${maxRequests}) reached. Please try with a smaller count.`;
      }
      
      try {
        // Construct API URL with proper encoding
        const apiUrl = `/api/sns/web/v2/note/collect/page?num=10&cursor=${cursor}&user_id=${user_id}&image_formats=jpg,webp,avif&xsec_token=${encodeURIComponent(xsec_token)}&xsec_source=pc_feed`;
        
        const res = await httpGet(apiUrl);
        requestCount++;
        
        // Check if response is valid
        if (!res || typeof res !== 'object') {
          return 'Error: Invalid response format received from API.';
        }
        
        // Check if notes exist in response
        if (!res['notes'] || !Array.isArray(res['notes']) || res['notes'].length === 0) {
          break;
        }
        
        // Process notes data
        for (const note of res['notes']) {
          // Check if we've reached the desired count
          if (count > 0 && results.length >= count) {
            break;
          }
          
          // Validate note structure
          if (!note || !note['noteId'] || !note['user']) {
            continue; // Skip invalid notes
          }
          
          results.push({
            note_id: note['noteId'],
            title: note['displayTitle'] || 'Untitled',
            type: note['type'] || 'unknown',
            user: {
              id: note['user']['userId'] || 'unknown',
              nick_name: note['user']['nickName'] || 'Unknown User'
            },
            xsec_token: note['xsecToken'] || '',
            liked_count: note['interactInfo']?.['likedCount'] || 0,
            cover: note['cover']?.['urlPre'] || ''
          });
        }
        
        // Check if there are more pages
        if (!res['hasMore']) {
          break;
        }
        
        cursor = res['cursor'] || '';
        
      } catch (error) {
        // Enhanced error handling with more specific messages
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        return `Failed to retrieve data: ${errorMessage}. Please check your xsec_token and user_id.`;
      }
      
      // Break if we've reached the desired count
      if (count !== -1 && results.length >= count) {
        break;
      }
      
      // Add delay to prevent rate limiting
      await sleep(2);
    }
    
    // Handle empty results
    if (results.length === 0) {
      return 'No collected notes found for this user.';
    }
    
    try {
      // Convert results to CSV format
      const result_csv = jsonToCsv(results, [
        'note_id', 'type', 'title', 'xsec_token', 'liked_count', 'cover', 
        'user_id@user.id', 'user_name@user.nick_name'
      ]);
      
      // Handle file download if requested
      if (download) {
        const fileName = `user_collected_notes_${user_id}_${count}_${Date.now()}.csv`;
        const download_result = downloadCsvData(fileName, result_csv);
        
        if (download_result['error']) {
          return `Failed to save data: ${download_result['error']}`;
        }
        
        return `Data saved successfully. Count: ${results.length}. File: ${download_result.link}`;
      }
      
      return result_csv;
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      return `Failed to process data: ${errorMessage}`;
    }
  }
}

module.exports = GetCollectNotesTool;