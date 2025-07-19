// Library imports
import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";

// Local imports
const { httpPost, jsonToCsv, sleep, downloadCsvData } = require("../xhs-browser.js");

/**
 * Generates a unique search ID for Xiaohongshu search requests
 * @returns {string} - Unique search identifier
 */
const createSearchId = (): string => {
  /**
   * Creates a timestamp string padded to 13 characters
   * @returns {string} - Formatted timestamp
   */
  const generateTimestamp = (): string => {
    let timestamp = new Date().getTime().toString();
    if (timestamp.length < 13) {
      timestamp = timestamp.padEnd(13, "0");
    }
    return timestamp;
  };

  /**
   * Generates a unique identifier using BigInt operations
   * @returns {string} - Base36 encoded unique ID
   */
  const generateUniqueId = (): string => {
    const timestamp = BigInt(generateTimestamp());
    const randomComponent = BigInt(Math.ceil(2147483646 * Math.random()));
    const shiftedTimestamp = timestamp << BigInt(64);
    return (shiftedTimestamp + randomComponent).toString(36);
  };

  return generateUniqueId();
};

/**
 * Input interface for SearchNotesTool
 */
interface SearchNotesInput {
  keyword: string;
  count: number;
  sort: 'general' | 'time_descending' | 'popularity_descending';
  noteType: 0 | 1 | 2; // 0 = all, 1 = video, 2 = image and text
  download: boolean;
}

/**
 * Tool for searching Xiaohongshu notes based on keywords
 * Provides comprehensive search functionality with filtering and sorting options
 */
class SearchNotesTool extends MCPTool<SearchNotesInput> {
  name = "search_notes";
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
      type: z.union([z.literal(0), z.literal(1), z.literal(2)]),
      default: 0,
      description: 'Type of notes to search for'
    },
    download: {
      type: z.boolean(),
      description: 'Whether to export data as a file. If the user specifically requests a download, set to true, otherwise default is false',
      default: false
    }
  };

  /**
   * Executes the search operation for Xiaohongshu notes
   * @param input - Search parameters including keyword, count, sort, noteType, and download
   * @returns Promise<string> - CSV data or download confirmation message
   */
  async execute(input: SearchNotesInput): Promise<string> {
    const { keyword, count, sort, noteType, download } = input;
    
    // Input validation
    if (!keyword || typeof keyword !== 'string' || keyword.trim().length === 0) {
      return JSON.stringify({
        error: true,
        message: 'Invalid keyword: Must be a non-empty string'
      });
    }
    
    if (count <= 0 || count > 1000) {
      return JSON.stringify({
        error: true,
        message: 'Invalid count: Must be between 1 and 1000'
      });
    }

    try {
      const searchId = createSearchId();
      let loadedCount = 0;
      let currentPage = 1;
      const resultsAll: any[] = [];
      
      while (loadedCount < count) {
        try {
          const searchResponse = await httpPost('/api/sns/web/v1/search/notes', {
            "keyword": keyword,
            "page": currentPage,
            "page_size": 20,
            "search_id": searchId,
            "sort": sort,
            "note_type": noteType,
            "ext_flags": [],
            "filters": [
              {
                "tags": ["general"],
                "type": "sort_type"
              },
              {
                "tags": ["不限"],
                "type": "filter_note_type"
              },
              {
                "tags": ["不限"],
                "type": "filter_note_time"
              },
              {
                "tags": ["不限"],
                "type": "filter_note_range"
              },
              {
                "tags": ["不限"],
                "type": "filter_pos_distance"
              }
            ],
            "geo": "",
            "image_formats": ["jpg", "webp", "avif"]
          });
          
          // Process search results
          if (searchResponse && searchResponse.items && Array.isArray(searchResponse.items)) {
            searchResponse.items.forEach((item: any) => {
              if (loadedCount >= count) return;
              // Filter only note items
              if (item.modelType !== 'note') return;
              resultsAll.push(item);
              loadedCount++;
            });
          }
          
          if (loadedCount >= count) break;
          currentPage++;
          await sleep(2); // Rate limiting
        } catch (searchError) {
          const errorMessage = searchError instanceof Error ? searchError.message : 'Unknown search error';
          console.error('Search page error:', errorMessage);
          break;
        }
      }

      // Convert results to CSV format
      const resultCsv = jsonToCsv(resultsAll, [
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
        const fileName = `search_notes_${encodeURIComponent(keyword)}_${count}_${Date.now()}.csv`;
        const downloadResult = downloadCsvData(fileName, resultCsv);
        
        if (downloadResult.error) {
          return JSON.stringify({
            error: true,
            message: `Failed to save data: ${downloadResult.error}`
          });
        }
        
        return JSON.stringify({
          success: true,
          message: 'Data saved successfully',
          count: resultsAll.length,
          filename: fileName,
          link: downloadResult.link
        });
      }
      
      return JSON.stringify(resultsAll);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      console.error('SearchNotesTool error:', errorMessage);
      
      return JSON.stringify({
        error: true,
        message: `Failed to search notes: ${errorMessage}`,
        timestamp: new Date().toISOString()
      });
    }
  }
}

module.exports = SearchNotesTool;