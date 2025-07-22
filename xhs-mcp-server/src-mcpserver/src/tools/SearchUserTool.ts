import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";

// Local imports
const { httpPost, sleep, downloadCsvData, jsonToCsv } = require("../xhs-browser.js");

/**
 * Creates a unique search identifier for API requests
 * @returns {string} A base36 encoded timestamp-based identifier
 */
const createSearchId = (): string => {
  /**
   * Generates a padded timestamp string
   * @returns {string} 13-character timestamp string
   */
  const generateTimestamp = (): string => {
    let timestamp = new Date().getTime().toString();
    if (timestamp.length < 13) {
      timestamp = timestamp.padEnd(13, "0");
    }
    return timestamp;
  };

  /**
   * Creates a combined timestamp and random number as BigInt
   * @returns {string} Base36 encoded identifier
   */
  const generateUniqueId = (): string => {
    const timestamp = BigInt(generateTimestamp());
    const randomValue = BigInt(Math.ceil(2147483646 * Math.random()));
    const combined = (timestamp << BigInt(64)) + randomValue;
    return combined.toString(36);
  };

  return generateUniqueId();
};

/**
 * Interface for SearchUserTool input parameters
 */
interface SearchUserInput {
  keyword: string;
  count: number;
  download: boolean;
}

/**
 * Tool for searching Xiaohongshu users based on keywords
 * Implements security measures and proper error handling
 */
class SearchUserTool extends MCPTool<SearchUserInput> {
  name = "Search Xiaohongshu Users";
  description = "Search for specific users based on keywords. The returned data may include multiple results, which can be filtered by criteria such as verification status or follower count to help users select an appropriate account. If there are multiple similar results, please remind the user to choose one. The xsec_token in the returned data is very important and may need to be passed to the next tool call";

  schema = {
    keyword: {
      type: z.string().min(1).max(100), // Input validation for security
      description: 'Keyword for the username to search'
    },
    count: {
      type: z.number().int().min(1).max(50), // Limit count to prevent abuse
      default: 5,
      description: 'The amount of data to be retrieved, default is 5'
    },
    download: {
      type: z.boolean(),
      description: 'Whether to download and export data as a file. If the user specifically requests a download, it will be true, otherwise, the default is false',
      default: false
    }
  };

  /**
   * Executes the user search functionality
   * @param input - Search parameters including keyword, count, and download flag
   * @returns CSV data or download result
   */
  async execute(input: SearchUserInput): Promise<string> {
    // Input validation and sanitization
    const { keyword, count, download } = input;
    
    // Sanitize keyword to prevent injection attacks
    const sanitizedKeyword = keyword.trim().replace(/[<>]/g, '');
    
    if (!sanitizedKeyword) {
      return 'Error: Invalid keyword provided';
    }

    try {
      const searchId = createSearchId();
      let currentPage = 1;
      const pageSize = 20;
      const allResults: any[] = [];
      let loadedCount = 0;

      // Pagination loop with proper error handling
      while (loadedCount < count) {
        try {
          // Generate secure request ID
          const requestId = Math.random().toString(36).substring(2, 15) + 
                          Math.random().toString(36).substring(2, 15);
          
          const response = await httpPost('/api/sns/web/v1/search/usersearch', {
            "search_user_request": {
              "keyword": sanitizedKeyword,
              "search_id": searchId,
              "page": currentPage,
              "page_size": pageSize,
              "biz_type": "web_search_user",
              "request_id": requestId
            }
          });

          // Validate API response
          if (!response?.result?.success) {
            throw new Error(`API Error: ${JSON.stringify(response?.result || response)}`);
          }

          // Process user data safely
          if (response.users && Array.isArray(response.users)) {
            for (const user of response.users) {
              if (loadedCount >= count) break;
              
              // Validate user data structure
              if (user && typeof user === 'object') {
                allResults.push(user);
                loadedCount++;
              }
            }
          }

          if (loadedCount >= count) break;
          
          currentPage++;
          
          // Rate limiting to prevent overwhelming the API
          await sleep(Math.max(2, Math.random() * 2 + 1));
          
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
          return `Failed to search user data: ${errorMessage}`;
        }
      }

      // Generate CSV output with proper field mapping
      const csvData = jsonToCsv(allResults, [
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
        // Generate secure filename
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const fileName = `search_users_${encodeURIComponent(sanitizedKeyword)}_${count}_${timestamp}.csv`;
        
        const downloadResult = downloadCsvData(fileName, csvData);
        
        if (downloadResult.error) {
          return `Failed to save data: ${downloadResult.error}`;
        }
        
        return `Data saved successfully. Count: ${allResults.length}. File: ${downloadResult.link}`;
      }

      return csvData;
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      return `Failed to search user data: ${errorMessage}`;
    }
  }
}

module.exports = SearchUserTool;